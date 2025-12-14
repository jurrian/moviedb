import json

import mlflow
from django.conf import settings
from django.db.models import F, Value
from django.db.models.functions import Coalesce
from openai import OpenAI
from pgvector.django import CosineDistance

from core.settings import env
from misc.utils.embedding import combine_query_and_user, get_user_embedding

from .models import MotnGenre, MotnShow, UserRecommendation, UserViewInteraction

SYSTEM_PROMPT = """
You are a query parser for a movie/series recommender.

You receive a short English request and output **only one JSON object**:

{
  "intent": "find_tv_series" | "find_movie" | "find_any",
  "must_genres": [string],
  "should_genres": [string],
  "exclude_genres": [string],
  "must_be_series": boolean,
  "must_be_movie": boolean,
  "min_year": number | null,
  "max_year": number | null,
  "tone": [string],
  "keywords": [string],
  "cast": [string],
  "language": string | null,
  "embedding_query_text": string,
  "weights": {
    "plot": number,
    "meta": number,
    "tone": number,
    "tags": number,
    "genre": number,
    "cast": number,
    "language": number
  }
}

Constraints:
- Only use genres listed inside <available_genres> for must_genres, should_genres, exclude_genres.
- Infer preference for series/movie:
  - explicit request → set must_be_series or must_be_movie true.
  - no preference → both false.
- "intent":
  - explicit series → "find_tv_series"
  - explicit movie → "find_movie"
  - unclear → "find_any"
- Infer must_genres and should_genres from wording.
- Infer exclude_genres from implicit conflicts.
- Detect tone (e.g., dark, gritty, violent, comedic) and include in "tone".
- Extract non-genre topical keywords to "keywords".
- Extract specific actors/directors to "cast".
  - Extract year constraints if given; else null.
- embedding_query_text: short natural-language summary including format (movie/series) and tone if relevant.
- "weights":
  - Assign a float between 0.0 and 1.0 for each key.
  - **CRITICAL**: Use 0.0 or 0.1 for fields that are NOT relevant or NOT mentioned. We want sparse, high-signal weights.
  - "cast": High (0.8-1.0) ONLY if specific actors/directors are named. Otherwise 0.0.
  - "language": High (0.8-1.0) if language/country is explicit ("French", "American", "Bollywood"). Low (0.0) if implied only by genre ("Western" does NOT imply language unless "American Western" is said).
  - "genre": High (0.7-1.0) if genres are explicitly named.
  - "plot": High (0.6-1.0) if specific story elements/events are described.
  - "tone": High (0.6-1.0) if mood adjectives are used ("dark", "funny").
  - "meta": High (0.7-1.0) if decade/year/award-status is central.
  - "tags": High (0.7-1.0) for niche keywords not covered by genre.
  - "main": Always present, but other weights modulate the ranking.

Example: "modern western"
-> genre: 0.9, language: 0.1 (not explicit), plot: 0.3, cast: 0.0.

Example: "modern American western"
-> genre: 0.9, language: 0.8 (explicit "American"), plot: 0.3, cast: 0.0.

Output rules:
- Only valid JSON.
- No text outside the JSON.
- No genres outside those in <available_genres>.
"""


def get_openai_client():
    return OpenAI()


