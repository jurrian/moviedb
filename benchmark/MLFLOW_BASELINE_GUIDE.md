# MLflow Baseline Export/Import Quick Reference

## Overview

This project uses MLflow's Python API to export and import experiment results for sharing across collaborators without committing the MLflow database to Git.

## Quick Commands

### Import Baselines (for new contributors)
```bash
cd benchmark
uv run python import_baseline.py
```

### Export a Specific Run (for maintainers)
```bash
cd benchmark
# Find run ID in MLflow UI at http://localhost:5000
uv run python export_baseline.py --run-id <run-id>
git add baseline/
git commit -m "Add baseline: <description>"
git push
```

### Export an Entire Experiment
```bash
cd benchmark
uv run python export_baseline.py --experiment "Experiment Name"
git add baseline/
git commit -m "Add baseline experiment: <description>"
git push
```

### View MLflow UI
```bash
cd benchmark
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
# Visit http://localhost:5000
```

## Workflow

### For New Contributors
1. Clone the repository
2. Run `/setup` workflow (includes automatic baseline import)
3. Start experimenting with your own runs
4. Compare your results to imported baselines in MLflow UI

### For Maintainers Adding Baselines
1. Run your benchmark/experiment locally
2. Verify results in MLflow UI
3. Export the run or experiment using `export_baseline.py`
4. Commit the `benchmark/baseline/` directory
5. Push to GitHub
6. Other contributors will get the baseline on next pull + import

## What's Committed vs. What's Not

### ✅ Committed to Git
- `benchmark/baseline/` - Exported experiments and runs
- Export/import scripts
- This documentation

### ❌ NOT Committed (in .gitignore)
- `benchmark/mlflow.db` - Your local MLflow database
- `benchmark/mlartifacts/` - Your local artifacts
- `mlruns/` - Legacy MLflow storage

## Benefits

- **No merge conflicts**: Each developer has their own local database
- **Shared history**: Everyone can see the same baseline results
- **Flexible experimentation**: Run as many experiments as you want locally
- **Selective sharing**: Only export runs that matter
- **Git-friendly**: Exports are JSON + files, not binary databases

## Troubleshooting

### "No baselines to import"
This is normal for a fresh project. Run some experiments and export them!

### Import fails
Make sure you're in the `benchmark/` directory and the MLflow database exists:
```bash
cd benchmark
ls -la mlflow.db  # Should exist after first MLflow run
```

### Export fails
Verify the run ID or experiment name exists:
```bash
cd benchmark
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
# Check the UI for correct names/IDs
```

## More Information

See `benchmark/baseline/README.md` for detailed documentation.
