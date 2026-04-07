"""Shared UI helpers for Sahayak AI feature panels."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from services.ollama_service import (
    CancelToken,
    OllamaCancelledError,
    OllamaServiceError,
)


class PlaceholderText(tk.Text):
    """Text widget with lightweight placeholder support."""

    def __init__(self, master: tk.Misc, placeholder: str, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = "#8a8f98"
        self.default_fg = kwargs.get("fg", "#1f2933")
        self.is_placeholder_active = False

        self.bind("<FocusIn>", self._handle_focus_in)
        self.bind("<FocusOut>", self._handle_focus_out)
        self._show_placeholder()

    def _show_placeholder(self) -> None:
        if self.get("1.0", tk.END).strip():
            return
        self.is_placeholder_active = True
        self.configure(fg=self.placeholder_color)
        self.delete("1.0", tk.END)
        self.insert("1.0", self.placeholder)

    def _hide_placeholder(self) -> None:
        if not self.is_placeholder_active:
            return
        self.is_placeholder_active = False
        self.configure(fg=self.default_fg)
        self.delete("1.0", tk.END)

    def _handle_focus_in(self, _event: tk.Event) -> None:
        self._hide_placeholder()

    def _handle_focus_out(self, _event: tk.Event) -> None:
        if not self.get("1.0", tk.END).strip():
            self._show_placeholder()

    def get_value(self) -> str:
        """Return the user-entered text without placeholder content."""
        if self.is_placeholder_active:
            return ""
        return self.get("1.0", tk.END).strip()

    def clear(self) -> None:
        """Clear user text and restore the placeholder."""
        self.is_placeholder_active = False
        self.configure(fg=self.default_fg)
        self.delete("1.0", tk.END)
        self._show_placeholder()


def set_text_content(widget: tk.Text, value: str) -> None:
    """Replace the content of a Tk text widget safely."""
    current_state = widget.cget("state")
    if str(current_state) == "disabled":
        widget.configure(state="normal")
    widget.delete("1.0", tk.END)
    widget.insert("1.0", value)
    if str(current_state) == "disabled":
        widget.configure(state="disabled")


class AsyncToolFrame(ttk.Frame):
    """Base frame that runs Ollama requests on a worker thread."""

    def __init__(self, parent: tk.Misc, controller, **kwargs) -> None:
        super().__init__(parent, style="Panel.TFrame", padding=24, **kwargs)
        self.controller = controller
        self._cancel_token: CancelToken | None = None

    @property
    def is_running(self) -> bool:
        """Return whether the panel currently has a running request."""
        return self._cancel_token is not None

    def run_prompt(
        self,
        prompt: str,
        on_success,
        *,
        error_title: str,
        fallback_message: str,
    ) -> None:
        """Execute a prompt against Ollama without freezing the UI."""
        if self.is_running:
            return

        token = CancelToken()
        self._cancel_token = token
        self.set_busy(True)
        selected_model = self.controller.get_selected_model()

        def worker() -> None:
            try:
                response_text, model_name = self.controller.ollama_service.generate(
                    prompt,
                    model_name=selected_model,
                    cancel_token=token,
                )
            except OllamaCancelledError:
                return
            except OllamaServiceError as exc:
                self.after(
                    0,
                    self._handle_error_result,
                    token,
                    str(exc),
                    error_title,
                    fallback_message,
                )
                return

            self.after(
                0,
                self._handle_success_result,
                token,
                response_text,
                model_name,
                on_success,
            )

        threading.Thread(target=worker, daemon=True).start()

    def cancel_request(self, on_cancel=None) -> None:
        """Cancel the currently running request if one exists."""
        token = self._cancel_token
        if token is None:
            return

        token.cancel()
        self._cancel_token = None
        self.set_busy(False)
        if on_cancel is not None:
            on_cancel()

    def _handle_success_result(
        self,
        token: CancelToken,
        response_text: str,
        model_name: str,
        on_success,
    ) -> None:
        if token.is_cancelled or self._cancel_token is not token:
            return

        self._cancel_token = None
        self.set_busy(False)
        self.controller.set_selected_model(model_name)
        on_success(response_text, model_name)

    def _handle_error_result(
        self,
        token: CancelToken,
        error_message: str,
        error_title: str,
        fallback_message: str,
    ) -> None:
        if token.is_cancelled or self._cancel_token is not token:
            return

        self._cancel_token = None
        self.set_busy(False)
        self.on_request_error(fallback_message)
        self.controller.refresh_status_now()

        safe_message = error_message.strip() or fallback_message
        messagebox.showerror(error_title, safe_message)

    def set_busy(self, is_busy: bool) -> None:
        """Update panel-specific widget state while a request is running."""

    def on_request_error(self, fallback_message: str) -> None:
        """Allow child panels to surface a fallback UI message."""