@mlflow.trace
def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of valid strings using the OpenAI API.
    Replaces empty/None strings with a single space to avoid API errors.
    """
    client = get_openai_client()
    # Sanitize inputs
    sanitized = [t if t and t.strip() else " " for t in texts]
    response = client.embeddings.create(model=settings.OPENAI_EMBEDDING_MODEL, input=sanitized)
    return [item.embedding for item in response.data]


def parse_user_query(raw_query: str) -> dict:
    client = get_openai_client()
    available_genres = ",".join([x.name for x in MotnGenre.objects.all().order_by("name")])
    prompt = SYSTEM_PROMPT + f"<available_genres>{available_genres}</available_genres>"

    model = "gpt-4o-mini"
    
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": raw_query},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        content = resp.choices[0].message.content
        return json.loads(content)
    except Exception:
        # Fallback if parsing fails
        return {}


def _clean_genre_list(genres):
    cleaned = []
    for g in genres or []:
        if g is None:
            continue
        name = str(g).strip()
        if name:
            cleaned.append(name)
    return cleaned


def build_base_queryset(structured: dict):
    qs = MotnShow.objects.all()

    # # must_be_series / must_be_movie
    # if structured.get("must_be_series"):
    #     qs = qs.filter(show_type__iexact="series")
    # elif structured.get("must_be_movie"):
    #     qs = qs.filter(show_type__iexact="movie")
    #
    # # hard genre includes/excludes (MotnGenre M2M)
    # for genre in _clean_genre_list(structured.get("must_genres")):
    #     qs = qs.filter(genres__name__iexact=genre)
    #
    # # should_genres = _clean_genre_list(structured.get("should_genres"))
    # # if should_genres:
    # #     qs = qs.filter(genres__name__in=should_genres)
    #
    # for genre in _clean_genre_list(structured.get("exclude_genres")):
    #     qs = qs.exclude(genres__name__iexact=genre)
    #
    # # optional: min_year / max_year
    # min_year = structured.get("min_year")
    # max_year = structured.get("max_year")
    # if min_year:
    #     qs = qs.filter(year__gte=min_year)
    # if max_year:
    #     qs = qs.filter(year__lte=max_year)
    return qs.distinct()


@mlflow.trace
def search_shows(raw_query: str, top_k: int = 20, user=None, alpha: float = 0.5, user_embedding=None):
    # 1. Parse Query
    structured = parse_user_query(raw_query)
    
    # 2. Extract weights
    parsed_weights = structured.get("weights", {})
    # primary_key removed; we always use 'main'/embedding for retrieval now.
    
    w_main = 0.5 
    w_plot = parsed_weights.get("plot", 0.5)
    w_meta = parsed_weights.get("meta", 0.5)
    w_tone = parsed_weights.get("tone", 0.5)
    w_tags = parsed_weights.get("tags", 0.5)
    w_genre = parsed_weights.get("genre", 0.5)
    w_cast = parsed_weights.get("cast", 0.5)
    w_language = parsed_weights.get("language", 0.5)

    # 3. Construct specialized query strings
    # Main
    q_main_text = structured.get("embedding_query_text") or raw_query
     # Plot
    q_plot_text = raw_query
    # Tone
    tone_tokens = structured.get("tone") or []
    q_tone_text = " ".join(tone_tokens) if tone_tokens else raw_query
    # Tags
    tag_tokens = structured.get("keywords") or []
    q_tags_text = " ".join(tag_tokens) if tag_tokens else raw_query
    # Meta
    parts_meta = []
    if structured.get("min_year"): parts_meta.append(str(structured["min_year"]))
    if structured.get("intent") == "find_movie": parts_meta.append("movie")
    elif structured.get("intent") == "find_tv_series": parts_meta.append("series")
    q_meta_text = " ".join(parts_meta) if parts_meta else raw_query
    # Genres
    genres = structured.get("must_genres", []) + structured.get("should_genres", [])
    q_genre_text = " ".join(genres) if genres else raw_query
    # Cast
    cast_tokens = structured.get("cast") or []
    q_cast_text = " ".join(cast_tokens) if cast_tokens else " "
    # Language
    lang_token = structured.get("language")
    q_language_text = lang_token if lang_token else " " 

    # 4. Batch Embed
    # Order: [main, plot, meta, tone, tags, genre, cast, language]
    texts_to_embed = [
        q_main_text, 
        q_plot_text, 
        q_meta_text, 
        q_tone_text, 
        q_tags_text, 
        q_genre_text,
        q_cast_text,
        q_language_text
    ]
    
    embeddings = embed_texts(texts_to_embed)
    
    q_vec_main = embeddings[0]
    q_vec_plot = embeddings[1]
    q_vec_meta = embeddings[2]
    q_vec_tone = embeddings[3]
    q_vec_tags = embeddings[4]
    q_vec_genre = embeddings[5]
    q_vec_cast = embeddings[6]
    q_vec_language = embeddings[7]
    
    # Personalization: Only apply to the MAIN embedding vector for Stage 1 (if main is used)
    # AND for the final ranking.
    u_vec = user_embedding
    if u_vec is None and user is not None:
        u_vec = get_user_embedding(user)

    if u_vec is not None:
        q_vec_main = combine_query_and_user(q_vec_main, u_vec, alpha=alpha)

    # 5. Search Logic (Two-Stage)
    base_qs = build_base_queryset(structured)
    
    # Stage 1: Retrieve Candidates using MAIN embedding field
    # Fetch K candidates (e.g. 200)
    CANDIDATE_K = 200
    
    candidates = list(
        base_qs.exclude(embedding__isnull=True)
        .annotate(stage1_dist=CosineDistance("embedding", q_vec_main))
        .order_by("stage1_dist")
        .values_list("id", flat=True)[:CANDIDATE_K]
    )
    
    if not candidates:
        return [], structured

    # Stage 2: Rerank Candidates
    # Calculate full weighted score on the subset
    
    def dist_expr(field_name, vector):
        return Coalesce(CosineDistance(field_name, vector), Value(2.0))
        
    # We annotate individual distances first to expose them
    qs = MotnShow.objects.filter(id__in=candidates).annotate(
        dist_main=dist_expr("embedding", q_vec_main),
        dist_plot=dist_expr("plot_embedding", q_vec_plot),
        dist_meta=dist_expr("meta_embedding", q_vec_meta),
        dist_tone=dist_expr("tone_embedding", q_vec_tone),
        dist_tags=dist_expr("tags_embedding", q_vec_tags),
        dist_genre=dist_expr("genre_embedding", q_vec_genre),
        dist_cast=dist_expr("cast_embedding", q_vec_cast),
        dist_language=dist_expr("language_embedding", q_vec_language),
    )

    final_distance_expr = (F("dist_main") * w_main) + \
                          (F("dist_plot") * w_plot) + \
                          (F("dist_meta") * w_meta) + \
                          (F("dist_tone") * w_tone) + \
                          (F("dist_tags") * w_tags) + \
                          (F("dist_genre") * w_genre) + \
                          (F("dist_cast") * w_cast) + \
                          (F("dist_language") * w_language)
                          
    results = list(
        qs.annotate(weighted_distance=final_distance_expr)
        .order_by("weighted_distance")[:top_k]
    )

    # Log the query for analytics
    try:
        from .models import UserQueryLog
        
        log_user = user if (user and user.is_authenticated) else None
        result_ids = [r.id for r in results]
        
        UserQueryLog.objects.create(
            user=log_user,
            query=raw_query,
            top_k=top_k,
            result_ids=result_ids,
            result_metadata_dump={
                "structured": structured, 
                "alpha": alpha,
                "candidates": candidates,
                "weights_used": {
                    "main": w_main, "plot": w_plot, "meta": w_meta, 
                    "tone": w_tone, "tags": w_tags, "genre": w_genre,
                    "cast": w_cast, "language": w_language
                }
            },
        )
    except Exception as e:
        print(f"Error logging query: {e}")

    return results, structured


def analyze_search_result(raw_query: str, show_obj, structured: dict, component_dists: dict):
    """
    Debugs the search result by:
    1. Identifying the primary driver (lowest weighted distance).
    2. reconstructing the text used for that embedding.
    3. Checking for vector drift (staleness).
    4. Asking LLM to explain the semantic overlap.
    """
    from openai import OpenAI
    import numpy as np
    from pgvector.django import CosineDistance
    
    client = OpenAI()

    # 1. Identify Primary Driver
    # Calculate contribution: weight * distance
    # We want the lowest contribution (closest match that matters)
    drivers = []
    weights = structured.get("weights", {})
    
    for key, dist in component_dists.items():
        w = weights.get(key, 0.5)
        if w > 0.1: # Only consider relevant weights
            drivers.append((key, w, dist, w * dist))
    
    # Sort by contribution (score) ascending
    drivers.sort(key=lambda x: x[3])
    
    if not drivers:
        return "No significant drivers found (all weights low)."
        
    primary_key, primary_w, primary_dist, _ = drivers[0]
    
    # 2. Reconstruct Text
    doc_text = ""
    query_text = ""
    
    # Map key to show property
    text_map = {
        "plot": "plot_embedding_text",
        "cast": "embedding_text", # Fallback or specific if added later
        "genre": "embedding_text",
        "tone": "tone_embedding_text",
        "meta": "meta_embedding_text",
        "tags": "embedding_text",
        "main": "embedding_text",
        "language": "embedding_text"
    }
    
    prop = text_map.get(primary_key, "embedding_text")
    if hasattr(show_obj, prop):
        doc_text = getattr(show_obj, prop)
    else:
        doc_text = show_obj.embedding_text # Fallback
        
    # Determine Query Text used
    # unique to how we built the query vector. 
    # For now we use the main embedding query text or raw query as proxy for specific fields
    # ideally search.py should expose exactly what text was embedded
    query_text = structured.get("embedding_query_text", raw_query)
    
    # 3. Drift Check / Re-embed
    drift_msg = "N/A"
    try:
        resp = client.embeddings.create(input=doc_text, model=settings.OPENAI_EMBEDDING_MODEL, dimensions=settings.OPENAI_EMBEDDING_DIM)
        new_vec = resp.data[0].embedding
        
        # Get old vec
        # We need the vector from the DB. show_obj might have it loaded.
        # But VectorField in Django sometimes returns string or numpy.
        # Let's trust the distance passed in for now, but we can compare new_vec vs query_vec if we had it.
        # For this debug, let's just show the new text to the LLM.
        # Ideally we'd compare new_vec with show.embedding but let's keep it simple for now.
        pass
    except Exception as e:
        drift_msg = f"Error re-embedding: {e}"

    prompt = f"""
