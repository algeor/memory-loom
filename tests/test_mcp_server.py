from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import UUID

import pytest

from memory_loom.contracts import FIXTURE_DIRECTORY, load_json
from memory_loom.mcp_server import server
from memory_loom.mcp_proposals import ProposalNotFoundError, proposal_store
from memory_loom.models import Scenario
from memory_loom.store import MemoryStore


SCENARIO_PATH = (
    FIXTURE_DIRECTORY / "scenarios" / "v1" / "project-exception-001.json"
)
PROJECT_MEMORY_ID = "52000000-0000-4000-8000-000000000002"
GLOBAL_MEMORY_ID = "52000000-0000-4000-8000-000000000001"


def test_retrieve_tool_uses_host_bound_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "memory.db"
    scenario = Scenario.model_validate(load_json(SCENARIO_PATH))

    with MemoryStore(database_path) as store:
        store.load_scenario(scenario)

    monkeypatch.setenv("MEMORY_LOOM_USER_ID", "user-a")
    monkeypatch.setenv("MEMORY_LOOM_PROJECT_ID", "memory-loom")
    monkeypatch.setenv("MEMORY_LOOM_DATABASE_PATH", str(database_path))

    result = asyncio.run(
        server.call_tool(
            "memory_loom_retrieve",
            {"query": "Review the deletion section.", "limit": 5},
        )
    )

    assert result.structured_content is not None
    content = result.structured_content
    assert content["scope"]["user_id"] == "user-a"
    assert content["scope"]["project_id"] == "memory-loom"
    assert [item["memory_id"] for item in content["selected"]] == [
        PROJECT_MEMORY_ID
    ]
    assert content["selected"][0]["evidence_ids"] == [
        "51000000-0000-4000-8000-000000000002"
    ]
    assert PROJECT_MEMORY_ID in content["context"]
    assert GLOBAL_MEMORY_ID not in content["context"]


def test_retrieve_tool_does_not_accept_model_supplied_scope() -> None:
    tools = asyncio.run(server.list_tools())
    retrieve = next(tool for tool in tools if tool.name == "memory_loom_retrieve")

    assert set(retrieve.input_schema["properties"]) == {"query", "limit"}


