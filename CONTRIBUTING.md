# Contributing to MovieDB

Thank you for your interest in contributing to MovieDB! 🎉 We're excited to have you here. This guide will help you get started with contributing to our AI-powered recommendation system.

## 🌟 Philosophy: Be a Builder, Not Just a Requester

We love feature ideas, but we **love implementations even more**! When you spot something that could be better:

✅ **Do this:** "I noticed X could be improved. Here's my implementation..."  
❌ **Not this:** "Someone should add feature X..."

We encourage you to:
- Create an issue **and** submit a solution
- Discuss your approach, then build it
- Take ownership of improvements you care about

## 🚀 Ways to Contribute

- **Code:** Implement features, fix bugs, improve algorithms
- **Recommendation System:** Enhance the core ML algorithms (see special section below)
- **Documentation:** Improve guides, add examples, fix typos
- **Benchmarks:** Create new benchmarks, validate improvements
- **Bug Reports:** Find and report issues (bonus points for including a fix!)
- **Testing:** Add tests, improve test coverage

## 📚 Getting Started

### 1. Understand the Project

**Start here:** Read [project-purpose.md](.agent/knowledge/project-purpose.md) to understand MovieDB's vision and goals.

This document explains:
- What problem MovieDB solves
- How the embedding-based recommendation system works
- The project's technical approach
- Success criteria for recommendations

Understanding the "why" behind MovieDB will help you make meaningful contributions aligned with the project's vision.

### 2. Set Up Your Development Environment

Follow the setup instructions in the [README.md](README.md). The easiest way is using Antigravity:

```bash
/setup
```

This will:
- Set up your local environment
- Import MLflow baselines for comparison
- Get you ready to start developing

### 3. Explore the Codebase

Key areas:
- `src/movies/` - Core recommendation logic
- `benchmark/` - Benchmarking and evaluation scripts
- `src/streamlit_app.py` - User interface
- `.agent/knowledge/` - Project documentation

## 🔄 Contribution Workflow

### Step 1: Create an Issue First

Before writing code, **create an issue** to discuss your idea:

1. Check if a similar issue already exists
2. Create a new issue describing:
   - What you want to change/add
   - Why it's valuable
   - Your proposed approach
3. Wait for feedback from maintainers

This prevents duplicate work and ensures your contribution aligns with project goals.

### Step 2: Fork and Branch

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/moviedb.git
cd moviedb
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/natural-language-filters`
- `fix/embedding-cache-bug`
- `docs/benchmark-guide-improvements`

### Step 3: Make Your Changes

- Write clean, readable code
- Follow existing code style and conventions
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### Step 4: Test Your Changes

```bash
# Run tests (if available)
uv run pytest

# Test manually with the Streamlit app
uv run streamlit run src/streamlit_app.py

# For recommendation changes: run benchmarks (see below)
```

### Step 5: Submit a Pull Request

1. Push your branch to your fork
2. Create a Pull Request on GitHub
3. Fill out the PR template with:
   - Description of changes
   - Related issue number
   - Testing performed
   - Benchmark results (if applicable)
4. Respond to review feedback

## 🎯 Special Focus: Improving the Recommendation System

We **especially welcome** contributions to the recommendation algorithm! This is the heart of MovieDB.

### Quality Gate: Benchmark Requirement

> [!IMPORTANT]
> **All recommendation algorithm improvements must outperform the current baseline benchmark to be accepted.**

This ensures MovieDB continuously improves and doesn't regress in quality.

### How to Contribute Recommendation Improvements

1. **Understand the current approach**
   - Read [project-purpose.md](.agent/knowledge/project-purpose.md)
   - Study the existing recommendation code in `src/movies/`
   - Review current benchmark results

2. **Run the baseline benchmark**
   ```bash
   cd benchmark
   # Run existing benchmarks to establish baseline
   uv run python user_recommends.py
   uv run python query_recommends.py
   ```

3. **Implement your improvement**
   - Make your changes to the recommendation logic
   - Document your approach and rationale

4. **Benchmark your changes**
   - Run the same benchmarks with your changes
   - Compare results to the baseline
   - Document the performance improvement

5. **Submit your PR with evidence**
   - Include benchmark comparison in PR description
   - Show metrics demonstrating improvement
   - Explain why your approach works better

### What Makes a "Better" Recommendation?

See the [benchmark README](benchmark/README.md) for details on metrics, but generally:
- Higher relevance scores for recommended items
- Better hit rate (finding items users actually like)
- Improved ranking (best items ranked higher)
- Maintained or improved performance/speed

### Benchmarking Resources

- [benchmark/README.md](benchmark/README.md) - Detailed benchmarking howto
- [benchmark/MLFLOW_BASELINE_GUIDE.md](benchmark/MLFLOW_BASELINE_GUIDE.md) - Working with MLflow baselines

## 💻 Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and single-purpose

### Commit Messages

Write clear, descriptive commit messages:

```
Good: "Add cosine similarity caching to improve query performance"
Bad: "fix stuff"
```

Format:
```
Short summary (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain what and why, not how (code shows how).

Fixes #123
```

### Testing

- Add tests for new features
- Ensure existing tests still pass
- Test edge cases and error conditions
- For UI changes: test manually in Streamlit

## 📝 Issue Guidelines

### Creating Good Issues

**Bug Reports** should include:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Error messages or logs

**Feature Requests** should include:
- Problem you're trying to solve
- Proposed solution
- Why it's valuable to MovieDB users
- **Bonus:** Your plan to implement it!

### Issue Labels

Maintainers will add labels like:
- `good first issue` - Great for newcomers
- `help wanted` - We'd love contributions here
- `recommendation-system` - Core algorithm improvements
- `documentation` - Documentation improvements
- `bug` - Something isn't working

## 🔍 Pull Request Guidelines

### Before Submitting

- [ ] Code follows project style
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Commits are clean and well-described
- [ ] Branch is up to date with main
- [ ] For recommendation changes: benchmarks show improvement

### PR Description Template

```markdown
## Description
Brief description of changes

## Related Issue
Fixes #123

## Changes Made
- Change 1
- Change 2

## Testing Performed
- Test 1
- Test 2

## Benchmark Results (if applicable)
| Metric | Baseline | New | Improvement |
|--------|----------|-----|-------------|
| Hit Rate | 0.75 | 0.82 | +9.3% |
```

### Review Process

1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Once approved, your PR will be merged
4. Celebrate! 🎉 You're now a MovieDB contributor!

## 🤝 Community Guidelines

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Give constructive feedback
- Assume good intentions
- Focus on what's best for the project and users

## ❓ Questions?

- **General questions:** Create a GitHub issue with the `question` label
- **Bug reports:** Create an issue with steps to reproduce
- **Feature ideas:** Create an issue to discuss before implementing

## 🙏 Thank You!

Every contribution, no matter how small, makes MovieDB better. We appreciate your time and effort in helping build a better recommendation system!

---

**Ready to contribute?** Start by reading [project-purpose.md](.agent/knowledge/project-purpose.md), then pick an issue labeled `good first issue` or create your own! 🚀
