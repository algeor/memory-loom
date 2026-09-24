PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_lineages (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_events (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('explicit_preference', 'direct_correction')),
    content TEXT,
    content_state TEXT NOT NULL CHECK (content_state IN ('present', 'erased')),
    user_scope TEXT NOT NULL,
    project_scope TEXT,
    task_scope TEXT,
    recorded_at TEXT NOT NULL,
    consent TEXT NOT NULL CHECK (consent = 'approved'),
    CHECK (
        (content_state = 'present' AND content IS NOT NULL AND length(content) > 0)
        OR (content_state = 'erased' AND content IS NULL)
    )
);

CREATE TABLE IF NOT EXISTS memory_records (
    id TEXT NOT NULL REFERENCES memory_lineages(id),
    version INTEGER NOT NULL CHECK (version >= 1),
    rule_key TEXT NOT NULL,
    statement TEXT,
    kind TEXT NOT NULL CHECK (kind IN ('preference', 'correction')),
    user_scope TEXT NOT NULL,
    project_scope TEXT,
    task_scope TEXT,
    status TEXT NOT NULL CHECK (status IN ('active', 'superseded', 'deleted')),
    created_at TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_until TEXT,
    PRIMARY KEY (id, version),
    CHECK (
        (status = 'deleted' AND statement IS NULL)
        OR (status != 'deleted' AND statement IS NOT NULL AND length(statement) > 0)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS one_active_version_per_lineage
ON memory_records(id) WHERE status = 'active';

CREATE TABLE IF NOT EXISTS memory_evidence (
    memory_id TEXT NOT NULL,
    memory_version INTEGER NOT NULL,
    evidence_id TEXT NOT NULL REFERENCES evidence_events(id),
    PRIMARY KEY (memory_id, memory_version, evidence_id),
    FOREIGN KEY (memory_id, memory_version)
        REFERENCES memory_records(id, version)
);

CREATE TABLE IF NOT EXISTS revision_events (
    id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL REFERENCES memory_lineages(id),
    operation TEXT NOT NULL CHECK (operation IN ('approve', 'correct', 'supersede', 'delete')),
    from_version INTEGER,
    to_version INTEGER,
    actor TEXT NOT NULL CHECK (actor IN ('user', 'research_fixture')),
    reason_code TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS revision_evidence (
    revision_id TEXT NOT NULL REFERENCES revision_events(id),
    evidence_id TEXT NOT NULL REFERENCES evidence_events(id),
    PRIMARY KEY (revision_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS retrieval_traces (
    query_id TEXT NOT NULL,
    memory_id TEXT NOT NULL,
    memory_version INTEGER NOT NULL,
    eligible INTEGER NOT NULL CHECK (eligible IN (0, 1)),
    decision TEXT NOT NULL,
    lexical_score REAL,
    reason_code TEXT NOT NULL,
    position INTEGER,
    created_at TEXT NOT NULL,
    PRIMARY KEY (query_id, memory_id, memory_version),
    FOREIGN KEY (memory_id, memory_version)
        REFERENCES memory_records(id, version)
);

CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
    memory_id UNINDEXED,
    memory_version UNINDEXED,
    statement,
    tokenize = 'porter unicode61'
);
