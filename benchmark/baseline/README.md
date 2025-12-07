# MLflow Baseline Experiments

This directory contains exported MLflow experiments and runs that serve as baselines for the MovieDB recommendation system. These baselines are shared across all collaborators via Git.

## Purpose

- **Shared History**: All collaborators can see the same baseline experiment results
- **Reproducibility**: Track the performance of "blessed" model configurations
- **Collaboration**: Work on different branches with different experiments while maintaining a common reference

## Structure

Exported experiments are stored in subdirectories here. Each export contains:
- `experiment.json`: Experiment metadata (name, ID, tags)
- `runs/`: Individual run directories, each containing:
  - `run.json`: Run metadata (parameters, metrics, tags, timestamps)
  - `artifacts/`: Model artifacts, plots, and other files (when available)

## Usage

### For New Contributors

When you first clone the repository and run the setup workflow, baseline experiments will be automatically imported into your local MLflow database.

Manual import:
```bash
cd benchmark
uv run python import_baseline.py
```

### For Maintainers: Exporting New Baselines

When you've completed a benchmark run that should become the new baseline:

1. **Find the run ID** in the MLflow UI (http://localhost:5000)

2. **Export the run**:
   ```bash
   cd benchmark
   uv run python export_baseline.py --run-id <run-id>
   ```

3. **Or export an entire experiment**:
   ```bash
   uv run python export_baseline.py --experiment "User Recommendations"
   ```

4. **Commit to Git**:
   ```bash
   git add benchmark/baseline/
   git commit -m "Add baseline: <description of what changed>"
   git push
   ```

## Best Practices

- **Export selectively**: Only export runs that represent significant milestones or approved baselines
- **Document changes**: In your commit message, explain what changed and why this baseline is important
- **Keep it clean**: Periodically review and remove outdated baselines to avoid bloat
- **Naming**: Use descriptive experiment names that indicate the model version or feature being tested

## Local Development

Your local MLflow database (`mlflow.db`) is **not** committed to Git. You can:
- Run as many experiments as you want locally
- Compare your results to the imported baselines
- Only export runs when they're ready to be shared

## Viewing Results

After importing baselines, start the MLflow UI:
```bash
cd benchmark
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

Then visit http://localhost:5000 to explore all experiments and runs.
