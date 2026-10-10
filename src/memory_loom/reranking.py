from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from memory_loom.models import MemoryRecord


@dataclass(frozen=True)
class RetrievalCandidate:
    record: MemoryRecord
    lexical_score: float


@dataclass(frozen=True)
class RerankedCandidate:
    record: MemoryRecord
    lexical_score: float
    rerank_score: float
    reason_code: str


class CandidateReranker(Protocol):
    def rerank(
        self, query: str, candidates: tuple[RetrievalCandidate, ...]
    ) -> tuple[RerankedCandidate, ...]:
        """Return candidates in final retrieval order."""
        ...


class LexicalScoreReranker:
    """Preserve the Phase 1 lexical baseline behind an explicit reranking step."""

    def rerank(
        self, query: str, candidates: tuple[RetrievalCandidate, ...]
    ) -> tuple[RerankedCandidate, ...]:
        del query
        return tuple(
            RerankedCandidate(
                record=candidate.record,
                lexical_score=candidate.lexical_score,
                rerank_score=-candidate.lexical_score,
                reason_code="highest-lexical-score",
            )
            for candidate in sorted(candidates, key=_lexical_order_key)
        )


def _lexical_order_key(candidate: RetrievalCandidate) -> tuple[float, int, float, str]:
    record = candidate.record
    return (
        candidate.lexical_score,
        -_specificity(record),
        -record.valid_from.timestamp(),
        str(record.id),
    )


def _specificity(record: MemoryRecord) -> int:
    return 1 + int(record.scope.project_id is not None) + int(
        record.scope.task_id is not None
    )