DEBUG TARGET: Why did "{show_obj.title}" match the query?

PRIMARY DRIVER: '{primary_key.upper()}' (Weight: {primary_w:.2f}, Dist: {primary_dist:.2f})

---
QUERY VECTOR TEXT (User Intent):
"{query_text}"

---
DOCUMENT VECTOR TEXT (DB Content):
"{doc_text}"

---
TASK:
1. Identify the specific phrases in BOTH texts that define their semantic similarity.
2. Explain if the match is caused by "true semantic alignment", "ambiguous query", or "misleading document text".
3. **Highlight** the specific driving phrases in your explanation using **bold**.

STYLE:
- Concise paragraph (3-4 sentences) analyzing the match, using **bold** for key phrases.
- Then, output exactly these two headers:

### Conclusion
[Correct Match / Incorrect Match]

### Reason
[Short diagnosis of the root cause, e.g. "True Semantic Alignment", "Vague Query", etc.]
"""

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful search analyst."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error analyzing result: {e}"


def update_user_recommendations(user):
    """
    Recalculates recommendations for the user based solely on their interactions.
    Saves the result to UserRecommendation model.
    """
    if not user.is_authenticated:
        return

    # 1. Get user embedding based on interactions
    u_vec = get_user_embedding(user)
    
    if not u_vec:
        # If no embedding (e.g. no history), clear recommendations
        UserRecommendation.objects.update_or_create(
             user=user,
             defaults={'recommended_shows': []}
        )
        return

    # 2. Find shows similar to this embedding
    # Exclude shows the user has already interacted with
    watched_ids = UserViewInteraction.objects.filter(user=user).values_list('show_id', flat=True)
    
    qs = MotnShow.objects.exclude(id__in=watched_ids).exclude(embedding__isnull=True)
    
    # We use the user vector directly for similarity search
    qs = qs.annotate(distance=CosineDistance("embedding", u_vec)).order_by("distance")[:50]
    
    recommended_ids = list(qs.values_list('id', flat=True))
    
    # 3. Save to UserRecommendation
    UserRecommendation.objects.update_or_create(
        user=user,
        defaults={'recommended_shows': recommended_ids}
    )
