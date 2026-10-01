from __future__ import annotations

import math
from pathlib import Path
from uuid import UUID

from memory_loom.contracts import load_json
from memory_loom.models import (
    ConditionManifest,
    QueryLabels,
    RetrievalAggregateMetrics,
    RetrievalEvaluationArtifact,
    RetrievalEvaluationQueryResult,
    Scenario,
)
from memory_loom.replay import build_structured_memory_context, count_tokens
from memory_loom.retrieval import LexicalRetriever
from memory_loom.store import MemoryStore


def evaluate_retrieval(
    scenario_path: Path,
    condition_manifest_path: Path,
    *,
    limit: int = 5,
) -> RetrievalEvaluationArtifact:
    if limit < 1:
        raise ValueError("limit must be at least one")

    scenario_paths = _scenario_paths(scenario_path)
    scenarios = [Scenario.model_validate(load_json(path)) for path in scenario_paths]
    condition_manifest = ConditionManifest.model_validate(
        load_json(condition_manifest_path)
    )
    scenario_ids = [scenario.scenario_id for scenario in scenarios]
    if len(scenario_ids) != len(set(scenario_ids)):
        raise ValueError("scenario IDs must be unique across the evaluation dataset")

    query_results = [
        result
        for scenario in scenarios
        for result in _evaluate_scenario(scenario, condition_manifest, limit)
    ]
    return RetrievalEvaluationArtifact(
        artifact_type="retrieval_evaluation",
        schema_version="1.0.0",
        evaluator="sqlite-fts5-lexical-v1",
        dataset_path=str(scenario_path),
        condition_manifest_id=condition_manifest.manifest_id,
        limit=limit,
        scenario_ids=scenario_ids,
        query_results=query_results,
        metrics=_aggregate_metrics(query_results, len(scenarios)),
    )


def threshold_failures(
    artifact: RetrievalEvaluationArtifact,
    *,
    min_recall_at_k: float | None = None,
    min_mrr: float | None = None,
    max_no_memory_false_positive_rate: float | None = None,
) -> list[str]:
    thresholds = {
        "min_recall_at_k": min_recall_at_k,
        "min_mrr": min_mrr,
        "max_no_memory_false_positive_rate": max_no_memory_false_positive_rate,
    }
    for name, value in thresholds.items():
        if value is not None and not 0 <= value <= 1:
            raise ValueError(f"{name} must be between zero and one")

    metrics = artifact.metrics
    failures = []
    if metrics.forbidden_hit_count:
        failures.append(
            f"forbidden retrievals: {metrics.forbidden_hit_count} hit(s) "
            f"across {metrics.forbidden_query_count} query(s)"
        )
    if min_recall_at_k is not None and (
        metrics.recall_at_k is None or metrics.recall_at_k < min_recall_at_k
    ):
        failures.append(
            f"recall@{artifact.limit} {metrics.recall_at_k!r} is below "
            f"{min_recall_at_k}"
        )
    if min_mrr is not None and (
        metrics.mean_reciprocal_rank is None
        or metrics.mean_reciprocal_rank < min_mrr
    ):
        failures.append(
            f"MRR {metrics.mean_reciprocal_rank!r} is below {min_mrr}"
        )
    if max_no_memory_false_positive_rate is not None and (
        metrics.no_memory_false_positive_rate is None
        or metrics.no_memory_false_positive_rate
        > max_no_memory_false_positive_rate
    ):
        failures.append(
            "no-memory false-positive rate "
            f"{metrics.no_memory_false_positive_rate!r} exceeds "
            f"{max_no_memory_false_positive_rate}"
        )
    return failures


