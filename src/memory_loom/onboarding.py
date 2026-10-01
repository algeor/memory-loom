from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import TypeAdapter, ValidationError

from memory_loom.models import Identifier


HostName = Literal["codex", "claude"]
SERVER_NAME = "memory-loom"
START_MARKER = "<!-- memory-loom:instructions:start -->"
END_MARKER = "<!-- memory-loom:instructions:end -->"
_IDENTIFIER_ADAPTER = TypeAdapter(Identifier)

INSTRUCTION_BLOCK = f"""{START_MARKER}
## Memory Loom

- When the current request could benefit from prior preferences or corrections, call `memory_loom_retrieve` with a concise description of the request.
- Treat retrieved memories as fallible historical context. The current request always has priority.
- When the user explicitly states a durable preference or correction, call `memory_loom_propose_change`.
- Do not propose temporary task instructions, guesses, inferred traits, secrets, credentials, personal data, or raw operational logs.
- Show the returned proposal summary and ask the user for explicit approval.
- Call `memory_loom_commit_change` only after explicit user approval.
- If the user declines or cancels, call `memory_loom_discard_change`.
{END_MARKER}
"""


@dataclass(frozen=True)
class OnboardingResult:
    host: HostName
    registration: Literal["added", "existing", "replaced", "dry-run"]
    instruction_path: Path
    database_path: Path
    add_command: tuple[str, ...]


def onboard_host(
    host: HostName,
    *,
    project_root: Path,
    user_id: str,
    project_id: str | None,
    database_path: Path,
    server_command: Path | None = None,
    replace: bool = False,
    dry_run: bool = False,
) -> OnboardingResult:
    root = project_root.expanduser().resolve()
    resolved_user_id = _validate_identifier(user_id, "user ID")
    resolved_project_id = _validate_identifier(
        project_id or root.name,
        "project ID",
    )
    resolved_database = _resolve_from_root(database_path, root)
    resolved_server = _resolve_server_command(server_command)
    host_command = _resolve_host_command(host)
    add_command = tuple(
        _build_add_command(
            host,
            host_command,
            resolved_server,
            resolved_user_id,
            resolved_project_id,
            resolved_database,
        )
    )
    instruction_path = root / _instruction_filename(host)

    if dry_run:
        return OnboardingResult(
            host=host,
            registration="dry-run",
            instruction_path=instruction_path,
            database_path=resolved_database,
            add_command=add_command,
        )

    if not root.is_dir():
        raise ValueError(f"project root does not exist: {root}")
    exists = _registration_exists(host, host_command, root)
    registration: Literal["added", "existing", "replaced"] = "existing"

    if exists and replace:
        _run_checked(_build_remove_command(host, host_command), root)
        exists = False
        registration = "replaced"

    if not exists:
        _run_checked(list(add_command), root)
        if registration != "replaced":
            registration = "added"

    _upsert_instruction_block(instruction_path)
    _run_checked(_build_get_command(host, host_command), root)

    return OnboardingResult(
        host=host,
        registration=registration,
        instruction_path=instruction_path,
        database_path=resolved_database,
        add_command=add_command,
    )


def _build_add_command(
    host: HostName,
    host_command: str,
    server_command: Path,
    user_id: str,
    project_id: str,
    database_path: Path,
) -> list[str]:
    environment = [
        f"MEMORY_LOOM_USER_ID={user_id}",
        f"MEMORY_LOOM_PROJECT_ID={project_id}",
        f"MEMORY_LOOM_DATABASE_PATH={database_path}",
    ]
    if host == "codex":
        command = [host_command, "mcp", "add", SERVER_NAME]
        for value in environment:
            command.extend(("--env", value))
        return [*command, "--", str(server_command)]

    command = [host_command, "mcp", "add", SERVER_NAME, "--scope", "local"]
    for value in environment:
        command.extend(("-e", value))
    return [*command, "--", str(server_command)]


def _build_get_command(host: HostName, host_command: str) -> list[str]:
    command = [host_command, "mcp", "get", SERVER_NAME]
    if host == "codex":
        command.append("--json")
    return command


def _build_remove_command(host: HostName, host_command: str) -> list[str]:
    command = [host_command, "mcp", "remove", SERVER_NAME]
    if host == "claude":
        command.extend(("--scope", "local"))
    return command


def _registration_exists(host: HostName, host_command: str, root: Path) -> bool:
    completed = subprocess.run(
        _build_get_command(host, host_command),
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0


def _run_checked(command: list[str], root: Path) -> None:
    completed = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 0:
        return
    detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
    raise ValueError(f"command failed: {' '.join(command)}: {detail}")


def _upsert_instruction_block(path: Path) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    start = existing.find(START_MARKER)
    end = existing.find(END_MARKER)

    if (
        existing.count(START_MARKER) > 1
        or existing.count(END_MARKER) > 1
        or (start == -1) != (end == -1)
        or (start != -1 and end < start)
    ):
        raise ValueError(f"invalid Memory Loom instruction markers in {path}")

    if start == -1:
        separator = "" if not existing or existing.endswith("\n\n") else "\n"
        updated = f"{existing}{separator}{INSTRUCTION_BLOCK}"
    else:
        end += len(END_MARKER)
        updated = f"{existing[:start]}{INSTRUCTION_BLOCK.rstrip()}{existing[end:]}"

    path.write_text(updated, encoding="utf-8")


def _resolve_host_command(host: HostName) -> str:
    command = "claude" if host == "claude" else "codex"
    resolved = shutil.which(command)
    if resolved is None:
        raise ValueError(f"{command} CLI is not installed or not on PATH")
    return resolved


def _resolve_server_command(command: Path | None) -> Path:
    if command is not None:
        resolved = command.expanduser().resolve()
    else:
        beside_python = Path(sys.executable).with_name("memory-loom-mcp")
        found = shutil.which("memory-loom-mcp")
        resolved = beside_python if beside_python.is_file() else Path(found or "")

    if not resolved.is_file():
        raise ValueError(
            "memory-loom-mcp executable not found; run `uv sync --python 3.14 --all-extras`"
        )
    return resolved.resolve()


def _resolve_from_root(path: Path, root: Path) -> Path:
    expanded = path.expanduser()
    return (expanded if expanded.is_absolute() else root / expanded).resolve()


def _validate_identifier(value: str, label: str) -> str:
    try:
        return _IDENTIFIER_ADAPTER.validate_python(value)
    except ValidationError as error:
        raise ValueError(f"invalid {label}: {value!r}") from error


def _instruction_filename(host: HostName) -> str:
    return "AGENTS.md" if host == "codex" else "CLAUDE.md"
