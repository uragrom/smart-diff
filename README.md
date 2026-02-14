# Smart Diff (Git Deep-Diff)

**[Русский](README.ru.md)** | English

A CLI that turns raw `git diff` into **plain-language summaries** using a local LLM (Ollama). Use it for quick code-review or to generate concrete commit messages.

**Example:** run `git dd` and get something like:

> In this commit you refactored auth logic (JWT → server sessions) and fixed a possible leak in `cleanup()`.

## Requirements

- Python 3.8+
- [Ollama](https://ollama.com) installed and running
- An Ollama model (e.g. `ollama pull llama3` or `ollama pull deepseek-r1`; list: `ollama list`)

## Installation

From source:

```bash
git clone https://github.com/YOUR_USERNAME/smart-diff.git
cd smart-diff
pip install .
```

From GitHub (replace `YOUR_USERNAME` with your GitHub username):

```bash
pip install git+https://github.com/YOUR_USERNAME/smart-diff.git
```

## Use as `git dd`

Add a Git alias so you can run `git dd`:

```bash
git config --global alias.dd '!smart-diff'
```

Then:

```bash
git dd                  # analyze current changes (or last commit if working tree is clean)
git dd --staged         # only staged changes
git dd -r HEAD          # analyze last commit
git dd -m deepseek-r1   # use a specific model
```

## Commands

| Command | Description |
|--------|-------------|
| `smart-diff` | Analyze current changes (or last commit when clean) |
| `smart-diff --staged` / `-s` | Only staged changes |
| `smart-diff --ref HEAD` / `-r HEAD~1` | Analyze a given commit |
| `smart-diff --commit-msg` | Generate a **specific** one-line commit message (what changed, not generic “Fix code”) |
| `smart-diff -m <model>` | Override model (e.g. `deepseek-r1`) |
| `smart-diff -l en` / `--lang ru` | Output/LLM language: `en`, `ru`, `auto` |
| `smart-diff config set model <name>` | Set default model |
| `smart-diff config set lang en\|ru\|auto` | Set default language |
| `smart-diff config show` | Show current model, language, and config path |

## Features

- **Junk filtering** — Skips `package-lock.json`, `poetry.lock`, `yarn.lock`, `node_modules/`, etc. so the LLM sees only relevant code.
- **Large diffs** — Truncates huge diffs while keeping the tail so context stays usable.
- **Default model & language** — `smart-diff config set model deepseek-r1`, `smart-diff config set lang ru`; view with `smart-diff config show`.
- **Multiple models** — Default from config or `llama3`; e.g. `codestral` or `deepseek-r1` for code. List: `ollama list`.
- **Language** — `-l en` / `-l ru` / `-l auto` (match code); affects CLI messages and LLM response language.
- **Pre-commit hook** — Auto-fill commit message from staged diff:

```bash
cp hooks/prepare-commit-msg.example .git/hooks/prepare-commit-msg
chmod +x .git/hooks/prepare-commit-msg
```

On the next `git commit`, the message will be generated from staged changes (if the hook runs successfully).

## Example output

```
Model: llama3. Analyzing changes...
╭────────────────── Smart Diff — change analysis ──────────────────╮
│ **Brief summary**                                                │
│ Refactored auth: JWT replaced with server sessions.              │
│                                                                  │
│ **Key changes**                                                  │
│ - Switched to server sessions in `auth.py`                       │
│ - Removed token from headers in `api.py`                         │
│                                                                  │
│ **Potential risks**                                              │
│ None found.                                                      │
╰──────────────────────────────────────────────────────────────────╯
```

## Development

```bash
pip install -e ".[dev]"
ruff check src
```

## License

MIT — see [LICENSE](LICENSE).
