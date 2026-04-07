"""Chat feature panel."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from services.prompt_builder import build_chat_prompt
from ui.common import AsyncToolFrame


class ChatUI(AsyncToolFrame):
    """Chat interface backed by the local Ollama model."""

    def __init__(self, parent: tk.Misc, controller) -> None:
        super().__init__(parent, controller)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=3)
        self.grid_rowconfigure(4, weight=1)

        self.history: list[dict[str, str]] = []

        self.send_button: ttk.Button | None = None
        self.stop_button: ttk.Button | None = None
        self.clear_button: ttk.Button | None = None
        self.history_box: ScrolledText | None = None
        self.input_box: tk.Text | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        header = ttk.Label(self, text="Chat", style="Header.TLabel")
        header.grid(row=0, column=0, sticky="w")
        self.add_tooltip(header, "Open a conversation with your selected local model.")

        subtitle = ttk.Label(
            self,
            text="Chat with your selected Ollama model.",
            style="Body.TLabel",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(6, 18))
        self.add_tooltip(
            subtitle,
            "Use this workspace for multi-turn conversations powered by your local Ollama model.",
        )

        self.history_box = ScrolledText(
            self,
            wrap="word",
            font=("Segoe UI", 11),
            bd=1,
            relief="solid",
            padx=12,
            pady=12,
        )
        self.history_box.grid(row=2, column=0, sticky="nsew", pady=(0, 16))
        self.history_box.tag_configure(
            "user_label", foreground="#147cc1", font=("Segoe UI", 10, "bold")
        )
        self.history_box.tag_configure(
            "assistant_label", foreground="#0f766e", font=("Segoe UI", 10, "bold")
        )
        self.history_box.tag_configure(
            "system_label", foreground="#9f1239", font=("Segoe UI", 10, "bold")
        )
        self.add_tooltip(
            self.history_box,
            "Scrollable chat history for you and Sahayak AI. This area keeps the running conversation context.",
        )

        input_label = ttk.Label(self, text="Your Message", style="FieldLabel.TLabel")
        input_label.grid(
            row=3, column=0, sticky="w"
        )
        self.add_tooltip(input_label, "Type the message you want to send to the model.")

        self.input_box = tk.Text(
            self,
            height=5,
            wrap="word",
            font=("Segoe UI", 11),
            bd=1,
            relief="solid",
            padx=12,
            pady=12,
        )
        self.input_box.grid(row=4, column=0, sticky="ew", pady=(8, 6))
        self.input_box.bind("<Control-Return>", self._handle_ctrl_enter)
        self.add_tooltip(
            self.input_box,
            "Enter your message here. Press Ctrl+Enter or click Send to submit it.",
        )

        helper = ttk.Frame(self, style="Panel.TFrame")
        helper.grid(row=5, column=0, sticky="ew")
        helper.grid_columnconfigure(0, weight=1)

        shortcut_label = ttk.Label(
            helper,
            text="Ctrl+Enter to send",
            style="Body.TLabel",
        )
        shortcut_label.grid(row=0, column=0, sticky="w")
        self.add_tooltip(shortcut_label, "Keyboard shortcut for sending the current message.")

        self.clear_button = ttk.Button(
            helper,
            text="Clear Input",
            style="Secondary.TButton",
            command=self._clear_input,
        )
        self.clear_button.grid(row=0, column=1, sticky="e")
        self.add_tooltip(self.clear_button, "Clear the current chat input without affecting history.")

        actions = ttk.Frame(self, style="Panel.TFrame")
        actions.grid(row=6, column=0, sticky="e", pady=(12, 0))

        self.stop_button = ttk.Button(
            actions,
            text="Stop",
            style="Secondary.TButton",
            state="disabled",
            command=lambda: self.cancel_request(self._handle_stop),
        )
        self.stop_button.grid(row=0, column=0, padx=(0, 8))
        self.add_tooltip(self.stop_button, "Stop the active chat response.")

        self.send_button = ttk.Button(
            actions,
            text="Send",
            style="Primary.TButton",
            command=self._send_message,
        )
        self.send_button.grid(row=0, column=1)
        self.add_tooltip(self.send_button, "Send your message to the selected Ollama model.")

    def _handle_ctrl_enter(self, _event: tk.Event) -> str:
        """Send the message from the keyboard shortcut."""
        self._send_message()
        return "break"

    def _send_message(self) -> None:
        if self.input_box is None:
            return
        if self.is_running:
            return

        user_message = self.input_box.get("1.0", tk.END).strip()
        if not user_message:
            messagebox.showwarning("Input Required", "Please enter a message to send.")
            return

        self._append_message("user", user_message)
        self.history.append({"role": "user", "content": user_message})
        self.input_box.delete("1.0", tk.END)

        prompt = build_chat_prompt(self.history)
        self.run_prompt(
            prompt,
            self._handle_response,
            error_title="Chat Error",
            fallback_message="Unable to get a response right now.",
        )

    def _handle_response(self, response_text: str, _model_name: str) -> None:
        self.history.append({"role": "assistant", "content": response_text})
        self._append_message("assistant", response_text)

    def _handle_stop(self) -> None:
        self._append_message("system", "Response stopped.")

    def _clear_input(self) -> None:
        if self.input_box is not None:
            self.input_box.delete("1.0", tk.END)

    def _append_message(self, role: str, text: str) -> None:
        if self.history_box is None:
            return

        label_map = {
            "user": ("You", "user_label"),
            "assistant": ("Sahayak say:", "assistant_label"),
            "system": ("Status", "system_label"),
        }
        label, tag = label_map[role]

        if self.history_box.get("1.0", tk.END).strip():
            self.history_box.insert(tk.END, "\n\n")
        self.history_box.insert(tk.END, f"{label}\n", tag)
        self.history_box.insert(tk.END, text.strip())
        self.history_box.see(tk.END)

    def set_busy(self, is_busy: bool) -> None:
        if self.send_button is not None:
            self.send_button.configure(
                text="Sending..." if is_busy else "Send",
                state="disabled" if is_busy else "normal",
            )
        if self.stop_button is not None:
            self.stop_button.configure(state="normal" if is_busy else "disabled")
        if self.clear_button is not None:
            self.clear_button.configure(state="disabled" if is_busy else "normal")

    def on_request_error(self, fallback_message: str) -> None:
        self._append_message("system", fallback_message)
