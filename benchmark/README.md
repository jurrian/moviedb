# Benchmark

Experiments and performance comparisons for recommendation algorithms using MLflow.

## Overview

This directory contains benchmarking tools to evaluate and compare recommendation system performance. All recommendation algorithm improvements **must outperform the baseline** to be accepted into the project.

### Why Benchmarking Matters

Benchmarks ensure that:
- New algorithms actually improve recommendation quality
- Changes don't introduce performance regressions
- We have objective metrics to compare approaches
- The project continuously improves over time

## Quick Start

### View Current Benchmarks

```bash
cd benchmark
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
# Visit http://localhost:5000
```

### Import Baseline Results

When you first clone the repository, import shared baseline results:

```bash
cd benchmark
uv run python import_baseline.py
```

This imports benchmark results from other contributors so you can compare your improvements against established baselines.

## Running Benchmarks

### User-Based Recommendations

Evaluate how well the system recommends content based on user taste profiles:

```bash
cd benchmark
uv run python user_recommends.py
```

This benchmark:
- Uses actual user watch history and ratings
- Generates recommendations based on user embeddings
- Measures hit rate and ranking quality
- Logs results to MLflow

### Query-Based Recommendations

Evaluate how well the system handles natural language queries:

```bash
cd benchmark
uv run python query_recommends.py
```

This benchmark:
- Tests natural language query understanding
- Measures relevance of recommended titles
- Evaluates semantic similarity matching
- Logs results to MLflow

## Understanding Metrics

### Key Performance Indicators

| Metric | Description | Better Value |
|--------|-------------|--------------|
| **Hit Rate** | Percentage of test items found in recommendations | Higher |
| **Rank Score** | Average ranking position of relevant items | Lower |
| **Precision@K** | Proportion of relevant items in top K results | Higher |
| **Recall@K** | Proportion of all relevant items found in top K | Higher |

### What Makes a "Better" Recommendation?

A recommendation algorithm is better if it:
1. **Finds more relevant items** (higher hit rate)
2. **Ranks them higher** (lower rank score, higher precision@K)
3. **Maintains or improves speed** (comparable or faster execution)
4. **Generalizes well** (performs well across different users/queries)

## Contributing Recommendation Improvements

> [!IMPORTANT]
> **Quality Gate:** New recommendation algorithms must outperform the current baseline to be accepted.

### Step-by-Step Guide

#### 1. Understand the Current System

- Read [project-purpose.md](../.agent/knowledge/project-purpose.md)
- Study the recommendation code in `src/movies/`
- Review how embeddings and cosine similarity work

#### 2. Run the Baseline Benchmark

Establish the current performance:

```bash
cd benchmark

# Import shared baselines
uv run python import_baseline.py

# Run current benchmarks
uv run python user_recommends.py
uv run python query_recommends.py

# View results in MLflow UI
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

**Record baseline metrics** - you'll compare against these!

#### 3. Implement Your Improvement

Make your changes to the recommendation logic:
- Modify embedding generation
- Adjust similarity calculations
- Add new features or signals
- Optimize performance

**Document your approach:**
- What are you changing?
- Why should it work better?
- What's the theoretical improvement?

#### 4. Run Benchmarks with Your Changes

```bash
cd benchmark

# Run the same benchmarks
uv run python user_recommends.py
uv run python query_recommends.py
```

MLflow will log your new results alongside the baseline.

#### 5. Compare Results

Open the MLflow UI and compare:

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

In the UI:
- Select multiple runs (baseline + your improvement)
- Click "Compare" to see side-by-side metrics
- Look for improvements in hit rate, rank score, etc.

#### 6. Document Your Improvement

Create a clear comparison table:

```markdown
| Metric | Baseline | Your Improvement | Change |
|--------|----------|------------------|--------|
| Hit Rate | 0.75 | 0.82 | +9.3% ✅ |
| Rank Score | 12.3 | 10.1 | -17.9% ✅ |
| Execution Time | 1.2s | 1.1s | -8.3% ✅ |
```

#### 7. Submit Your Pull Request

Include in your PR:
- Description of your approach
- Benchmark comparison showing improvement
- Explanation of why it works better
- Any trade-offs or considerations

See [CONTRIBUTING.md](../CONTRIBUTING.md) for full PR guidelines.

## Creating New Benchmarks

Want to add a new benchmark? Great! Here's how:

### 1. Identify What to Test

Examples:
- Cold start recommendations (new users)
- Multi-service availability
- Specific genre performance
- Query complexity handling

### 2. Create Your Benchmark Script

Follow the pattern in existing benchmarks:

```python
import mlflow

# Set up MLflow experiment
mlflow.set_experiment("Your Experiment Name")

with mlflow.start_run():
    # Log parameters
    mlflow.log_param("algorithm", "your_algorithm")
    
    # Run your benchmark
    results = run_your_benchmark()
    
    # Log metrics
    mlflow.log_metric("hit_rate", results.hit_rate)
    mlflow.log_metric("rank_score", results.rank_score)
    
    # Log artifacts (plots, data, etc.)
    mlflow.log_artifact("results.json")
```

### 3. Document Your Benchmark

Add a section to this README explaining:
- What the benchmark tests
- How to run it
- What metrics it produces
- How to interpret results

### 4. Create a Baseline

Run your benchmark with the current system and export as baseline:

```bash
uv run python your_benchmark.py
uv run python export_baseline.py --run-id <run-id>
```

## Working with MLflow Baselines

### For Contributors

Import shared baselines when setting up:

```bash
cd benchmark
uv run python import_baseline.py
```

This is automatically done by the `/setup` workflow.

### For Maintainers

Export new baselines to share with the team:

```bash
cd benchmark

# Export a specific run
uv run python export_baseline.py --run-id <run-id>

# Or export an entire experiment
uv run python export_baseline.py --experiment "Experiment Name"

# Commit and push
git add baseline/
git commit -m "Add baseline: description"
git push
```

See [MLFLOW_BASELINE_GUIDE.md](MLFLOW_BASELINE_GUIDE.md) for detailed documentation.

## Troubleshooting

### MLflow UI won't start

```bash
# Make sure you're in the benchmark directory
cd benchmark

# Check if mlflow.db exists
ls -la mlflow.db

# If not, run a benchmark first
uv run python user_recommends.py
```

### No baseline results after import

This is normal for a fresh project. Run some benchmarks and they'll appear in the UI.

### Benchmark script fails

Check that:
- You've run `/setup` or manually set up the environment
- Database is populated (`uv run src/manage.py import_streaming_availability`)
- Embeddings are built (`uv run src/manage.py build_embeddings`)

## Best Practices

1. **Always run baselines first** - Know what you're comparing against
2. **Test multiple scenarios** - Don't optimize for just one case
3. **Document your changes** - Explain the "why" behind improvements
4. **Consider trade-offs** - Speed vs accuracy, complexity vs maintainability
5. **Use version control** - Tag significant benchmark runs in MLflow

## Additional Resources

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [MLFLOW_BASELINE_GUIDE.md](MLFLOW_BASELINE_GUIDE.md) - Baseline sharing workflow
- [CONTRIBUTING.md](../CONTRIBUTING.md) - General contribution guidelines
- [project-purpose.md](../.agent/knowledge/project-purpose.md) - Project vision and approach

---

**Ready to improve MovieDB's recommendations?** Start by running the baseline benchmarks and exploring the results in MLflow! 🚀

