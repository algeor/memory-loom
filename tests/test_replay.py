from __future__ import annotations

from memory_loom.contracts import FIXTURE_DIRECTORY, validate_path
from memory_loom.replay import replay_query_contexts


SCENARIO_PATH = FIXTURE_DIRECTORY / "scenarios" / "v1" / "scope-deletion-001.json"
MANIFEST_PATH = FIXTURE_DIRECTORY / "manifests" / "v1" / "default-conditions.json"


def test_all_conditions_replay_within_budget() -> None:
    scenario = validate_path(SCENARIO_PATH)
    manifest = validate_path(MANIFEST_PATH)

    contexts = replay_query_contexts(scenario, manifest, "query-001")

    assert [context.condition for context in contexts] == ["B0", "B1", "B2", "B3"]
    assert all(
        context.token_count <= manifest["max_context_tokens"] for context in contexts
    )
    assert contexts[0].context == ""
    assert contexts[1].included_ids == tuple(
        sorted(contexts[1].included_ids, key=_sequence)
    )
    assert contexts[2].included_ids == ("summary-001",)


def test_structured_context_has_scope_and_provenance_without_forbidden_records() -> (
    None
):
    scenario = validate_path(SCENARIO_PATH)
    manifest = validate_path(MANIFEST_PATH)
    contexts = {
        context.condition: context
        for context in replay_query_contexts(scenario, manifest, "query-001")
    }
    structured = contexts["B3"]

    assert structured.included_ids == ("20000000-0000-4000-8000-000000000002",)
    assert "project=memory-loom" in structured.context
    assert "evidence_ids: 10000000-0000-4000-8000-000000000002" in structured.context
    assert "20000000-0000-4000-8000-000000000003" not in structured.context
    assert "20000000-0000-4000-8000-000000000004" not in structured.context


def _sequence(event_id: str) -> int:
    return int(event_id.rsplit("-", 1)[1])