def _scenario_paths(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.is_dir():
        raise ValueError(f"scenario path does not exist: {path}")
    paths = sorted(path.rglob("*.json"))
    if not paths:
        raise ValueError(f"no scenario JSON files found under {path}")
    return paths


def _evaluate_scenario(
    scenario: Scenario,
    condition_manifest: ConditionManifest,
    limit: int,
) -> list[RetrievalEvaluationQueryResult]:
    results = []
    with MemoryStore() as store:
        store.load_scenario(scenario)
        retriever = LexicalRetriever(store)
        for query in scenario.queries:
            retrieval = retriever.retrieve(
                query.query_id,
                query.content,
                query.scope,
                query.occurred_at,
                limit=limit,
            )
            context, included_ids = build_structured_memory_context(
                retrieval.selected_records,
                condition_manifest.conditions.B3.header,
                condition_manifest.max_context_tokens,
            )
            selected_ids = [record.id for record in retrieval.selected_records]
            results.append(
                _query_result(
                    scenario,
                    query.query_id,
                    query.labels,
                    selected_ids,
                    [UUID(value) for value in included_ids],
                    count_tokens(context),
                    limit,
                )
            )
    return results


def _query_result(
    scenario: Scenario,
    query_id: str,
    labels: QueryLabels,
    selected_ids: list[UUID],
    included_ids: list[UUID],
    context_token_count: int,
    limit: int,
) -> RetrievalEvaluationQueryResult:
    relevant = set(labels.relevant_memory_ids)
    acceptable = set(labels.acceptable_memory_ids)
    forbidden = set(labels.forbidden_memory_ids)
    relevant_hits = [memory_id for memory_id in selected_ids if memory_id in relevant]
    forbidden_hits = [memory_id for memory_id in selected_ids if memory_id in forbidden]
    irrelevant = [memory_id for memory_id in selected_ids if memory_id not in acceptable]

    recall = len(relevant_hits) / len(relevant) if relevant else None
    precision = len(relevant_hits) / len(selected_ids) if selected_ids else None
    reciprocal_rank = _reciprocal_rank(selected_ids, relevant) if relevant else None
    ndcg = _ndcg_at_k(selected_ids, relevant, limit) if relevant else None
    abstention_match = not selected_ids if labels.abstention_correct else None

    return RetrievalEvaluationQueryResult(
        scenario_id=scenario.scenario_id,
        template_family=scenario.template_family,
        split=scenario.split,
        query_id=query_id,
        memory_needed=labels.memory_needed,
        abstention_expected=labels.abstention_correct,
        relevant_memory_ids=labels.relevant_memory_ids,
        acceptable_memory_ids=labels.acceptable_memory_ids,
        forbidden_memory_ids=labels.forbidden_memory_ids,
        selected_memory_ids=selected_ids,
        included_memory_ids=included_ids,
        irrelevant_selected_ids=irrelevant,
        forbidden_hits=forbidden_hits,
        recall_at_k=recall,
        precision_at_k=precision,
        reciprocal_rank=reciprocal_rank,
        ndcg_at_k=ndcg,
        abstention_match=abstention_match,
        no_memory_false_positive=not labels.memory_needed and bool(selected_ids),
        context_token_count=context_token_count,
    )


def _aggregate_metrics(
    results: list[RetrievalEvaluationQueryResult],
    scenario_count: int,
) -> RetrievalAggregateMetrics:
    relevant_count = sum(len(result.relevant_memory_ids) for result in results)
    relevant_hits = sum(
        len(set(result.selected_memory_ids) & set(result.relevant_memory_ids))
        for result in results
    )
    selected_count = sum(len(result.selected_memory_ids) for result in results)
    memory_needed = [result for result in results if result.memory_needed]
    abstention = [result for result in results if result.abstention_expected]
    no_memory = [result for result in results if not result.memory_needed]
    forbidden_queries = [result for result in results if result.forbidden_hits]

    return RetrievalAggregateMetrics(
        total_scenarios=scenario_count,
        total_queries=len(results),
        memory_needed_queries=len(memory_needed),
        abstention_queries=len(abstention),
        recall_at_k=(relevant_hits / relevant_count if relevant_count else None),
        precision_at_k=(relevant_hits / selected_count if selected_count else None),
        mean_reciprocal_rank=_mean(
            [result.reciprocal_rank for result in memory_needed]
        ),
        mean_ndcg_at_k=_mean([result.ndcg_at_k for result in memory_needed]),
        abstention_accuracy=_mean(
            [
                1.0 if result.abstention_match else 0.0
                for result in abstention
            ]
        ),
        no_memory_false_positive_rate=_mean(
            [1.0 if result.no_memory_false_positive else 0.0 for result in no_memory]
        ),
        forbidden_hit_count=sum(len(result.forbidden_hits) for result in results),
        forbidden_query_count=len(forbidden_queries),
        mean_context_tokens=sum(result.context_token_count for result in results)
        / len(results),
    )


def _reciprocal_rank(selected_ids: list[UUID], relevant: set[UUID]) -> float:
    for position, memory_id in enumerate(selected_ids, 1):
        if memory_id in relevant:
            return 1 / position
    return 0.0


def _ndcg_at_k(selected_ids: list[UUID], relevant: set[UUID], limit: int) -> float:
    dcg = sum(
        1 / math.log2(position + 1)
        for position, memory_id in enumerate(selected_ids[:limit], 1)
        if memory_id in relevant
    )
    ideal_hits = min(len(relevant), limit)
    ideal_dcg = sum(1 / math.log2(position + 1) for position in range(1, ideal_hits + 1))
    return dcg / ideal_dcg


def _mean(values: list[float | None]) -> float | None:
    defined = [value for value in values if value is not None]
    return sum(defined) / len(defined) if defined else None
