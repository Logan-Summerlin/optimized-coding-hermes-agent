"""Voice shortcut formatting helpers for the classic CLI.

The lean fork no longer ships the process-wide voice runtime, but the
classic CLI still renders legacy voice status fields in a few places.
Keep the small, dependency-free key parser separate from the removed
voice implementation.
"""

from __future__ import annotations

import sys
from typing import Any

_VOICE_MOD_ALIASES = {
    "ctrl": "c-",
    "control": "c-",
    "alt": "a-",
    "option": "a-",
    "opt": "a-",
}

_VOICE_NAMED_KEYS = {
    "space": "space",
    "spc": "space",
    "enter": "enter",
    "return": "enter",
    "ret": "enter",
    "tab": "tab",
    "escape": "escape",
    "esc": "escape",
    "backspace": "backspace",
    "bs": "backspace",
    "delete": "delete",
    "del": "delete",
}

_VOICE_RESERVED_CTRL_CHARS = frozenset({"c", "d", "l"})
_VOICE_RESERVED_ALT_CHARS_MAC = frozenset({"c", "d", "l"})
_DEFAULT_PT_KEY = "c-b"

def voice_record_key_from_config(cfg: Any) -> Any:
    if not isinstance(cfg, dict):
        return None
    voice = cfg.get("voice")
    if not isinstance(voice, dict):
        return None
    return voice.get("record_key")

def normalize_voice_record_key_for_prompt_toolkit(raw: Any) -> str:
    if not isinstance(raw, str):
        return _DEFAULT_PT_KEY
    lowered = raw.strip().lower()
    if not lowered:
        return _DEFAULT_PT_KEY
    parts = [p.strip() for p in lowered.split("+") if p.strip()]
    if not parts or len(parts) != 2:
        return _DEFAULT_PT_KEY
    modifier_token, key_token = parts
    if modifier_token in {"super", "win", "windows"}:
        return _DEFAULT_PT_KEY
    normalized_mod = _VOICE_MOD_ALIASES.get(modifier_token)
    if not normalized_mod:
        return _DEFAULT_PT_KEY
    if len(key_token) == 1:
        if normalized_mod == "c-" and key_token in _VOICE_RESERVED_CTRL_CHARS:
            return _DEFAULT_PT_KEY
        if normalized_mod == "a-" and sys.platform == "darwin" and key_token in _VOICE_RESERVED_ALT_CHARS_MAC:
            return _DEFAULT_PT_KEY
        return f"{normalized_mod}{key_token}"
    named = _VOICE_NAMED_KEYS.get(key_token)
    if not named:
        return _DEFAULT_PT_KEY
    return f"{normalized_mod}{named}"

def format_voice_record_key_for_status(raw: Any) -> str:
    normalized = normalize_voice_record_key_for_prompt_toolkit(raw)
    if normalized.startswith("c-"):
        prefix, key = "Ctrl+", normalized[2:]
    elif normalized.startswith("a-"):
        prefix, key = "Alt+", normalized[2:]
    elif "+" in normalized:
        mod, key = normalized.split("+", 1)
        prefix = mod[0].upper() + mod[1:] + "+"
    else:
        return "Ctrl+B"
    if not key:
        return prefix.rstrip("+")
    if len(key) == 1:
        return prefix + key.upper()
    return prefix + key[0].upper() + key[1:]
