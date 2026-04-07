"""Clipboard helpers for the desktop app."""

from __future__ import annotations

import tkinter as tk


def copy_text(root: tk.Misc, value: str) -> None:
    """Copy text into the system clipboard."""
    root.clipboard_clear()
    root.clipboard_append(value)
    root.update_idletasks()
