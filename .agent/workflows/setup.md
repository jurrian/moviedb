---
description: Set up the MovieDB development environment
---

# MovieDB Development Environment Setup

This workflow guides you through setting up the MovieDB project from scratch.

## Prerequisites

- Docker and Docker Compose installed
- Nginx installed (for production setup)
- `uv` package manager

## Setup Steps

### 1. Configure Environment Variables

Copy the default environment file and configure it:

```bash
cp .env-default .env
chmod +x scripts/switch_db_branch.sh
./scripts/switch_db_branch.sh
```

**Important**: Open the `.env` file and fill in a value for the `SECRET_KEY` variable.

### 2. Configure Nginx (Optional - Production Only)

If you're setting up for production deployment:

```bash
cp nginx/moviedb.conf /etc/nginx/sites-enabled/moviedb.conf
service nginx reload
mkdir -p /var/www/moviedb/nginx/
cp nginx/error.html /var/www/moviedb/nginx/error.html
```

**Note**: Skip this step for local development.

### 3. Start Docker Services

// turbo
Build and start the Docker containers:

```bash
docker compose up --build -d
```

### 4. Access the Streamlit Container

Enter the Streamlit container shell:

```bash
docker compose exec -it streamlit bash
```

### 5. Run Database Migrations

Inside the container, run migrations:

```bash
uv run src/manage.py migrate
```

### 6. Import Initial Data

Import streaming availability data:

```bash
uv run src/manage.py import_streaming_availability
```

### 7. Build Embeddings

Generate movie embeddings for the recommendation system:

```bash
uv run src/manage.py build_embeddings
```

### 8. Import MLflow Baselines

// turbo
Import shared baseline experiments into your local MLflow database:

```bash
uv run python benchmark/import_baseline.py
```

**Note**: This step imports experiment results shared by other contributors. It's safe to skip if no baselines exist yet.

### 9. Start the Streamlit Application

// turbo
Launch the Streamlit app:

```bash
uv run streamlit run src/main.py
```

## Verification

Once the Streamlit app is running, you should be able to access it at:
- **Local**: http://localhost:8501
- **Production**: According to your Nginx configuration

## Troubleshooting

- **Docker issues**: Ensure Docker daemon is running
- **Permission errors**: You may need `sudo` for Nginx commands
- **Missing data**: Verify steps 6 and 7 completed successfully
- **Port conflicts**: Check if port 8501 is already in use

## Next Steps

After setup, you can:
- Run benchmarks using `/run-benchmarks` workflow
- Explore the recommendation system
- Make changes and test locally
