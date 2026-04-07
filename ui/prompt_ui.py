"""Detailed prompt creator feature panel."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from services.prompt_builder import (
    RESPONSE_LENGTH_GUIDANCE,
    build_prompt_creator_prompt,
)
from ui.common import AsyncToolFrame, set_text_content
from utils.clipboard import copy_text


CATEGORIES = [
    "Programmer",
    "Designer",
    "Content Writer",
    "General Work",
    "Medical Expert",
    "Marketing Expert",
    "Product Manager",
    "Data Analyst",
    "Teacher",
    "Legal Advisor",
]
RESPONSE_LENGTHS = list(RESPONSE_LENGTH_GUIDANCE.keys())


class PromptUI(AsyncToolFrame):
    """Prompt creator interface."""

    def __init__(self, parent: tk.Misc, controller) -> None:
        super().__init__(parent, controller)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(8, weight=1)

        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.response_length_var = tk.StringVar(value=RESPONSE_LENGTHS[1])
        self.generate_button: ttk.Button | None = None
        self.stop_button: ttk.Button | None = None
        self.clear_button: ttk.Button | None = None
        self.idea_box: ScrolledText | None = None
        self.output_box: ScrolledText | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        ttk.Label(self, text="Prompt Creator", style="Header.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            self,
            text="Turn a rough idea into a more detailed AI prompt.",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 18))

        controls = ttk.Frame(self, style="Panel.TFrame")
        controls.grid(row=2, column=0, sticky="w", pady=(0, 16))

        ttk.Label(controls, text="Category", style="FieldLabel.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            controls,
            text="Response Length",
            style="FieldLabel.TLabel",
        ).grid(row=0, column=1, sticky="w", padx=(16, 0))

        ttk.Combobox(
            controls,
            textvariable=self.category_var,
            values=CATEGORIES,
            state="readonly",
            width=20,
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        ttk.Combobox(
            controls,
            textvariable=self.response_length_var,
            values=RESPONSE_LENGTHS,
            state="readonly",
            width=24,
        ).grid(row=1, column=1, sticky="w", padx=(16, 0), pady=(8, 0))

        ttk.Label(self, text="User Idea", style="FieldLabel.TLabel").grid(
            row=3, column=0, sticky="w"
        )
        self.idea_box = ScrolledText(
            self,
            height=8,
            wrap="word",
            font=("Segoe UI", 11),
            bd=1,
            relief="solid",
            padx=12,
            pady=12,
        )
        self.idea_box.grid(row=4, column=0, sticky="nsew", pady=(8, 6))

        input_actions = ttk.Frame(self, style="Panel.TFrame")
        input_actions.grid(row=5, column=0, sticky="e", pady=(0, 12))

        self.clear_button = ttk.Button(
            input_actions,
            text="Clear Input",
            style="Secondary.TButton",
            command=self._clear_input,
        )
        self.clear_button.grid(row=0, column=0)

        actions = ttk.Frame(self, style="Panel.TFrame")
        actions.grid(row=6, column=0, sticky="e", pady=(0, 16))

        self.stop_button = ttk.Button(
            actions,
            text="Stop",
            style="Secondary.TButton",
            state="disabled",
            command=lambda: self.cancel_request(
                lambda: self._set_output("Prompt generation stopped.")
            ),
        )
        self.stop_button.grid(row=0, column=0, padx=(0, 8))

        self.generate_button = ttk.Button(
            actions,
            text="Generate",
            style="Primary.TButton",
            command=self._generate_prompt,
        )
        self.generate_button.grid(row=0, column=1, padx=(0, 8))

        ttk.Button(
            actions,
            text="Copy Text",
            style="Secondary.TButton",
            command=self._copy_output,
        ).grid(row=0, column=2)

        ttk.Label(self, text="Output", style="FieldLabel.TLabel").grid(
            row=7, column=0, sticky="w"
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
        self.output_box.grid(row=8, column=0, sticky="nsew", pady=(8, 0))

    def _generate_prompt(self) -> None:
        if self.idea_box is None:
            return

        idea = self.idea_box.get("1.0", tk.END).strip()
        if not idea:
            messagebox.showwarning("Input Required", "Please enter a request idea.")
            return

        self._set_output("Generating response...")
        prompt = build_prompt_creator_prompt(
            self.category_var.get(),
            idea,
            self.response_length_var.get(),
        )
        self.run_prompt(
            prompt,
            self._handle_response,
            error_title="Prompt Creator Error",
            fallback_message="Unable to generate the prompt right now.",
        )

    def _handle_response(self, response_text: str, _model_name: str) -> None:
        self._set_output(response_text)

    def _set_output(self, value: str) -> None:
        if self.output_box is not None:
            set_text_content(self.output_box, value)

    def _clear_input(self) -> None:
        if self.idea_box is not None:
            self.idea_box.delete("1.0", tk.END)

    def _copy_output(self) -> None:
        if self.output_box is None:
            return
        text = self.output_box.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Nothing to Copy", "There is no generated prompt yet.")
            return
        copy_text(self, text)
        messagebox.showinfo("Copied", "Prompt copied to clipboard.")

    def set_busy(self, is_busy: bool) -> None:
        if self.generate_button is not None:
            self.generate_button.configure(
                text="Generating..." if is_busy else "Generate",
                state="disabled" if is_busy else "normal",
            )
        if self.stop_button is not None:
            self.stop_button.configure(state="normal" if is_busy else "disabled")
        if self.clear_button is not None:
            self.clear_button.configure(state="disabled" if is_busy else "normal")

    def on_request_error(self, fallback_message: str) -> None:
        self._set_output(fallback_message)
