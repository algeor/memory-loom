from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from memory_loom.models import (
    ConditionManifest,
    EvidenceEvent,
    MemoryRecord,
    RetrievalDecision,
    RevisionEvent,
    RunManifest,
    Scenario,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIRECTORY = REPOSITORY_ROOT / "schemas" / "v1"
FIXTURE_DIRECTORY = REPOSITORY_ROOT / "fixtures"

MODEL_BY_ARTIFACT_TYPE: dict[str, type[BaseModel]] = {
    "scenario": Scenario,
    "condition_manifest": ConditionManifest,
    "run_manifest": RunManifest,
}

MODEL_BY_SCHEMA_NAME: dict[str, type[BaseModel]] = {
    "scenario.schema.json": Scenario,
    "condition-manifest.schema.json": ConditionManifest,
    "run-manifest.schema.json": RunManifest,
    "evidence-event.schema.json": EvidenceEvent,
    "memory-record.schema.json": MemoryRecord,
    "revision-event.schema.json": RevisionEvent,
    "retrieval-decision.schema.json": RetrievalDecision,
}


class ContractValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("\n".join(errors))


def load_json(path: str | Path) -> dict[str, Any]:
    artifact_path = Path(path)
    with artifact_path.open(encoding="utf-8") as artifact_file:
        document = json.load(artifact_file)
    if not isinstance(document, dict):
        raise ContractValidationError(
            [f"{artifact_path}: document must be a JSON object"]
        )
    return document


def validate_document(
    document: dict[str, Any], schema_name: str | None = None
) -> dict[str, Any]:
    model = _resolve_model(document, schema_name)
    try:
        validated = model.model_validate(document)
    except ValidationError as error:
        raise ContractValidationError(
            [
                f"{_format_location(item['loc'])}: {item['msg']}"
                for item in error.errors(include_url=False)
            ]
        ) from error
    return validated.model_dump(mode="json")


def validate_path(path: str | Path, schema_name: str | None = None) -> dict[str, Any]:
    return validate_document(load_json(path), schema_name)


def validate_all_fixtures() -> list[Path]:
    validated_paths = []
    documents = []
    for fixture_path in sorted(FIXTURE_DIRECTORY.rglob("*.json")):
        document = validate_path(fixture_path)
        documents.append((fixture_path, document))
        validated_paths.append(fixture_path)
    _validate_fixture_references(documents)
    return validated_paths


def generated_schema_catalog() -> dict[str, dict[str, Any]]:
    catalog = {}
    for schema_name, model in MODEL_BY_SCHEMA_NAME.items():
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        schema["$id"] = f"https://memory-loom.local/schemas/v1/{schema_name}"
        catalog[schema_name] = schema
    return catalog


def export_schema_catalog() -> list[Path]:
    SCHEMA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    exported_paths = []
    for schema_name, schema in generated_schema_catalog().items():
        schema_path = SCHEMA_DIRECTORY / schema_name
        schema_path.write_text(
            json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        exported_paths.append(schema_path)
    return exported_paths


def validate_schema_catalog() -> list[str]:
    generated = generated_schema_catalog()
    checked_in_names = {path.name for path in SCHEMA_DIRECTORY.glob("*.schema.json")}
    if checked_in_names != set(generated):
        raise ContractValidationError(
            ["schema catalog filenames differ from the Pydantic model catalog"]
        )
    stale = [
        schema_name
        for schema_name, schema in generated.items()
        if load_json(SCHEMA_DIRECTORY / schema_name) != schema
    ]
    if stale:
        raise ContractValidationError(
            [f"generated schemas are stale: {', '.join(sorted(stale))}"]
        )
    return sorted(generated)


def _resolve_model(
    document: dict[str, Any], schema_name: str | None
) -> type[BaseModel]:
    if schema_name is not None:
        try:
            return MODEL_BY_SCHEMA_NAME[schema_name]
        except KeyError as error:
            raise ContractValidationError(
                [f"unknown schema {schema_name!r}"]
            ) from error
    artifact_type = document.get("artifact_type")
    try:
        return MODEL_BY_ARTIFACT_TYPE[artifact_type]
    except KeyError as error:
        raise ContractValidationError(
            [f"artifact_type: unsupported value {artifact_type!r}"]
        ) from error


def _validate_fixture_references(documents: list[tuple[Path, dict[str, Any]]]) -> None:
    scenario_ids = {
        document["scenario_id"]
        for _, document in documents
        if document["artifact_type"] == "scenario"
    }
    condition_manifest_ids = {
        document["manifest_id"]
        for _, document in documents
        if document["artifact_type"] == "condition_manifest"
    }
    errors = []
    for path, document in documents:
        if document["artifact_type"] != "run_manifest":
            continue
        if document["condition_manifest_id"] not in condition_manifest_ids:
            errors.append(
                f"{path}: unknown condition manifest {document['condition_manifest_id']!r}"
            )
        for scenario_id in document["scenario_ids"]:
            if scenario_id not in scenario_ids:
                errors.append(f"{path}: unknown scenario {scenario_id!r}")
    if errors:
        raise ContractValidationError(errors)


def _format_location(location: tuple[int | str, ...]) -> str:
    if not location:
        return "$"
    return "$" + "".join(
        f"[{part}]" if isinstance(part, int) else f".{part}" for part in location
    )
