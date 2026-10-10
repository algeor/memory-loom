from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from memory_loom.models import MemoryRecord, Scope
from memory_loom.semantic_index import (
    SEMANTIC_EMBEDDING_DIMENSION,
    SEMANTIC_EMBEDDING_MODEL,
    SemanticMemoryIndexer,
)


MEMORY_ID = UUID("40000000-0000-4000-8000-000000000001")
EVIDENCE_ID = UUID("50000000-0000-4000-8000-000000000001")
BASE_TIME = datetime(2026, 10, 10, 9, 0, tzinfo=UTC)


def test_semantic_indexer_chunks_facets_and_embeds_memory() -> None:
    memory = MemoryRecord(
        id=MEMORY_ID,
        rule_key="reviews.output.style",
        statement=(
            "When reviewing code, lead with concrete risks, cite files, keep "
            "summaries short, and call out missing tests separately."
        ),
        kind="preference",
        scope=Scope(user_id="user-a", project_id="memory-loom", task_id="task-7"),
        status="active",
        evidence_ids=[EVIDENCE_ID],
        created_at=BASE_TIME,
        valid_from=BASE_TIME,
        valid_until=None,
        version=1,
    )
    indexer = SemanticMemoryIndexer(chunk_token_limit=8, chunk_token_overlap=2)

    entries = indexer.index_entries(memory)

    assert [entry.chunk.chunk_kind for entry in entries] == [
        "statement",
        "statement",
        "statement",
        "rule_key",
        "scope",
    ]
    assert entries[0].chunk.content.split()[-2:] == entries[1].chunk.content.split()[:2]
    assert entries[0].embedding.embedding_model == SEMANTIC_EMBEDDING_MODEL
    assert entries[0].embedding.embedding_dimension == SEMANTIC_EMBEDDING_DIMENSION
    assert len(json.loads(entries[0].embedding.vector_json)) == SEMANTIC_EMBEDDING_DIMENSION
    assert {facet.facet_value for facet in entries[-1].chunk.facets} >= {
        "scope",
        "preference",
        "task",
        "reviews",
        "output",
        "style",
    }


def test_semantic_indexer_skips_non_active_or_erased_memory() -> None:
    memory = MemoryRecord(
        id=MEMORY_ID,
        rule_key="reviews.output.style",
        statement=None,
        kind="preference",
        scope=Scope(user_id="user-a", project_id="memory-loom", task_id=None),
        status="deleted",
        evidence_ids=[EVIDENCE_ID],
        created_at=BASE_TIME,
        valid_from=BASE_TIME,
        valid_until=BASE_TIME,
        version=1,
    )

    assert SemanticMemoryIndexer().index_entries(memory) == ()
