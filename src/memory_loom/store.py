from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from memory_loom.models import (
    EvidenceEvent,
    MemoryRecord,
    RetrievalDecision,
    RevisionEvent,
    Scenario,
)


MIGRATION_DIRECTORY = Path(__file__).with_name("migrations")


class MemoryStoreError(ValueError):
    pass


@dataclass(frozen=True)
class Migration:
    version: int
    path: Path


class MemoryStore:
    def __init__(
        self,
        database_path: str | Path = ":memory:",
        *,
        migration_directory: Path | None = None,
    ) -> None:
        self.database_path = str(database_path)
        self.migration_directory = migration_directory or MIGRATION_DIRECTORY
        self.last_backup_path: Path | None = None
        self._database_existed = self._database_file_exists()
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        try:
            self.migrate()
        except Exception:
            self.connection.close()
            raise

    def __enter__(self) -> MemoryStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    @property
    def schema_version(self) -> int:
        versions = self._applied_migration_versions()
        return max(versions, default=0)

    def migrate(self) -> None:
        migrations = _load_migrations(self.migration_directory)
        self.connection.execute("BEGIN IMMEDIATE")
        current_migration: Migration | None = None
        try:
            applied = self._applied_migration_versions()
            _validate_migration_history(applied, migrations)
            pending = [item for item in migrations if item.version not in applied]

            if pending and self._database_existed:
                self.last_backup_path = self._backup_database(pending[-1].version)

            self.connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
            for migration in pending:
                current_migration = migration
                _execute_sql_script(
                    self.connection,
                    migration.path.read_text(encoding="utf-8"),
                )
                self.connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (migration.version, _timestamp(datetime.now(UTC))),
                )
            self.connection.commit()
        except sqlite3.Error as error:
            self.connection.rollback()
            version = current_migration.version if current_migration else "unknown"
            backup = (
                f"; backup: {self.last_backup_path}"
                if self.last_backup_path is not None
                else ""
            )
            raise MemoryStoreError(
                f"database migration {version} failed{backup}: {error}"
            ) from error
        except Exception:
            self.connection.rollback()
            raise

    def _applied_migration_versions(self) -> set[int]:
        table_exists = self.connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' "
            "AND name = 'schema_migrations'"
        ).fetchone()
        if table_exists is None:
            return set()
        return {
            row["version"]
            for row in self.connection.execute("SELECT version FROM schema_migrations")
        }

    def _backup_database(self, target_version: int) -> Path:
        database_path = Path(self.database_path).expanduser().resolve()
        backup_directory = database_path.parent / f"{database_path.name}.backups"
        backup_directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        suffix = database_path.suffix or ".db"
        backup_path = backup_directory / (
            f"{database_path.stem}.pre-v{target_version}.{timestamp}{suffix}"
        )

        source = sqlite3.connect(database_path)
        destination = sqlite3.connect(backup_path)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()
        backup_path.chmod(0o600)
        return backup_path

    def _database_file_exists(self) -> bool:
        if self.database_path == ":memory:":
            return False
        path = Path(self.database_path).expanduser()
        return path.is_file() and path.stat().st_size > 0

    def approve(
        self,
        evidence: EvidenceEvent,
        memory: MemoryRecord,
        revision: RevisionEvent,
    ) -> None:
        if memory.status != "active" or memory.version != 1:
            raise MemoryStoreError("approval requires an active version-one memory")
        self._validate_transition(memory, revision, "approve", None, 1)
        self._validate_new_evidence(evidence, memory, revision)
        with self.connection:
            self.connection.execute(
                "INSERT INTO memory_lineages(id, created_at) VALUES (?, ?)",
                (str(memory.id), _timestamp(memory.created_at)),
            )
            self._insert_evidence(evidence)
            self._insert_memory(memory)
            self._insert_revision(revision)
            self._index_memory(memory)

    def correct(
        self,
        evidence: EvidenceEvent,
        memory: MemoryRecord,
        revision: RevisionEvent,
    ) -> None:
        current = self.get_active(memory.id)
        if current is None:
            raise MemoryStoreError("correction requires an active memory")
        if memory.version != current.version + 1 or memory.status != "active":
            raise MemoryStoreError("correction must create the next active version")
        if (memory.rule_key, memory.kind, memory.scope) != (
            current.rule_key,
            current.kind,
            current.scope,
        ):
            raise MemoryStoreError("correction cannot change rule key, kind, or scope")
        self._validate_transition(
            memory, revision, "correct", current.version, memory.version
        )
        self._validate_new_evidence(evidence, memory, revision)
        with self.connection:
            self.connection.execute(
                "UPDATE memory_records SET status = 'superseded', valid_until = ? "
                "WHERE id = ? AND version = ?",
                (_timestamp(memory.valid_from), str(memory.id), current.version),
            )
            self.connection.execute(
                "DELETE FROM memory_fts WHERE memory_id = ?", (str(memory.id),)
            )
            self._insert_evidence(evidence)
            self._insert_memory(memory)
            self._insert_revision(revision)
            self._index_memory(memory)

    def supersede(self, memory_id: UUID, revision: RevisionEvent) -> None:
        current = self.get_active(memory_id)
        if current is None:
            raise MemoryStoreError("supersession requires an active memory")
        self._validate_transition(current, revision, "supersede", current.version, None)
        if revision.evidence_ids:
            raise MemoryStoreError("supersession revision cannot add evidence")
        with self.connection:
            self.connection.execute(
                "UPDATE memory_records SET status = 'superseded', valid_until = ? "
                "WHERE id = ? AND version = ?",
                (_timestamp(revision.created_at), str(memory_id), current.version),
            )
            self.connection.execute(
                "DELETE FROM memory_fts WHERE memory_id = ?", (str(memory_id),)
            )
            self._insert_revision(revision)

    def delete(self, memory_id: UUID, revision: RevisionEvent) -> None:
        current = self.get_active(memory_id)
        if current is None:
            raise MemoryStoreError("deletion requires an active memory")
        self._validate_transition(current, revision, "delete", current.version, None)
        if revision.evidence_ids:
            raise MemoryStoreError("deletion revision cannot retain evidence content")
        with self.connection:
            self.connection.execute(
                "UPDATE memory_records SET status = 'deleted', statement = NULL, "
                "valid_until = COALESCE(valid_until, ?) WHERE id = ?",
                (_timestamp(revision.created_at), str(memory_id)),
            )
            self.connection.execute(
                "UPDATE evidence_events SET content = NULL, content_state = 'erased' "
                "WHERE id IN (SELECT evidence_id FROM memory_evidence WHERE memory_id = ?)",
                (str(memory_id),),
            )
            self.connection.execute(
                "DELETE FROM memory_fts WHERE memory_id = ?", (str(memory_id),)
            )
            self._insert_revision(revision)

    def load_snapshot(
        self,
        evidence_events: Iterable[EvidenceEvent],
        memory_records: Iterable[MemoryRecord],
        revision_events: Iterable[RevisionEvent],
    ) -> None:
        evidence = list(evidence_events)
        memories = list(memory_records)
        revisions = list(revision_events)
        with self.connection:
            lineages: dict[str, str] = {}
            for memory in memories:
                memory_id = str(memory.id)
                created_at = _timestamp(memory.created_at)
                lineages[memory_id] = min(
                    lineages.get(memory_id, created_at), created_at
                )
            for memory_id, created_at in sorted(lineages.items()):
                self.connection.execute(
                    "INSERT INTO memory_lineages(id, created_at) VALUES (?, ?)",
                    (memory_id, created_at),
                )
            for event in evidence:
                self._insert_evidence(event)
            for memory in memories:
                self._insert_memory(memory)
                if memory.status == "active":
                    self._index_memory(memory)
            for revision in revisions:
                self._insert_revision(revision)

    def load_scenario(self, scenario: Scenario) -> None:
        self.load_snapshot(
            scenario.evidence_events,
            scenario.memory_records,
            scenario.revision_events,
        )

    def latest_records(self) -> list[MemoryRecord]:
        rows = self.connection.execute(
            "SELECT record.* FROM memory_records AS record "
            "JOIN (SELECT id, MAX(version) AS version FROM memory_records GROUP BY id) latest "
            "ON record.id = latest.id AND record.version = latest.version "
            "ORDER BY record.id"
        ).fetchall()
        return [self._row_to_memory(row) for row in rows]

    def records_for_lineage(self, memory_id: UUID) -> list[MemoryRecord]:
        rows = self.connection.execute(
            "SELECT * FROM memory_records WHERE id = ? ORDER BY version",
            (str(memory_id),),
        ).fetchall()
        return [self._row_to_memory(row) for row in rows]

    def revisions_for_lineage(self, memory_id: UUID) -> list[RevisionEvent]:
        rows = self.connection.execute(
            "SELECT * FROM revision_events WHERE memory_id = ? ORDER BY created_at, id",
            (str(memory_id),),
        ).fetchall()
        revisions = []
        for row in rows:
            evidence_ids = [
                item["evidence_id"]
                for item in self.connection.execute(
                    "SELECT evidence_id FROM revision_evidence "
                    "WHERE revision_id = ? ORDER BY evidence_id",
                    (row["id"],),
                )
            ]
            revisions.append(
                RevisionEvent.model_validate(
                    {
                        "id": row["id"],
                        "memory_id": row["memory_id"],
                        "operation": row["operation"],
                        "from_version": row["from_version"],
                        "to_version": row["to_version"],
                        "evidence_ids": evidence_ids,
                        "actor": row["actor"],
                        "reason_code": row["reason_code"],
                        "approval_event_id": row["approval_event_id"],
                        "created_at": row["created_at"],
                    }
                )
            )
        return revisions

    def get_active(self, memory_id: UUID) -> MemoryRecord | None:
        row = self.connection.execute(
            "SELECT * FROM memory_records WHERE id = ? AND status = 'active' "
            "ORDER BY version DESC LIMIT 1",
            (str(memory_id),),
        ).fetchone()
        return self._row_to_memory(row) if row else None

    def evidence_content(self, evidence_id: UUID) -> tuple[str | None, str]:
        row = self.connection.execute(
            "SELECT content, content_state FROM evidence_events WHERE id = ?",
            (str(evidence_id),),
        ).fetchone()
        if row is None:
            raise MemoryStoreError(f"unknown evidence {evidence_id}")
        return row["content"], row["content_state"]

    def indexed_memory_ids(self) -> set[str]:
        return {
            row["memory_id"]
            for row in self.connection.execute(
                "SELECT DISTINCT memory_id FROM memory_fts"
            )
        }

    def rank_eligible(
        self, records: list[MemoryRecord], query: str
    ) -> list[tuple[UUID, float]]:
        terms = _fts_query(query)
        if not records or not terms:
            return []
        self.connection.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS temp.eligible_memory_fts USING fts5("
            "memory_id UNINDEXED, statement, tokenize = 'porter unicode61')"
        )
        self.connection.execute("DELETE FROM temp.eligible_memory_fts")
        self.connection.executemany(
            "INSERT INTO temp.eligible_memory_fts(memory_id, statement) VALUES (?, ?)",
            [(str(record.id), record.statement) for record in records],
        )
        rows = self.connection.execute(
            "SELECT memory_id, bm25(eligible_memory_fts) AS score "
            "FROM eligible_memory_fts WHERE eligible_memory_fts MATCH ?",
            (terms,),
        ).fetchall()
        return [(UUID(row["memory_id"]), float(row["score"])) for row in rows]

    def replace_retrieval_traces(
        self, query_id: str, decisions: Iterable[tuple[RetrievalDecision, int]]
    ) -> None:
        with self.connection:
            self.connection.execute(
                "DELETE FROM retrieval_traces WHERE query_id = ?", (query_id,)
            )
            self.connection.executemany(
                "INSERT INTO retrieval_traces("
                "query_id, memory_id, memory_version, eligible, decision, "
                "lexical_score, rerank_score, reason_code, position, created_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        decision.query_id,
                        str(decision.memory_id),
                        version,
                        int(decision.eligible),
                        decision.decision,
                        decision.lexical_score,
                        decision.rerank_score,
                        decision.reason_code,
                        decision.position,
                        _timestamp(datetime.now(UTC)),
                    )
                    for decision, version in decisions
                ],
            )

    def retrieval_trace_count(self, query_id: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS count FROM retrieval_traces WHERE query_id = ?",
            (query_id,),
        ).fetchone()
        return int(row["count"])

    def _insert_evidence(self, evidence: EvidenceEvent) -> None:
        self.connection.execute(
            "INSERT INTO evidence_events("
            "id, scenario_id, source_event_id, kind, content, content_state, "
            "user_scope, project_scope, task_scope, recorded_at, consent"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(evidence.id),
                evidence.scenario_id,
                evidence.source_event_id,
                evidence.kind,
                evidence.content,
                evidence.content_state,
                evidence.scope.user_id,
                evidence.scope.project_id,
                evidence.scope.task_id,
                _timestamp(evidence.recorded_at),
                evidence.consent,
            ),
        )

    def _insert_memory(self, memory: MemoryRecord) -> None:
        for evidence_id in memory.evidence_ids:
            owner = self.connection.execute(
                "SELECT memory_id FROM memory_evidence WHERE evidence_id = ? "
                "AND memory_id != ? LIMIT 1",
                (str(evidence_id), str(memory.id)),
            ).fetchone()
            if owner:
                raise MemoryStoreError(
                    f"evidence {evidence_id} belongs to another memory lineage"
                )
        self.connection.execute(
            "INSERT INTO memory_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(memory.id),
                memory.version,
                memory.rule_key,
                memory.statement,
                memory.kind,
                memory.scope.user_id,
                memory.scope.project_id,
                memory.scope.task_id,
                memory.status,
                _timestamp(memory.created_at),
                _timestamp(memory.valid_from),
                _timestamp(memory.valid_until),
            ),
        )
        self.connection.executemany(
            "INSERT INTO memory_evidence(memory_id, memory_version, evidence_id) "
            "VALUES (?, ?, ?)",
            [
                (str(memory.id), memory.version, str(evidence_id))
                for evidence_id in memory.evidence_ids
            ],
        )

    def _insert_revision(self, revision: RevisionEvent) -> None:
        self.connection.execute(
            "INSERT INTO revision_events("
            "id, memory_id, operation, from_version, to_version, actor, "
            "reason_code, approval_event_id, created_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(revision.id),
                str(revision.memory_id),
                revision.operation,
                revision.from_version,
                revision.to_version,
                revision.actor,
                revision.reason_code,
                revision.approval_event_id,
                _timestamp(revision.created_at),
            ),
        )
        self.connection.executemany(
            "INSERT INTO revision_evidence(revision_id, evidence_id) VALUES (?, ?)",
            [(str(revision.id), str(item)) for item in revision.evidence_ids],
        )

    def _index_memory(self, memory: MemoryRecord) -> None:
        self.connection.execute(
            "INSERT INTO memory_fts(memory_id, memory_version, statement) VALUES (?, ?, ?)",
            (str(memory.id), memory.version, memory.statement),
        )

    def _row_to_memory(self, row: sqlite3.Row) -> MemoryRecord:
        evidence_ids = [
            item["evidence_id"]
            for item in self.connection.execute(
                "SELECT evidence_id FROM memory_evidence "
                "WHERE memory_id = ? AND memory_version = ? ORDER BY evidence_id",
                (row["id"], row["version"]),
            )
        ]
        return MemoryRecord.model_validate(
            {
                "id": row["id"],
                "rule_key": row["rule_key"],
                "statement": row["statement"],
                "kind": row["kind"],
                "scope": {
                    "user_id": row["user_scope"],
                    "project_id": row["project_scope"],
                    "task_id": row["task_scope"],
                },
                "status": row["status"],
                "evidence_ids": evidence_ids,
                "created_at": row["created_at"],
                "valid_from": row["valid_from"],
                "valid_until": row["valid_until"],
                "version": row["version"],
            }
        )

    @staticmethod
    def _validate_new_evidence(
        evidence: EvidenceEvent,
        memory: MemoryRecord,
        revision: RevisionEvent,
    ) -> None:
        if evidence.id not in memory.evidence_ids:
            raise MemoryStoreError("new evidence must be linked from the memory")
        if evidence.id not in revision.evidence_ids:
            raise MemoryStoreError("new evidence must be linked from the revision")
        if evidence.scope != memory.scope:
            raise MemoryStoreError("evidence and memory scopes must match")

    @staticmethod
    def _validate_transition(
        memory: MemoryRecord,
        revision: RevisionEvent,
        operation: str,
        from_version: int | None,
        to_version: int | None,
    ) -> None:
        if (
            revision.memory_id != memory.id
            or revision.operation != operation
            or revision.from_version != from_version
            or revision.to_version != to_version
        ):
            raise MemoryStoreError(f"invalid {operation} revision")


