from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest

from memory_loom.cli import main
from memory_loom.store import MIGRATION_DIRECTORY, MemoryStore, MemoryStoreError


MEMORY_ID = "40000000-0000-4000-8000-000000000001"
EVIDENCE_ID = "50000000-0000-4000-8000-000000000001"
REVISION_ID = "60000000-0000-4000-8000-000000000001"


def test_real_migration_preserves_v1_records_and_creates_backup(tmp_path: Path) -> None:
    database_path = tmp_path / "memory.db"
    v1_migrations = tmp_path / "v1-migrations"
    v1_migrations.mkdir()
    shutil.copy(MIGRATION_DIRECTORY / "001_initial.sql", v1_migrations)
    _create_v1_database(database_path, v1_migrations)

    with MemoryStore(database_path) as store:
        assert store.last_backup_path is not None
        backup_path = store.last_backup_path
        active = store.get_active(_uuid(MEMORY_ID))
        assert active is not None
        assert active.statement == "Prefer concise answers."
        assert store.evidence_content(_uuid(EVIDENCE_ID)) == (
            "Prefer concise answers.",
            "present",
        )
        assert [item.operation for item in store.revisions_for_lineage(active.id)] == [
            "approve"
        ]
        trace_columns = {
            row[1]
            for row in store.connection.execute("PRAGMA table_info(retrieval_traces)")
        }
        assert "rerank_score" in trace_columns

    assert backup_path.is_file()
    with sqlite3.connect(backup_path) as backup:
        assert backup.execute("SELECT statement FROM memory_records").fetchone() == (
            "Prefer concise answers.",
        )
        evidence_columns = {
            row[1] for row in backup.execute("PRAGMA table_info(evidence_events)")
        }
        assert "source_event_id" not in evidence_columns


def test_failed_migration_rolls_back_and_keeps_backup(tmp_path: Path) -> None:
    database_path = tmp_path / "memory.db"
    with MemoryStore(database_path):
        pass
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO memory_lineages(id, created_at) VALUES (?, ?)",
            (MEMORY_ID, "2026-10-01T09:00:00Z"),
        )
        connection.commit()

    migrations = _copy_current_migrations(tmp_path)
    (migrations / "004_failure.sql").write_text(
        "ALTER TABLE memory_lineages ADD COLUMN test_marker TEXT;\n"
        "THIS IS NOT VALID SQL;\n",
        encoding="utf-8",
    )

    with pytest.raises(MemoryStoreError, match="migration 4 failed"):
        MemoryStore(database_path, migration_directory=migrations)

    backups = list((tmp_path / "memory.db.backups").glob("*.db"))
    assert len(backups) == 1
    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(memory_lineages)")
        }
        versions = {
            row[0] for row in connection.execute("SELECT version FROM schema_migrations")
        }
        assert "test_marker" not in columns
        assert versions == {1, 2, 3}
        assert connection.execute("SELECT id FROM memory_lineages").fetchone() == (
            MEMORY_ID,
        )


def test_newer_database_schema_is_rejected_without_changes(tmp_path: Path) -> None:
    database_path = tmp_path / "memory.db"
    with MemoryStore(database_path):
        pass
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO schema_migrations(version, applied_at) VALUES (999, ?)",
            ("2026-10-01T09:00:00Z",),
        )
        connection.commit()

    with pytest.raises(MemoryStoreError, match="newer migration versions"):
        MemoryStore(database_path)

    assert not (tmp_path / "memory.db.backups").exists()
    with sqlite3.connect(database_path) as connection:
        versions = {
            row[0] for row in connection.execute("SELECT version FROM schema_migrations")
        }
    assert versions == {1, 2, 3, 999}


def test_current_database_does_not_create_redundant_backup(tmp_path: Path) -> None:
    database_path = tmp_path / "memory.db"
    with MemoryStore(database_path):
        pass
    with MemoryStore(database_path) as store:
        assert store.last_backup_path is None
    assert not (tmp_path / "memory.db.backups").exists()


def test_migrate_cli_reports_backup_and_preserves_database(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_path = tmp_path / "memory.db"
    v1_migrations = tmp_path / "v1-migrations"
    v1_migrations.mkdir()
    shutil.copy(MIGRATION_DIRECTORY / "001_initial.sql", v1_migrations)
    _create_v1_database(database_path, v1_migrations)

    assert main(["migrate", "--database", str(database_path)]) == 0

    output = capsys.readouterr().out
    assert f"ready: {database_path} (schema 3)" in output
    assert "backup:" in output
    with MemoryStore(database_path) as store:
        active = store.get_active(_uuid(MEMORY_ID))
        assert active is not None
        assert active.statement == "Prefer concise answers."


def _create_v1_database(database_path: Path, migrations: Path) -> None:
    with MemoryStore(database_path, migration_directory=migrations) as store:
        store.connection.execute(
            "INSERT INTO memory_lineages(id, created_at) VALUES (?, ?)",
            (MEMORY_ID, "2026-10-01T09:00:00Z"),
        )
        store.connection.execute(
            "INSERT INTO evidence_events("
            "id, scenario_id, kind, content, content_state, user_scope, "
            "project_scope, task_scope, recorded_at, consent"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                EVIDENCE_ID,
                "upgrade-test",
                "explicit_preference",
                "Prefer concise answers.",
                "present",
                "user-a",
                "memory-loom",
                None,
                "2026-10-01T09:00:00Z",
                "approved",
            ),
        )
        store.connection.execute(
            "INSERT INTO memory_records("
            "id, version, rule_key, statement, kind, user_scope, project_scope, "
            "task_scope, status, created_at, valid_from, valid_until"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                MEMORY_ID,
                1,
                "response.conciseness",
                "Prefer concise answers.",
                "preference",
                "user-a",
                "memory-loom",
                None,
                "active",
                "2026-10-01T09:00:00Z",
                "2026-10-01T09:00:00Z",
                None,
            ),
        )
        store.connection.execute(
            "INSERT INTO memory_evidence(memory_id, memory_version, evidence_id) "
            "VALUES (?, 1, ?)",
            (MEMORY_ID, EVIDENCE_ID),
        )
        store.connection.execute(
            "INSERT INTO revision_events("
            "id, memory_id, operation, from_version, to_version, actor, "
            "reason_code, created_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                REVISION_ID,
                MEMORY_ID,
                "approve",
                None,
                1,
                "user",
                "explicit-user-approval",
                "2026-10-01T09:00:00Z",
            ),
        )
        store.connection.execute(
            "INSERT INTO revision_evidence(revision_id, evidence_id) VALUES (?, ?)",
            (REVISION_ID, EVIDENCE_ID),
        )
        store.connection.execute(
            "INSERT INTO memory_fts(memory_id, memory_version, statement) "
            "VALUES (?, 1, ?)",
            (MEMORY_ID, "Prefer concise answers."),
        )
        store.connection.commit()


def _copy_current_migrations(tmp_path: Path) -> Path:
    destination = tmp_path / "migrations"
    destination.mkdir()
    for migration in MIGRATION_DIRECTORY.glob("*.sql"):
        shutil.copy(migration, destination)
    return destination


def _uuid(value: str):
    from uuid import UUID

    return UUID(value)
