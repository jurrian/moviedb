---
description: Managing dependencies and python environment with uv
---

# Python Environment & Dependency Management

This project uses `uv` for dependency management.

## Activating the Virtual Environment

To run python scripts or use the environment in the terminal, activate the venv:

```bash
. ./.venv/bin/activate
```

## Installing New Packages

**DO NOT** use `pip install`. Use `uv add` instead:

```bash
uv add <package_name>
```

Example:
```bash
uv add extra-streamlit-components
```

## Running Scripts

You can also run scripts directly without manual activation using `uv run`:

```bash
uv run src/manage.py <command>
uv run streamlit run src/streamlit_app.py
```
