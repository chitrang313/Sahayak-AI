"""Helpers for checking the local Ollama server status."""

from __future__ import annotations

import requests


def is_ollama_running(base_url: str = "http://localhost:11434") -> bool:
    """Return whether the Ollama server responds at the configured base URL."""
    try:
        response = requests.get(base_url, timeout=3)
        return response.ok
    except requests.RequestException:
        return False
