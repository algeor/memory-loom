CREATE TABLE IF NOT EXISTS memory_semantic_chunks (
    chunk_id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL,
    memory_version INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    chunk_kind TEXT NOT NULL CHECK (chunk_kind IN ('statement', 'rule_key', 'scope')),
    content TEXT NOT NULL CHECK (length(content) > 0),
    token_count INTEGER NOT NULL CHECK (token_count >= 1),
    content_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (memory_id, memory_version, chunk_index, chunk_kind),
    FOREIGN KEY (memory_id, memory_version)
        REFERENCES memory_records(id, version)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS memory_semantic_facets (
    chunk_id TEXT NOT NULL REFERENCES memory_semantic_chunks(chunk_id) ON DELETE CASCADE,
    facet_type TEXT NOT NULL,
    facet_value TEXT NOT NULL,
    PRIMARY KEY (chunk_id, facet_type, facet_value)
);

CREATE TABLE IF NOT EXISTS memory_semantic_embeddings (
    chunk_id TEXT NOT NULL REFERENCES memory_semantic_chunks(chunk_id) ON DELETE CASCADE,
    embedding_model TEXT NOT NULL,
    embedding_dimension INTEGER NOT NULL CHECK (embedding_dimension >= 1),
    vector_json TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (chunk_id, embedding_model)
);

CREATE INDEX IF NOT EXISTS memory_semantic_chunks_memory_idx
ON memory_semantic_chunks(memory_id, memory_version);

CREATE INDEX IF NOT EXISTS memory_semantic_facets_type_value_idx
ON memory_semantic_facets(facet_type, facet_value);
