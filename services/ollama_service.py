"""Service layer for talking to the local Ollama API."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from threading import Event

import requests


BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5-coder:14b"
DEFAULT_TIMEOUT = 90
DEFAULT_ERROR_MESSAGE = "The request failed. Please try again."
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
PERCENTAGE_PATTERN = re.compile(r"(\d{1,3})(?:\.\d+)?%")


class OllamaServiceError(Exception):
    """Raised when a request to Ollama cannot be completed."""


class OllamaCancelledError(Exception):
    """Raised when a running request is cancelled by the user."""


class CancelToken:
    """Simple cancellation token used by background worker threads."""

    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        """Mark the associated request as cancelled."""
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        """Return whether the request has been cancelled."""
        return self._event.is_set()


@dataclass(frozen=True)
class OllamaStatus:
    """Current status of the local Ollama server."""

    is_online: bool
    available_models: list[str]
    active_model: str


class OllamaService:
    """Thin client around the Ollama HTTP API."""

    def __init__(self, base_url: str = BASE_URL, default_model: str = DEFAULT_MODEL):
        self.base_url = base_url.rstrip("/")
        self.generate_url = f"{self.base_url}/api/generate"
        self.tags_url = f"{self.base_url}/api/tags"
        self.default_model = default_model

    def get_status(self) -> OllamaStatus:
        """Fetch the currently installed models and chosen active model."""
        try:
            response = requests.get(self.tags_url, timeout=5)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            return OllamaStatus(
                is_online=False,
                available_models=[],
                active_model=self.default_model,
            )

        available_models = [
            model.get("name", "").strip()
            for model in payload.get("models", [])
            if model.get("name")
        ]

        if available_models:
            if self.default_model in available_models:
                active_model = self.default_model
            else:
                active_model = available_models[0]
        else:
            active_model = self.default_model

        return OllamaStatus(
            is_online=True,
            available_models=available_models,
            active_model=active_model,
        )

    def get_model_options(self) -> tuple[list[str], OllamaStatus]:
        """Return model options for the dropdown plus current server status."""
        status = self.get_status()
        return status.available_models[:], status

    def is_model_installed(
        self, model_name: str, status: OllamaStatus | None = None
    ) -> bool:
        """Return whether the given model is installed locally."""
        current_status = status or self.get_status()
        return model_name in current_status.available_models

    def generate(
        self,
        prompt: str,
        model_name: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        cancel_token: CancelToken | None = None,
    ) -> tuple[str, str]:
        """Execute a non-streaming text generation request."""
        if cancel_token and cancel_token.is_cancelled:
            raise OllamaCancelledError()

        status = self.get_status()
        if not status.is_online:
            raise OllamaServiceError(
                "Could not connect to Ollama. Please make sure Ollama is running."
            )

        if not status.available_models:
            raise OllamaServiceError(
                "Ollama is online, but no models are installed. Please pull a model and try again."
            )

        selected_model = (model_name or self.default_model).strip()
        if selected_model not in status.available_models:
            raise OllamaServiceError(
                f"The selected model '{selected_model}' is not installed. "
                "Choose an installed model from the dropdown."
            )

        payload = {
            "model": selected_model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            response = requests.post(self.generate_url, json=payload, timeout=timeout)
            data = response.json()
        except requests.exceptions.ConnectionError as exc:
            raise OllamaServiceError(
                "Could not connect to Ollama. Please make sure Ollama is running."
            ) from exc
        except ValueError as exc:
            raise OllamaServiceError(
                "Ollama returned an invalid response. Please try again."
            ) from exc
        except requests.RequestException as exc:
            raise OllamaServiceError(
                "The request timed out or failed. Please try again."
            ) from exc

        if cancel_token and cancel_token.is_cancelled:
            raise OllamaCancelledError()

        if response.status_code >= 400:
            raise OllamaServiceError(self._clean_error_message(data.get("error")))

        if data.get("error"):
            raise OllamaServiceError(self._clean_error_message(data["error"]))

        response_text = data.get("response", "").strip()
        if not response_text:
            raise OllamaServiceError(
                "Ollama returned an empty response. Please try again."
            )

        return response_text, selected_model

    def spawn_model_download(self, model_name: str) -> subprocess.Popen[str]:
        """Start a background Ollama pull process for the requested model."""
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        return subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=creationflags,
        )

    def iter_download_messages(
        self, process: subprocess.Popen[str]
    ):
        """Yield normalized progress messages from an Ollama pull process."""
        if process.stdout is None:
            return

        buffer = ""
        while True:
            chunk = process.stdout.read(1)
            if chunk == "" and process.poll() is not None:
                cleaned = self.normalize_download_message(buffer)
                if cleaned:
                    yield cleaned
                break

            if chunk in {"\r", "\n"}:
                cleaned = self.normalize_download_message(buffer)
                if cleaned:
                    yield cleaned
                buffer = ""
                continue

            buffer += chunk

    def normalize_download_message(self, raw_message: str) -> str:
        """Remove ANSI escape codes and extra whitespace from CLI output."""
        return ANSI_ESCAPE_PATTERN.sub("", raw_message).strip()

    def extract_progress_value(self, message: str) -> int | None:
        """Return a progress percentage if one is present in the CLI output."""
        match = PERCENTAGE_PATTERN.search(message)
        if match is None:
            return None

        percent = int(match.group(1))
        return max(0, min(percent, 100))

    def _clean_error_message(self, message: object) -> str:
        """Normalize API errors into a safe user-facing message."""
        cleaned = str(message).strip() if message is not None else ""
        return cleaned or DEFAULT_ERROR_MESSAGE
