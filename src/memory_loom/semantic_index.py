from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from uuid import NAMESPACE_URL, UUID, uuid5

from memory_loom.models import MemoryRecord


SEMANTIC_EMBEDDING_MODEL = "local-hash-embedding-v1"
SEMANTIC_EMBEDDING_DIMENSION = 64


@dataclass(frozen=True)
class SemanticFacet:
    facet_type: str
    facet_value: str


@dataclass(frozen=True)
class SemanticChunk:
    chunk_id: UUID
    memory_id: UUID
    memory_version: int
    chunk_index: int
    chunk_kind: str
    content: str
    token_count: int
    content_sha256: str
    facets: tuple[SemanticFacet, ...]


@dataclass(frozen=True)
class SemanticEmbedding:
    chunk_id: UUID
    embedding_model: str
    embedding_dimension: int
    vector_json: str
    content_sha256: str


@dataclass(frozen=True)
class SemanticIndexEntry:
    chunk: SemanticChunk
    embedding: SemanticEmbedding


class SemanticMemoryIndexer:
    def __init__(
        self,
        *,
        embedding_model: str = SEMANTIC_EMBEDDING_MODEL,
        embedding_dimension: int = SEMANTIC_EMBEDDING_DIMENSION,
        chunk_token_limit: int = 32,
        chunk_token_overlap: int = 6,
    ) -> None:
        if embedding_dimension < 1:
            raise ValueError("embedding dimension must be positive")
        if chunk_token_limit < 4:
            raise ValueError("chunk token limit must be at least four")
        if not 0 <= chunk_token_overlap < chunk_token_limit:
            raise ValueError("chunk token overlap must be smaller than the limit")
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension
        self.chunk_token_limit = chunk_token_limit
        self.chunk_token_overlap = chunk_token_overlap

    def index_entries(self, memory: MemoryRecord) -> tuple[SemanticIndexEntry, ...]:
        if memory.status != "active" or not memory.statement:
            return ()

        chunks = self._chunks(memory)
        return tuple(
            SemanticIndexEntry(chunk, self._embedding(chunk)) for chunk in chunks
        )

    def _chunks(self, memory: MemoryRecord) -> tuple[SemanticChunk, ...]:
        contents = [
            ("statement", item)
            for item in _chunk_text(
                memory.statement or "",
                limit=self.chunk_token_limit,
                overlap=self.chunk_token_overlap,
            )
        ]
        rule_key_content = " ".join(_tokenize(memory.rule_key.replace(".", " ")))
        if rule_key_content:
            contents.append(("rule_key", rule_key_content))
        scope_content = _scope_content(memory)
        if scope_content:
            contents.append(("scope", scope_content))

        chunks = []
        for index, (kind, content) in enumerate(contents):
            content_hash = _sha256(content)
            chunk_id = uuid5(
                NAMESPACE_URL,
                ":".join(
                    [
                        "memory-loom",
                        "semantic-chunk",
                        str(memory.id),
                        str(memory.version),
                        str(index),
                        kind,
                        content_hash,
                    ]
                ),
            )
            chunks.append(
                SemanticChunk(
                    chunk_id=chunk_id,
                    memory_id=memory.id,
                    memory_version=memory.version,
                    chunk_index=index,
                    chunk_kind=kind,
                    content=content,
                    token_count=len(_tokenize(content)),
                    content_sha256=content_hash,
                    facets=_facets(memory, kind),
                )
            )
        return tuple(chunks)

    def _embedding(self, chunk: SemanticChunk) -> SemanticEmbedding:
        vector = _hash_embedding(chunk.content, self.embedding_dimension)
        return SemanticEmbedding(
            chunk_id=chunk.chunk_id,
            embedding_model=self.embedding_model,
            embedding_dimension=self.embedding_dimension,
            vector_json=json.dumps(vector, separators=(",", ":")),
            content_sha256=chunk.content_sha256,
        )


def _chunk_text(text: str, *, limit: int, overlap: int) -> list[str]:
    tokens = _tokenize(text)
    if not tokens:
        return []
    if len(tokens) <= limit:
        return [" ".join(tokens)]

    chunks = []
    step = limit - overlap
    for start in range(0, len(tokens), step):
        chunk = tokens[start : start + limit]
        if chunk:
            chunks.append(" ".join(chunk))
        if start + limit >= len(tokens):
            break
    return chunks


def _hash_embedding(text: str, dimension: int) -> list[float]:
    vector = [0.0] * dimension
    for token in _tokenize(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimension
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 6) for value in vector]


def _facets(memory: MemoryRecord, chunk_kind: str) -> tuple[SemanticFacet, ...]:
    rule_parts = [part for part in memory.rule_key.split(".") if part]
    scope_level = "task" if memory.scope.task_id else "project" if memory.scope.project_id else "user"
    facets = [
        SemanticFacet("chunk_kind", chunk_kind),
        SemanticFacet("memory_kind", memory.kind),
        SemanticFacet("scope_level", scope_level),
    ]
    facets.extend(SemanticFacet("rule_key_part", part) for part in rule_parts)
    return tuple(facets)


def _scope_content(memory: MemoryRecord) -> str:
    parts = ["user", memory.scope.user_id]
    if memory.scope.project_id:
        parts.extend(["project", memory.scope.project_id])
    if memory.scope.task_id:
        parts.extend(["task", memory.scope.task_id])
    return " ".join(parts)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _tokenize(value: str) -> list[str]:
    token = []
    tokens = []
    for character in value.casefold():
        if character.isalnum() or character == "_":
            token.append(character)
        elif token:
            tokens.append("".join(token))
            token = []
    if token:
        tokens.append("".join(token))
    return tokens
