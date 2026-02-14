"""Constants and default settings."""

# Files/patterns to skip when sending diff to LLM (lock files, build artifacts)
IGNORED_PATTERNS = (
    "package-lock.json",
    "poetry.lock",
    "Pipfile.lock",
    "yarn.lock",
    "pnpm-lock.yaml",
    "bun.lockb",
    "*.min.js",
    "*.min.css",
    ".bundle",
    "vendor/",
    "node_modules/",
    "__pycache__/",
    ".git/",
    "*.pyc",
    "*.egg-info/",
    ".eggs/",
    "dist/",
    "build/",
)

# Max diff size in chars (to avoid overflowing context)
MAX_DIFF_CHARS = 30_000

# When truncating, keep this many chars at the end (often important)
TAIL_CHARS = 5_000

# Fallback defaults when not in user config (ollama list for installed models)
DEFAULT_MODEL = "llama3"
DEEP_MODEL = "codestral"

# Language: "en", "ru", or "auto" (follow code/commits)
VALID_LANGS = ("en", "ru", "auto")


def _lang_instruction(lang: str, for_commit: bool = False) -> str:
    if lang == "en":
        return "Write your entire response in English."
    if lang == "ru":
        return "Пиши весь ответ по-русски."
    return "Use the same language as the code and commit messages (Russian or English)."


def get_system_prompt(lang: str) -> str:
    """Analysis prompt with language instruction."""
    li = _lang_instruction(lang, for_commit=False)
    return f"""You are an experienced tech lead. Analyze the following git diff and respond in Markdown. {li}

Structure (required):

1. **Brief summary** — One sentence: what was done in these changes.
2. **Key changes** — List main edits (files, logic, refactoring).
3. **Potential risks** — Possible bugs, leaks, or bad practices; if none, say "None found."

Be concise. Do not repeat the diff."""


def get_commit_msg_prompt(lang: str) -> str:
    """Commit message prompt: specific, not generic. Language instruction included."""
    li = _lang_instruction(lang, for_commit=True)
    return f"""Based on this git diff, write ONE short commit message line (max 72 characters, imperative mood). {li}

Be SPECIFIC: state what was actually changed — mention files or logic (e.g. "Add JWT validation in auth.py", "Refactor login to use server sessions"). Avoid generic phrases like "Fix code", "Update", "Add comments", "Fix code structure".

Output ONLY the message text, no quotes or explanation."""
