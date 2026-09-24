from __future__ import annotations

from memory_loom.contracts import FIXTURE_DIRECTORY, load_json
from memory_loom.models import EvidenceEvent, MemoryRecord, RevisionEvent, Scenario
from memory_loom.retrieval import LexicalRetriever
from memory_loom.store import MemoryStore


SCENARIO_PATH = FIXTURE_DIRECTORY / "scenarios" / "v1" / "scope-deletion-001.json"


def test_live_retrieval_reproduces_fixture_decisions() -> None:
    scenario = Scenario.model_validate(load_json(SCENARIO_PATH))
    query = scenario.queries[0]
    expected = {
        decision.memory_id: (
            decision.eligible,
            decision.decision,
            decision.reason_code,
            decision.position,
        )
        for decision in scenario.retrieval_decisions
    }

    with MemoryStore() as store:
        store.load_scenario(scenario)
        result = LexicalRetriever(store).retrieve(
            query.query_id,
            query.content,
            query.scope,
            query.occurred_at,
        )

        actual = {
            decision.memory_id: (
                decision.eligible,
                decision.decision,
                decision.reason_code,
                decision.position,
            )
            for decision in result.decisions
        }
        assert actual == expected
        assert [record.id for record in result.selected_records] == [
            scenario.memory_records[1].id
        ]
        assert store.retrieval_trace_count(query.query_id) == 4


def test_equal_scope_conflicts_never_reach_ranking() -> None:
    scenario = Scenario.model_validate(load_json(SCENARIO_PATH))
    conflicting = MemoryRecord.model_validate(
        {
            **scenario.memory_records[1].model_dump(),
            "id": "20000000-0000-4000-8000-000000000005",
            "statement": "For Memory Loom reviews, provide only a verdict.",
            "evidence_ids": ["10000000-0000-4000-8000-000000000005"],
        }
    )
    conflicting_evidence = EvidenceEvent.model_validate(
        {
            **scenario.evidence_events[1].model_dump(),
            "id": "10000000-0000-4000-8000-000000000005",
            "content": "For Memory Loom reviews, provide only a verdict.",
        }
    )
    conflicting_revision = RevisionEvent.model_validate(
        {
            **scenario.revision_events[1].model_dump(),
            "id": "30000000-0000-4000-8000-000000000006",
            "memory_id": conflicting.id,
            "evidence_ids": [conflicting_evidence.id],
        }
    )

    with MemoryStore() as store:
        store.load_snapshot(
            [*scenario.evidence_events, conflicting_evidence],
            [*scenario.memory_records, conflicting],
            [*scenario.revision_events, conflicting_revision],
        )
        query = scenario.queries[0]
        result = LexicalRetriever(store).retrieve(
            "query-conflict", query.content, query.scope, query.occurred_at
        )

    conflict_ids = {
        decision.memory_id
        for decision in result.decisions
        if decision.decision == "conflict_filtered"
    }
    assert conflict_ids == {scenario.memory_records[1].id, conflicting.id}
    assert result.selected_records == ()
