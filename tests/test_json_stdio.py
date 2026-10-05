from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from uuid import UUID

import pytest

from memory_loom.json_stdio import handle_json_line, serve_json_lines
from memory_loom.mcp_proposals import ProposalNotFoundError, proposal_store
from memory_loom.store import MemoryStore


def test_json_stdio_preserves_propose_then_commit_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = _configure(tmp_path, monkeypatch)
    propose = _request(
        "request-001",
        "memory_loom_propose_change",
        {
            "change": {
                "operation": "create",
                "kind": "preference",
                "rule_key": "review.priority",
                "statement": "Lead with correctness issues.",
                "scope_level": "project",
                "source_event": {
                    "event_id": "message-001",
                    "content": "Lead with correctness issues.",
                },
            }
        },
    )

    assert propose["ok"] is True
    proposal_id = UUID(propose["result"]["proposal_id"])
    with MemoryStore(database_path) as store:
        assert store.latest_records() == []

    committed = _request(
        "request-002",
        "memory_loom_commit_change",
        {
            "proposal_id": str(proposal_id),
            "approval_event_id": "message-002",
            "approved_by": "user",
        },
    )

    assert committed["ok"] is True
    assert committed["result"]["status"] == "active"
    with MemoryStore(database_path) as store:
        records = store.latest_records()
        assert len(records) == 1
        assert records[0].scope.project_id == "memory-loom"
    with pytest.raises(ProposalNotFoundError):
        proposal_store.get(proposal_id)


def test_json_stdio_rejects_model_supplied_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(tmp_path, monkeypatch)

    response = _request(
        "request-003",
        "memory_loom_retrieve",
        {
            "query": "Review this code.",
            "scope": {"user_id": "other-user"},
        },
    )

    assert response == {
        "id": "request-003",
        "ok": False,
        "error": {
            "code": "invalid_request",
            "message": "request does not satisfy the JSON CLI contract",
        },
    }


def test_json_stdio_keeps_running_after_bad_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(tmp_path, monkeypatch)
    input_stream = StringIO(
        "not-json\n"
        + json.dumps(
            {
                "id": "request-004",
                "method": "memory_loom_inspect",
                "params": {},
            }
        )
        + "\n"
    )
    output_stream = StringIO()

    assert serve_json_lines(input_stream, output_stream) == 0

    responses = [json.loads(line) for line in output_stream.getvalue().splitlines()]
    assert responses[0]["error"]["code"] == "invalid_request"
    assert responses[1]["ok"] is True
    assert responses[1]["result"]["scope"]["user_id"] == "user-a"


def _configure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    database_path = tmp_path / "memory.db"
    monkeypatch.setenv("MEMORY_LOOM_USER_ID", "user-a")
    monkeypatch.setenv("MEMORY_LOOM_PROJECT_ID", "memory-loom")
    monkeypatch.setenv("MEMORY_LOOM_DATABASE_PATH", str(database_path))
    return database_path


def _request(request_id: str, method: str, params: dict[str, object]):
    return handle_json_line(
        json.dumps({"id": request_id, "method": method, "params": params})
    )

