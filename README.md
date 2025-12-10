# MovieDB 🎬

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**🌐 Website:** [moviedb.nl](https://moviedb.nl)

> AI-powered movie and series recommendation system that understands what you'll love, even before you know it exists.

## About

MovieDB is an intelligent recommendation engine that goes beyond simple genre matching. Using advanced embedding-based similarity and natural language understanding, it provides highly personalized recommendations based on your viewing history, preferences, and even conversational queries.

**Ask naturally:** "I want to see a series where King Alfred confronts the vikings" → Get *The Last Kingdom* and similar titles.

### Key Features

- 🎯 **Personalized Recommendations** - Analyzes your Netflix watch history and ratings to build a comprehensive taste profile
- 💬 **Natural Language Queries** - Search by theme, mood, plot elements, or vague memories instead of just titles
- 🎬 **Streaming Availability** - Only recommends content currently available on your streaming services (Netflix NL initially)
- 🧠 **Embedding-Based Intelligence** - Uses cosine similarity between your query, taste profile, and comprehensive movie metadata
- 📊 **Benchmarked Quality** - All recommendation improvements are validated against performance baselines

### How It Works

MovieDB uses **embeddings** to measure semantic similarity between:
1. Your natural language query
2. Your viewing preferences (from watch history and ratings)
3. Comprehensive movie/series metadata (plot, cast, themes, etc.)

This enables discovery of hidden gems that match your taste but you'd never find through traditional browsing.

## Quick Start

The easiest way to get started is using [Antigravity](https://antigravity.dev/) IDE:

```bash
/setup
```

### Manual Setup

<details>
<summary>Click to expand manual setup instructions</summary>

Set up environment variables and Nginx configuration:
```bash
cp .env-default .env
touch .env.branch
# Fill a value for the SECRET_KEY variable in the .env file

cp nginx/moviedb.conf /etc/nginx/sites-enabled/moviedb.conf
service nginx reload

mkdir -p /var/www/moviedb/nginx/
cp nginx/error.html /var/www/moviedb/nginx/error.html
```

To populate and run the application:
```bash
docker compose up --build -d
docker compose exec -it streamlit bash

### Database Branch Switching

To automatically switch databases when changing branches, set up a Git hook:

# Symlink the hook script
ln -s scripts/switch_db_branch.sh .git/hooks/post-checkout

# Execute it once to set up the environment
chmod +x scripts/switch_db_branch.sh
./scripts/switch_db_branch.sh
```

### Running the App

```bash
uv run src/manage.py migrate

# Add initial data
uv run src/manage.py import_streaming_availability
uv run src/manage.py build_embeddings

uv run streamlit run src/main.py
```

</details>

## Documentation

- 📖 [Project Purpose & Vision](.agent/knowledge/project-purpose.md) - **Start here** to understand the project goals
- 🧪 [Benchmarking Guide](benchmark/README.md) - How to run and create benchmarks
- 🔄 [MLflow Baseline Guide](benchmark/MLFLOW_BASELINE_GUIDE.md) - Sharing experiment results

## Contributing

We welcome contributions! 🎉 Whether you're fixing bugs, improving documentation, or enhancing the recommendation algorithm, your help makes MovieDB better.

**We encourage active participation:**
- 💡 Found a bug? Create an issue **and** submit a fix
- 🚀 Have an idea? Discuss it in an issue, then implement it
- 📈 Improving recommendations? Make sure your changes outperform the benchmark baseline

👉 **Get started:** Read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines

**Special focus area:** We especially welcome improvements to the recommendation system! See the [benchmarking guide](benchmark/README.md) to learn how to validate your improvements.

## Code Quality

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

To format code:
```bash
ruff format .
```

To run linting checks (and fix fixable issues):
```bash
ruff check --fix .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for the UI
- Backend powered by [Django](https://www.djangoproject.com/)
- Experiment tracking with [MLflow](https://mlflow.org/)
- Netflix availability and metadata powered by [Movie of the Night](https://www.movieofthenight.com/)
- Thanks to all [contributors](https://github.com/jurrian/moviedb/graphs/contributors) who help improve MovieDB!

---

**Ready to discover your next favorite show?** Get started with the [Quick Start](#quick-start) guide above! 🍿
