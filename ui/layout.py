"""Main layout for the Sahayak AI desktop application."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from services.ollama_service import DEFAULT_MODEL, OllamaService
from ui.chat_ui import ChatUI
from ui.email_ui import EmailUI
from ui.grammar_ui import GrammarUI
from ui.prompt_ui import PromptUI
from ui.translator_ui import TranslatorUI
from utils.profile_store import load_profile, save_profile
from utils.status_checker import is_ollama_running


NAV_ITEMS = [
    ("Chat", ChatUI),
    ("Grammar Fix", GrammarUI),
    ("Translator", TranslatorUI),
    ("Email Helper", EmailUI),
    ("Prompt Creator", PromptUI),
]


class SahayakAIApp:
    """Desktop application shell for Sahayak AI."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Sahayak AI")
        self.root.geometry("1280x820")
        self.root.minsize(1080, 700)
        self.root.configure(bg="#eef2f6")

        self.ollama_service = OllamaService()
        self.default_model = DEFAULT_MODEL
        self.selected_model_var = tk.StringVar(value=self.default_model)
        self.menu_button_var = tk.StringVar(value="Hide Menu")

        profile = load_profile()
        self.profile_full_name_var = tk.StringVar(value=profile["full_name"])
        self.profile_email_var = tk.StringVar(value=profile["email"])
        self.profile_phone_var = tk.StringVar(value=profile["phone"])
        self.profile_linkedin_var = tk.StringVar(value=profile["linkedin"])
        self.profile_display_name_var = tk.StringVar()
        self._update_profile_display_name()
        self.profile_full_name_var.trace_add(
            "write", lambda *_args: self._update_profile_display_name()
        )

        self.active_nav = "Chat"
        self.left_panel_visible = True
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

        self.download_process = None
        self.download_cancel_requested = False
        self.last_download_message = ""

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
            font=("Segoe UI", 18, "bold"),
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

        ttk.Button(
            top_bar,
            textvariable=self.menu_button_var,
            style="Secondary.TButton",
            command=self.toggle_side_panel,
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))

        ttk.Label(top_bar, text="Sahayak AI", style="TopTitle.TLabel").grid(
            row=0, column=1, sticky="w"
        )
        ttk.Label(
            top_bar,
            text="100% Free & Unlimited",
            style="TopMeta.TLabel",
        ).grid(row=0, column=2, sticky="e")

    def _build_content_shell(self) -> None:
        self.shell = ttk.Frame(self.root, style="App.TFrame", padding=(20, 0, 20, 0))
        self.shell.grid(row=1, column=0, sticky="nsew")
        self.shell.grid_rowconfigure(0, weight=1)
        self.shell.grid_columnconfigure(0, weight=1)
        self.shell.grid_columnconfigure(1, weight=4)

        self.left_panel = tk.Frame(self.shell, bg="#102a43", padx=18, pady=20)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

        self.content_area = ttk.Frame(self.shell, style="App.TFrame")
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        nav_container = tk.Frame(self.left_panel, bg="#102a43")
        nav_container.pack(fill="both", expand=True)

        tk.Label(
            nav_container,
            text="Navigation",
            bg="#102a43",
            fg="#9fb3c8",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 14))

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
            self.nav_buttons[item_name] = button

        footer = tk.Frame(self.left_panel, bg="#102a43")
        footer.pack(side="bottom", fill="x", pady=(20, 0))

        divider = tk.Frame(footer, bg="#36506b", height=1)
        divider.pack(fill="x", pady=(0, 12))

        tk.Label(
            footer,
            text="Profile",
            bg="#102a43",
            fg="#f0f4f8",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            footer,
            textvariable=self.profile_display_name_var,
            bg="#102a43",
            fg="#9fb3c8",
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=240,
        ).pack(fill="x", pady=(4, 10))

        self._build_profile_field(footer, "Your Full Name", self.profile_full_name_var)
        self._build_profile_field(footer, "Your Email Address", self.profile_email_var)
        self._build_profile_field(footer, "Your Phone Number", self.profile_phone_var)
        self._build_profile_field(
            footer,
            "LinkedIn Profile (if applicable)",
            self.profile_linkedin_var,
        )

        tk.Button(
            footer,
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
        ).pack(anchor="e", pady=(10, 0))

    def _build_profile_field(
        self, parent: tk.Misc, label_text: str, variable: tk.StringVar
    ) -> None:
        """Render one profile input row in the left footer."""
        tk.Label(
            parent,
            text=label_text,
            bg="#102a43",
            fg="#d9e2ec",
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
        ).pack(fill="x", pady=(0, 3))

        ttk.Entry(parent, textvariable=variable, font=("Segoe UI", 9)).pack(
            fill="x", pady=(0, 8)
        )

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
        self.status_dot.grid(row=0, column=0, padx=(0, 8))
        self.status_dot_shape = self.status_dot.create_oval(
            2, 2, 12, 12, fill="#ef4444", outline=""
        )

        tk.Label(
            status_wrap,
            textvariable=self.status_label_var,
            bg="#ffffff",
            fg="#102a43",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=1, sticky="w")

        tk.Label(
            status_wrap,
            textvariable=self.model_status_var,
            bg="#ffffff",
            fg="#52606d",
            font=("Segoe UI", 9),
        ).grid(row=1, column=1, sticky="w", pady=(3, 0))

        model_wrap = ttk.Frame(bottom_bar, style="BottomBar.TFrame")
        model_wrap.grid(row=0, column=1, sticky="e")
        model_wrap.grid_columnconfigure(1, weight=1)

        ttk.Label(model_wrap, text="Installed Model", style="FieldLabel.TLabel").grid(
            row=0, column=0, sticky="e", padx=(0, 8)
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

        self.download_button = ttk.Button(
            model_wrap,
            text="Download Model",
            style="Secondary.TButton",
            command=self.start_model_download,
        )
        self.download_button.grid(row=0, column=2, sticky="e")

        self.cancel_download_button = ttk.Button(
            model_wrap,
            text="Cancel Download",
            style="Secondary.TButton",
            command=self.cancel_model_download,
        )
        self.cancel_download_button.grid(row=0, column=2, sticky="e")
        self.cancel_download_button.grid_remove()

        self.download_progress = ttk.Progressbar(
            model_wrap,
            orient="horizontal",
            length=260,
            mode="determinate",
            maximum=100,
            variable=self.download_progress_var,
        )
        self.download_progress.grid(
            row=1, column=0, columnspan=3, sticky="e", pady=(8, 0)
        )
        self.download_progress.grid_remove()

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

    def toggle_side_panel(self) -> None:
        """Show or hide the left navigation panel."""
        if self.left_panel is None or self.shell is None:
            return

        if self.left_panel_visible:
            self.left_panel.grid_remove()
            self.shell.grid_columnconfigure(0, weight=0, minsize=0)
            self.shell.grid_columnconfigure(1, weight=1)
            self.left_panel_visible = False
            self.menu_button_var.set("Show Menu")
        else:
            self.left_panel.grid()
            self.shell.grid_columnconfigure(0, weight=1, minsize=0)
            self.shell.grid_columnconfigure(1, weight=4)
            self.left_panel_visible = True
            self.menu_button_var.set("Hide Menu")

    def _update_profile_display_name(self) -> None:
        """Refresh the profile header text shown in the left panel footer."""
        full_name = self.profile_full_name_var.get().strip()
        if full_name:
            self.profile_display_name_var.set(f"Signed in as: {full_name}")
        else:
            self.profile_display_name_var.set("Signed in as: Your Full Name")

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

        is_downloading = self.download_process is not None and self.download_process.poll() is None
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
