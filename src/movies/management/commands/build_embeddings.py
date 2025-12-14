import json
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from openai import OpenAI

from core.settings import env
from movies.models import MotnShow

SYSTEM_PROMPT = """
You generate normalized textual fields for movie/series recommendation embeddings.

## Goal

You receive a single input string describing one show (movie or series).  
From this string, you must produce a JSON object with 4 string fields:

- plot_embedding_text
- meta_embedding_text
- tone_embedding_text
- tags_embedding_text

These texts will be embedded and used for semantic search and recommendations.

## Input format (embedding_text)

The input is a single English string constructed from a database record.  
It follows this general pattern (not all parts are always present):

- "Title (Year) - <type>" OR "Title - <type>"
- Optionally: "Also known as: <original_title>"
- Optionally: "Genres: <genre1>, <genre2>, ..."
- Optionally: "Countries: <country1>, <country2>, ..."
- Optionally: "Language: <language_code>"
- Optionally: "Age rating: <certification>"
- Optionally: "Starring: <actor1>, <actor2>, ..."
- Optionally: "Directed by: <director1>, <director2>, ..."
- Optionally: "Keywords: <tag1>, <tag2>, ..."
- Optionally: "Plot: <overview text>"

All of this is concatenated into one string, typically with ". " separators.

The input string is authoritative for this show. If a field is missing, you must treat it as unknown.

## Allowed data sources and truthfulness

You may use:

1. The input string itself.
2. Your own stable factual knowledge and trusted external sources.
3. Simple logical inferences.

However, you must obey these rules:

- Do NOT include any information that could be false.
- Only add facts from memory or external sources when you are **absolutely certain** they are correct for this specific show.
- If there is any doubt about a fact (plot details, themes, tone, tags, etc.), omit it.
- It is better to under-describe the show than to include even partially incorrect information.
- If the title is ambiguous and you are not sure which work it refers to, rely ONLY on the input string.

## Output format

Return ONLY a single JSON object with these 4 keys:

- "plot_embedding_text"
- "meta_embedding_text"
- "tone_embedding_text"
- "tags_embedding_text"

Each value MUST be a string.  
If you cannot safely populate a field, set it to the empty string "".

Do not wrap the JSON in backticks or any extra text.

## Field-specific instructions

### 1. plot_embedding_text

Purpose: a clean, normalized plot/summary optimized for semantic search.

Rules:
- Language: English.
- Length: roughly 80–200 words.
- Use:
  - the part after "Plot:" from the input string, if present,
  - any **certain** external knowledge about the plot for this exact show,
  - obvious inferences from the genres or keywords.
- You may:
  - rewrite and reorganize the plot text,
  - expand slightly with missing but **certain** details,
  - remove noisy phrasing.
- You must NOT:
  - invent characters, events, or settings you are not sure about,
  - contradict the plot text in the input string.
- Focus on:
  - main situation and conflict,
  - central characters and their relationships,
  - key themes and stakes, only when certain.
- Do NOT mention:
  - actors, directors, ratings, streaming platforms,
  - subjective quality judgments (“masterpiece”, “underrated”).

If there is no plot text and you are not certain of any external plot details, set this field to "".

### 2. meta_embedding_text

Purpose: rich metadata for semantic search, answering "what kind of thing is this", "where is it from", "who made it".

Rules:
- Language: English.
- Length: roughly 40–100 words.
- Structure: formatted to clearly present key identifying facts.
- **Content Priorities** (include if available in input or certainly known):
  - Title and Year.
  - Show Type (Movie / Series).
  - Original Language and Countries.
  - Full list of Genres.
  - Key Tags/Keywords.
  - Main Cast (up to ~5 top names).
  - Directors.
- Format style preference (concise but complete):
  "[Title] ([Year]) - [Type].
   Original language: [Language]. Countries: [Countries].
   Genres: [Genre list]. Tags: [Tag list].
   Starring: [Cast list]. Directed by: [Director list]."
- Do NOT guess. If a field like "Directed by" is missing and you don't know it, omit that specific part.

If you cannot say anything beyond trivial restatement of the title without guessing, you may keep this short, or set it to "" if nothing reliable is available.

### 3. tone_embedding_text

Purpose: a short description of mood/tone, including tone that you reliably know from external knowledge.

Rules:
- Language: English.
- Length: 1–2 short sentences or a comma-separated list, maximum ~30 words.
- Derive tone from:
  - tone-like words in the plot text or keywords (e.g. “dark”, “lighthearted”, “tragic”, “suspenseful”, “satirical”),
  - strongly tone-implying genres (e.g. Horror → horror tone, Comedy → comedic tone),
  - any **certain** knowledge you have about this show’s mood.
- Express tone as concise descriptors, for example:
  - "dark, violent, and suspenseful crime drama"
  - "lighthearted, romantic, and family-friendly"

If you are not confident about the tone, set this field to "".

### 4. tags_embedding_text

Purpose: a normalized, embedding-friendly set of tags/keywords and themes.

Rules:
- Language: English.
- Length: about 10–60 words.
- Use:
  - the part after "Keywords:" (tags/keywords) from the input string, cleaned and de-duplicated,
  - clear keyword phrases from the plot text,
  - any themes, settings, or topics you are **certain** about from external knowledge (e.g. “time travel”, “high school”, “post-apocalyptic”, “organized crime”).
- Tags should be short noun phrases or adjectives that describe:
  - themes (e.g. "family conflict", "revenge"),
  - settings (e.g. "small town", "outer space"),
  - topics (e.g. "drug trade", "political intrigue"),
  - narrative elements (e.g. "coming of age", "serial killer").
- Do NOT include:
  - subjective quality judgments (“critically acclaimed”, “overrated”),
  - platform-specific labels or IDs.
- **Critical**: If the show is a documentary (based on genre, type, or plot), YOU MUST include "documentary" as a tag.

If there are no keywords and you cannot confidently derive tags from plot/external knowledge, set this field to "".

## General style guidelines

- Always write in neutral, descriptive language.
- Do not mention ratings, popularity, or quality.
- Do not mention external services (Netflix, IMDb, TMDb, etc.).
- Do not address the reader; just describe the show.
- When in doubt about correctness, leave the questionable detail out.

## Final requirement

Return ONLY a valid JSON object with exactly these 4 keys:

"plot_embedding_text",
"meta_embedding_text",
"tone_embedding_text",
"tags_embedding_text"

No extra keys, no comments, no surrounding text.
"""


