"""User config: default model and language. Stored in JSON under config dir."""

import json
import os
from pathlib import Path

CONFIG_FILENAME = "config.json"
CONFIG_KEYS = ("model", "lang")

# Default config dir: Windows = APPDATA/smart-diff, Unix = ~/.config/smart-diff
def _config_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA", Path.home())
    else:
        base = Path.home() / ".config"
    return Path(base) / "smart-diff"


def get_config_path() -> Path:
    return _config_dir() / CONFIG_FILENAME


def load_config() -> dict:
    """Load config dict. Returns defaults for missing keys."""
    path = get_config_path()
    defaults = {"model": None, "lang": "auto"}
    if not path.exists():
        return defaults
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {k: data.get(k, defaults[k]) for k in CONFIG_KEYS}
    except (json.JSONDecodeError, OSError):
        return defaults


def save_config(updates: dict) -> None:
    """Save only CONFIG_KEYS. Creates config dir if needed."""
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = load_config()
    for k in CONFIG_KEYS:
        if k in updates:
            data[k] = updates[k]
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
