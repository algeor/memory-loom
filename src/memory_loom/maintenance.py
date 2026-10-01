from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from uuid import uuid4

from memory_loom import __version__
from memory_loom.store import MIGRATION_DIRECTORY, MemoryStore


@dataclass(frozen=True)
class DoctorReport:
    status: str
    package_version: str
    python_version: str
    expected_schema_version: int
    database_path: str
    database_exists: bool
    database_schema_version: int | None
    database_integrity: str | None
    database_compatible: bool
    database_writable: bool
    fts5_available: bool
    codex_available: bool
    claude_available: bool
    messages: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass(frozen=True)
class RestoreResult:
    database_path: Path
    safety_backup_path: Path | None
    migration_backup_path: Path | None
    schema_version: int


def diagnose(database_path: Path) -> DoctorReport:
    path = database_path.expanduser().resolve()
    expected_version = _available_migration_versions()[-1]
    exists = path.is_file()
    schema_version: int | None = None
    integrity: str | None = None
    compatible = True
    messages = []

    if exists:
        try:
            with _read_only_connection(path) as connection:
                integrity = str(connection.execute("PRAGMA quick_check").fetchone()[0])
                versions = _read_migration_versions(connection)
            schema_version = max(versions, default=0)
            compatible = bool(versions) and _versions_are_compatible(versions)
            if integrity != "ok":
                messages.append(f"database integrity check returned {integrity!r}")
            if not compatible:
                messages.append("database migration history is unsupported")
            elif schema_version < expected_version:
                messages.append("database has pending migrations")
        except sqlite3.Error as error:
            integrity = f"error: {error}"
            compatible = False
            messages.append("database could not be inspected")
    else:
        messages.append("database will be created on first use")

    writable = _destination_is_writable(path)
    if not writable:
        messages.append("database path is not writable")
    fts5_available = _fts5_available()
    if not fts5_available:
        messages.append("SQLite FTS5 is unavailable")

    has_error = (
        not compatible
        or not writable
        or not fts5_available
        or (integrity is not None and integrity != "ok")
    )
    has_warning = any("pending migrations" in message for message in messages)
    status = "error" if has_error else "warning" if has_warning else "ok"

    return DoctorReport(
        status=status,
        package_version=_package_version(),
        python_version=".".join(map(str, sys.version_info[:3])),
        expected_schema_version=expected_version,
        database_path=str(path),
        database_exists=exists,
        database_schema_version=schema_version,
        database_integrity=integrity,
        database_compatible=compatible,
        database_writable=writable,
        fts5_available=fts5_available,
        codex_available=shutil.which("codex") is not None,
        claude_available=shutil.which("claude") is not None,
        messages=tuple(messages),
    )


def backup_database(
    database_path: Path,
    output_path: Path | None = None,
    *,
    overwrite: bool = False,
) -> Path:
    source_path = database_path.expanduser().resolve()
    if not source_path.is_file():
        raise ValueError(f"database does not exist: {source_path}")

    destination_path = (
        output_path.expanduser().resolve()
        if output_path is not None
        else _default_backup_path(source_path, "manual")
    )
    if source_path == destination_path:
        raise ValueError("backup output must differ from the database path")
    if destination_path.exists() and not overwrite:
        raise ValueError(f"backup already exists: {destination_path}")

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination_path.with_name(
        f".{destination_path.name}.{uuid4().hex}.tmp"
    )
    try:
        with sqlite3.connect(source_path) as source:
            with sqlite3.connect(temporary_path) as destination:
                source.backup(destination)
        _require_healthy_database(temporary_path)
        _remove_sqlite_sidecars(destination_path)
        os.replace(temporary_path, destination_path)
        destination_path.chmod(0o600)
    finally:
        temporary_path.unlink(missing_ok=True)
    return destination_path


def restore_database(
    backup_path: Path,
    database_path: Path,
    *,
    confirmed: bool,
) -> RestoreResult:
    source_path = backup_path.expanduser().resolve()
    destination_path = database_path.expanduser().resolve()
    if not source_path.is_file():
        raise ValueError(f"backup does not exist: {source_path}")
    if source_path == destination_path:
        raise ValueError("backup and database paths must differ")
    _require_compatible_database(source_path)

    safety_backup = None
    if destination_path.exists():
        if not confirmed:
            raise ValueError("restoring over an existing database requires --yes")
        safety_backup = backup_database(destination_path)

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination_path.with_name(
        f".{destination_path.name}.{uuid4().hex}.restore"
    )
    try:
        with sqlite3.connect(source_path) as source:
            with sqlite3.connect(temporary_path) as destination:
                source.backup(destination)
        _require_healthy_database(temporary_path)
        os.replace(temporary_path, destination_path)
        destination_path.chmod(0o600)
    finally:
        temporary_path.unlink(missing_ok=True)

    with MemoryStore(destination_path) as store:
        schema_version = store.schema_version
        migration_backup = store.last_backup_path

    return RestoreResult(
        database_path=destination_path,
        safety_backup_path=safety_backup,
        migration_backup_path=migration_backup,
        schema_version=schema_version,
    )


def _default_backup_path(database_path: Path, label: str) -> Path:
    backup_directory = database_path.parent / f"{database_path.name}.backups"
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    suffix = database_path.suffix or ".db"
    return backup_directory / f"{database_path.stem}.{label}.{timestamp}{suffix}"


def _available_migration_versions() -> list[int]:
    versions = [
        int(path.name.split("_", 1)[0])
        for path in sorted(MIGRATION_DIRECTORY.glob("*.sql"))
    ]
    if not versions:
        raise ValueError("no bundled database migrations found")
    return versions


def _read_migration_versions(connection: sqlite3.Connection) -> list[int]:
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' "
        "AND name = 'schema_migrations'"
    ).fetchone()
    if exists is None:
        return []
    return sorted(
        int(row[0])
        for row in connection.execute("SELECT version FROM schema_migrations")
    )


def _versions_are_compatible(versions: list[int]) -> bool:
    available = _available_migration_versions()
    return versions == available[: len(versions)]


def _require_compatible_database(path: Path) -> None:
    _require_healthy_database(path)
    with _read_only_connection(path) as connection:
        versions = _read_migration_versions(connection)
    if not versions:
        raise ValueError(f"backup has no Memory Loom migration history: {path}")
    if not _versions_are_compatible(versions):
        raise ValueError(f"backup schema is incompatible with this release: {path}")


def _require_healthy_database(path: Path) -> None:
    try:
        with _read_only_connection(path) as connection:
            result = connection.execute("PRAGMA quick_check").fetchone()[0]
    except sqlite3.Error as error:
        raise ValueError(f"invalid SQLite database {path}: {error}") from error
    if result != "ok":
        raise ValueError(f"SQLite integrity check failed for {path}: {result}")


def _read_only_connection(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)


def _destination_is_writable(path: Path) -> bool:
    candidate = path if path.exists() else path.parent
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return os.access(candidate, os.W_OK)


def _remove_sqlite_sidecars(path: Path) -> None:
    for suffix in ("-wal", "-shm"):
        Path(f"{path}{suffix}").unlink(missing_ok=True)


def _fts5_available() -> bool:
    try:
        with sqlite3.connect(":memory:") as connection:
            connection.execute("CREATE VIRTUAL TABLE probe USING fts5(content)")
    except sqlite3.Error:
        return False
    return True


def _package_version() -> str:
    try:
        return version("memory-loom")
    except PackageNotFoundError:
        return __version__
