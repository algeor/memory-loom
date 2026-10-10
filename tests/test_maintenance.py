from __future__ import annotations

from pathlib import Path

import pytest

from memory_loom.contracts import FIXTURE_DIRECTORY, load_json
from memory_loom.maintenance import backup_database, diagnose, restore_database
from memory_loom.models import Scenario
from memory_loom.store import MemoryStore


SCENARIO_PATH = FIXTURE_DIRECTORY / "scenarios" / "v1" / "global-preference-001.json"


def test_doctor_reports_fresh_and_current_databases(tmp_path: Path) -> None:
    database_path = tmp_path / "memory.db"

    fresh = diagnose(database_path)
    assert fresh.status == "ok"
    assert fresh.database_exists is False
    assert fresh.fts5_available is True

    with MemoryStore(database_path):
        pass
    current = diagnose(database_path)
    assert current.status == "ok"
    assert current.database_exists is True
    assert current.database_schema_version == current.expected_schema_version
    assert current.database_integrity == "ok"
    assert current.database_compatible is True


def test_backup_and_restore_preserve_memory(tmp_path: Path) -> None:
    database_path = tmp_path / "memory.db"
    scenario = Scenario.model_validate(load_json(SCENARIO_PATH))
    memory_id = scenario.memory_records[0].id
    with MemoryStore(database_path) as store:
        store.load_scenario(scenario)

    backup_path = backup_database(database_path)
    with MemoryStore(database_path) as store:
        store.connection.execute(
            "UPDATE memory_records SET statement = ? WHERE id = ?",
            ("Changed after backup.", str(memory_id)),
        )
        store.connection.commit()

    restored = restore_database(backup_path, database_path, confirmed=True)

    assert restored.safety_backup_path is not None
    assert restored.safety_backup_path.is_file()
    assert restored.schema_version == 4
    with MemoryStore(database_path) as store:
        memory = store.get_active(memory_id)
        assert memory is not None
        assert memory.statement == scenario.memory_records[0].statement


def test_restore_requires_confirmation_before_overwrite(tmp_path: Path) -> None:
    database_path = tmp_path / "memory.db"
    with MemoryStore(database_path):
        pass
    backup_path = backup_database(database_path)

    with pytest.raises(ValueError, match="requires --yes"):
        restore_database(backup_path, database_path, confirmed=False)


def test_backup_refuses_to_overwrite_without_force(tmp_path: Path) -> None:
    database_path = tmp_path / "memory.db"
    output_path = tmp_path / "backup.db"
    with MemoryStore(database_path):
        pass
    backup_database(database_path, output_path)

    with pytest.raises(ValueError, match="already exists"):
        backup_database(database_path, output_path)
