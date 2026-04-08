"""Input preparation helpers for developer-assistant workflows."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


RELEVANT_CODE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".md",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scss",
    ".sql",
    ".swift",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
RELEVANT_FILE_NAMES = {
    "Dockerfile",
    "Makefile",
}
SKIP_DIRECTORY_NAMES = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".vs",
    "__pycache__",
    "bin",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "obj",
    "venv",
}
ENTRY_FILE_NAMES = {
    "app.py",
    "index.js",
    "index.ts",
    "main.py",
    "main.ts",
    "program.cs",
    "server.js",
}

MAX_TEXT_INPUT_CHARS = 14_000
MAX_JSON_INPUT_CHARS = 18_000
MAX_SINGLE_FILE_CHARS = 6_000
MAX_DIRECTORY_FILES = 18
MAX_DIRECTORY_CONTEXT_CHARS = 36_000
MAX_REVIEW_DIFF_CHARS = 18_000
MAX_SECURITY_DIFF_CHARS = 14_000
MAX_SECURITY_FILE_CHARS = 20_000
MIN_SECTION_REMAINING_CHARS = 1_000
GIT_COMMAND_TIMEOUT_SECONDS = 12


class DeveloperContextError(Exception):
    """Raised when developer-assistant input cannot be prepared safely."""


def truncate_text(text: str, max_chars: int, *, label: str) -> str:
    """Trim large text blocks so prompts stay within the model context budget."""
    cleaned = text.strip("\r\n")
    if len(cleaned) <= max_chars:
        return cleaned

    truncated = cleaned[:max_chars].rstrip()
    return f"{truncated}\n\n[{label} truncated to fit input limits.]"


def prepare_text_input(raw_text: str, *, label: str) -> str:
    """Validate and trim free-form text input from the UI."""
    if not raw_text.strip():
        raise DeveloperContextError("Please enter the required input text.")
    return truncate_text(raw_text, MAX_TEXT_INPUT_CHARS, label=label)


def prepare_json_input(raw_json: str) -> str:
    """Validate JSON input and return a pretty-printed version."""
    cleaned = raw_json.strip()
    if not cleaned:
        raise DeveloperContextError("Please paste JSON to analyze.")

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise DeveloperContextError(
            f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}."
        ) from exc

    pretty_json = json.dumps(payload, indent=2, ensure_ascii=False)
    return truncate_text(pretty_json, MAX_JSON_INPUT_CHARS, label="JSON input")


def prepare_code_understanding_input(raw_path: str) -> str:
    """Collect code context from a file or directory path."""
    path = resolve_input_path(raw_path)
    if path.is_dir():
        return _build_directory_context(
            path,
            purpose="Code understanding",
            max_files=MAX_DIRECTORY_FILES,
            max_total_chars=MAX_DIRECTORY_CONTEXT_CHARS,
        )
    return _build_file_context(path, header="Selected file")


def prepare_precommit_input(raw_path: str) -> str:
    """Collect repository diffs for pre-commit review."""
    target_path = resolve_input_path(raw_path)
    repo_root = find_git_root(target_path)
    diff_context = collect_git_diff_context(
        repo_root,
        max_chars=MAX_REVIEW_DIFF_CHARS,
    )
    return (
        f"Repository Root: {repo_root}\n"
        "Review Scope: staged changes plus unstaged working-tree changes.\n\n"
        f"{diff_context}"
    )


def prepare_security_input(raw_path: str) -> str:
    """Collect repository diff plus file content for security analysis."""
    target_path = resolve_input_path(raw_path)
    repo_root = find_git_root(target_path)
    diff_context = collect_git_diff_context(
        repo_root,
        max_chars=MAX_SECURITY_DIFF_CHARS,
    )

    changed_files = extract_changed_files(diff_context)
    if changed_files:
        file_context = _build_selected_files_context(
            repo_root,
            changed_files,
            max_total_chars=MAX_SECURITY_FILE_CHARS,
        )
    else:
        file_context = _build_directory_context(
            repo_root,
            purpose="Security analysis",
            max_files=10,
            max_total_chars=MAX_SECURITY_FILE_CHARS,
        )

    return (
        f"Repository Root: {repo_root}\n"
        "Security Scope: git diff plus current file contents.\n\n"
        f"{diff_context}\n\n"
        f"{file_context}"
    )


def resolve_input_path(raw_path: str) -> Path:
    """Resolve and validate a path typed or selected in the UI."""
    cleaned = raw_path.strip().strip('"').strip("'")
    if not cleaned:
        raise DeveloperContextError("Please choose or enter a valid path.")

    try:
        return Path(cleaned).expanduser().resolve(strict=True)
    except FileNotFoundError as exc:
        raise DeveloperContextError(f"Path not found: {cleaned}") from exc
    except OSError as exc:
        raise DeveloperContextError(str(exc)) from exc


def find_git_root(target_path: Path) -> Path:
    """Find the Git repository root for a path or raise a user-friendly error."""
    working_directory = target_path if target_path.is_dir() else target_path.parent

    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=working_directory,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as exc:
        raise DeveloperContextError(
            "Git is required for this feature but was not found on this computer."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise DeveloperContextError(
            "Timed out while trying to locate the Git repository."
        ) from exc

    if completed.returncode == 0 and completed.stdout.strip():
        return Path(completed.stdout.strip())

    for candidate in [working_directory, *working_directory.parents]:
        if (candidate / ".git").exists():
            return candidate

    raise DeveloperContextError(
        "No Git repository was found for the selected path."
    )


def collect_git_diff_context(repo_root: Path, *, max_chars: int) -> str:
    """Return staged and unstaged diffs for the target repository."""
    staged_diff = _run_git_command(
        repo_root,
        ["diff", "--staged", "--no-ext-diff", "--unified=3"],
    )
    working_diff = _run_git_command(
        repo_root,
        ["diff", "--no-ext-diff", "--unified=3"],
    )

    sections = [
        "Staged Diff:",
        truncate_text(staged_diff, max_chars, label="Staged diff")
        if staged_diff
        else "(No staged changes.)",
        "",
        "Working Tree Diff:",
        truncate_text(working_diff, max_chars, label="Working tree diff")
        if working_diff
        else "(No unstaged changes.)",
    ]
    return "\n".join(sections)


def extract_changed_files(diff_context: str) -> list[Path]:
    """Extract changed repository-relative file paths from a git diff."""
    changed_files: list[Path] = []
    seen: set[str] = set()

    for line in diff_context.splitlines():
        if not line.startswith("+++ "):
            continue

        raw_path = line[4:].strip()
        if raw_path == "/dev/null":
            continue
        if raw_path.startswith("b/"):
            raw_path = raw_path[2:]

        if raw_path and raw_path not in seen:
            changed_files.append(Path(raw_path))
            seen.add(raw_path)

    return changed_files


def _run_git_command(repo_root: Path, args: list[str]) -> str:
    """Execute a git command safely and return stdout."""
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as exc:
        raise DeveloperContextError(
            "Git is required for this feature but was not found on this computer."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise DeveloperContextError(
            "Timed out while running a Git command for the selected repository."
        ) from exc

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if completed.returncode not in {0, 1} and stderr:
        raise DeveloperContextError(stderr)
    return stdout


def _build_selected_files_context(
    repo_root: Path,
    relative_paths: list[Path],
    *,
    max_total_chars: int,
) -> str:
    """Read changed files first so security analysis focuses on active work."""
    sections: list[str] = []
    included_paths: list[str] = []
    consumed_chars = 0

    for relative_path in relative_paths:
        full_path = repo_root / relative_path
        if not full_path.exists() or full_path.is_dir():
            continue

        try:
            section = _build_file_context(
                full_path,
                header=f"Changed file: {relative_path.as_posix()}",
            )
        except DeveloperContextError:
            continue

        if sections and consumed_chars + len(section) > max_total_chars:
            break
        if not sections and len(section) > max_total_chars:
            section = truncate_text(
                section,
                max_total_chars,
                label=f"{relative_path.as_posix()} content",
            )

        sections.append(section)
        included_paths.append(relative_path.as_posix())
        consumed_chars += len(section)

    if not sections:
        return "Changed File Contents:\n(No readable changed files were available.)"

    lines = [
        "Changed File Contents:",
        f"Included files: {', '.join(included_paths)}",
        "",
        "\n\n".join(sections),
    ]
    return "\n".join(lines)


def _build_directory_context(
    root_path: Path,
    *,
    purpose: str,
    max_files: int,
    max_total_chars: int,
) -> str:
    """Read a bounded set of relevant files from a directory tree."""
    relevant_files = _collect_relevant_files(root_path)
    if not relevant_files:
        raise DeveloperContextError(
            "No supported text files were found in the selected directory."
        )

    ordered_files = sorted(
        relevant_files,
        key=lambda path: _directory_sort_key(root_path, path),
    )

    sections: list[str] = []
    included_paths: list[str] = []
    consumed_chars = 0

    for path in ordered_files:
        if len(sections) >= max_files:
            break

        remaining_chars = max_total_chars - consumed_chars
        if remaining_chars < MIN_SECTION_REMAINING_CHARS:
            break

        relative_path = path.relative_to(root_path).as_posix()
        header = f"File: {relative_path}"
        try:
            section = _build_file_context(path, header=header)
        except DeveloperContextError:
            continue

        if len(section) > remaining_chars:
            section = truncate_text(
                section,
                remaining_chars,
                label=f"{relative_path} content",
            )

        sections.append(section)
        included_paths.append(relative_path)
        consumed_chars += len(section)

    if not sections:
        raise DeveloperContextError(
            "No readable text files were found in the selected directory."
        )

    omitted_files = max(0, len(relevant_files) - len(sections))
    summary_lines = [
        f"{purpose} directory context",
        f"Root Path: {root_path}",
        f"Included files: {len(sections)}",
        f"Omitted relevant files: {omitted_files}",
        "Files are prioritized toward entry points, shallow paths, and smaller files.",
        "",
        "\n\n".join(sections),
    ]
    return "\n".join(summary_lines)


def _collect_relevant_files(root_path: Path) -> list[Path]:
    """Return supported text files while skipping heavy build directories."""
    collected: list[Path] = []

    for current_root, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname not in SKIP_DIRECTORY_NAMES
        ]

        base_path = Path(current_root)
        for filename in filenames:
            path = base_path / filename
            suffix = path.suffix.lower()
            if suffix in RELEVANT_CODE_EXTENSIONS or path.name in RELEVANT_FILE_NAMES:
                collected.append(path)

    return collected


def _directory_sort_key(root_path: Path, path: Path) -> tuple[int, int, int, str]:
    """Prefer likely entry files, shallow paths, and smaller files first."""
    relative_path = path.relative_to(root_path)
    name = path.name.lower()
    priority = 0 if name in ENTRY_FILE_NAMES else 1
    depth = len(relative_path.parts)
    try:
        file_size = path.stat().st_size
    except OSError:
        file_size = 0
    return (priority, depth, file_size, relative_path.as_posix().lower())


def _build_file_context(path: Path, *, header: str) -> str:
    """Read one text file with truncation and metadata."""
    content = _read_text_file(path)
    return f"{header}\nPath: {path}\n\n{content}"


def _read_text_file(path: Path) -> str:
    """Read a text file with utf-8 fallback behavior."""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as file_handle:
            content = file_handle.read(MAX_SINGLE_FILE_CHARS + 1)
    except OSError as exc:
        raise DeveloperContextError(f"Could not read {path}: {exc}") from exc

    if "\x00" in content:
        raise DeveloperContextError(
            f"The file '{path.name}' appears to be binary and cannot be analyzed as text."
        )

    is_truncated = len(content) > MAX_SINGLE_FILE_CHARS
    safe_content = content[:MAX_SINGLE_FILE_CHARS].rstrip()
    if not safe_content:
        safe_content = "[File is empty.]"

    if is_truncated:
        safe_content += "\n\n[File truncated to fit input limits.]"

    return safe_content
