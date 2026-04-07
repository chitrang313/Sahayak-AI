"""Translator feature panel."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from services.prompt_builder import build_translation_prompt
from ui.common import AsyncToolFrame, set_text_content
from utils.clipboard import copy_text


LANGUAGES = [
    "Hindi",
    "Gujarati",
    "English",
    "Spanish",
    "French",
    "German",
    "Japanese",
]


class TranslatorUI(AsyncToolFrame):
    """Translation interface."""

    def __init__(self, parent: tk.Misc, controller) -> None:
        super().__init__(parent, controller)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(7, weight=1)

        self.from_language = tk.StringVar(value="English")
        self.to_language = tk.StringVar(value="Hindi")

        self.translate_button: ttk.Button | None = None
        self.stop_button: ttk.Button | None = None
        self.copy_button: ttk.Button | None = None
        self.clear_button: ttk.Button | None = None
        self.input_box: ScrolledText | None = None
        self.output_box: ScrolledText | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        ttk.Label(self, text="Translator", style="Header.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            self,
            text="Translate text between supported languages.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 18))

        ttk.Label(self, text="Input Text", style="FieldLabel.TLabel").grid(
            row=2, column=0, sticky="w"
        )

        self.input_box = ScrolledText(
            self,
            height=10,
            wrap="word",
            font=("Segoe UI", 11),
            bd=1,
            relief="solid",
            padx=12,
            pady=12,
        )
        self.input_box.grid(row=3, column=0, sticky="nsew", pady=(8, 6))

        input_actions = ttk.Frame(self, style="Panel.TFrame")
        input_actions.grid(row=4, column=0, sticky="e", pady=(0, 12))

        self.clear_button = ttk.Button(
            input_actions,
            text="Clear Input",
            style="Secondary.TButton",
            command=self._clear_input,
        )
        self.clear_button.grid(row=0, column=0)

        controls = ttk.Frame(self, style="Panel.TFrame")
        controls.grid(row=5, column=0, sticky="ew", pady=(0, 16))
        controls.grid_columnconfigure(2, weight=1)

        ttk.Label(controls, text="From", style="FieldLabel.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(controls, text="To", style="FieldLabel.TLabel").grid(
            row=0, column=1, sticky="w", padx=(12, 0)
        )

        ttk.Combobox(
            controls,
            textvariable=self.from_language,
            values=LANGUAGES,
            state="readonly",
            width=16,
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        ttk.Combobox(
            controls,
            textvariable=self.to_language,
            values=LANGUAGES,
            state="readonly",
            width=16,
        ).grid(row=1, column=1, sticky="w", padx=(12, 0), pady=(8, 0))

        button_wrap = ttk.Frame(controls, style="Panel.TFrame")
        button_wrap.grid(row=1, column=2, sticky="e", pady=(8, 0))

        self.stop_button = ttk.Button(
            button_wrap,
            text="Stop Translate",
            style="Secondary.TButton",
            state="disabled",
            command=lambda: self.cancel_request(
                lambda: self._set_output("Translation stopped.")
            ),
        )
        self.stop_button.grid(row=0, column=0, padx=(0, 8))

        self.translate_button = ttk.Button(
            button_wrap,
            text="Translate",
            style="Primary.TButton",
            command=self._translate_text,
        )
        self.translate_button.grid(row=0, column=1, padx=(0, 8))

        self.copy_button = ttk.Button(
            button_wrap,
            text="Copy Text",
            style="Secondary.TButton",
            command=self._copy_output,
        )
        self.copy_button.grid(row=0, column=2)

        ttk.Label(self, text="Output", style="FieldLabel.TLabel").grid(
            row=6, column=0, sticky="w"
        )

        self.output_box = ScrolledText(
            self,
            height=10,
            wrap="word",
            font=("Segoe UI", 11),
            bd=1,
            relief="solid",
            padx=12,
            pady=12,
        )
        self.output_box.grid(row=7, column=0, sticky="nsew", pady=(8, 0))

    def _translate_text(self) -> None:
        if self.input_box is None:
            return

        user_input = self.input_box.get("1.0", tk.END).strip()
        from_language = self.from_language.get()
        to_language = self.to_language.get()

        if not user_input:
            messagebox.showwarning("Input Required", "Please enter text to translate.")
            return
        if from_language == to_language:
            messagebox.showwarning(
                "Language Selection",
                "Source and target languages must be different.",
            )
            return

        self._set_output("Translating...")
        prompt = build_translation_prompt(user_input, from_language, to_language)
        self.run_prompt(
            prompt,
            self._handle_response,
            error_title="Translation Error",
            fallback_message="Unable to translate right now. Please try again.",
        )

    def _handle_response(self, response_text: str, _model_name: str) -> None:
        self._set_output(response_text)

    def _set_output(self, value: str) -> None:
        if self.output_box is not None:
            set_text_content(self.output_box, value)

    def _clear_input(self) -> None:
        if self.input_box is not None:
            self.input_box.delete("1.0", tk.END)

    def _copy_output(self) -> None:
        if self.output_box is None:
            return
        text = self.output_box.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Nothing to Copy", "There is no translated text yet.")
            return
        copy_text(self, text)
        messagebox.showinfo("Copied", "Translated text copied to clipboard.")

    def set_busy(self, is_busy: bool) -> None:
        if self.translate_button is not None:
            self.translate_button.configure(
                text="Translating..." if is_busy else "Translate",
                state="disabled" if is_busy else "normal",
            )
        if self.stop_button is not None:
            self.stop_button.configure(state="normal" if is_busy else "disabled")
        if self.clear_button is not None:
            self.clear_button.configure(state="disabled" if is_busy else "normal")

    def on_request_error(self, fallback_message: str) -> None:
        self._set_output(fallback_message)
