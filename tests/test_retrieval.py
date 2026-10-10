from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from memory_loom.contracts import FIXTURE_DIRECTORY, load_json
from memory_loom.models import EvidenceEvent, MemoryRecord, RevisionEvent, Scenario, Scope
from memory_loom.reranking import RerankedCandidate, RetrievalCandidate
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
        expected[scenario.memory_records[1].id] = (
            True,
            "selected",
            "hybrid-score",
            1,
        )
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


def test_custom_reranker_can_reorder_lexical_candidates() -> None:
    scenario = Scenario.model_validate(load_json(SCENARIO_PATH))
    first_candidate = scenario.memory_records[1]
    preferred_candidate = MemoryRecord.model_validate(
        {
            **first_candidate.model_dump(),
            "id": "20000000-0000-4000-8000-000000000006",
            "rule_key": "response.verdict",
            "statement": "For Memory Loom documentation reviews, return a short verdict.",
            "evidence_ids": ["10000000-0000-4000-8000-000000000006"],
        }
    )
    preferred_evidence = EvidenceEvent.model_validate(
        {
            **scenario.evidence_events[1].model_dump(),
            "id": "10000000-0000-4000-8000-000000000006",
            "content": preferred_candidate.statement,
        }
    )
    preferred_revision = RevisionEvent.model_validate(
        {
            **scenario.revision_events[1].model_dump(),
            "id": "30000000-0000-4000-8000-000000000006",
            "memory_id": preferred_candidate.id,
            "evidence_ids": [preferred_evidence.id],
        }
    )

    with MemoryStore() as store:
        store.load_snapshot(
            [*scenario.evidence_events, preferred_evidence],
            [*scenario.memory_records, preferred_candidate],
            [*scenario.revision_events, preferred_revision],
        )
        query = scenario.queries[0]
        result = LexicalRetriever(store, reranker=_PreferVerdictReranker()).retrieve(
            "query-rerank", query.content, query.scope, query.occurred_at, limit=1
        )

        assert result.selected_records[0].id == preferred_candidate.id
        selected_decision = next(
            decision
            for decision in result.decisions
            if decision.memory_id == preferred_candidate.id
        )
        assert selected_decision.reason_code == "semantic-reranker"
        assert selected_decision.rerank_score == 1.0
        trace = store.connection.execute(
            "SELECT rerank_score FROM retrieval_traces WHERE query_id = ? "
            "AND memory_id = ?",
            ("query-rerank", str(preferred_candidate.id)),
        ).fetchone()
        assert trace["rerank_score"] == 1.0


def test_semantic_candidates_are_used_when_statement_has_no_lexical_match() -> None:
    memory_id = UUID("40000000-0000-4000-8000-000000000001")
    evidence_id = UUID("50000000-0000-4000-8000-000000000001")
    revision_id = UUID("60000000-0000-4000-8000-000000000001")
    timestamp = datetime(2026, 10, 10, 9, 0, tzinfo=UTC)
    scope = Scope(user_id="user-a", project_id="memory-loom", task_id=None)
    evidence = EvidenceEvent(
        id=evidence_id,
        scenario_id="semantic-retrieval-test",
        kind="explicit_preference",
        content="Prefer short answers.",
        content_state="present",
        scope=scope,
        recorded_at=timestamp,
        consent="approved",
    )
    memory = MemoryRecord(
        id=memory_id,
        rule_key="response.conciseness",
        statement="Prefer short answers.",
        kind="preference",
        scope=scope,
        status="active",
        evidence_ids=[evidence_id],
        created_at=timestamp,
        valid_from=timestamp,
        valid_until=None,
        version=1,
    )
    revision = RevisionEvent.model_validate(
        {
            "id": revision_id,
            "memory_id": memory_id,
            "operation": "approve",
            "from_version": None,
            "to_version": 1,
            "evidence_ids": [evidence_id],
            "actor": "research_fixture",
            "reason_code": "explicit-user-approval",
            "created_at": timestamp,
        }
    )

    with MemoryStore() as store:
        store.approve(evidence, memory, revision)
        result = LexicalRetriever(store).retrieve(
            "semantic-query",
            "response conciseness",
            scope,
            timestamp,
        )

        assert [record.id for record in result.selected_records] == [memory_id]
        selected = next(
            decision for decision in result.decisions if decision.position == 1
        )
        assert selected.reason_code == "semantic-score"
        assert selected.rerank_score is not None and selected.rerank_score > 0


class _PreferVerdictReranker:
    def rerank(
        self, query: str, candidates: tuple[RetrievalCandidate, ...]
    ) -> tuple[RerankedCandidate, ...]:
        del query
        ranked = sorted(
            candidates,
            key=lambda candidate: "verdict" in (candidate.record.statement or ""),
            reverse=True,
        )
        return tuple(
            RerankedCandidate(
                record=candidate.record,
                lexical_score=candidate.lexical_score,
                rerank_score=1.0 if candidate is ranked[0] else 0.0,
                reason_code="semantic-reranker",
            )
            for candidate in ranked
        )
