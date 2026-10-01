from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import UUID

import pytest

from memory_loom.contracts import FIXTURE_DIRECTORY, load_json
from memory_loom.mcp_server import server
from memory_loom.mcp_proposals import proposal_store
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