class Command(BaseCommand):
    help = "Compute embeddings for titles using GPT-4o-mini for text generation and then embedding backend"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--backend",
            choices=["sentence-transformer", "openai"],
            default="openai",
            help="Embedding backend to use.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of records to embed.",
        )
        parser.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Offset for batching through the queryset.",
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=10,
            help="Number of concurrent workers for text generation (default: 10).",
        )

    def handle(self, *args, **options):
        backend = options["backend"]
        limit = options["limit"]
        offset = options["offset"]
        workers = options["workers"]

        # Prefetch genres so embedding_text access is efficient
        qs = MotnShow.objects.exclude(overview="").filter(embedding__isnull=True).prefetch_related("genres")[offset:]
        if limit is not None:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(f"Computing generated embeddings for {total} titles using backend={backend} with {workers} workers")

        if backend == "openai":
            embed_fn = self._embed_with_openai
        else:
            embed_fn = self._embed_with_sentence_transformer

        # We process in small batches because we generate text with GPT (slow-ish)
        # then embed in bulk.
        batch_size = 100
        self.openai_client = OpenAI()

        for start in range(0, total, batch_size):
            batch = list(qs[start : start + batch_size])
            
            # 1. Generate text fields using GPT-4o-mini in parallel
            self.stdout.write(f"Generating text for batch {start}-{start+len(batch)}...")
            with ThreadPoolExecutor(max_workers=workers) as executor:
                # Returns list of (obj, dict) tuple or None
                results = list(executor.map(self._generate_text_fields, batch))
            
            # Filter out failures
            valid_results = [r for r in results if r is not None]

            if not valid_results:
                continue

            # 2. Prepare for embedding
            # We need 8 embeddings per object: Main, Plot, Meta, Tone, Tags, Genre, Cast, Language
            all_texts_flat = []
            for obj, text_data in valid_results:
                plot = text_data.get("plot_embedding_text", "")
                meta = text_data.get("meta_embedding_text", "")
                tone = text_data.get("tone_embedding_text", "")
                tags = text_data.get("tags_embedding_text", "")
                
                # Main embedding is a combination of all GPT generated fields
                main = f"{plot} {meta} {tone} {tags}".strip()
                
                # Genre (Direct from DB)
                genre_names = [g.name for g in obj.genres.all()]
                genre_text = ", ".join(genre_names)

                # Cast (Direct from DB)
                # obj.cast can be list of strings or list of dicts
                cast_names = []
                if obj.cast:
                    for item in obj.cast:
                        if isinstance(item, str):
                            cast_names.append(item)
                        elif isinstance(item, dict):
                            # Try common keys
                            for key in ("name", "title", "full_name"):
                                if key in item and item[key]:
                                    cast_names.append(str(item[key]))
                                    break
                cast_text = ", ".join(cast_names)

                # Language (Direct from DB)
                parts_lang = []
                if obj.original_language:
                    parts_lang.append(f"Language: {obj.original_language}")
                if obj.countries:
                    parts_lang.append("Countries: " + ", ".join([str(c) for c in obj.countries]))
                language_text = ". ".join(parts_lang)

                # Order: Main, Plot, Meta, Tone, Tags, Genre, Cast, Language
                # OpenAI API cannot embed empty strings. Replace with " " if empty.
                normalized_texts = [
                    t if t and t.strip() else " " 
                    for t in [main, plot, meta, tone, tags, genre_text, cast_text, language_text]
                ]
                all_texts_flat.extend(normalized_texts)

            # 3. Embed
            if not all_texts_flat:
                continue

            embeddings_flat = embed_fn(all_texts_flat)

            # 4. Save
            for i, (obj, _) in enumerate(valid_results):
                base_idx = i * 8
                
                obj.embedding = embeddings_flat[base_idx]
                obj.plot_embedding = embeddings_flat[base_idx + 1]
                obj.meta_embedding = embeddings_flat[base_idx + 2]
                obj.tone_embedding = embeddings_flat[base_idx + 3]
                obj.tags_embedding = embeddings_flat[base_idx + 4]
                obj.genre_embedding = embeddings_flat[base_idx + 5]
                obj.cast_embedding = embeddings_flat[base_idx + 6]
                obj.language_embedding = embeddings_flat[base_idx + 7]
                
                # Save the generated text data for future reference/debugging
                obj.generated_embedding_texts = valid_results[i][1]

                obj.save(update_fields=[
                    "embedding", 
                    "plot_embedding", 
                    "meta_embedding", 
                    "tone_embedding",
                    "tags_embedding",
                    "genre_embedding",
                    "cast_embedding",
                    "language_embedding",
                    "generated_embedding_texts",
                ])

            self.stdout.write(f"Processed {start + len(batch)}/{total}")

    def _generate_text_fields(self, obj: MotnShow) -> tuple[MotnShow, dict] | None:
        """
        Calls GPT-4o-mini to generate embedding texts.
        Returns (obj, data_dict) or None on failure.
        """
        input_text = obj.embedding_text
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT.strip()},
                    {"role": "user", "content": input_text},
                ],
                response_format={"type": "json_object"},
                temperature=0.3, # Low temperature for stability
            )
            content = response.choices[0].message.content
            if not content:
                return None
            data = json.loads(content)
            return (obj, data)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error generating text for {obj}: {e}"))
            return None

    def _embed_with_sentence_transformer(self, texts: Iterable[str]):
        if not hasattr(self, "_st_model"):
            from sentence_transformers import SentenceTransformer

            self._st_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")

        embeddings = self._st_model.encode(list(texts), normalize_embeddings=True)
        padded = []
        for emb in embeddings:
            emb_list = emb.tolist()
            # pad to target dimension for storage compatibility
            if len(emb_list) < settings.OPENAI_EMBEDDING_DIM:
                emb_list = emb_list + [0.0] * (settings.OPENAI_EMBEDDING_DIM - len(emb_list))
            padded.append(emb_list)
        return padded

    def _embed_with_openai(self, texts: Iterable[str]):
        # Batching for embedding API is handled by user of this method or we can chunk here.
        # But we are passing ~20 * 5 = 100 texts, which is fine for one call.
        response = self.openai_client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=list(texts),
        )
        return [item.embedding for item in response.data]
