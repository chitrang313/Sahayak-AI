"""Email helper feature panel."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from services.prompt_builder import RESPONSE_LENGTH_GUIDANCE, build_email_prompt
from ui.common import AsyncToolFrame, set_text_content
from utils.clipboard import copy_text


TITLES = ["Mr.", "Ms.", "Mrs.", "Dr.", "Prof.", "Mx."]
RESPONSE_LENGTHS = list(RESPONSE_LENGTH_GUIDANCE.keys())


class EmailUI(AsyncToolFrame):
    """Professional email helper interface."""

    def __init__(self, parent: tk.Misc, controller) -> None:
        super().__init__(parent, controller)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(9, weight=1)
        self.grid_rowconfigure(13, weight=1)

        self.title_var = tk.StringVar(value="Mr.")
        self.name_var = tk.StringVar()
        self.subject_var = tk.StringVar()
        self.response_length_var = tk.StringVar(value=RESPONSE_LENGTHS[1])

        self.generate_button: ttk.Button | None = None
        self.stop_button: ttk.Button | None = None
        self.clear_button: ttk.Button | None = None
        self.details_box: ScrolledText | None = None
        self.output_box: ScrolledText | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        ttk.Label(self, text="Email Helper", style="Header.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            self,
            text="Generate a professional email draft from a few details.",
            style="Body.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 18))

        ttk.Label(self, text="Recipient Title", style="FieldLabel.TLabel").grid(
            row=2, column=0, sticky="w"
        )
        ttk.Label(self, text="Recipient Name", style="FieldLabel.TLabel").grid(
            row=2, column=1, sticky="w", padx=(12, 0)
        )

        ttk.Combobox(
            self,
            textvariable=self.title_var,
            values=TITLES,
            state="readonly",
            width=12,
        ).grid(row=3, column=0, sticky="w", pady=(8, 16))

        ttk.Entry(
            self,
            textvariable=self.name_var,
            font=("Segoe UI", 10),
        ).grid(row=3, column=1, sticky="ew", padx=(12, 0), pady=(8, 16))

        ttk.Label(self, text="Subject", style="FieldLabel.TLabel").grid(
            row=4, column=0, columnspan=2, sticky="w"
        )
        ttk.Entry(
            self,
            textvariable=self.subject_var,
            font=("Segoe UI", 10),
        ).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 16))

        ttk.Label(self, text="Response Length", style="FieldLabel.TLabel").grid(
            row=6, column=0, columnspan=2, sticky="w"
        )
        ttk.Combobox(
            self,
            textvariable=self.response_length_var,
            values=RESPONSE_LENGTHS,
            state="readonly",
            width=24,
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(8, 16))

        ttk.Label(self, text="Content / Purpose", style="FieldLabel.TLabel").grid(
            row=8, column=0, columnspan=2, sticky="w"
        )
        self.details_box = ScrolledText(
            self,
            height=8,
            wrap="word",
            font=("Segoe UI", 11),
            bd=1,
            relief="solid",
            padx=12,
            pady=12,
        )
        self.details_box.grid(
            row=9, column=0, columnspan=2, sticky="nsew", pady=(8, 6)
        )

        detail_actions = ttk.Frame(self, style="Panel.TFrame")
        detail_actions.grid(row=10, column=0, columnspan=2, sticky="e", pady=(0, 12))

        self.clear_button = ttk.Button(
            detail_actions,
            text="Clear Form",
            style="Secondary.TButton",
            command=self._clear_form,
        )
        self.clear_button.grid(row=0, column=0)

        actions = ttk.Frame(self, style="Panel.TFrame")
        actions.grid(row=11, column=0, columnspan=2, sticky="e", pady=(0, 16))

        self.stop_button = ttk.Button(
            actions,
            text="Stop",
            style="Secondary.TButton",
            state="disabled",
            command=lambda: self.cancel_request(
                lambda: self._set_output("Email generation stopped.")
            ),
        )
        self.stop_button.grid(row=0, column=0, padx=(0, 8))

        self.generate_button = ttk.Button(
            actions,
            text="Generate",
            style="Primary.TButton",
            command=self._generate_email,
        )
        self.generate_button.grid(row=0, column=1, padx=(0, 8))

        ttk.Button(
            actions,
            text="Copy Text",
            style="Secondary.TButton",
            command=self._copy_output,
        ).grid(row=0, column=2)

        ttk.Label(self, text="Output", style="FieldLabel.TLabel").grid(
            row=12, column=0, columnspan=2, sticky="w"
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
        self.output_box.grid(
            row=13, column=0, columnspan=2, sticky="nsew", pady=(8, 0)
        )

    def _generate_email(self) -> None:
        if self.details_box is None:
            return

        name = self.name_var.get().strip()
        subject = self.subject_var.get().strip()
        details = self.details_box.get("1.0", tk.END).strip()

        if not name or not subject or not details:
            messagebox.showwarning(
                "Input Required",
                "Please enter recipient name, subject, and content details.",
            )
            return

        self._set_output("Generating email...")
        prompt = build_email_prompt(
            self.title_var.get(),
            name,
            subject,
            details,
            self.response_length_var.get(),
            self.controller.get_profile_data(),
        )
        self.run_prompt(
            prompt,
            self._handle_response,
            error_title="Email Helper Error",
            fallback_message="Unable to generate the email right now.",
        )

    def _handle_response(self, response_text: str, _model_name: str) -> None:
        self._set_output(response_text)

    def _set_output(self, value: str) -> None:
        if self.output_box is not None:
            set_text_content(self.output_box, value)

    def _clear_form(self) -> None:
        self.title_var.set(TITLES[0])
        self.name_var.set("")
        self.subject_var.set("")
        self.response_length_var.set(RESPONSE_LENGTHS[1])
        if self.details_box is not None:
            self.details_box.delete("1.0", tk.END)

    def _copy_output(self) -> None:
        if self.output_box is None:
            return
        text = self.output_box.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Nothing to Copy", "There is no email text yet.")
            return
        copy_text(self, text)
        messagebox.showinfo("Copied", "Email copied to clipboard.")

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
