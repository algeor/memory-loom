from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from memory_loom.models import EvidenceEvent, MemoryRecord, RevisionEvent, Scope
from memory_loom.retrieval import LexicalRetriever
from memory_loom.store import MemoryStore


MEMORY_ID = UUID("40000000-0000-4000-8000-000000000001")
EVIDENCE_ONE = UUID("50000000-0000-4000-8000-000000000001")
EVIDENCE_TWO = UUID("50000000-0000-4000-8000-000000000002")
BASE_TIME = datetime(2026, 9, 23, 9, 0, tzinfo=UTC)
SCOPE = Scope(user_id="user-a", project_id="memory-loom", task_id=None)


def test_approval_correction_and_deletion_survive_restart(tmp_path) -> None:
    database_path = tmp_path / "memory.db"
    evidence_one = _evidence(EVIDENCE_ONE, "Prefer concise answers.", BASE_TIME)
    memory_one = _memory(1, "Prefer concise answers.", [EVIDENCE_ONE], BASE_TIME)
    approval = _revision(
        "60000000-0000-4000-8000-000000000001",
        "approve",
        None,
        1,
        [EVIDENCE_ONE],
        BASE_TIME,
    )

    with MemoryStore(database_path) as store:
        store.approve(evidence_one, memory_one, approval)
        assert store.get_active(MEMORY_ID) == memory_one
        assert str(MEMORY_ID) in store.indexed_memory_ids()

    correction_time = BASE_TIME + timedelta(days=1)
    evidence_two = _evidence(
        EVIDENCE_TWO, "Prefer concise bullet-point answers.", correction_time
    )
    memory_two = _memory(
        2,
        "Prefer concise bullet-point answers.",
        [EVIDENCE_ONE, EVIDENCE_TWO],
        correction_time,
    )
    correction = _revision(
        "60000000-0000-4000-8000-000000000002",
        "correct",
        1,
        2,
        [EVIDENCE_TWO],
        correction_time,
    )

    with MemoryStore(database_path) as store:
        store.correct(evidence_two, memory_two, correction)
        assert store.get_active(MEMORY_ID) == memory_two
        assert [record.status for record in store.records_for_lineage(MEMORY_ID)] == [
            "superseded",
            "active",
        ]
        assert [
            revision.operation for revision in store.revisions_for_lineage(MEMORY_ID)
        ] == ["approve", "correct"]
        result = LexicalRetriever(store).retrieve(
            "query-before-delete",
            "Give me a concise review",
            SCOPE,
            correction_time + timedelta(hours=1),
        )
        assert [record.id for record in result.selected_records] == [MEMORY_ID]

        deletion_time = correction_time + timedelta(days=1)
        deletion = _revision(
            "60000000-0000-4000-8000-000000000003",
            "delete",
            2,
            None,
            [],
            deletion_time,
        )
        store.delete(MEMORY_ID, deletion)

    with MemoryStore(database_path) as store:
        assert store.get_active(MEMORY_ID) is None
        assert store.latest_records()[0].statement is None
        assert [record.status for record in store.records_for_lineage(MEMORY_ID)] == [
            "deleted",
            "deleted",
        ]
        assert [
            revision.operation for revision in store.revisions_for_lineage(MEMORY_ID)
        ] == ["approve", "correct", "delete"]
        assert store.evidence_content(EVIDENCE_ONE) == (None, "erased")
        assert store.evidence_content(EVIDENCE_TWO) == (None, "erased")
        assert str(MEMORY_ID) not in store.indexed_memory_ids()
        result = LexicalRetriever(store).retrieve(
            "query-after-delete",
            "Give me a concise review",
            SCOPE,
            deletion_time + timedelta(hours=1),
        )
        assert result.selected_records == ()
        assert result.decisions[0].decision == "state_filtered"


def test_supersession_removes_memory_from_search(tmp_path) -> None:
    evidence = _evidence(EVIDENCE_ONE, "Use tables for reviews.", BASE_TIME)
    memory = _memory(1, "Use tables for reviews.", [EVIDENCE_ONE], BASE_TIME)
    approval = _revision(
        "60000000-0000-4000-8000-000000000004",
        "approve",
        None,
        1,
        [EVIDENCE_ONE],
        BASE_TIME,
    )
    supersession = _revision(
        "60000000-0000-4000-8000-000000000005",
        "supersede",
        1,
        None,
        [],
        BASE_TIME + timedelta(hours=1),
    )

    with MemoryStore(tmp_path / "memory.db") as store:
        store.approve(evidence, memory, approval)
        store.supersede(MEMORY_ID, supersession)
        assert store.get_active(MEMORY_ID) is None
        assert str(MEMORY_ID) not in store.indexed_memory_ids()


def _evidence(evidence_id: UUID, content: str, recorded_at: datetime) -> EvidenceEvent:
    return EvidenceEvent(
        id=evidence_id,
        scenario_id="lifecycle-test",
        kind="explicit_preference",
        content=content,
        content_state="present",
        scope=SCOPE,
        recorded_at=recorded_at,
        consent="approved",
    )


def _memory(
    version: int,
    statement: str,
    evidence_ids: list[UUID],
    valid_from: datetime,
) -> MemoryRecord:
    return MemoryRecord(
        id=MEMORY_ID,
        rule_key="response.style",
        statement=statement,
        kind="preference",
        scope=SCOPE,
        status="active",
        evidence_ids=evidence_ids,
        created_at=BASE_TIME,
        valid_from=valid_from,
        valid_until=None,
        version=version,
    )


def _revision(
    revision_id: str,
    operation: str,
    from_version: int | None,
    to_version: int | None,
    evidence_ids: list[UUID],
    created_at: datetime,
) -> RevisionEvent:
    return RevisionEvent.model_validate(
        {
            "id": revision_id,
            "memory_id": MEMORY_ID,
            "operation": operation,
            "from_version": from_version,
            "to_version": to_version,
            "evidence_ids": evidence_ids,
            "actor": "research_fixture",
            "reason_code": f"test-{operation}",
            "created_at": created_at,
        }
    )
