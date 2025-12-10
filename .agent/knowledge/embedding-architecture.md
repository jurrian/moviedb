---
title: Embedding-Based Recommendation Architecture
category: technical-architecture
tags: [embeddings, cosine-similarity, machine-learning, vector-search]
created: 2025-12-07
---

# Embedding-Based Recommendation Architecture

## Core Technology: Embeddings

### What Are Embeddings?
Embeddings are dense vector representations of text that capture semantic meaning. Similar concepts have similar embeddings, allowing mathematical comparison of meaning.

### Why Embeddings for Recommendations?
Traditional recommendation systems rely on:
- Collaborative filtering (what similar users watched)
- Content-based filtering (genre, tags, etc.)

MovieDB uses **semantic embeddings** to enable:
- **Natural language understanding**: "King Alfred confronts vikings" → "Last Kingdom"
- **Deep content matching**: Beyond surface-level genre tags to actual plot themes
- **Taste profiling**: Mathematical representation of user preferences

## Three-Component Similarity System

### 1. Query Embedding
**Input**: User's natural language query
- Example: "I want to see a serie where King Alfred confronts the vikings"

**Process**: 
- Convert query text to embedding vector
- Captures semantic intent, themes, and context

**Output**: Dense vector representing query meaning

### 2. User Taste Embedding
**Input**: User's watch history and ratings
- Watched titles
- Like/dislike data from Netflix export

**Process**:
- Generate embeddings for all watched content
- Weight by user ratings (likes vs dislikes)
- Aggregate into a single "taste profile" embedding

**Output**: Dense vector representing user's preferences

### 3. Title Embeddings
**Input**: For each movie/series in the database
- Title
- Metadata (genre, cast, director, year, runtime, etc.)
- Plot summary/description

**Process**:
- Combine all metadata into rich text representation
- Convert to embedding vector
- Store for efficient retrieval

**Output**: Dense vector per title representing its content

## Cosine Similarity Scoring

### Mathematical Foundation
Cosine similarity measures the angle between two vectors:
```
similarity = (A · B) / (||A|| × ||B||)
```
- Range: -1 to 1 (typically 0 to 1 for text embeddings)
- Higher score = more similar meaning

### Recommendation Scoring
For each candidate title, calculate:

1. **Query Match Score**: 
   - `cosine_similarity(query_embedding, title_embedding)`
   - How well does this title match what the user asked for?

2. **Taste Match Score**:
   - `cosine_similarity(user_taste_embedding, title_embedding)`
   - How well does this title match the user's demonstrated preferences?

3. **Combined Score**:
   - Weighted combination of query match and taste match
   - Filters out already-watched titles
   - Filters for current availability on target service

### Ranking
- Sort all candidates by combined score (descending)
- Return top N recommendations
- Ensure diversity (avoid recommending 10 nearly-identical titles)

## Data Flow

```
User Query → Embedding Model → Query Vector
                                      ↓
User History → Taste Profile → User Vector
                                      ↓
                              Cosine Similarity ← Title Vectors (pre-computed)
                                      ↓
                              Ranked Recommendations
                                      ↓
                              Filter (availability, not watched)
                                      ↓
                              Top N Results
```

## Key Advantages

### 1. Semantic Understanding
- Understands meaning, not just keywords
- "epic battle" and "grand warfare" are semantically similar
- Can match themes even with different vocabulary

### 2. Cold Start Mitigation
- Can recommend based on query alone (no history needed)
- Taste profile improves recommendations but isn't required

### 3. Explainability
- Can show why a title was recommended
- Query match vs taste match scores
- Specific metadata that contributed to the match

### 4. Scalability
- Pre-compute title embeddings (one-time cost)
- Fast cosine similarity calculation
- Efficient vector search with proper indexing

### 5. Flexibility
- Easy to incorporate new metadata fields
- Can adjust weighting between query and taste
- Can add additional signals (popularity, recency, etc.)

## Implementation Considerations

### Embedding Model Selection
- Must capture semantic meaning well
- Should handle movie/entertainment domain vocabulary
- Balance between quality and inference speed

### User Taste Aggregation
- How to weight likes vs dislikes?
- How much history is needed for reliable taste profile?
- How to handle evolving tastes over time?

### Availability Filtering
- Must keep Netflix NL catalog up-to-date
- Efficient filtering before or after similarity calculation?
- Handle titles that come and go from the service

### Performance Optimization
- Pre-compute and cache title embeddings
- Use vector databases or approximate nearest neighbor search
- Batch processing for user taste updates

## Future Enhancements

### Multi-Vector Search
- Separate embeddings for different aspects (plot, mood, style)
- Allow users to weight different dimensions

### Hybrid Approaches
- Combine embedding similarity with collaborative filtering
- Incorporate popularity and trending signals
- Use metadata filters (year, runtime) as hard constraints

### Continuous Learning
- Update taste profile as user watches more content
- A/B test different embedding models and scoring functions
- Track recommendation acceptance rates to improve system
