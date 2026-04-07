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
        header = ttk.Label(self, text="Email Helper", style="Header.TLabel")
        header.grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        self.add_tooltip(header, "Draft a professional email with your local model.")

        subtitle = ttk.Label(
            self,
            text="Generate a professional email draft from a few details.",
            style="Body.TLabel",
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 18))
        self.add_tooltip(
            subtitle,
            "Use your saved profile plus the form fields below to generate a polished email draft.",
        )

        title_label = ttk.Label(self, text="Recipient Title", style="FieldLabel.TLabel")
        title_label.grid(
            row=2, column=0, sticky="w"
        )
        self.add_tooltip(title_label, "Choose the recipient title for the email.")

        name_label = ttk.Label(self, text="Recipient Name", style="FieldLabel.TLabel")
        name_label.grid(
            row=2, column=1, sticky="w", padx=(12, 0)
        )
        self.add_tooltip(name_label, "Enter the recipient name.")

        title_combo = ttk.Combobox(
            self,
            textvariable=self.title_var,
            values=TITLES,
            state="readonly",
            width=12,
        )
        title_combo.grid(row=3, column=0, sticky="w", pady=(8, 16))
        self.add_tooltip(title_combo, "Select how the recipient should be addressed.")

        name_entry = ttk.Entry(
            self,
            textvariable=self.name_var,
            font=("Segoe UI", 10),
        )
        name_entry.grid(row=3, column=1, sticky="ew", padx=(12, 0), pady=(8, 16))
        self.add_tooltip(name_entry, "Recipient name used in the generated email.")

        subject_label = ttk.Label(self, text="Subject", style="FieldLabel.TLabel")
        subject_label.grid(
            row=4, column=0, columnspan=2, sticky="w"
        )
        self.add_tooltip(subject_label, "Subject line for the email draft.")

        subject_entry = ttk.Entry(
            self,
            textvariable=self.subject_var,
            font=("Segoe UI", 10),
        )
        subject_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 16))
        self.add_tooltip(subject_entry, "Enter the email subject.")

        length_label = ttk.Label(self, text="Response Length", style="FieldLabel.TLabel")
        length_label.grid(
            row=6, column=0, columnspan=2, sticky="w"
        )
        self.add_tooltip(length_label, "Choose how short or detailed the email should be.")

        length_combo = ttk.Combobox(
            self,
            textvariable=self.response_length_var,
            values=RESPONSE_LENGTHS,
            state="readonly",
            width=24,
        )
        length_combo.grid(row=7, column=0, columnspan=2, sticky="w", pady=(8, 16))
        self.add_tooltip(length_combo, "Select short, mid, or long email response length.")

        details_label = ttk.Label(self, text="Content / Purpose", style="FieldLabel.TLabel")
        details_label.grid(
            row=8, column=0, columnspan=2, sticky="w"
        )
        self.add_tooltip(details_label, "Describe what the email should say and why it is being written.")
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
        self.add_tooltip(
            self.details_box,
            "Enter the context, purpose, and any important details for the email draft.",
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
        self.add_tooltip(self.clear_button, "Clear all email form fields and reset the defaults.")

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
        self.add_tooltip(self.stop_button, "Stop the active email generation request.")

        self.generate_button = ttk.Button(
            actions,
            text="Generate",
            style="Primary.TButton",
            command=self._generate_email,
        )
        self.generate_button.grid(row=0, column=1, padx=(0, 8))
        self.add_tooltip(self.generate_button, "Generate a professional email from the current form.")

        copy_button = ttk.Button(
            actions,
            text="Copy Text",
            style="Secondary.TButton",
            command=self._copy_output,
        )
        copy_button.grid(row=0, column=2)
        self.add_tooltip(copy_button, "Copy the generated email to your clipboard.")

        output_label = ttk.Label(self, text="Output", style="FieldLabel.TLabel")
        output_label.grid(
            row=12, column=0, columnspan=2, sticky="w"
        )
        self.add_tooltip(output_label, "Generated email draft.")
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
        self.add_tooltip(
            self.output_box,
            "Editable email draft. You can tweak the final wording before sending it.",
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
