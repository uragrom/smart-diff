"""Ollama API: analyze diff and generate commit message."""

from ollama import chat

from .config import get_commit_msg_prompt, get_system_prompt


def analyze_diff(diff_text: str, model: str, lang: str = "auto") -> str:
    """Send diff to Ollama and return analysis: summary, changes, risks."""
    if not diff_text.strip():
        return "No changes to analyze (or diff empty after filtering)."

    response = chat(
        model=model,
        messages=[
            {"role": "system", "content": get_system_prompt(lang)},
            {"role": "user", "content": f"```diff\n{diff_text}\n```"},
        ],
        options={"temperature": 0.3},
    )
    return response.message.content or ""


def generate_commit_message(diff_text: str, model: str, lang: str = "auto") -> str:
    """Generate one-line commit message; specific, not generic."""
    if not diff_text.strip():
        return "Update"

    response = chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"```diff\n{diff_text}\n```\n\n{get_commit_msg_prompt(lang)}",
            },
        ],
        options={"temperature": 0.2},
    )
    text = (response.message.content or "Update").strip()
    # Strip surrounding quotes if present
    for q in ('"', "'", "`"):
        if text.startswith(q) and text.endswith(q) and len(text) > 2:
            text = text[1:-1]
    return text[:72]
