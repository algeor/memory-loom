from __future__ import annotations

import json
from datetime import datetime, timezone
from itertools import count

from memory_loom.cli import main
from memory_loom.contracts import FIXTURE_DIRECTORY, load_json, validate_document
from memory_loom.runner import ModelRequest, NoModelAdapter, run_scenario


SCENARIO_PATH = FIXTURE_DIRECTORY / "scenarios" / "v1" / "scope-deletion-001.json"
CONDITION_MANIFEST_PATH = (
    FIXTURE_DIRECTORY / "manifests" / "v1" / "default-conditions.json"
)
RUN_MANIFEST_PATH = FIXTURE_DIRECTORY / "manifests" / "v1" / "contract-replay-run.json"
FIXED_TIME = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)


class FailingAdapter:
    provider = "none"
    model = "no-model-contract-replay"

    def generate(self, request: ModelRequest) -> str:
        if "fallible rolling summary" in request.user_prompt:
            raise RuntimeError("synthetic provider failure")
        return "ok"


def test_no_model_runner_is_complete_and_reproducible() -> None:
    first = _run(NoModelAdapter())
    second = _run(NoModelAdapter())

    assert first == second
    assert first.status == "completed"
    assert [result.condition for result in first.results] == ["B0", "B1", "B2", "B3"]
    assert all(result.status == "completed" for result in first.results)
    assert all(
        result.raw_output.startswith("NO_MODEL_OUTPUT") for result in first.results
    )
    assert all(result.user_prompt is not None for result in first.results)
    assert first.results[0].injected_context == ""
    assert first.results[3].included_ids == ["20000000-0000-4000-8000-000000000002"]
    validate_document(first.model_dump(mode="json"))


def test_runner_preserves_failure_and_continues() -> None:
    artifact = _run(FailingAdapter())

    assert artifact.status == "completed_with_failures"
    failed = [result for result in artifact.results if result.status == "failed"]
    assert len(failed) == 1
    assert failed[0].condition == "B2"
    assert failed[0].failure is not None
    assert failed[0].failure.stage == "model_invocation"
    assert artifact.results[-1].condition == "B3"
    assert artifact.results[-1].status == "completed"


def test_run_cli_writes_valid_artifact(tmp_path) -> None:
    output_path = tmp_path / "run.json"

    exit_code = main(
        [
            "run",
            str(SCENARIO_PATH),
            str(CONDITION_MANIFEST_PATH),
            str(RUN_MANIFEST_PATH),
            "--output",
            str(output_path),
            "--frozen-retrieval",
        ]
    )

    assert exit_code == 0
    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert validate_document(artifact)["status"] == "completed"


def _run(adapter: NoModelAdapter | FailingAdapter):
    ticks = count(step=0.001)
    return run_scenario(
        load_json(SCENARIO_PATH),
        load_json(CONDITION_MANIFEST_PATH),
        load_json(RUN_MANIFEST_PATH),
        adapter,
        frozen_retrieval=True,
        clock=lambda: FIXED_TIME,
        timer=lambda: next(ticks),
    )
