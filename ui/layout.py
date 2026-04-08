"""Main layout for the Sahayak AI desktop application."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from services.ollama_service import DEFAULT_MODEL, OllamaService
from ui.chat_ui import ChatUI
from ui.common import add_tooltip
from ui.developer_ui import DeveloperAssistantUI
from ui.email_ui import EmailUI
from ui.grammar_ui import GrammarUI
from ui.prompt_ui import PromptUI
from ui.translator_ui import TranslatorUI
from utils.profile_store import load_profile, save_profile
from utils.status_checker import is_ollama_running


APP_DISPLAY_NAME = "AI Developer Assistant (Extended)"

NAV_ITEMS = [
    ("Chat", ChatUI),
    ("Developer Assistant", DeveloperAssistantUI),
    ("Grammar Fix", GrammarUI),
    ("Translator", TranslatorUI),
    ("Email Helper", EmailUI),
    ("Prompt Creator", PromptUI),
]

HOW_TO_USE_TEXT = f"""How To Use {APP_DISPLAY_NAME}

1. Start Ollama on your computer.
2. Open the app and check the bottom-left status dot.
3. Pick an installed model from the bottom-right dropdown.
4. Use the left navigation to switch tools.

Feature Guide

Chat
- Type your message and click Send.
- Press Ctrl+Enter to send faster.
- Click Stop to cancel a running response.

Developer Assistant
- Choose a developer mode such as code explanation, debug, refactor, or security scan.
- Use the text box for code, JSON, errors, or requirements.
- Use the path picker for file, folder, or repository-based analysis.
- Copy or edit the structured output after generation.

Grammar Fix
- Paste your text into the input box and click Correct.
- Edit or copy the output after generation.

Translator
- Enter the source text.
- Select the source and target languages.
- Click Translate and refine the editable output if needed.

Email Helper
- Fill in recipient details and purpose.
- Choose a response length and click Generate.

Prompt Creator
- Choose a category and response length.
- Enter your request and click Generate.

Helpful Tips

- Clear buttons reset each input box quickly.
- The left menu and profile editor can both be collapsed.
- Output boxes are editable for final polishing."""

LOCAL_SETUP_TEXT = """Local Setup

Required Components

1. Python 3.10 or newer
2. pip
3. Tkinter
4. Ollama installed locally
5. At least one installed Ollama model

Recommended Models

- Preferred: qwen2.5-coder:14b
- Smaller fallback: qwen2.5-coder:7b

Initial Setup

1. Clone the repository:
   git clone https://github.com/chitrang313/Sahayak-AI.git
   cd Sahayak-AI

2. Create a virtual environment:
   python -m venv .venv
   .venv\\Scripts\\activate

3. Install dependencies:
   pip install -r requirements.txt

4. Start Ollama.

5. Pull a model:
   ollama pull qwen2.5-coder:14b

Easy Ways To Open The App

