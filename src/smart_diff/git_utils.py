"""Git operations: get diff and filter by ignored patterns."""

import fnmatch
import subprocess
from pathlib import Path

from .config import IGNORED_PATTERNS, MAX_DIFF_CHARS, TAIL_CHARS


class GitError(Exception):
    """Git command failed; output is not a valid diff."""

    def __init__(self, message: str, returncode: int = -1):
        self.returncode = returncode
        super().__init__(message)


def _run_git(args: list[str], cwd: Path | None = None) -> tuple[str, str, int]:
    """Run git command. Returns (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd or Path.cwd(),
            timeout=30,
        )
        return (
            (result.stdout or "").strip(),
            (result.stderr or "").strip(),
            result.returncode,
        )
    except FileNotFoundError:
        return "", "Git not found. Install Git.", 127
    except subprocess.TimeoutExpired:
        return "", "Git command timed out.", -1


def _should_ignore(path: str) -> bool:
    """Whether to skip this path by ignored patterns."""
    path = path.replace("\\", "/")
    for pattern in IGNORED_PATTERNS:
        if pattern.endswith("/"):
            if pattern.rstrip("/") in path or path.startswith(pattern):
                return True
        elif fnmatch.fnmatch(path, pattern) or pattern in path:
            return True
    return False


def get_diff(
    staged: bool = False,
    ref: str | None = None,
    cwd: Path | None = None,
) -> str:
    """
    Get diff of current changes.
    - staged: only staged (--cached)
    - ref: commit to show (e.g. HEAD); use git show for that commit's patch
    """
    cwd = cwd or Path.cwd()
    stdout, stderr, code = _run_git(["rev-parse", "--is-inside-work-tree"], cwd=cwd)
    if code != 0 or "true" not in stdout:
        return ""

    if ref:
        # Diff of a specific commit — git show, no commit message (patch only)
        stdout, stderr, code = _run_git(
            ["show", ref, "--format=", "--no-color", "--"],
            cwd=cwd,
        )
    else:
        args = ["diff", "--no-color"]
        if staged:
            args.append("--cached")
        stdout, stderr, code = _run_git(args, cwd=cwd)

    if code != 0:
        raise GitError(stderr or stdout or "Unknown git error", code)

    # Filter out ignored files from diff
    return _filter_diff_by_ignored(stdout)


def _filter_diff_by_ignored(diff_text: str) -> str:
    """Remove from diff hunks for ignored files."""
    lines = diff_text.split("\n")
    result: list[str] = []
    skip_until_next_file = True

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git "):
            # Parse file path: "diff --git a/path b/path"
            parts = line.split()
            if len(parts) >= 4:
                file_path = parts[2]
                if file_path.startswith("a/"):
                    file_path = file_path[2:]
                if _should_ignore(file_path):
                    skip_until_next_file = True
                    i += 1
                    while i < len(lines) and not lines[i].startswith("diff --git "):
                        i += 1
                    continue
            skip_until_next_file = False
            result.append(line)
            i += 1
            continue
        if not skip_until_next_file:
            result.append(line)
        i += 1

    return "\n".join(result)


def truncate_diff(diff_text: str) -> str:
    """Truncate diff to MAX_DIFF_CHARS, keeping TAIL_CHARS at the end."""
    if len(diff_text) <= MAX_DIFF_CHARS:
        return diff_text
    head = MAX_DIFF_CHARS - TAIL_CHARS
    return (
        diff_text[:head]
        + "\n\n... [diff truncated to save context] ...\n\n"
        + diff_text[-TAIL_CHARS:]
    )


def get_diff_for_llm(
    staged: bool = False,
    ref: str | None = None,
    cwd: Path | None = None,
) -> str:
    """Return filtered and optionally truncated diff for the LLM."""
    diff = get_diff(staged=staged, ref=ref, cwd=cwd)
    return truncate_diff(diff)


def get_commit_info(ref: str, cwd: Path | None = None) -> dict | None:
    """Get commit metadata for ref (hash, author, date, subject, body). Returns None on error."""
    cwd = cwd or Path.cwd()
    # %H hash, %an author, %ae email, %ai date ISO, %s subject, %b body
    fmt = "%H%n%an%n%ae%n%ai%n%s%n%b"
    stdout, stderr, code = _run_git(["log", "-1", f"--format={fmt}", ref], cwd=cwd)
    if code != 0 or not stdout.strip():
        return None
    parts = stdout.strip().split("\n", 5)
    if len(parts) < 5:
        return None
    return {
        "hash": parts[0][:12],
        "hash_full": parts[0],
        "author": parts[1],
        "email": parts[2],
        "date": parts[3],
        "subject": parts[4],
        "body": parts[5] if len(parts) > 5 else "",
    }


def get_diff_numstat(
    staged: bool = False,
    ref: str | None = None,
    cwd: Path | None = None,
) -> list[dict]:
    """Per-file stats: added/deleted lines. Returns list of {path, added, deleted} (filtered)."""
    cwd = cwd or Path.cwd()
    if ref:
        stdout, stderr, code = _run_git(["show", ref, "--numstat", "--format="], cwd=cwd)
    else:
        args = ["diff", "--numstat"]
        if staged:
            args.append("--cached")
        stdout, stderr, code = _run_git(args, cwd=cwd)
    if code != 0:
        return []
    result = []
    for line in stdout.strip().split("\n"):
        if not line.strip():
            continue
        # numstat: "add\tdel\tpath" or "-\t-\tpath" for binary
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        add_s, del_s, path = parts
        path = path.strip().replace("\\", "/")
        if _should_ignore(path):
            continue
        try:
            added = int(add_s) if add_s != "-" else 0
            deleted = int(del_s) if del_s != "-" else 0
        except ValueError:
            continue
        result.append({"path": path, "added": added, "deleted": deleted})
    return result
