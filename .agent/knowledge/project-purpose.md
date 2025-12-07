---
title: MovieDB Project Purpose
category: project-overview
tags: [recommendation-system, embeddings, netflix, machine-learning]
created: 2025-12-07
---

> **New Contributors: Start Here!** 👋  
> This document explains MovieDB's vision, goals, and technical approach. Understanding this will help you make meaningful contributions aligned with the project's mission.



# MovieDB Project Purpose

## Overview
MovieDB is an AI-powered movie and series recommendation system designed to provide highly personalized, context-aware recommendations based on comprehensive movie metadata and user preferences.

## Core Objective
The main purpose is to give the most meaningful recommendations - the best fit that the user will probably like but has not watched yet.

## Key Features

### 1. Personalized Recommendations
- Uses Netflix watch history export and like/dislike data to understand user preferences
- Analyzes what the user has watched and their ratings to build a taste profile
- Identifies titles the user will likely enjoy but hasn't discovered yet

### 2. Natural Language Queries
Users can make conversational requests like:
- "I want to see a serie where King Alfred confronts the vikings" → recommends "Last Kingdom" and similar titles
- The system understands context, themes, and plot elements from natural language

### 3. Streaming Service Integration
- **Phase 1**: Netflix-only recommendations (current focus)
  - Tracks which titles are currently available on Netflix NL
  - Ensures recommendations are actually watchable
- **Phase 2**: Multi-service support (planned)
  - Expand to all major streaming platforms

## Technical Approach

### Embedding-Based Similarity
The recommendation engine uses **embeddings** to measure **cosine similarity** between three key components:

1. **User's Query**: Natural language input converted to embedding
2. **User's Taste Profile**: Embedding representing the user's preferences based on watch history and ratings
3. **Title Metadata**: Embedding of each movie/series including:
   - Title
   - Comprehensive metadata (genre, cast, director, year, etc.)
   - Plot summary/description

### Similarity Scoring
By calculating cosine similarity between these embeddings, the system can:
- Find titles that match the semantic meaning of the user's query
- Align recommendations with the user's demonstrated preferences
- Rank results by relevance and fit

## Data Sources

### User Data (Input)
- Netflix watch history export
- Netflix like/dislike data export

### Content Data
- Movie and series metadata (comprehensive)
- Plot descriptions and summaries
- Current availability on Netflix NL (and other services in future)

## Success Criteria
A successful recommendation is one that:
1. Matches the user's query intent (if provided)
2. Aligns with the user's demonstrated taste
3. Is currently available on the target streaming service
4. Has NOT been watched by the user yet
5. Maximizes the likelihood of user satisfaction

## Use Cases

### Discovery
Help users find hidden gems they would love but might never discover through traditional browsing

### Contextual Search
Enable users to search by theme, mood, plot elements, or vague memories rather than just titles or genres

### Taste Evolution
Track and adapt to changing user preferences over time as more watch history accumulates

## Future Enhancements
- Multi-service availability tracking
- Group recommendations (for families/friends with different tastes)
- Temporal recommendations (what to watch next based on recent viewing)
- Mood-based filtering
- Advanced filtering (runtime, release year, etc.)

## Contributing

Now that you understand MovieDB's purpose and approach, you're ready to contribute! 

**Next steps:**
1. Read [CONTRIBUTING.md](../../CONTRIBUTING.md) for contribution guidelines
2. Check out the [benchmark documentation](../../benchmark/README.md) if you're interested in improving recommendations
3. Browse open issues or create your own
4. Start building! 🚀

We especially welcome improvements to the recommendation system. Remember: new algorithms must outperform the baseline benchmarks to be accepted.

