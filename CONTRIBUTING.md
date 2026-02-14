# Contributing to Smart Diff

Thanks for your interest in contributing.

## Setup

```bash
git clone https://github.com/uragrom/smart-diff.git
cd smart-diff
pip install -e ".[dev]"
```

## Code style

- **Ruff** for linting. Run before committing:

  ```bash
  ruff check src
  ruff format src
  ```

- Use Python 3.8+ features; keep comments and docstrings in English.

## Testing

- Manual: run `smart-diff --help`, `smart-diff config show`, and (with a repo with changes) `smart-diff --html report.html`.
- CI runs `ruff check src` on push/PR to `main` or `master`.

## Pull requests

1. Open an issue or comment on an existing one if the change is non-trivial.
2. Branch from `main`, make your changes, run `ruff check src`.
3. Open a PR with a short description. Link the issue if applicable.

## Reporting issues

Use [GitHub Issues](https://github.com/uragrom/smart-diff/issues). Include:

- OS and Python version
- Ollama version and model (e.g. `ollama list`)
- Minimal steps to reproduce (and expected vs actual behavior)

