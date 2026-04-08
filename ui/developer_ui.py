"""Developer-focused assistant panel."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from services.prompt_builder import (
    BOILERPLATE_LANGUAGES,
    DEVELOPER_MODE_OPTIONS,
    build_developer_prompt,
)
from ui.common import AsyncToolFrame, set_text_content
from utils.clipboard import copy_text
from utils.developer_context import (
    DeveloperContextError,
    prepare_code_understanding_input,
    prepare_json_input,
    prepare_precommit_input,
    prepare_security_input,
    prepare_text_input,
)


DEVELOPER_REQUEST_TIMEOUT = 180

MODE_CONFIGS = {
    "code_explain": {
        "description": (
            "Explain a file or directory path with purpose, flow, components, and risks."
        ),
        "path_required": True,
        "text_required": False,
        "language_required": False,
        "path_label": "File or Directory Path",
        "text_label": "Input",
        "generate_label": "Analyze",
        "busy_label": "Analyzing...",
        "status_label": "Preparing code understanding analysis...",
        "allow_file": True,
        "allow_directory": True,
    },
    "debug": {
        "description": "Analyze an error message and explain the root cause in simple language.",
        "path_required": False,
        "text_required": True,
        "language_required": False,
        "path_label": "Path",
        "text_label": "Error Text",
        "generate_label": "Debug",
        "busy_label": "Debugging...",
        "status_label": "Analyzing the error...",
        "allow_file": False,
        "allow_directory": False,
    },
    "refactor": {
        "description": "Review code, keep behavior the same, and return a cleaner refactored version.",
        "path_required": False,
        "text_required": True,
        "language_required": False,
        "path_label": "Path",
        "text_label": "Code",
        "generate_label": "Refactor",
        "busy_label": "Refactoring...",
        "status_label": "Refactoring code...",
        "allow_file": False,
        "allow_directory": False,
    },
    "boilerplate": {
        "description": "Generate production-ready boilerplate from requirements and a language choice.",
        "path_required": False,
        "text_required": True,
        "language_required": True,
        "path_label": "Path",
        "text_label": "Requirements",
        "generate_label": "Generate",
        "busy_label": "Generating...",
        "status_label": "Generating boilerplate code...",
        "allow_file": False,
        "allow_directory": False,
    },
    "api_explain": {
        "description": "Explain large JSON payloads with hierarchy, field meaning, and a short summary.",
        "path_required": False,
        "text_required": True,
        "language_required": False,
        "path_label": "Path",
        "text_label": "JSON Input",
        "generate_label": "Explain JSON",
        "busy_label": "Explaining...",
        "status_label": "Preparing JSON explanation...",
        "allow_file": False,
        "allow_directory": False,
    },
    "precommit": {
        "description": "Review staged and unstaged git changes as a strict pre-commit code reviewer.",
        "path_required": True,
        "text_required": False,
        "language_required": False,
        "path_label": "Repository Path",
        "text_label": "Input",
        "generate_label": "Review Changes",
        "busy_label": "Reviewing...",
        "status_label": "Collecting git changes for review...",
        "allow_file": False,
        "allow_directory": True,
    },
    "security": {
        "description": "Scan repository diffs and file contents for secrets and security vulnerabilities.",
        "path_required": True,
        "text_required": False,
        "language_required": False,
        "path_label": "Repository Path",
        "text_label": "Input",
        "generate_label": "Run Security Scan",
        "busy_label": "Scanning...",
        "status_label": "Collecting repository content for security analysis...",
        "allow_file": False,
        "allow_directory": True,
    },
    "performance": {
        "description": "Find bottlenecks in code and suggest a faster version with expected impact.",
        "path_required": False,
        "text_required": True,
        "language_required": False,
        "path_label": "Path",
        "text_label": "Code",
        "generate_label": "Optimize",
        "busy_label": "Optimizing...",
        "status_label": "Analyzing performance bottlenecks...",
        "allow_file": False,
        "allow_directory": False,
    },
}
MODE_LABEL_TO_ID = {
    label: mode_id
    for mode_id, label in DEVELOPER_MODE_OPTIONS
}
MODE_ID_TO_LABEL = {
    mode_id: label
    for mode_id, label in DEVELOPER_MODE_OPTIONS
}
DEFAULT_MODE = DEVELOPER_MODE_OPTIONS[0][0]


class DeveloperAssistantUI(AsyncToolFrame):
    """Integrated developer assistant workspace."""

    def __init__(self, parent: tk.Misc, controller) -> None:
        super().__init__(parent, controller)
        self.grid_columnconfigure(0, weight=1)

        self.mode_var = tk.StringVar(value=MODE_ID_TO_LABEL[DEFAULT_MODE])
        self.path_var = tk.StringVar()
        self.language_var = tk.StringVar(value=BOILERPLATE_LANGUAGES[0])
        self.mode_description_var = tk.StringVar()
        self.path_label_var = tk.StringVar()
        self.text_label_var = tk.StringVar()

        self.mode_combo: ttk.Combobox | None = None
        self.path_section: ttk.Frame | None = None
        self.path_entry: ttk.Entry | None = None
        self.file_button: ttk.Button | None = None
        self.folder_button: ttk.Button | None = None
        self.text_label_widget: ttk.Label | None = None
        self.input_box: ScrolledText | None = None
        self.language_section: ttk.Frame | None = None
        self.generate_button: ttk.Button | None = None
        self.stop_button: ttk.Button | None = None
        self.clear_button: ttk.Button | None = None
        self.output_box: ScrolledText | None = None

        self._build_ui()
        self._apply_mode_config()

    def _build_ui(self) -> None:
        header = ttk.Label(self, text="Developer Assistant", style="Header.TLabel")
        header.grid(row=0, column=0, sticky="w")
        self.add_tooltip(
            header,
            "Use developer-focused analysis and generation tools with your local model.",
        )

        subtitle = ttk.Label(
            self,
            text=(
                "Analyze code, review diffs, explain JSON, and generate structured "
                "developer outputs."
            ),
            style="Body.TLabel",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(6, 18))
        self.add_tooltip(
            subtitle,
            "This panel reuses the existing local Ollama flow for developer-specific work.",
        )

        controls = ttk.Frame(self, style="Panel.TFrame")
        controls.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        controls.grid_columnconfigure(1, weight=1)

        mode_label = ttk.Label(controls, text="Mode", style="FieldLabel.TLabel")
        mode_label.grid(row=0, column=0, sticky="w")
        self.add_tooltip(mode_label, "Choose the developer task you want to run.")

        self.mode_combo = ttk.Combobox(
            controls,
            textvariable=self.mode_var,
            values=[label for _mode_id, label in DEVELOPER_MODE_OPTIONS],
            state="readonly",
            width=34,
        )
        self.mode_combo.grid(row=0, column=1, sticky="w", padx=(12, 0))
        self.mode_combo.bind("<<ComboboxSelected>>", lambda _event: self._apply_mode_config())
        self.add_tooltip(
            self.mode_combo,
            "Switch between code explanation, debugging, refactoring, review, and other developer modes.",
        )

        description_label = ttk.Label(
            self,
            textvariable=self.mode_description_var,
            style="Body.TLabel",
            wraplength=900,
            justify="left",
        )
        description_label.grid(row=3, column=0, sticky="w", pady=(0, 14))
        self.add_tooltip(
            description_label,
            "Quick explanation of the currently selected developer workflow.",
        )

        self.path_section = ttk.Frame(self, style="Panel.TFrame")
        self.path_section.grid(row=4, column=0, sticky="ew", pady=(0, 14))
        self.path_section.grid_columnconfigure(1, weight=1)

        path_label = ttk.Label(
            self.path_section,
            textvariable=self.path_label_var,
            style="FieldLabel.TLabel",
        )
        path_label.grid(row=0, column=0, sticky="w")
        self.add_tooltip(
            path_label,
            "Provide a file, directory, or repository path depending on the selected mode.",
        )

        self.path_entry = ttk.Entry(
            self.path_section,
            textvariable=self.path_var,
            font=("Segoe UI", 10),
        )
        self.path_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.add_tooltip(
            self.path_entry,
            "You can type a path manually or use the browse buttons.",
        )

        button_row = ttk.Frame(self.path_section, style="Panel.TFrame")
        button_row.grid(row=1, column=2, sticky="e", padx=(12, 0), pady=(8, 0))

        self.file_button = ttk.Button(
            button_row,
            text="Browse File",
            style="Secondary.TButton",
            command=self._browse_file,
        )
        self.file_button.grid(row=0, column=0, padx=(0, 8))
        self.add_tooltip(
            self.file_button,
            "Select a single file to analyze when the mode supports file input.",
        )

        self.folder_button = ttk.Button(
            button_row,
            text="Browse Folder",
            style="Secondary.TButton",
            command=self._browse_folder,
        )
        self.folder_button.grid(row=0, column=1)
        self.add_tooltip(
            self.folder_button,
            "Select a directory or repository folder for analysis.",
        )

        self.text_label_widget = ttk.Label(
            self,
            textvariable=self.text_label_var,
            style="FieldLabel.TLabel",
        )
        self.text_label_widget.grid(row=5, column=0, sticky="w")
        self.add_tooltip(
            self.text_label_widget,
            "Enter code, errors, JSON, or requirements depending on the selected mode.",
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
        self.input_box.grid(row=6, column=0, sticky="nsew", pady=(8, 14))
        self.add_tooltip(
            self.input_box,
            "Primary text input area for the selected developer task.",
        )

        self.language_section = ttk.Frame(self, style="Panel.TFrame")
        self.language_section.grid(row=7, column=0, sticky="w", pady=(0, 14))

        language_label = ttk.Label(
            self.language_section,
            text="Language",
            style="FieldLabel.TLabel",
        )
        language_label.grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.add_tooltip(
            language_label,
            "Choose the target language for boilerplate generation.",
        )

        for index, language in enumerate(BOILERPLATE_LANGUAGES):
            radio = ttk.Radiobutton(
                self.language_section,
                text=language,
                value=language,
                variable=self.language_var,
            )
            row = (index // 4) + 1
            column = index % 4
            radio.grid(row=row, column=column, sticky="w", padx=(0, 18), pady=(0, 4))
            self.add_tooltip(radio, f"Generate boilerplate in {language}.")

        utility_row = ttk.Frame(self, style="Panel.TFrame")
        utility_row.grid(row=9, column=0, sticky="e", pady=(0, 12))

        self.clear_button = ttk.Button(
            utility_row,
            text="Clear Input",
            style="Secondary.TButton",
            command=self._clear_inputs,
        )
        self.clear_button.grid(row=0, column=0)
        self.add_tooltip(
            self.clear_button,
            "Clear the current path, text input, and generated output.",
        )

        actions = ttk.Frame(self, style="Panel.TFrame")
        actions.grid(row=10, column=0, sticky="e", pady=(0, 16))

        self.stop_button = ttk.Button(
            actions,
            text="Stop",
            style="Secondary.TButton",
            state="disabled",
            command=lambda: self.cancel_request(
                lambda: self._set_output("Developer request stopped.")
            ),
        )
        self.stop_button.grid(row=0, column=0, padx=(0, 8))
        self.add_tooltip(self.stop_button, "Stop the active developer-assistant request.")

        self.generate_button = ttk.Button(
            actions,
            text="Analyze",
            style="Primary.TButton",
            command=self._run_mode,
        )
        self.generate_button.grid(row=0, column=1, padx=(0, 8))
        self.add_tooltip(
            self.generate_button,
            "Run the selected developer workflow with the current input.",
        )

        copy_button = ttk.Button(
            actions,
            text="Copy Text",
            style="Secondary.TButton",
            command=self._copy_output,
        )
        copy_button.grid(row=0, column=2)
        self.add_tooltip(copy_button, "Copy the generated developer output to your clipboard.")

        output_label = ttk.Label(self, text="Output", style="FieldLabel.TLabel")
        output_label.grid(row=11, column=0, sticky="w")
        self.add_tooltip(output_label, "Structured output from the selected developer mode.")

        self.output_box = ScrolledText(
            self,
            height=12,
            wrap="word",
            font=("Segoe UI", 11),
            bd=1,
            relief="solid",
            padx=12,
            pady=12,
        )
        self.output_box.grid(row=12, column=0, sticky="nsew", pady=(8, 0))
        self.add_tooltip(
            self.output_box,
            "Editable developer output so you can refine or reuse the result.",
        )
        self.grid_rowconfigure(12, weight=1)

    def _get_selected_mode(self) -> str:
        """Resolve the selected mode identifier from the combobox label."""
        return MODE_LABEL_TO_ID[self.mode_var.get()]

    def _apply_mode_config(self) -> None:
        """Refresh visible inputs and labels for the selected developer mode."""
        mode = self._get_selected_mode()
        config = MODE_CONFIGS[mode]

        self.mode_description_var.set(config["description"])
        self.path_label_var.set(config["path_label"])
        self.text_label_var.set(config["text_label"])

        if self.path_section is not None:
            if config["path_required"]:
                self.path_section.grid()
            else:
                self.path_section.grid_remove()

        if self.text_label_widget is not None and self.input_box is not None:
            if config["text_required"]:
                self.text_label_widget.grid()
                self.input_box.grid()
            else:
                self.text_label_widget.grid_remove()
                self.input_box.grid_remove()

        if self.language_section is not None:
            if config["language_required"]:
                self.language_section.grid()
            else:
                self.language_section.grid_remove()

        if self.file_button is not None:
            self.file_button.configure(
                state="normal" if config["allow_file"] else "disabled"
            )
        if self.folder_button is not None:
            self.folder_button.configure(
                state="normal" if config["allow_directory"] else "disabled"
            )
        if self.generate_button is not None and not self.is_running:
            self.generate_button.configure(text=config["generate_label"])

    def _browse_file(self) -> None:
        """Open a file picker for file-based analysis."""
        selected_path = filedialog.askopenfilename()
        if selected_path:
            self.path_var.set(selected_path)

    def _browse_folder(self) -> None:
        """Open a folder picker for directory-based analysis."""
        selected_path = filedialog.askdirectory()
        if selected_path:
            self.path_var.set(selected_path)

    def _run_mode(self) -> None:
        """Prepare the selected input and send the request to Ollama."""
        mode = self._get_selected_mode()
        config = MODE_CONFIGS[mode]

        try:
            prepared_input = self._prepare_input_for_mode(mode)
        except DeveloperContextError as exc:
            messagebox.showwarning("Developer Assistant", str(exc))
            return

        self._set_output(config["status_label"])
        prompt = build_developer_prompt(
            mode,
            prepared_input,
            language=self.language_var.get() if config["language_required"] else None,
        )
        self.run_prompt(
            prompt,
            self._handle_response,
            error_title="Developer Assistant Error",
            fallback_message="Unable to complete the developer request right now.",
            timeout=DEVELOPER_REQUEST_TIMEOUT,
        )

    def _prepare_input_for_mode(self, mode: str) -> str:
        """Prepare the correct prompt input for the selected mode."""
        text_input = self._get_text_input()
        path_input = self.path_var.get()

        if mode == "code_explain":
            return prepare_code_understanding_input(path_input)
        if mode == "debug":
            return prepare_text_input(text_input, label="Error text")
        if mode == "refactor":
            return prepare_text_input(text_input, label="Code input")
        if mode == "boilerplate":
            return prepare_text_input(text_input, label="Requirements")
        if mode == "api_explain":
            return prepare_json_input(text_input)
        if mode == "precommit":
            return prepare_precommit_input(path_input)
        if mode == "security":
            return prepare_security_input(path_input)
        if mode == "performance":
            return prepare_text_input(text_input, label="Code input")

        raise DeveloperContextError("Unsupported developer mode selected.")

    def _get_text_input(self) -> str:
        """Read the current text-box value safely."""
        if self.input_box is None:
            return ""
        return self.input_box.get("1.0", tk.END).rstrip()

    def _handle_response(self, response_text: str, _model_name: str) -> None:
        """Render the model response into the output box."""
        self._set_output(response_text)

    def _set_output(self, value: str) -> None:
        """Update the output box contents."""
        if self.output_box is not None:
            set_text_content(self.output_box, value)

    def _clear_inputs(self) -> None:
        """Reset the current developer-assistant inputs."""
        self.path_var.set("")
        self.language_var.set(BOILERPLATE_LANGUAGES[0])
        if self.input_box is not None:
            self.input_box.delete("1.0", tk.END)
        self._set_output("")

    def _copy_output(self) -> None:
        """Copy the generated output to the clipboard."""
        if self.output_box is None:
            return

        text = self.output_box.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Nothing to Copy", "There is no generated output yet.")
            return

        copy_text(self, text)
        messagebox.showinfo("Copied", "Developer output copied to clipboard.")

    def set_busy(self, is_busy: bool) -> None:
        """Update button state while a request is running."""
        mode = self._get_selected_mode()
        config = MODE_CONFIGS[mode]

        if self.mode_combo is not None:
            self.mode_combo.configure(state="disabled" if is_busy else "readonly")
        if self.generate_button is not None:
            self.generate_button.configure(
                text=config["busy_label"] if is_busy else config["generate_label"],
                state="disabled" if is_busy else "normal",
            )
        if self.stop_button is not None:
            self.stop_button.configure(state="normal" if is_busy else "disabled")
        if self.clear_button is not None:
            self.clear_button.configure(state="disabled" if is_busy else "normal")
        if self.file_button is not None:
            self.file_button.configure(
                state="disabled"
                if is_busy or not config["allow_file"]
                else "normal"
            )
        if self.folder_button is not None:
            self.folder_button.configure(
                state="disabled"
                if is_busy or not config["allow_directory"]
                else "normal"
            )

    def on_request_error(self, fallback_message: str) -> None:
        """Show a fallback message in the output box on failure."""
        self._set_output(fallback_message)
