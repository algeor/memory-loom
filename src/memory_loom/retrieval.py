from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from memory_loom.models import MemoryRecord, RetrievalDecision, Scope
from memory_loom.store import MemoryStore


@dataclass(frozen=True)
class RetrievalResult:
    decisions: tuple[RetrievalDecision, ...]
    selected_records: tuple[MemoryRecord, ...]


class LexicalRetriever:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def retrieve(
        self,
        query_id: str,
        query: str,
        scope: Scope,
        at: datetime,
        limit: int = 5,
    ) -> RetrievalResult:
        if limit < 1:
            raise ValueError("limit must be at least one")

        records = self.store.latest_records()
        versions = {record.id: record.version for record in records}
        decisions: dict[UUID, RetrievalDecision] = {}
        eligible: list[MemoryRecord] = []

        for record in records:
            scope_reason = _scope_filter_reason(record.scope, scope)
            if scope_reason:
                decisions[record.id] = _decision(
                    query_id, record.id, False, "scope_filtered", scope_reason
                )
            elif not _active_at(record, at):
                decisions[record.id] = _decision(
                    query_id,
                    record.id,
                    False,
                    "state_filtered",
                    _state_reason(record),
                )
            else:
                eligible.append(record)

        rankable: list[MemoryRecord] = []
        by_rule: dict[str, list[MemoryRecord]] = defaultdict(list)
        for record in eligible:
            by_rule[record.rule_key].append(record)

        for rule_records in by_rule.values():
            most_specific = max(_specificity(record.scope) for record in rule_records)
            specific_records = []
            for record in rule_records:
                if _specificity(record.scope) < most_specific:
                    decisions[record.id] = _decision(
                        query_id,
                        record.id,
                        True,
                        "specificity_filtered",
                        "narrower-rule-match",
                    )
                else:
                    specific_records.append(record)

            statements = {record.statement for record in specific_records}
            if len(statements) > 1:
                for record in specific_records:
                    decisions[record.id] = _decision(
                        query_id,
                        record.id,
                        True,
                        "conflict_filtered",
                        "equal-scope-conflict",
                    )
                continue

            rankable.append(min(specific_records, key=lambda item: str(item.id)))
            for duplicate in sorted(specific_records, key=lambda item: str(item.id))[
                1:
            ]:
                decisions[duplicate.id] = _decision(
                    query_id,
                    duplicate.id,
                    True,
                    "conflict_filtered",
                    "duplicate-rule-collapsed",
                )

        scores = dict(self.store.rank_eligible(rankable, query))
        ranked = sorted(
            (record for record in rankable if record.id in scores),
            key=lambda record: (
                scores[record.id],
                -_specificity(record.scope),
                -record.valid_from.timestamp(),
                str(record.id),
            ),
        )
        for record in rankable:
            if record.id not in scores:
                decisions[record.id] = _decision(
                    query_id,
                    record.id,
                    True,
                    "lexical_filtered",
                    "no-lexical-match",
                )

        selected_records = ranked[:limit]
        for position, record in enumerate(selected_records, 1):
            decisions[record.id] = _decision(
                query_id,
                record.id,
                True,
                "selected",
                "highest-lexical-score",
                lexical_score=scores[record.id],
                position=position,
            )
        for record in ranked[limit:]:
            decisions[record.id] = _decision(
                query_id,
                record.id,
                True,
                "budget_filtered",
                "result-limit",
                lexical_score=scores[record.id],
            )

        ordered_decisions = tuple(decisions[record.id] for record in records)
        self.store.replace_retrieval_traces(
            query_id,
            (
                (decision, versions[decision.memory_id])
                for decision in ordered_decisions
            ),
        )
        return RetrievalResult(ordered_decisions, tuple(selected_records))


def _decision(
    query_id: str,
    memory_id: UUID,
    eligible: bool,
    decision: str,
    reason_code: str,
    lexical_score: float | None = None,
    position: int | None = None,
) -> RetrievalDecision:
    return RetrievalDecision.model_validate(
        {
            "query_id": query_id,
            "memory_id": memory_id,
            "eligible": eligible,
            "decision": decision,
            "lexical_score": lexical_score,
            "reason_code": reason_code,
            "position": position,
        }
    )


def _scope_filter_reason(record_scope: Scope, query_scope: Scope) -> str | None:
    if record_scope.user_id != query_scope.user_id:
        return "user-scope-mismatch"
    if record_scope.project_id not in (None, query_scope.project_id):
        return "project-scope-mismatch"
    if record_scope.task_id not in (None, query_scope.task_id):
        return "task-scope-mismatch"
    return None


def _active_at(record: MemoryRecord, at: datetime) -> bool:
    if record.status != "active" or record.valid_from > at:
        return False
    return record.valid_until is None or at < record.valid_until


def _state_reason(record: MemoryRecord) -> str:
    if record.status == "deleted":
        return "deleted-record"
    if record.status == "superseded":
        return "superseded-record"
    return "outside-validity-window"


def _specificity(scope: Scope) -> int:
    return 1 + int(scope.project_id is not None) + int(scope.task_id is not None)
