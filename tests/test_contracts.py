from __future__ import annotations

from copy import deepcopy

import pytest

from memory_loom.contracts import (
    ContractValidationError,
    FIXTURE_DIRECTORY,
    load_json,
    validate_all_fixtures,
    validate_document,
    validate_schema_catalog,
)


SCENARIO_PATH = FIXTURE_DIRECTORY / "scenarios" / "v1" / "scope-deletion-001.json"


def test_schema_catalog_and_fixtures_validate() -> None:
    assert len(validate_schema_catalog()) == 9
    validated_fixtures = validate_all_fixtures()
    assert validated_fixtures


def test_deleted_memory_cannot_retain_statement() -> None:
    scenario = load_json(SCENARIO_PATH)
    invalid_scenario = deepcopy(scenario)
    deleted_memory = next(
        memory
        for memory in invalid_scenario["memory_records"]
        if memory["status"] == "deleted"
    )
    deleted_memory["statement"] = "content that should have been erased"

    with pytest.raises(ContractValidationError, match="statement"):
        validate_document(invalid_scenario)


def test_forbidden_memory_cannot_be_selected() -> None:
    scenario = load_json(SCENARIO_PATH)
    invalid_scenario = deepcopy(scenario)
    forbidden_id = invalid_scenario["queries"][0]["labels"]["forbidden_memory_ids"][0]
    decision = next(
        item
        for item in invalid_scenario["retrieval_decisions"]
        if item["memory_id"] == forbidden_id
    )
    decision.update(
        {
            "eligible": True,
            "decision": "selected",
            "lexical_score": 0.5,
            "reason_code": "invalid-test-selection",
            "position": 2,
        }
    )

    with pytest.raises(ContractValidationError, match="selects forbidden memories"):
        validate_document(invalid_scenario)
