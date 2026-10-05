from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from memory_loom.mcp_server import CONTEXT_HEADER
from memory_loom.models import Scope
from memory_loom.retrieval import LexicalRetriever
from memory_loom.store import MIGRATION_DIRECTORY, MemoryStore


MEMORY_ID = "91000000-0000-4000-8000-000000000001"
EVIDENCE_ID = "92000000-0000-4000-8000-000000000001"
REVISION_ID = "93000000-0000-4000-8000-000000000001"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bin-dir", type=Path, required=True)
    args = parser.parse_args()
    cli = args.bin_dir / "memory-loom"
    server = args.bin_dir / "memory-loom-mcp"

    assert (MIGRATION_DIRECTORY / "001_initial.sql").is_file()
    assert (MIGRATION_DIRECTORY / "002_mcp_provenance.sql").is_file()

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        _test_onboarding(cli, server, root)
        _test_mcp_restart(server, root / "fresh.db")
        _test_json_stdio(cli, root / "json.db")
        _test_v1_upgrade_and_retrieval(cli, root / "upgrade.db")

    print("release smoke test passed")


def _test_onboarding(cli: Path, server: Path, root: Path) -> None:
    project = root / "project"
    project.mkdir()
    fake_bin = root / "fake-bin"
    fake_bin.mkdir()
    state = root / "codex-registered"
    fake_codex = fake_bin / "codex"
    fake_codex.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = mcp ] && [ \"$2\" = get ]; then\n"
        "  test -f \"$FAKE_CODEX_STATE\"\n"
        "elif [ \"$1\" = mcp ] && [ \"$2\" = add ]; then\n"
        "  touch \"$FAKE_CODEX_STATE\"\n"
        "else\n"
        "  exit 1\n"
        "fi\n",
        encoding="utf-8",
    )
    fake_codex.chmod(0o755)
    environment = os.environ.copy()
    environment["PATH"] = f"{fake_bin}{os.pathsep}{environment['PATH']}"
    environment["FAKE_CODEX_STATE"] = str(state)
    completed = subprocess.run(
        [
            str(cli),
            "onboard",
            "codex",
            "--project-root",
            str(project),
            "--project-id",
            "early-test",
            "--database",
            str(root / "fresh.db"),
            "--server-command",
            str(server),
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert state.is_file()
    assert "memory_loom_retrieve" in (project / "AGENTS.md").read_text(
        encoding="utf-8"
    )


def _test_mcp_restart(server: Path, database: Path) -> None:
    with _McpClient(server, database) as client:
        proposal = client.call(
            "memory_loom_propose_change",
            {
                "change": {
                    "operation": "create",
                    "kind": "preference",
                    "rule_key": "release.notes",
                    "statement": "Prefer concise release notes.",
                    "scope_level": "project",
                    "source_event": {
                        "event_id": "release-source-001",
                        "content": "Prefer concise release notes.",
                    },
                }
            },
        )
        committed = client.call(
            "memory_loom_commit_change",
            {
                "proposal_id": proposal["proposal_id"],
                "approval_event_id": "release-approval-001",
                "approved_by": "user",
            },
        )

    with _McpClient(server, database) as client:
        retrieved = client.call(
            "memory_loom_retrieve",
            {"query": "Write concise release notes.", "limit": 5},
        )
    assert [item["memory_id"] for item in retrieved["selected"]] == [
        committed["memory_id"]
    ]
    assert CONTEXT_HEADER in retrieved["context"]


def _test_json_stdio(cli: Path, database: Path) -> None:
    environment = os.environ.copy()
    environment.update(
        {
            "MEMORY_LOOM_USER_ID": "default",
            "MEMORY_LOOM_PROJECT_ID": "early-test",
            "MEMORY_LOOM_DATABASE_PATH": str(database),
        }
    )
    process = subprocess.Popen(
        [str(cli), "json-stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=environment,
    )
    try:
        proposal = _json_request(
            process,
            "request-001",
            "memory_loom_propose_change",
            {
                "change": {
                    "operation": "create",
                    "kind": "preference",
                    "rule_key": "release.format",
                    "statement": "Use compact release summaries.",
                    "scope_level": "project",
                    "source_event": {
                        "event_id": "json-source-001",
                        "content": "Use compact release summaries.",
                    },
                }
            },
        )
        committed = _json_request(
            process,
            "request-002",
            "memory_loom_commit_change",
            {
                "proposal_id": proposal["proposal_id"],
                "approval_event_id": "json-approval-001",
                "approved_by": "user",
            },
        )
        assert committed["status"] == "active"
    finally:
        process.terminate()
        process.wait(timeout=5)


def _json_request(
    process: subprocess.Popen[str],
    request_id: str,
    method: str,
    params: dict,
) -> dict:
    assert process.stdin is not None
    assert process.stdout is not None
    process.stdin.write(
        json.dumps({"id": request_id, "method": method, "params": params}) + "\n"
    )
    process.stdin.flush()
    response = json.loads(process.stdout.readline())
    assert response["id"] == request_id
    assert response["ok"] is True
    return response["result"]


def _test_v1_upgrade_and_retrieval(cli: Path, database: Path) -> None:
    with sqlite3.connect(database) as connection:
        connection.executescript(
            (MIGRATION_DIRECTORY / "001_initial.sql").read_text(encoding="utf-8")
        )
        connection.execute(
            "INSERT INTO schema_migrations(version, applied_at) VALUES (1, ?)",
            ("2026-01-01T00:00:00+00:00",),
        )
        connection.execute(
            "INSERT INTO memory_lineages(id, created_at) VALUES (?, ?)",
            (MEMORY_ID, "2026-01-01T00:00:00+00:00"),
        )
        connection.execute(
            "INSERT INTO evidence_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                EVIDENCE_ID,
                "release-upgrade",
                "explicit_preference",
                "Prefer concise release notes.",
                "present",
                "default",
                "early-test",
                None,
                "2026-01-01T00:00:00+00:00",
                "approved",
            ),
        )
        connection.execute(
            "INSERT INTO memory_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                MEMORY_ID,
                1,
                "release.notes",
                "Prefer concise release notes.",
                "preference",
                "default",
                "early-test",
                None,
                "active",
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:00:00+00:00",
                None,
            ),
        )
        connection.execute(
            "INSERT INTO memory_evidence VALUES (?, 1, ?)",
            (MEMORY_ID, EVIDENCE_ID),
        )
        connection.execute(
            "INSERT INTO revision_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                REVISION_ID,
                MEMORY_ID,
                "approve",
                None,
                1,
                "user",
                "explicit-user-approval",
                "2026-01-01T00:00:00+00:00",
            ),
        )
        connection.execute(
            "INSERT INTO revision_evidence VALUES (?, ?)",
            (REVISION_ID, EVIDENCE_ID),
        )
        connection.execute(
            "INSERT INTO memory_fts VALUES (?, 1, ?)",
            (MEMORY_ID, "Prefer concise release notes."),
        )
        connection.commit()

    completed = subprocess.run(
        [str(cli), "migrate", "--database", str(database)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert "schema 2" in completed.stdout
    assert list((database.parent / f"{database.name}.backups").glob("*.db"))

    with MemoryStore(database) as store:
        retrieval = LexicalRetriever(store).retrieve(
            "release-upgrade-query",
            "Write concise release notes.",
            Scope(user_id="default", project_id="early-test", task_id=None),
            datetime.now(UTC),
        )
    assert [str(record.id) for record in retrieval.selected_records] == [MEMORY_ID]


class _McpClient:
    def __init__(self, server: Path, database: Path) -> None:
        environment = os.environ.copy()
        environment.update(
            {
                "MEMORY_LOOM_USER_ID": "default",
                "MEMORY_LOOM_PROJECT_ID": "early-test",
                "MEMORY_LOOM_DATABASE_PATH": str(database),
            }
        )
        self.process = subprocess.Popen(
            [str(server)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=environment,
        )
        self.request_id = 0

    def __enter__(self) -> _McpClient:
        self.request(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "release-smoke", "version": "1"},
            },
        )
        self.notify("notifications/initialized", {})
        return self

    def __exit__(self, *_: object) -> None:
        self.process.terminate()
        self.process.wait(timeout=5)

    def request(self, method: str, params: dict) -> dict:
        self.request_id += 1
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        self.process.stdin.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": self.request_id,
                    "method": method,
                    "params": params,
                }
            )
            + "\n"
        )
        self.process.stdin.flush()
        while line := self.process.stdout.readline():
            response = json.loads(line)
            if response.get("id") == self.request_id:
                if "error" in response:
                    raise RuntimeError(response["error"])
                return response["result"]
        raise RuntimeError("MCP server closed before replying")

    def notify(self, method: str, params: dict) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(
            json.dumps({"jsonrpc": "2.0", "method": method, "params": params})
            + "\n"
        )
        self.process.stdin.flush()

    def call(self, name: str, arguments: dict) -> dict:
        result = self.request(
            "tools/call",
            {"name": name, "arguments": arguments},
        )
        assert result.get("isError") is False
        return result["structuredContent"]


if __name__ == "__main__":
    main()
