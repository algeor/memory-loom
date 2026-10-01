from __future__ import annotations

import json
from pathlib import Path

from memory_loom.cli import main
from memory_loom.contracts import FIXTURE_DIRECTORY, load_json, validate_document
from memory_loom.retrieval_evaluation import evaluate_retrieval, threshold_failures


SCENARIO_DIRECTORY = FIXTURE_DIRECTORY / "scenarios" / "v1"
CONDITION_MANIFEST_PATH = (
    FIXTURE_DIRECTORY / "manifests" / "v1" / "default-conditions.json"
)


def test_fixture_catalog_retrieval_metrics_are_reproducible() -> None:
    artifact = evaluate_retrieval(
        SCENARIO_DIRECTORY,
        CONDITION_MANIFEST_PATH,
        limit=5,
    )

    assert artifact.metrics.total_scenarios == 25
    assert artifact.metrics.total_queries == 25
    assert artifact.metrics.memory_needed_queries == 17
    assert artifact.metrics.abstention_queries == 8
    assert artifact.metrics.recall_at_k == 1.0
    assert artifact.metrics.precision_at_k == 1.0
    assert artifact.metrics.mean_reciprocal_rank == 1.0
    assert artifact.metrics.mean_ndcg_at_k == 1.0
    assert artifact.metrics.abstention_accuracy == 1.0
    assert artifact.metrics.no_memory_false_positive_rate == 0.0
    assert artifact.metrics.forbidden_hit_count == 0
    assert threshold_failures(artifact, min_recall_at_k=1.0, min_mrr=1.0) == []
    validate_document(artifact.model_dump(mode="json"))


def test_forbidden_live_retrieval_is_reported(tmp_path: Path) -> None:
    scenario = load_json(SCENARIO_DIRECTORY / "global-preference-001.json")
    memory_id = scenario["memory_records"][0]["id"]
    labels = scenario["queries"][0]["labels"]
    labels.update(
        {
            "memory_needed": False,
            "relevant_memory_ids": [],
            "acceptable_memory_ids": [],
            "forbidden_memory_ids": [memory_id],
            "abstention_correct": True,
        }
    )
    scenario["retrieval_decisions"][0].update(
        {
            "decision": "lexical_filtered",
            "lexical_score": None,
            "reason_code": "frozen-negative-label",
            "position": None,
        }
    )
    scenario_path = tmp_path / "scenario.json"
    scenario_path.write_text(json.dumps(scenario), encoding="utf-8")

    artifact = evaluate_retrieval(
        scenario_path,
        CONDITION_MANIFEST_PATH,
        limit=5,
    )

    assert artifact.metrics.forbidden_hit_count == 1
    assert artifact.metrics.forbidden_query_count == 1
    assert artifact.metrics.no_memory_false_positive_rate == 1.0
    assert artifact.query_results[0].forbidden_hits
    assert threshold_failures(artifact) == [
        "forbidden retrievals: 1 hit(s) across 1 query(s)"
    ]


def test_cli_writes_retrieval_evaluation_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "retrieval.json"

    exit_code = main(
        [
            "evaluate-retrieval",
            str(SCENARIO_DIRECTORY),
            "--condition-manifest",
            str(CONDITION_MANIFEST_PATH),
            "--output",
            str(output_path),
            "--min-recall-at-k",
            "1",
            "--min-mrr",
            "1",
            "--max-no-memory-fpr",
            "0",
        ]
    )

    assert exit_code == 0
    artifact = validate_document(load_json(output_path))
    assert artifact["artifact_type"] == "retrieval_evaluation"
    assert artifact["metrics"]["forbidden_hit_count"] == 0
