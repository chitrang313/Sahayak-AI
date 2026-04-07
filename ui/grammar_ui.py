"""Grammar fix feature panel."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from services.prompt_builder import build_grammar_prompt
from ui.common import AsyncToolFrame, set_text_content
from utils.clipboard import copy_text


class GrammarUI(AsyncToolFrame):
    """Grammar and spelling correction interface."""

    def __init__(self, parent: tk.Misc, controller) -> None:
        super().__init__(parent, controller)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(7, weight=1)

        self.correct_button: ttk.Button | None = None
        self.stop_button: ttk.Button | None = None
        self.copy_button: ttk.Button | None = None
        self.clear_button: ttk.Button | None = None
        self.input_box: ScrolledText | None = None
        self.output_box: ScrolledText | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        header = ttk.Label(self, text="Grammar Fix", style="Header.TLabel")
        header.grid(
            row=0, column=0, sticky="w"
        )
        self.add_tooltip(header, "Clean up spelling, grammar, punctuation, and light phrasing.")

        subtitle = ttk.Label(
            self,
            text="Correct spelling and grammar using your local model.",
            style="Body.TLabel",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(6, 18))
        self.add_tooltip(
            subtitle,
            "Paste rough text here and Sahayak AI will return a cleaner version using your local model.",
        )

        input_label = ttk.Label(self, text="Input Text", style="FieldLabel.TLabel")
        input_label.grid(
            row=2, column=0, sticky="w"
        )
        self.add_tooltip(input_label, "Enter the text you want to correct.")

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
        self.add_tooltip(
            self.input_box,
            "Editable input area for the text that needs grammar and spelling correction.",
        )

        input_actions = ttk.Frame(self, style="Panel.TFrame")
        input_actions.grid(row=4, column=0, sticky="e", pady=(0, 12))

        self.clear_button = ttk.Button(
            input_actions,
            text="Clear Input",
            style="Secondary.TButton",
            command=self._clear_input,
        )
        self.clear_button.grid(row=0, column=0)
        self.add_tooltip(self.clear_button, "Clear the current input text.")

        controls = ttk.Frame(self, style="Panel.TFrame")
        controls.grid(row=5, column=0, sticky="e", pady=(0, 16))

        self.stop_button = ttk.Button(
            controls,
            text="Stop",
            style="Secondary.TButton",
            state="disabled",
            command=lambda: self.cancel_request(
                lambda: self._set_output("Correction stopped.")
            ),
        )
        self.stop_button.grid(row=0, column=0, padx=(0, 8))
        self.add_tooltip(self.stop_button, "Stop the active grammar correction request.")

        self.correct_button = ttk.Button(
            controls,
            text="Correct",
            style="Primary.TButton",
            command=self._correct_text,
        )
        self.correct_button.grid(row=0, column=1, padx=(0, 8))
        self.add_tooltip(self.correct_button, "Send the input text for correction.")

        self.copy_button = ttk.Button(
            controls,
            text="Copy Text",
            style="Secondary.TButton",
            command=self._copy_output,
        )
        self.copy_button.grid(row=0, column=2)
        self.add_tooltip(self.copy_button, "Copy the corrected output to your clipboard.")

        output_label = ttk.Label(self, text="Output", style="FieldLabel.TLabel")
        output_label.grid(
            row=6, column=0, sticky="w"
        )
        self.add_tooltip(output_label, "Corrected result from the model.")

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
        self.add_tooltip(
            self.output_box,
            "Editable corrected output. You can fine-tune the result before copying it.",
        )

    def _correct_text(self) -> None:
        if self.input_box is None:
            return

        user_input = self.input_box.get("1.0", tk.END).strip()
        if not user_input:
            messagebox.showwarning("Input Required", "Please enter text to correct.")
            return

        self._set_output("Correcting text...")
        prompt = build_grammar_prompt(user_input)
        self.run_prompt(
            prompt,
            self._handle_response,
            error_title="Grammar Fix Error",
            fallback_message="Unable to correct the text right now.",
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
            messagebox.showwarning("Nothing to Copy", "There is no corrected text yet.")
            return
        copy_text(self, text)
        messagebox.showinfo("Copied", "Corrected text copied to clipboard.")

    def set_busy(self, is_busy: bool) -> None:
        if self.correct_button is not None:
            self.correct_button.configure(
                text="Correcting..." if is_busy else "Correct",
                state="disabled" if is_busy else "normal",
            )
        if self.stop_button is not None:
            self.stop_button.configure(state="normal" if is_busy else "disabled")
        if self.clear_button is not None:
            self.clear_button.configure(state="disabled" if is_busy else "normal")

    def on_request_error(self, fallback_message: str) -> None:
        self._set_output(fallback_message)