- Double-click Sahayak AI.pyw
- Double-click Launch Sahayak AI.bat
- Run python main.py from a terminal"""

NAV_TOOLTIPS = {
    "Chat": "Chat with your local Ollama model and keep the conversation history in one place.",
    "Developer Assistant": "Analyze code, debug errors, refactor, review diffs, and run developer-focused prompts.",
    "Grammar Fix": "Fix spelling, grammar, punctuation, and small clarity issues in your text.",
    "Translator": "Translate text between supported languages with your selected local model.",
    "Email Helper": "Generate a polished email draft from a few quick inputs.",
    "Prompt Creator": "Turn a rough request into a clearer, more structured AI prompt.",
}


class SahayakAIApp:
    """Desktop application shell for Sahayak AI."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(APP_DISPLAY_NAME)
        self.root.geometry("1320x840")
        self.root.minsize(1120, 720)
        self.root.configure(bg="#eef2f6")

        self.ollama_service = OllamaService()
        self.default_model = DEFAULT_MODEL
        self.selected_model_var = tk.StringVar(value=self.default_model)
        self.menu_button_var = tk.StringVar(value="Hide Menu")
        self.profile_toggle_var = tk.StringVar(value="Show Details")

        profile = load_profile()
        self.profile_full_name_var = tk.StringVar(value=profile["full_name"])
        self.profile_email_var = tk.StringVar(value=profile["email"])
        self.profile_phone_var = tk.StringVar(value=profile["phone"])
        self.profile_linkedin_var = tk.StringVar(value=profile["linkedin"])
        self.profile_display_name_var = tk.StringVar()

        self.active_nav = "Chat"
        self.left_panel_visible = True
        self.profile_details_visible = False
        self.nav_buttons: dict[str, tk.Button] = {}
        self.tool_frames: dict[str, ttk.Frame] = {}

        self.status_label_var = tk.StringVar(value="Checking Ollama...")
        self.model_status_var = tk.StringVar(value="Active Model: Detecting...")
        self.download_status_var = tk.StringVar(value="")
        self.download_progress_var = tk.DoubleVar(value=0.0)

        self.model_selector: ttk.Combobox | None = None
        self.status_dot: tk.Canvas | None = None
        self.status_dot_shape: int | None = None
        self.shell: ttk.Frame | None = None
        self.left_panel: tk.Frame | None = None
        self.content_area: ttk.Frame | None = None
        self.current_frame: ttk.Frame | None = None
        self.download_button: ttk.Button | None = None
        self.cancel_download_button: ttk.Button | None = None
        self.download_progress: ttk.Progressbar | None = None
        self.download_status_label: tk.Label | None = None
        self.profile_details_frame: tk.Frame | None = None
        self.help_window: tk.Toplevel | None = None

        self.download_process = None
        self.download_cancel_requested = False
        self.last_download_message = ""
        self._update_profile_display_name()
        self.profile_full_name_var.trace_add(
            "write", lambda *_args: self._update_profile_display_name()
        )
        self.profile_email_var.trace_add(
            "write", lambda *_args: self._update_profile_display_name()
        )

        self._configure_styles()
        self._build_layout()
        self.show_tool("Chat")
        self.refresh_status_now()
        self._schedule_status_refresh()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("App.TFrame", background="#eef2f6")
        style.configure("Panel.TFrame", background="#ffffff")
        style.configure("TopBar.TFrame", background="#ffffff")
        style.configure("BottomBar.TFrame", background="#ffffff")
        style.configure("Help.TFrame", background="#ffffff")
        style.configure(
            "Header.TLabel",
            background="#ffffff",
            foreground="#102a43",
            font=("Segoe UI", 20, "bold"),
        )
        style.configure(
            "Body.TLabel",
            background="#ffffff",
            foreground="#52606d",
            font=("Segoe UI", 10),
        )
        style.configure(
            "FieldLabel.TLabel",
            background="#ffffff",
            foreground="#1f2933",
            font=("Segoe UI", 10, "bold"),
        )
        style.configure(
            "TopTitle.TLabel",
            background="#ffffff",
            foreground="#102a43",
            font=("Segoe UI", 22, "bold"),
        )
        style.configure(
            "TopMeta.TLabel",
            background="#ffffff",
            foreground="#16a34a",
            font=("Segoe UI", 20, "bold"),
        )
        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(14, 10),
        )
        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 10),
            padding=(12, 10),
        )
        style.configure(
            "Help.TNotebook",
            background="#ffffff",
            borderwidth=0,
            tabmargins=(0, 0, 0, 0),
        )
        style.configure(
            "Help.TNotebook.Tab",
            font=("Segoe UI", 10, "bold"),
            padding=(16, 10),
        )
        style.map(
            "Primary.TButton",
            background=[
                ("disabled", "#9fb3c8"),
                ("active", "#1069a7"),
                ("!disabled", "#147cc1"),
            ],
            foreground=[("!disabled", "#ffffff"), ("disabled", "#ffffff")],
        )
        style.map(
            "Secondary.TButton",
            background=[
                ("disabled", "#d9e2ec"),
                ("active", "#bcccdc"),
                ("!disabled", "#f0f4f8"),
            ],
            foreground=[("!disabled", "#102a43"), ("disabled", "#7b8794")],
        )

    def _build_layout(self) -> None:
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self._build_top_bar()
        self._build_content_shell()
        self._build_bottom_bar()

    def _build_top_bar(self) -> None:
        top_bar = ttk.Frame(self.root, style="TopBar.TFrame", padding=(20, 16))
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.grid_columnconfigure(1, weight=1)

        menu_button = ttk.Button(
            top_bar,
            textvariable=self.menu_button_var,
            style="Secondary.TButton",
            command=self.toggle_side_panel,
        )
        menu_button.grid(row=0, column=0, sticky="w", padx=(0, 14))
        add_tooltip(menu_button, "Show or hide the left navigation panel.")

        title_label = ttk.Label(top_bar, text=APP_DISPLAY_NAME, style="TopTitle.TLabel")
        title_label.grid(row=0, column=1, sticky="w")
        add_tooltip(
            title_label,
            "Desktop workspace for the extended AI developer assistant.",
        )

        right_cluster = ttk.Frame(top_bar, style="TopBar.TFrame")
        right_cluster.grid(row=0, column=2, sticky="e")

        meta_label = ttk.Label(
            right_cluster,
            text="100% Free & Unlimited",
            style="TopMeta.TLabel",
        )
        meta_label.grid(row=0, column=0, sticky="e", padx=(0, 14))
        add_tooltip(
            meta_label,
            "This app is designed to run locally with Ollama, without usage limits from a hosted service.",
        )

        help_button = ttk.Button(
            right_cluster,
            text="?",
            style="Secondary.TButton",
            width=3,
            command=self.open_help_panel,
        )
        help_button.grid(row=0, column=1, sticky="e")
        add_tooltip(
            help_button,
            "Open setup instructions, usage tips, and local troubleshooting help.",
        )

    def _build_content_shell(self) -> None:
        self.shell = ttk.Frame(self.root, style="App.TFrame", padding=(20, 0, 20, 0))
        self.shell.grid(row=1, column=0, sticky="nsew")
        self.shell.grid_rowconfigure(0, weight=1)
        self.shell.grid_columnconfigure(0, weight=1, minsize=260, uniform="shell")
        self.shell.grid_columnconfigure(1, weight=4, uniform="shell")

        self.left_panel = tk.Frame(
            self.shell,
            bg="#102a43",
            padx=18,
            pady=20,
            width=280,
        )
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        self.left_panel.grid_propagate(False)

        self.content_area = ttk.Frame(self.shell, style="App.TFrame")
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        nav_container = tk.Frame(self.left_panel, bg="#102a43")
        nav_container.pack(fill="both", expand=True)

        nav_label = tk.Label(
            nav_container,
            text="Navigation",
            bg="#102a43",
            fg="#9fb3c8",
            font=("Segoe UI", 10, "bold"),
        )
        nav_label.pack(anchor="w", pady=(0, 14))
        add_tooltip(nav_label, "Switch between the available AI tools.")

        for item_name, _panel_class in NAV_ITEMS:
            button = tk.Button(
                nav_container,
                text=item_name,
                relief="flat",
                anchor="w",
                padx=14,
                pady=12,
                font=("Segoe UI", 11, "bold"),
                bg="#102a43",
                fg="#d9e2ec",
                activebackground="#1f4f7a",
                activeforeground="#ffffff",
                cursor="hand2",
                command=lambda name=item_name: self.show_tool(name),
            )
            button.pack(fill="x", pady=4)
            add_tooltip(button, NAV_TOOLTIPS[item_name])
            self.nav_buttons[item_name] = button

        footer = tk.Frame(self.left_panel, bg="#102a43")
        footer.pack(side="bottom", fill="x", pady=(20, 0))

        divider = tk.Frame(footer, bg="#36506b", height=1)
        divider.pack(fill="x", pady=(0, 12))

        profile_header = tk.Frame(footer, bg="#102a43")
        profile_header.pack(fill="x")

        profile_label = tk.Label(
            profile_header,
            text="Profile",
            bg="#102a43",
            fg="#f0f4f8",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        profile_label.pack(side="left")
        add_tooltip(
            profile_label,
            "Saved profile details used for personalized email generation and quick reference.",
        )

        toggle_button = tk.Button(
            profile_header,
            textvariable=self.profile_toggle_var,
            relief="flat",
            bg="#102a43",
            fg="#9fb3c8",
            activebackground="#1f4f7a",
            activeforeground="#ffffff",
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=4,
            cursor="hand2",
            command=self.toggle_profile_section,
        )
        toggle_button.pack(side="right")
        add_tooltip(
            toggle_button,
            "Show or hide the editable profile details to save space in the side panel.",
        )

        profile_summary_label = tk.Label(
            footer,
            textvariable=self.profile_display_name_var,
            bg="#102a43",
            fg="#9fb3c8",
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=220,
        )
        profile_summary_label.pack(fill="x", pady=(6, 10))
        add_tooltip(
            profile_summary_label,
            "Quick profile summary shown in the side panel.",
        )

        self.profile_details_frame = tk.Frame(footer, bg="#102a43")
        self.profile_details_frame.pack(fill="x")

        self._build_profile_field(
            self.profile_details_frame,
            "Your Full Name",
            self.profile_full_name_var,
            "Enter the name you want the assistant to use in profile-aware tools.",
        )
        self._build_profile_field(
            self.profile_details_frame,
            "Your Email Address",
            self.profile_email_var,
            "Store your preferred email address for quicker email drafting.",
        )
        self._build_profile_field(
            self.profile_details_frame,
            "Your Phone Number",
            self.profile_phone_var,
            "Store your phone number for optional use in generated email signatures.",
        )
        self._build_profile_field(
            self.profile_details_frame,
            "LinkedIn Profile (if applicable)",
            self.profile_linkedin_var,
            "Optionally store a LinkedIn profile URL for professional email closings.",
        )

        save_button = tk.Button(
            self.profile_details_frame,
            text="Save Profile",
            relief="flat",
            bg="#1f4f7a",
            fg="#ffffff",
            activebackground="#2f6b9a",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=8,
            cursor="hand2",
            command=self.save_profile_data,
        )
        save_button.pack(anchor="e", pady=(10, 0))
        add_tooltip(save_button, "Save the current profile details to this computer.")

        self._set_profile_details_visible(False)

    def _build_profile_field(
        self,
        parent: tk.Misc,
        label_text: str,
        variable: tk.StringVar,
        tooltip_text: str,
    ) -> None:
        """Render one profile input row in the left footer."""
        label = tk.Label(
            parent,
            text=label_text,
            bg="#102a43",
            fg="#d9e2ec",
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
        )
        label.pack(fill="x", pady=(0, 3))
        add_tooltip(label, tooltip_text)

        entry = ttk.Entry(parent, textvariable=variable, font=("Segoe UI", 9))
        entry.pack(fill="x", pady=(0, 8))
        add_tooltip(entry, tooltip_text)

    def _build_bottom_bar(self) -> None:
        bottom_bar = ttk.Frame(self.root, style="BottomBar.TFrame", padding=(20, 14))
        bottom_bar.grid(row=2, column=0, sticky="ew")
        bottom_bar.grid_columnconfigure(0, weight=1)
        bottom_bar.grid_columnconfigure(1, weight=1)

        status_wrap = ttk.Frame(bottom_bar, style="BottomBar.TFrame")
        status_wrap.grid(row=0, column=0, sticky="w")

        self.status_dot = tk.Canvas(
            status_wrap,
            width=14,
            height=14,
            bg="#ffffff",
            highlightthickness=0,
        )
        self.status_dot.grid(row=0, column=0, rowspan=2, padx=(0, 8))
        self.status_dot_shape = self.status_dot.create_oval(
            2, 2, 12, 12, fill="#ef4444", outline=""
        )
        add_tooltip(
            self.status_dot,
            "Green means Ollama is reachable. Red means the local Ollama server is offline.",
        )

        status_label = tk.Label(
            status_wrap,
            textvariable=self.status_label_var,
            bg="#ffffff",
            fg="#102a43",
            font=("Segoe UI", 10, "bold"),
        )
        status_label.grid(row=0, column=1, sticky="w")
        add_tooltip(
            status_label,
            "Current local Ollama server status checked from http://localhost:11434.",
        )

        model_status_label = tk.Label(
            status_wrap,
            textvariable=self.model_status_var,
            bg="#ffffff",
            fg="#52606d",
            font=("Segoe UI", 9),
        )
        model_status_label.grid(row=1, column=1, sticky="w", pady=(3, 0))
        add_tooltip(
            model_status_label,
            "Shows which installed model is currently selected for requests.",
        )

        model_wrap = ttk.Frame(bottom_bar, style="BottomBar.TFrame")
        model_wrap.grid(row=0, column=1, sticky="e")
        model_wrap.grid_columnconfigure(1, weight=1)

        model_label = ttk.Label(
            model_wrap,
            text="Installed Model",
            style="FieldLabel.TLabel",
        )
        model_label.grid(row=0, column=0, sticky="e", padx=(0, 8))
        add_tooltip(
            model_label,
            "Choose one of the models already installed on this computer.",
        )

        self.model_selector = ttk.Combobox(
            model_wrap,
            textvariable=self.selected_model_var,
            values=[],
            state="readonly",
            width=24,
        )
        self.model_selector.grid(row=0, column=1, sticky="e", padx=(0, 8))
        self.model_selector.bind(
            "<<ComboboxSelected>>", lambda _event: self._handle_model_selection()
        )
        add_tooltip(
            self.model_selector,
            "Switch the active model used by all tools. Only installed local models appear here.",
        )

        self.download_button = ttk.Button(
            model_wrap,
            text="Download Model",
            style="Secondary.TButton",
            command=self.start_model_download,
        )
        self.download_button.grid(row=0, column=2, sticky="e")
        add_tooltip(
            self.download_button,
            f"Download the recommended model {self.default_model} with Ollama.",
        )

        self.cancel_download_button = ttk.Button(
            model_wrap,
            text="Cancel Download",
            style="Secondary.TButton",
            command=self.cancel_model_download,
        )
        self.cancel_download_button.grid(row=0, column=2, sticky="e")
        self.cancel_download_button.grid_remove()
        add_tooltip(
            self.cancel_download_button,
            "Cancel the active model download.",
        )

        self.download_progress = ttk.Progressbar(
            model_wrap,
            orient="horizontal",
            length=280,
            mode="determinate",
            maximum=100,
            variable=self.download_progress_var,
        )
        self.download_progress.grid(
            row=1, column=0, columnspan=3, sticky="e", pady=(8, 0)
        )
        self.download_progress.grid_remove()
        add_tooltip(
            self.download_progress,
            "Shows the current progress of the recommended model download.",
        )

        self.download_status_label = tk.Label(
            model_wrap,
            textvariable=self.download_status_var,
            bg="#ffffff",
            fg="#52606d",
            font=("Segoe UI", 9),
            justify="right",
            anchor="e",
            wraplength=420,
        )
        self.download_status_label.grid(
            row=2, column=0, columnspan=3, sticky="e", pady=(4, 0)
        )
        add_tooltip(
            self.download_status_label,
            "Detailed status for recommended model downloads.",
        )

    def toggle_side_panel(self) -> None:
        """Show or hide the left navigation panel."""
        if self.left_panel is None or self.shell is None:
            return

        if self.left_panel_visible:
            self.left_panel.grid_remove()
            self.shell.grid_columnconfigure(0, weight=0, minsize=0, uniform="")
            self.shell.grid_columnconfigure(1, weight=1, uniform="")
            self.left_panel_visible = False
            self.menu_button_var.set("Show Menu")
        else:
            self.left_panel.grid()
            self.shell.grid_columnconfigure(0, weight=1, minsize=260, uniform="shell")
            self.shell.grid_columnconfigure(1, weight=4, uniform="shell")
            self.left_panel_visible = True
            self.menu_button_var.set("Hide Menu")

    def toggle_profile_section(self) -> None:
        """Show or hide the editable profile section."""
        self._set_profile_details_visible(not self.profile_details_visible)

    def _set_profile_details_visible(self, is_visible: bool) -> None:
        """Apply the profile editor visibility state."""
        if self.profile_details_frame is None:
            return

        if is_visible:
            self.profile_details_frame.pack(fill="x")
            self.profile_toggle_var.set("Hide Details")
        else:
            self.profile_details_frame.pack_forget()
            self.profile_toggle_var.set("Show Details")

        self.profile_details_visible = is_visible

    def _update_profile_display_name(self) -> None:
        """Refresh the profile summary shown in the left panel footer."""
        full_name = self.profile_full_name_var.get().strip()
        email = self.profile_email_var.get().strip()

        if not full_name and not email:
            self.profile_display_name_var.set(
                "Profile not set yet.\nAdd your details to personalize email drafts."
            )
            return

        lines = [full_name or "Your Full Name"]
        if email:
            lines.append(email)
        self.profile_display_name_var.set("\n".join(lines))

    def save_profile_data(self) -> None:
        """Persist the current profile data to disk."""
        save_profile(self.get_profile_data())
        messagebox.showinfo("Profile Saved", "Your profile information has been saved.")

    def get_profile_data(self) -> dict[str, str]:
        """Return the current profile values."""
        return {
            "full_name": self.profile_full_name_var.get().strip(),
            "email": self.profile_email_var.get().strip(),
            "phone": self.profile_phone_var.get().strip(),
            "linkedin": self.profile_linkedin_var.get().strip(),
        }

    def open_help_panel(self) -> None:
        """Open the in-app usage and setup help panel."""
        if self.help_window is not None and self.help_window.winfo_exists():
            self.help_window.lift()
            self.help_window.focus_force()
            return

        self.help_window = tk.Toplevel(self.root)
        self.help_window.title(f"{APP_DISPLAY_NAME} Help")
        self.help_window.geometry("860x620")
        self.help_window.minsize(760, 560)
        self.help_window.configure(bg="#eef2f6")
        self.help_window.transient(self.root)
        self.help_window.grid_rowconfigure(1, weight=1)
        self.help_window.grid_columnconfigure(0, weight=1)
        self.help_window.protocol("WM_DELETE_WINDOW", self._close_help_panel)

        header = ttk.Frame(self.help_window, style="TopBar.TFrame", padding=(18, 16))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_label = ttk.Label(
            header,
            text=f"{APP_DISPLAY_NAME} Help Center",
            style="Header.TLabel",
        )
        title_label.grid(row=0, column=0, sticky="w")
        add_tooltip(
            title_label,
            "Usage tips and setup guidance for the extended developer assistant.",
        )

        close_button = ttk.Button(
            header,
            text="Close",
            style="Secondary.TButton",
            command=self._close_help_panel,
        )
        close_button.grid(row=0, column=1, sticky="e")
        add_tooltip(close_button, "Close this help panel.")

        notebook = ttk.Notebook(self.help_window, style="Help.TNotebook")
        notebook.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        add_tooltip(
            notebook,
            "Switch between feature usage guidance and local setup instructions.",
        )

        self._build_help_tab(notebook, "How To Use", HOW_TO_USE_TEXT)
        self._build_help_tab(notebook, "Local Setup", LOCAL_SETUP_TEXT)

    def _build_help_tab(
        self,
        notebook: ttk.Notebook,
        title: str,
        content: str,
    ) -> None:
        """Create one help tab with read-only scrollable content."""
        tab = ttk.Frame(notebook, style="Help.TFrame", padding=16)
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        notebook.add(tab, text=title)

        text_widget = ScrolledText(
            tab,
            wrap="word",
            font=("Segoe UI", 10),
            bd=1,
            relief="solid",
            padx=14,
            pady=14,
        )
        text_widget.grid(row=0, column=0, sticky="nsew")
        text_widget.insert("1.0", content)
        text_widget.configure(state="disabled")
        add_tooltip(text_widget, f"{title} guidance for {APP_DISPLAY_NAME}.")

    def _close_help_panel(self) -> None:
        """Close the help dialog if it is open."""
        if self.help_window is not None and self.help_window.winfo_exists():
            self.help_window.destroy()
        self.help_window = None

    def show_tool(self, tool_name: str) -> None:
        """Switch the right panel to the selected tool."""
        if self.content_area is None:
            return

        self.active_nav = tool_name
        self._refresh_nav_state()

        if self.current_frame is not None:
            self.current_frame.grid_remove()

        frame = self.tool_frames.get(tool_name)
        if frame is None:
            panel_class = dict(NAV_ITEMS)[tool_name]
            frame = panel_class(self.content_area, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.tool_frames[tool_name] = frame
        else:
            frame.grid()

        self.current_frame = frame

    def _refresh_nav_state(self) -> None:
        """Highlight the active navigation item."""
        for name, button in self.nav_buttons.items():
            is_active = name == self.active_nav
            button.configure(
                bg="#1f4f7a" if is_active else "#102a43",
                fg="#ffffff" if is_active else "#d9e2ec",
            )

    def get_selected_model(self) -> str:
        """Return the model currently selected in the dropdown."""
        return self.selected_model_var.get().strip() or self.default_model

    def set_selected_model(self, model_name: str) -> None:
        """Update the selected model if needed."""
        if model_name:
            self.selected_model_var.set(model_name)
            self.model_status_var.set(f"Active Model: {model_name}")

    def _handle_model_selection(self) -> None:
        """Refresh the active model text when the dropdown changes."""
        selected_model = self.get_selected_model()
        self.model_status_var.set(f"Active Model: {selected_model}")

    def refresh_status_now(self) -> None:
        """Refresh server status, the indicator dot, and model selector options."""
        is_online = is_ollama_running(self.ollama_service.base_url)
        installed_models, status = self.ollama_service.get_model_options()

        if self.status_dot is not None and self.status_dot_shape is not None:
            color = "#22c55e" if is_online else "#ef4444"
            self.status_dot.itemconfigure(self.status_dot_shape, fill=color)

        self.status_label_var.set("Ollama Online" if is_online else "Ollama Offline")

        if self.model_selector is not None:
            self.model_selector.configure(values=installed_models)
            if installed_models:
                self.model_selector.configure(state="readonly")
            else:
                self.model_selector.configure(state="disabled")

        if installed_models:
            current_model = self.get_selected_model()
            if current_model not in installed_models:
                current_model = status.active_model
                self.selected_model_var.set(current_model)
            self.model_status_var.set(f"Active Model: {current_model}")
        else:
            self.selected_model_var.set("")
            self.model_status_var.set("Active Model: No installed model")

        self._sync_download_controls(status)

    def _schedule_status_refresh(self) -> None:
        """Keep polling Ollama status so the footer stays current."""
        if not self.root.winfo_exists():
            return
        self.refresh_status_now()
        self.root.after(10000, self._schedule_status_refresh)

    def _sync_download_controls(self, status) -> None:
        """Show or hide download controls based on the installed models."""
        if (
            self.download_button is None
            or self.cancel_download_button is None
            or self.download_progress is None
            or self.download_status_label is None
        ):
            return

        is_downloading = (
            self.download_process is not None and self.download_process.poll() is None
        )
        preferred_installed = self.ollama_service.is_model_installed(
            self.default_model, status
        )

        if is_downloading:
            self.download_button.grid_remove()
            self.cancel_download_button.grid()
            self.download_progress.grid()
            self.download_status_label.grid()
            return

        self.cancel_download_button.grid_remove()
        self.download_progress.stop()
        self.download_progress_var.set(0.0)
        self.download_progress.grid_remove()

        if preferred_installed:
            self.download_button.grid_remove()
            self.download_status_var.set(
                f"Preferred model installed: {self.default_model}"
            )
            self.download_status_label.grid()
        else:
            self.download_button.grid()
            self.download_status_var.set(
                f"Recommended download available: {self.default_model}"
            )
            self.download_status_label.grid()

    def start_model_download(self) -> None:
        """Download the preferred model with visible progress and cancel support."""
        if self.download_process is not None and self.download_process.poll() is None:
            return

        status = self.ollama_service.get_status()
        if self.ollama_service.is_model_installed(self.default_model, status):
            self.refresh_status_now()
            return

        try:
            self.download_process = self.ollama_service.spawn_model_download(
                self.default_model
            )
        except FileNotFoundError:
            messagebox.showerror(
                "Download Error",
                "Could not find the Ollama CLI. Please make sure Ollama is installed.",
            )
            return
        except OSError as exc:
            messagebox.showerror("Download Error", str(exc))
            return

        self.download_cancel_requested = False
        self.last_download_message = f"Downloading {self.default_model}..."
        self.download_status_var.set(self.last_download_message)

        if self.download_progress is not None:
            self.download_progress.configure(mode="indeterminate")
            self.download_progress_var.set(0.0)
            self.download_progress.start(10)

        self._sync_download_controls(status)
        threading.Thread(target=self._monitor_model_download, daemon=True).start()

    def cancel_model_download(self) -> None:
        """Cancel the currently running model download."""
        process = self.download_process
        if process is None or process.poll() is not None:
            return

        self.download_cancel_requested = True
        self.download_status_var.set("Cancelling download...")

        try:
            process.terminate()
        except OSError:
            return

    def _monitor_model_download(self) -> None:
        """Read progress output from the background Ollama pull process."""
        process = self.download_process
        if process is None:
            return

        for message in self.ollama_service.iter_download_messages(process):
            progress_value = self.ollama_service.extract_progress_value(message)
            self.root.after(
                0,
                self._update_download_progress,
                message,
                progress_value,
            )

        exit_code = process.wait()
        self.root.after(0, self._finish_model_download, exit_code)

    def _update_download_progress(
        self, message: str, progress_value: int | None
    ) -> None:
        """Update the visible download progress message and bar."""
        if self.download_progress is None:
            return

        cleaned_message = message.strip()
        if cleaned_message:
            self.last_download_message = cleaned_message
            self.download_status_var.set(cleaned_message)

        if progress_value is None:
            if self.download_progress.cget("mode") != "indeterminate":
                self.download_progress.configure(mode="indeterminate")
                self.download_progress.start(10)
            return

        self.download_progress.stop()
        self.download_progress.configure(mode="determinate")
        self.download_progress_var.set(progress_value)

    def _finish_model_download(self, exit_code: int) -> None:
        """Reset download UI after the pull process exits."""
        cancelled = self.download_cancel_requested
        self.download_process = None
        self.download_cancel_requested = False

        if self.download_progress is not None:
            self.download_progress.stop()

        self.refresh_status_now()

        if cancelled:
            self.download_status_var.set(f"Download cancelled: {self.default_model}")
            return

        if exit_code == 0:
            self.download_status_var.set(f"Downloaded: {self.default_model}")
            self.selected_model_var.set(self.default_model)
            self.model_status_var.set(f"Active Model: {self.default_model}")
            self.refresh_status_now()
            return

        error_message = self.last_download_message or (
            f"Failed to download {self.default_model}."
        )
        messagebox.showerror("Download Error", error_message)

    def _on_close(self) -> None:
        """Persist app data and stop background work before closing."""
        save_profile(self.get_profile_data())
        process = self.download_process
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass
        self.root.destroy()

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()
