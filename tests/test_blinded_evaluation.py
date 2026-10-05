from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from memory_loom.blinded_evaluation import (
    analyze_pilot,
    create_blinded_review,
    render_pilot_report,
)
from memory_loom.contracts import FIXTURE_DIRECTORY, load_json, validate_document
from memory_loom.models import BlindedReview, RunManifest
from memory_loom.runner import NoModelAdapter, run_scenario


SCENARIO_PATH = (
    FIXTURE_DIRECTORY / "scenarios" / "v1" / "global-preference-001.json"
)
CONDITIONS_PATH = (
    FIXTURE_DIRECTORY / "manifests" / "v1" / "default-conditions.json"
)
RUN_MANIFEST_PATH = (
    FIXTURE_DIRECTORY / "manifests" / "v1" / "contract-replay-run.json"
)
FIXED_TIME = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)


def test_blinding_hides_conditions_and_analysis_recovers_pairs(
    tmp_path: Path,
) -> None:
    scenario_directory = tmp_path / "scenarios"
    run_directory = tmp_path / "runs"
    scenario_directory.mkdir()
    run_directory.mkdir()
    scenario = load_json(SCENARIO_PATH)
    (scenario_directory / "scenario.json").write_text(
        SCENARIO_PATH.read_text(encoding="utf-8"), encoding="utf-8"
    )
    manifest_document = load_json(RUN_MANIFEST_PATH)
    manifest_document["scenario_ids"] = [scenario["scenario_id"]]
    manifest = RunManifest.model_validate(manifest_document)
    artifact = run_scenario(
        scenario,
        load_json(CONDITIONS_PATH),
        manifest.model_dump(mode="json"),
        NoModelAdapter(),
        frozen_retrieval=True,
        clock=lambda: FIXED_TIME,
    )
    (run_directory / "run.json").write_text(
        artifact.model_dump_json(indent=2), encoding="utf-8"
    )

    packet, key, template = create_blinded_review(
        scenario_directory,
        run_directory,
        packet_id="pilot-001",
        seed=42,
        reviewer_id="reviewer-a",
        created_at=FIXED_TIME,
    )

    assert '"condition"' not in packet.model_dump_json()
    assert len(packet.items) == 4
    assert {item.condition for item in key.items} == {"B0", "B1", "B2", "B3"}
    review_document = template.model_dump(mode="json")
    for rating in review_document["ratings"]:
        condition = next(
            item.condition
            for item in key.items
            if item.item_id == rating["item_id"]
        )
        rating["decision"] = "adheres" if condition == "B3" else "violates"
        rating["task_success"] = True
        rating["memory_override"] = False
        rating["unsupported_memory_claim"] = False

    analysis = analyze_pilot(
        key.model_dump(mode="json"),
        [BlindedReview.model_validate(review_document).model_dump(mode="json")],
        run_directory,
        bootstrap_samples=100,
        seed=7,
        created_at=FIXED_TIME,
    )

    assert analysis.status == "exploratory_pilot"
    assert [contrast.estimate for contrast in analysis.contrasts] == [1.0, 1.0, 1.0]
    assert analysis.forbidden_context_count == 0
    assert analysis.no_memory_false_positive_count == 0
    report = render_pilot_report(analysis)
    assert "not a confirmatory scientific result" in report
    assert "| Condition | Memory-needed n | Unclear |" in report
    assert "| B3-B0 | 1.0000 |" in report
    validate_document(packet.model_dump(mode="json"))
    validate_document(key.model_dump(mode="json"))
    validate_document(review_document)
    validate_document(analysis.model_dump(mode="json"))
