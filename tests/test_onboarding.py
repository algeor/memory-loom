from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from memory_loom import onboarding


def test_codex_onboarding_adds_registration_and_instructions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _executable(tmp_path / "memory-loom-mcp")
    host = _executable(tmp_path / "codex")
    calls: list[list[str]] = []

    monkeypatch.setattr(
        onboarding.shutil,
        "which",
        lambda command: str(host) if command == "codex" else None,
    )
    monkeypatch.setattr(
        onboarding.subprocess,
        "run",
        _fake_runner(calls, existing=False),
    )

    result = onboarding.onboard_host(
        "codex",
        project_root=tmp_path,
        user_id="default",
        project_id="sample-project",
        database_path=Path("memory-loom.db"),
        server_command=server,
    )

    assert result.registration == "added"
    assert calls[1] == [
        str(host),
        "mcp",
        "add",
        "memory-loom",
        "--env",
        "MEMORY_LOOM_USER_ID=default",
        "--env",
        "MEMORY_LOOM_PROJECT_ID=sample-project",
        "--env",
        f"MEMORY_LOOM_DATABASE_PATH={tmp_path / 'memory-loom.db'}",
        "--",
        str(server),
    ]
    instructions = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert instructions.count(onboarding.START_MARKER) == 1
    assert "memory_loom_retrieve" in instructions
    assert "explicit user approval" in instructions


def test_claude_onboarding_is_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _executable(tmp_path / "memory-loom-mcp")
    host = _executable(tmp_path / "claude")
    instruction_path = tmp_path / "CLAUDE.md"
    instruction_path.write_text("# Existing instructions\n", encoding="utf-8")
    calls: list[list[str]] = []

    monkeypatch.setattr(onboarding.shutil, "which", lambda _: str(host))
    monkeypatch.setattr(
        onboarding.subprocess,
        "run",
        _fake_runner(calls, existing=True),
    )

    first = onboarding.onboard_host(
        "claude",
        project_root=tmp_path,
        user_id="default",
        project_id=None,
        database_path=Path("memory-loom.db"),
        server_command=server,
    )
    second = onboarding.onboard_host(
        "claude",
        project_root=tmp_path,
        user_id="default",
        project_id=None,
        database_path=Path("memory-loom.db"),
        server_command=server,
    )

    assert first.registration == second.registration == "existing"
    assert all("add" not in command for command in calls)
    instructions = instruction_path.read_text(encoding="utf-8")
    assert instructions.startswith("# Existing instructions\n")
    assert instructions.count(onboarding.START_MARKER) == 1


def test_replace_removes_existing_claude_registration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _executable(tmp_path / "memory-loom-mcp")
    host = _executable(tmp_path / "claude")
    calls: list[list[str]] = []

    monkeypatch.setattr(onboarding.shutil, "which", lambda _: str(host))
    monkeypatch.setattr(
        onboarding.subprocess,
        "run",
        _fake_runner(calls, existing=True),
    )

    result = onboarding.onboard_host(
        "claude",
        project_root=tmp_path,
        user_id="default",
        project_id="sample-project",
        database_path=Path("memory-loom.db"),
        server_command=server,
        replace=True,
    )

    assert result.registration == "replaced"
    assert calls[1] == [str(host), "mcp", "remove", "memory-loom", "--scope", "local"]
    assert calls[2][0:6] == [
        str(host),
        "mcp",
        "add",
        "memory-loom",
        "--scope",
        "local",
    ]


def test_dry_run_does_not_write_or_execute(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _executable(tmp_path / "memory-loom-mcp")
    host = _executable(tmp_path / "codex")
    monkeypatch.setattr(onboarding.shutil, "which", lambda _: str(host))

    def unexpected_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise AssertionError("dry run executed a host command")

    monkeypatch.setattr(onboarding.subprocess, "run", unexpected_run)

    result = onboarding.onboard_host(
        "codex",
        project_root=tmp_path,
        user_id="default",
        project_id="sample-project",
        database_path=Path("memory-loom.db"),
        server_command=server,
        dry_run=True,
    )

    assert result.registration == "dry-run"
    assert not (tmp_path / "AGENTS.md").exists()


def test_invalid_project_id_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _executable(tmp_path / "memory-loom-mcp")
    monkeypatch.setattr(onboarding.shutil, "which", lambda _: "/usr/bin/codex")

    with pytest.raises(ValueError, match="invalid project ID"):
        onboarding.onboard_host(
            "codex",
            project_root=tmp_path,
            user_id="default",
            project_id="Invalid Project",
            database_path=Path("memory-loom.db"),
            server_command=server,
        )


def _executable(path: Path) -> Path:
    path.write_text("", encoding="utf-8")
    path.chmod(0o755)
    return path


def _fake_runner(
    calls: list[list[str]],
    *,
    existing: bool,
):
    get_calls = 0

    def run(
        command: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        nonlocal get_calls
        calls.append(command)
        is_get = command[1:3] == ["mcp", "get"]
        if is_get:
            get_calls += 1
            return_code = 0 if existing or get_calls > 1 else 1
        else:
            return_code = 0
        return subprocess.CompletedProcess(command, return_code, stdout="", stderr="")

    return run