def _timestamp(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _load_migrations(directory: Path) -> list[Migration]:
    migrations = []
    for path in sorted(directory.glob("*.sql")):
        try:
            version = int(path.name.split("_", 1)[0])
        except ValueError as error:
            raise MemoryStoreError(f"invalid migration filename: {path.name}") from error
        migrations.append(Migration(version=version, path=path))

    if not migrations:
        raise MemoryStoreError(f"no SQLite migrations found in {directory}")
    versions = [item.version for item in migrations]
    if len(versions) != len(set(versions)):
        raise MemoryStoreError("SQLite migration versions must be unique")
    expected = list(range(1, versions[-1] + 1))
    if versions != expected:
        raise MemoryStoreError(
            f"SQLite migration versions must be contiguous: expected {expected}, "
            f"found {versions}"
        )
    return migrations


def _validate_migration_history(
    applied: set[int], migrations: list[Migration]
) -> None:
    available = [item.version for item in migrations]
    unknown = sorted(applied - set(available))
    if unknown:
        if unknown[-1] > available[-1]:
            raise MemoryStoreError(
                "database uses newer migration versions unsupported by this "
                f"release: {unknown}"
            )
        raise MemoryStoreError(f"database uses unavailable migration versions: {unknown}")

    expected_applied = set(available[: len(applied)])
    if applied != expected_applied:
        raise MemoryStoreError(
            f"database migration history is not contiguous: {sorted(applied)}"
        )


def _execute_sql_script(connection: sqlite3.Connection, script: str) -> None:
    statement = ""
    for line in script.splitlines(keepends=True):
        statement += line
        if not sqlite3.complete_statement(statement):
            continue
        sql = statement.strip()
        if sql:
            connection.execute(sql)
        statement = ""
    if statement.strip():
        raise MemoryStoreError("migration contains an incomplete SQL statement")


def _fts_query(query: str) -> str:
    terms = [term for term in _tokenize(query) if len(term) > 1]
    return " OR ".join(f'"{term}"' for term in terms)


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
