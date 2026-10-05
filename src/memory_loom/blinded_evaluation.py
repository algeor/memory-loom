from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from memory_loom.contracts import load_json
from memory_loom.models import (
    BlindedRating,
    BlindedReview,
    BlindedReviewItem,
    BlindedReviewPacket,
    BlindingKey,
    BlindingKeyItem,
    ConditionPilotMetrics,
    FamilyPilotMetrics,
    PilotAnalysis,
    PilotContrast,
    RunArtifact,
    Scenario,
)


REVIEW_INSTRUCTIONS = (
    "Judge only the visible request, behavior criteria, and response. "
    "Do not infer or guess the hidden experimental condition. Mark adheres "
    "only when the required behavior is present and no violating behavior occurs."
)
CONDITIONS = ("B0", "B1", "B2", "B3")


def create_blinded_review(
    scenario_directory: Path,
    run_directory: Path,
    *,
    packet_id: str,
    seed: int,
    reviewer_id: str,
    created_at: datetime | None = None,
) -> tuple[BlindedReviewPacket, BlindingKey, BlindedReview]:
    scenarios = {
        scenario.scenario_id: scenario
        for scenario in (
            Scenario.model_validate(load_json(path))
            for path in sorted(scenario_directory.glob("*.json"))
        )
    }
    artifacts = _load_artifacts(run_directory)
    created = created_at or datetime.now(UTC)
    dataset_versions = {artifact.run_manifest.dataset_version for artifact in artifacts}
    if len(dataset_versions) != 1:
        raise ValueError("run artifacts use multiple dataset versions")

    rows: list[tuple[BlindedReviewItem, BlindingKeyItem]] = []
    for artifact in artifacts:
        for result in artifact.results:
            if result.status != "completed" or result.raw_output is None:
                continue
            scenario = scenarios.get(result.scenario_id)
            if scenario is None:
                raise ValueError(f"missing scenario {result.scenario_id}")
            query = next(
                item for item in scenario.queries if item.query_id == result.query_id
            )
            item_id = _item_id(
                seed,
                result.scenario_id,
                result.query_id,
                result.repeat,
                result.condition,
            )
            rows.append(
                (
                    BlindedReviewItem(
                        item_id=item_id,
                        scenario_id=result.scenario_id,
                        query_id=result.query_id,
                        repeat=result.repeat,
                        current_request=query.content,
                        required_behavior=query.labels.required_behavior,
                        violating_behaviors=query.labels.violating_behaviors,
                        response=result.raw_output,
                    ),
                    BlindingKeyItem(
                        item_id=item_id,
                        scenario_id=result.scenario_id,
                        template_family=scenario.template_family,
                        query_id=result.query_id,
                        repeat=result.repeat,
                        condition=result.condition,
                        memory_needed=query.labels.memory_needed,
                        relevant_memory_ids=query.labels.relevant_memory_ids,
                        forbidden_memory_ids=query.labels.forbidden_memory_ids,
                        provider=result.provider,
                        model=result.model,
                        provider_model=result.provider_model,
                    ),
                )
            )

    random.Random(seed).shuffle(rows)
    packet = BlindedReviewPacket(
        artifact_type="blinded_review_packet",
        schema_version="1.0.0",
        packet_id=packet_id,
        created_at=created,
        dataset_version=next(iter(dataset_versions)),
        instructions=REVIEW_INSTRUCTIONS,
        items=[row[0] for row in rows],
    )
    key = BlindingKey(
        artifact_type="blinding_key",
        schema_version="1.0.0",
        packet_id=packet_id,
        created_at=created,
        seed_hash=hashlib.sha256(str(seed).encode()).hexdigest(),
        items=[row[1] for row in rows],
    )
    template = BlindedReview(
        artifact_type="blinded_review",
        schema_version="1.0.0",
        packet_id=packet_id,
        reviewer_id=reviewer_id,
        created_at=created,
        reviewer_type="human",
        provider=None,
        model=None,
        ratings=[
            BlindedRating(item_id=item.item_id, decision="unreviewed")
            for item in packet.items
        ],
    )
    return packet, key, template


