from __future__ import annotations

import os
from pathlib import Path

from pydantic import TypeAdapter

from memory_loom.models import Identifier, Scope


_IDENTIFIER_ADAPTER = TypeAdapter(Identifier)


def configured_user_id() -> str:
    value = os.environ.get("MEMORY_LOOM_USER_ID")
    if value is None:
        raise RuntimeError("MEMORY_LOOM_USER_ID is required")
    return _IDENTIFIER_ADAPTER.validate_python(value)


def configured_scope() -> Scope:
    project_id = _optional_identifier("MEMORY_LOOM_PROJECT_ID")
    task_id = _optional_identifier("MEMORY_LOOM_TASK_ID")

    if task_id is not None and project_id is None:
        raise RuntimeError("MEMORY_LOOM_TASK_ID requires MEMORY_LOOM_PROJECT_ID")

    return Scope(
        user_id=configured_user_id(),
        project_id=project_id,
        task_id=task_id,
    )


def configured_database_path() -> str:
    value = os.environ.get("MEMORY_LOOM_DATABASE_PATH")
    if value is None:
        raise RuntimeError("MEMORY_LOOM_DATABASE_PATH is required")
    if value == ":memory:":
        return value

    path = Path(value).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def _optional_identifier(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None:
        return None
    return _IDENTIFIER_ADAPTER.validate_python(value)
