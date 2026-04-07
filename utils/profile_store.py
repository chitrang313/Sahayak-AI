"""Profile persistence helpers for the Sahayak AI desktop app."""

from __future__ import annotations

import json
from pathlib import Path


PROFILE_PATH = Path(__file__).resolve().parents[1] / "user_profile.json"
DEFAULT_PROFILE = {
    "full_name": "",
    "email": "",
    "phone": "",
    "linkedin": "",
}


def load_profile() -> dict[str, str]:
    """Load the persisted user profile if it exists."""
    if not PROFILE_PATH.exists():
        return DEFAULT_PROFILE.copy()

    try:
        payload = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_PROFILE.copy()

    profile = DEFAULT_PROFILE.copy()
    for key in profile:
        value = payload.get(key, "")
        profile[key] = value.strip() if isinstance(value, str) else ""
    return profile


def save_profile(profile: dict[str, str]) -> None:
    """Persist the user profile as JSON."""
    payload = {
        key: str(profile.get(key, "")).strip()
        for key in DEFAULT_PROFILE
    }
    PROFILE_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