def analyze_pilot(
    key_document: dict[str, object],
    review_documents: list[dict[str, object]],
    run_directory: Path,
    *,
    bootstrap_samples: int = 10_000,
    seed: int = 0,
    created_at: datetime | None = None,
) -> PilotAnalysis:
    if bootstrap_samples < 1:
        raise ValueError("bootstrap_samples must be positive")
    key = BlindingKey.model_validate(key_document)
    reviews = [BlindedReview.model_validate(item) for item in review_documents]
    if not reviews:
        raise ValueError("at least one completed review is required")
    if any(review.packet_id != key.packet_id for review in reviews):
        raise ValueError("review packet does not match blinding key")

    key_by_id = {item.item_id: item for item in key.items}
    decisions: dict[str, list[BlindedRating]] = defaultdict(list)
    for review in reviews:
        seen: set[str] = set()
        for rating in review.ratings:
            if rating.item_id not in key_by_id:
                raise ValueError(f"unknown review item {rating.item_id}")
            if rating.item_id in seen:
                raise ValueError(f"duplicate review item {rating.item_id}")
            if rating.decision == "unreviewed":
                raise ValueError(f"review item {rating.item_id} is unreviewed")
            seen.add(rating.item_id)
            decisions[rating.item_id].append(rating)
        if seen != set(key_by_id):
            raise ValueError("review does not cover every blinded item")

    adjudicated: dict[str, BlindedRating] = {}
    disagreements = 0
    for item_id, ratings in decisions.items():
        if len({rating.decision for rating in ratings}) > 1:
            disagreements += 1
        adjudicated[item_id] = _adjudicate(item_id, ratings)

    artifacts = _load_artifacts(run_directory)
    run_by_key = {
        (result.scenario_id, result.query_id, result.repeat, result.condition): result
        for artifact in artifacts
        for result in artifact.results
    }
    rows = []
    for item in key.items:
        result = run_by_key[
            (item.scenario_id, item.query_id, item.repeat, item.condition)
        ]
        rows.append((item, adjudicated[item.item_id], result))

    condition_metrics = [
        _condition_metrics(condition, rows) for condition in CONDITIONS
    ]
    family_metrics = [
        _family_metrics(family, condition, rows)
        for family in sorted({row[0].template_family for row in rows})
        for condition in CONDITIONS
    ]
    contrasts = _bootstrap_contrasts(
        rows,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
    )
    failed_runs = sum(
        result.status == "failed"
        for artifact in artifacts
        for result in artifact.results
    )
    reviewer_models = sorted(
        {
            f"{review.provider}:{review.model}"
            for review in reviews
            if review.provider is not None and review.model is not None
        }
    )
    generation_models = sorted(
        {
            f"{item.provider}:{item.provider_model or item.model}"
            for item in key.items
        }
    )
    limitations = [
        "This development pilot is exploratory and not confirmatory evidence.",
        "Synthetic scenarios may overstate preference clarity.",
    ]
    if any(review.reviewer_type == "model" for review in reviews):
        limitations.append(
            "Model reviews are secondary and are not calibrated against blinded human review."
        )
    if len(reviews) == 1:
        limitations.append(
            "A single reviewer cannot estimate inter-reviewer disagreement."
        )
    if any(item.provider == "claude-cli" for item in key.items):
        limitations.append(
            "Claude CLI did not expose temperature, top-p, seed, or output-token controls."
        )
    if any(
        item.provider_model is None or item.model != item.provider_model
        for item in key.items
    ):
        limitations.append(
            "At least one generation used an alias or lacked a provider-reported model version."
        )
    return PilotAnalysis(
        artifact_type="pilot_analysis",
        schema_version="1.0.0",
        packet_id=key.packet_id,
        created_at=created_at or datetime.now(UTC),
        status="exploratory_pilot",
        reviewer_types=sorted({review.reviewer_type for review in reviews}),
        generation_models=generation_models,
        reviewer_models=reviewer_models,
        reviewed_items=len(adjudicated),
        reviewer_disagreements=disagreements,
        failed_runs=failed_runs,
        memory_override_count=sum(
            rating.memory_override is True for rating in adjudicated.values()
        ),
        unsupported_memory_claim_count=sum(
            rating.unsupported_memory_claim is True
            for rating in adjudicated.values()
        ),
        forbidden_context_count=sum(
            key.condition == "B3"
            and bool(set(result.included_ids or ()) & set(key.forbidden_memory_ids))
            for key, _, result in rows
        ),
        no_memory_false_positive_count=sum(
            key.condition == "B3"
            and not key.memory_needed
            and bool(result.included_ids)
            for key, _, result in rows
        ),
        bootstrap_samples=bootstrap_samples,
        condition_metrics=condition_metrics,
        family_metrics=family_metrics,
        contrasts=contrasts,
        limitations=limitations,
    )