def test_propose_change_stages_without_writing_memory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "memory.db"
    monkeypatch.setenv("MEMORY_LOOM_USER_ID", "user-a")
    monkeypatch.setenv("MEMORY_LOOM_PROJECT_ID", "memory-loom")
    monkeypatch.setenv("MEMORY_LOOM_DATABASE_PATH", str(database_path))

    result = asyncio.run(
        server.call_tool(
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
    )

    assert result.structured_content is not None
    content = result.structured_content
    assert content["durable"] is False
    proposal_id = UUID(content["proposal_id"])
    try:
        proposal = proposal_store.get(proposal_id)
        assert proposal.scope.user_id == "user-a"
        assert proposal.scope.project_id == "memory-loom"
        with MemoryStore(database_path) as store:
            assert store.latest_records() == []
    finally:
        proposal_store.discard(proposal_id)


def test_commit_change_persists_create_correct_delete_lifecycle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "memory.db"
    monkeypatch.setenv("MEMORY_LOOM_USER_ID", "user-a")
    monkeypatch.setenv("MEMORY_LOOM_PROJECT_ID", "memory-loom")
    monkeypatch.setenv("MEMORY_LOOM_DATABASE_PATH", str(database_path))

    create_proposal = _call_tool(
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
    create_id = UUID(create_proposal["proposal_id"])
    created = _call_tool(
        "memory_loom_commit_change",
        {
            "proposal_id": str(create_id),
            "approval_event_id": "message-002",
            "approved_by": "user",
        },
    )
    memory_id = UUID(created["memory_id"])
    assert created["version"] == 1
    with pytest.raises(ProposalNotFoundError):
        proposal_store.get(create_id)

    correction = _call_tool(
        "memory_loom_propose_change",
        {
            "change": {
                "operation": "correct",
                "target_memory_id": str(memory_id),
                "statement": "Lead with correctness, then discuss style.",
                "source_event": {
                    "event_id": "message-003",
                    "content": "Please include style after correctness.",
                },
            }
        },
    )
    corrected = _call_tool(
        "memory_loom_commit_change",
        {
            "proposal_id": correction["proposal_id"],
            "approval_event_id": "message-004",
            "approved_by": "user",
        },
    )
    assert corrected["version"] == 2

    deletion = _call_tool(
        "memory_loom_propose_change",
        {
            "change": {
                "operation": "delete",
                "target_memory_id": str(memory_id),
            }
        },
    )
    deleted = _call_tool(
        "memory_loom_commit_change",
        {
            "proposal_id": deletion["proposal_id"],
            "approval_event_id": "message-005",
            "approved_by": "user",
        },
    )
    assert deleted["status"] == "deleted"

    active_inspection = _call_tool("memory_loom_inspect", {})
    assert active_inspection["memories"] == []
    assert active_inspection["revisions"] == []

    deleted_inspection = _call_tool(
        "memory_loom_inspect",
        {
            "memory_id": str(memory_id),
            "include_inactive": True,
        },
    )
    assert [item["version"] for item in deleted_inspection["memories"]] == [1, 2]
    assert all(
        item["statement"] is None for item in deleted_inspection["memories"]
    )
    assert [item["operation"] for item in deleted_inspection["revisions"]] == [
        "approve",
        "correct",
        "delete",
    ]

    with MemoryStore(database_path) as store:
        assert store.get_active(memory_id) is None
        assert str(memory_id) not in store.indexed_memory_ids()
        assert [item.status for item in store.records_for_lineage(memory_id)] == [
            "deleted",
            "deleted",
        ]
        revisions = store.revisions_for_lineage(memory_id)
        assert [item.operation for item in revisions] == [
            "approve",
            "correct",
            "delete",
        ]
        assert [item.approval_event_id for item in revisions] == [
            "message-002",
            "message-004",
            "message-005",
        ]
        evidence = store.connection.execute(
            "SELECT source_event_id, content_state FROM evidence_events"
        ).fetchall()
        assert {(row["source_event_id"], row["content_state"]) for row in evidence} == {
            ("message-001", "erased"),
            ("message-003", "erased"),
        }


def _call_tool(name: str, arguments: dict[str, object]) -> dict[str, object]:
    result = asyncio.run(server.call_tool(name, arguments))
    assert result.structured_content is not None
    return result.structured_content

def test_discard_change_removes_proposal_without_writing_memory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "memory.db"
    monkeypatch.setenv("MEMORY_LOOM_USER_ID", "user-a")
    monkeypatch.setenv("MEMORY_LOOM_PROJECT_ID", "memory-loom")
    monkeypatch.setenv("MEMORY_LOOM_DATABASE_PATH", str(database_path))

    proposed = _call_tool(
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
    proposal_id = UUID(proposed["proposal_id"])

    discarded = _call_tool(
        "memory_loom_discard_change",
        {
            "proposal_id": str(proposal_id),
            "reason": "user_declined",
        },
    )

    assert discarded["discarded"] is True
    assert discarded["durable_artifacts_created"] is False
    with pytest.raises(ProposalNotFoundError):
        proposal_store.get(proposal_id)
    with MemoryStore(database_path) as store:
        assert store.latest_records() == []


def test_inspect_does_not_reveal_out_of_scope_memory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "memory.db"
    scenario = Scenario.model_validate(load_json(SCENARIO_PATH))
    with MemoryStore(database_path) as store:
        store.load_scenario(scenario)

    monkeypatch.setenv("MEMORY_LOOM_USER_ID", "user-a")
    monkeypatch.setenv("MEMORY_LOOM_PROJECT_ID", "another-project")
    monkeypatch.setenv("MEMORY_LOOM_DATABASE_PATH", str(database_path))

    inspected = _call_tool(
        "memory_loom_inspect",
        {
            "memory_id": PROJECT_MEMORY_ID,
            "include_inactive": True,
        },
    )

    assert inspected["memories"] == []
    assert inspected["revisions"] == []


def test_inspect_is_declared_read_only_and_has_no_scope_argument() -> None:
    tools = asyncio.run(server.list_tools())
    inspect = next(tool for tool in tools if tool.name == "memory_loom_inspect")

    assert inspect.annotations is not None
    assert inspect.annotations.read_only_hint is True
    assert "scope" not in inspect.input_schema["properties"]
