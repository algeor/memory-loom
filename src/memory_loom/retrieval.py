from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from memory_loom.models import MemoryRecord, RetrievalDecision, Scope
from memory_loom.reranking import (
    CandidateReranker,
    LexicalScoreReranker,
    RetrievalCandidate,
)
from memory_loom.store import MemoryStore


@dataclass(frozen=True)
class RetrievalResult:
    decisions: tuple[RetrievalDecision, ...]
    selected_records: tuple[MemoryRecord, ...]


class LexicalRetriever:
    def __init__(
        self, store: MemoryStore, reranker: CandidateReranker | None = None
    ) -> None:
        self.store = store
        self.reranker = reranker or LexicalScoreReranker()

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

        lexical_scores = dict(self.store.rank_eligible(rankable, query))
        semantic_scores = dict(self.store.rank_semantic_eligible(rankable, query))
        candidate_ids = set(lexical_scores) | set(semantic_scores)
        ranked = self.reranker.rerank(
            query,
            tuple(
                RetrievalCandidate(
                    record=record,
                    lexical_score=_candidate_score(
                        lexical_scores.get(record.id), semantic_scores.get(record.id)
                    ),
                    semantic_score=semantic_scores.get(record.id),
                    reason_code=_candidate_reason(
                        lexical_scores.get(record.id), semantic_scores.get(record.id)
                    ),
                )
                for record in rankable
                if record.id in candidate_ids
            ),
        )
        for record in rankable:
            if record.id not in candidate_ids:
                decisions[record.id] = _decision(
                    query_id,
                    record.id,
                    True,
                    "lexical_filtered",
                    "no-hybrid-match",
                )

        selected_candidates = ranked[:limit]
        for position, candidate in enumerate(selected_candidates, 1):
            record = candidate.record
            decisions[record.id] = _decision(
                query_id,
                record.id,
                True,
                "selected",
                candidate.reason_code,
                lexical_score=candidate.lexical_score,
                rerank_score=candidate.rerank_score,
                position=position,
            )
        for candidate in ranked[limit:]:
            record = candidate.record
            decisions[record.id] = _decision(
                query_id,
                record.id,
                True,
                "budget_filtered",
                "result-limit",
                lexical_score=candidate.lexical_score,
                rerank_score=candidate.rerank_score,
            )

        ordered_decisions = tuple(decisions[record.id] for record in records)
        self.store.replace_retrieval_traces(
            query_id,
            (
                (decision, versions[decision.memory_id])
                for decision in ordered_decisions
            ),
        )
        return RetrievalResult(
            ordered_decisions,
            tuple(candidate.record for candidate in selected_candidates),
        )


def _decision(
    query_id: str,
    memory_id: UUID,
    eligible: bool,
    decision: str,
    reason_code: str,
    lexical_score: float | None = None,
    rerank_score: float | None = None,
    position: int | None = None,
) -> RetrievalDecision:
    return RetrievalDecision.model_validate(
        {
            "query_id": query_id,
            "memory_id": memory_id,
            "eligible": eligible,
            "decision": decision,
            "lexical_score": lexical_score,
            "rerank_score": rerank_score,
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


def _candidate_score(
    lexical_score: float | None, semantic_score: float | None
) -> float:
    if lexical_score is not None:
        return lexical_score
    if semantic_score is not None:
        return -semantic_score
    raise ValueError("candidate requires a lexical or semantic score")


def _candidate_reason(
    lexical_score: float | None, semantic_score: float | None
) -> str:
    if lexical_score is not None and semantic_score is not None:
        return "hybrid-score"
    if semantic_score is not None:
        return "semantic-score"
    return "highest-lexical-score"