def render_pilot_report(analysis: PilotAnalysis) -> str:
    lines = [
        "# Development Pilot Report",
        "",
        "## Status",
        "",
        "**Exploratory pilot observation, not a confirmatory scientific result.**",
        "",
        f"- Blinded outputs reviewed: {analysis.reviewed_items}",
        f"- Reviewer types: {', '.join(analysis.reviewer_types)}",
        f"- Generation models: {', '.join(analysis.generation_models)}",
        f"- Reviewer models: {', '.join(analysis.reviewer_models) or 'none'}",
        (
            "- Pairwise reviewer disagreements: "
            f"{analysis.reviewer_disagreements} "
            "(not estimable with one reviewer)"
            if "A single reviewer cannot estimate inter-reviewer disagreement."
            in analysis.limitations
            else f"- Pairwise reviewer disagreements: {analysis.reviewer_disagreements}"
        ),
        f"- Failed model runs: {analysis.failed_runs}",
        f"- Forbidden context inclusions: {analysis.forbidden_context_count}",
        (
            "- No-memory false-positive retrievals: "
            f"{analysis.no_memory_false_positive_count}"
        ),
        f"- Current-request override failures: {analysis.memory_override_count}",
        (
            "- Unsupported memory claims: "
            f"{analysis.unsupported_memory_claim_count}"
        ),
        "",
        "## Condition Metrics",
        "",
        (
            "| Condition | Memory-needed n | Unclear | Adherence | Task success | "
            "Overrides | Unsupported claims | Context tokens | Latency ms | Cost USD |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for metric in analysis.condition_metrics:
        lines.append(
            "| "
            + " | ".join(
                [
                    metric.condition,
                    str(metric.scored_items),
                    str(metric.unclear_items),
                    _format_optional(metric.preference_adherence),
                    _format_optional(metric.task_success),
                    str(metric.memory_override_count),
                    str(metric.unsupported_memory_claim_count),
                    _format_optional(metric.mean_context_tokens),
                    _format_optional(metric.mean_latency_ms),
                    _format_optional(metric.estimated_cost_usd, digits=6),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Paired Contrasts",
            "",
            "| Contrast | Estimate | Simultaneous 95% interval |",
            "|---|---:|---:|",
        ]
    )
    for contrast in analysis.contrasts:
        lines.append(
            f"| {contrast.comparison} | {contrast.estimate:.4f} | "
            f"[{contrast.simultaneous_ci_low:.4f}, "
            f"{contrast.simultaneous_ci_high:.4f}] |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in analysis.limitations)
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "These numbers describe this frozen synthetic development run only. "
                "They must not be generalized to real users, other models, or a "
                "held-out dataset."
            ),
        ]
    )
    if analysis.contrasts and all(
        contrast.simultaneous_ci_low <= 0 <= contrast.simultaneous_ci_high
        for contrast in analysis.contrasts
    ):
        lines.extend(
            [
                "",
                (
                    "All simultaneous 95% intervals include zero. This pilot "
                    "therefore does not distinguish B3 from any baseline on "
                    "preference adherence."
                ),
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _load_artifacts(run_directory: Path) -> list[RunArtifact]:
    artifacts = [
        RunArtifact.model_validate(load_json(path))
        for path in sorted(run_directory.glob("*.json"))
    ]
    if not artifacts:
        raise ValueError("run directory contains no JSON artifacts")
    return artifacts


def _item_id(
    seed: int,
    scenario_id: str,
    query_id: str,
    repeat: int,
    condition: str,
) -> str:
    value = f"{seed}:{scenario_id}:{query_id}:{repeat}:{condition}"
    return f"item-{hashlib.sha256(value.encode()).hexdigest()[:24]}"


def _adjudicate(item_id: str, ratings: list[BlindedRating]) -> BlindedRating:
    counts = {value: 0 for value in ("adheres", "violates", "unclear")}
    for rating in ratings:
        counts[rating.decision] += 1
    best = max(counts.values())
    winners = [value for value, count in counts.items() if count == best]
    decision = winners[0] if len(winners) == 1 else "unclear"
    return BlindedRating(
        item_id=item_id,
        decision=decision,
        task_success=_majority_bool([rating.task_success for rating in ratings]),
        memory_override=_any_true([rating.memory_override for rating in ratings]),
        unsupported_memory_claim=_any_true(
            [rating.unsupported_memory_claim for rating in ratings]
        ),
    )


def _condition_metrics(condition: str, rows) -> ConditionPilotMetrics:
    selected = [row for row in rows if row[0].condition == condition]
    adherence = [
        1.0 if rating.decision == "adheres" else 0.0
        for key, rating, _ in selected
        if key.memory_needed
    ]
    task_success = [
        float(rating.task_success)
        for _, rating, _ in selected
        if rating.task_success is not None
    ]
    latency = [
        result.latency_ms
        for _, _, result in selected
        if result.latency_ms is not None
    ]
    costs = [result.estimated_cost_usd for _, _, result in selected]
    return ConditionPilotMetrics(
        condition=condition,
        scored_items=len(adherence),
        unclear_items=sum(
            rating.decision == "unclear" for _, rating, _ in selected
        ),
        preference_adherence=_mean(adherence),
        task_success=_mean(task_success),
        mean_context_tokens=_mean(
            result.context_token_count
            for _, _, result in selected
            if result.context_token_count is not None
        ),
        mean_latency_ms=_mean(latency),
        memory_override_count=sum(
            rating.memory_override is True for _, rating, _ in selected
        ),
        unsupported_memory_claim_count=sum(
            rating.unsupported_memory_claim is True
            for _, rating, _ in selected
        ),
        input_tokens=sum(result.input_tokens or 0 for _, _, result in selected),
        output_tokens=sum(result.output_tokens or 0 for _, _, result in selected),
        estimated_cost_usd=(
            sum(cost for cost in costs if cost is not None)
            if costs and all(cost is not None for cost in costs)
            else None
        ),
    )


def _family_metrics(
    family: str,
    condition: str,
    rows,
) -> FamilyPilotMetrics:
    selected = [
        row
        for row in rows
        if row[0].template_family == family and row[0].condition == condition
    ]
    adherence = [
        1.0 if rating.decision == "adheres" else 0.0
        for key, rating, _ in selected
        if key.memory_needed
    ]
    task_success = [
        float(rating.task_success)
        for _, rating, _ in selected
        if rating.task_success is not None
    ]
    return FamilyPilotMetrics(
        template_family=family,
        condition=condition,
        scored_items=len(adherence),
        preference_adherence=_mean(adherence),
        task_success=_mean(task_success),
    )


def _bootstrap_contrasts(
    rows,
    *,
    bootstrap_samples: int,
    seed: int,
) -> list[PilotContrast]:
    scenario_scores: dict[tuple[str, str], list[float]] = defaultdict(list)
    family_by_scenario = {}
    for key, rating, _ in rows:
        family_by_scenario[key.scenario_id] = key.template_family
        if key.memory_needed:
            scenario_scores[(key.scenario_id, key.condition)].append(
                1.0 if rating.decision == "adheres" else 0.0
            )
    scenarios = sorted(
        scenario_id
        for scenario_id in family_by_scenario
        if all(
            (scenario_id, condition) in scenario_scores
            for condition in CONDITIONS
        )
    )
    if not scenarios:
        return []
    point = _contrasts_for_scenarios(scenarios, scenario_scores)
    families = sorted({family_by_scenario[item] for item in scenarios})
    scenarios_by_family = {
        family: [
            scenario
            for scenario in scenarios
            if family_by_scenario[scenario] == family
        ]
        for family in families
    }
    rng = random.Random(seed)
    errors = []
    for _ in range(bootstrap_samples):
        sampled_families = [rng.choice(families) for _ in families]
        sampled_scenarios = [
            scenario
            for family in sampled_families
            for scenario in scenarios_by_family[family]
        ]
        sample = _contrasts_for_scenarios(sampled_scenarios, scenario_scores)
        errors.append(max(abs(sample[name] - point[name]) for name in point))
    critical = sorted(errors)[min(len(errors) - 1, int(0.95 * len(errors)))]
    return [
        PilotContrast(
            comparison=name,
            estimate=estimate,
            simultaneous_ci_low=max(-1.0, estimate - critical),
            simultaneous_ci_high=min(1.0, estimate + critical),
        )
        for name, estimate in point.items()
    ]


def _contrasts_for_scenarios(scenarios, scores) -> dict[str, float]:
    condition_means = {
        condition: _mean(
            [_mean(scores[(scenario, condition)]) for scenario in scenarios]
        )
        for condition in CONDITIONS
    }
    return {
        f"B3-{baseline}": condition_means["B3"] - condition_means[baseline]
        for baseline in ("B0", "B1", "B2")
    }


def _mean(values) -> float | None:
    values = list(values)
    return sum(values) / len(values) if values else None


def _majority_bool(values: list[bool | None]) -> bool | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    true_count = sum(present)
    if true_count * 2 == len(present):
        return None
    return true_count * 2 > len(present)


def _any_true(values: list[bool | None]) -> bool | None:
    present = [value for value in values if value is not None]
    return any(present) if present else None


def _format_optional(value: float | None, *, digits: int = 4) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"
