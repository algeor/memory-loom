from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, Field

from memory_loom.models import (
    BlindedRating,
    BlindedReview,
    BlindedReviewItem,
    BlindedReviewPacket,
)
from memory_loom.runner import ModelAdapter, ModelRequest


REVIEWER_SYSTEM_PROMPT = (
    "You are evaluating coding-assistant responses in a condition-blind study. "
    "Use only the supplied request, required behavior, violating behaviors, and "
    "response. Do not guess the hidden condition. Return only valid JSON."
)


class ModelRating(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str
    decision: str
    task_success: bool
    memory_override: bool
    unsupported_memory_claim: bool
    notes: str = Field(min_length=1)


class ModelRatingBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ratings: list[ModelRating] = Field(min_length=1)


def review_packet_with_model(
    packet_document: dict[str, object],
    adapter: ModelAdapter,
    *,
    reviewer_id: str,
    batch_size: int = 8,
    jobs: int = 1,
    seed: int = 0,
    created_at: datetime | None = None,
    existing_review_document: dict[str, object] | None = None,
    checkpoint_path: Path | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> BlindedReview:
    if batch_size < 1 or jobs < 1:
        raise ValueError("batch_size and jobs must be positive")
    packet = BlindedReviewPacket.model_validate(packet_document)
    created = created_at or datetime.now(UTC)
    ratings: list[BlindedRating] = []
    if existing_review_document is not None:
        existing = BlindedReview.model_validate(existing_review_document)
        if existing.packet_id != packet.packet_id:
            raise ValueError("existing review packet does not match")
        if existing.reviewer_id != reviewer_id:
            raise ValueError("existing review belongs to another reviewer")
        ratings.extend(existing.ratings)
        created = existing.created_at
    rated_ids = {rating.item_id for rating in ratings}
    pending = [item for item in packet.items if item.item_id not in rated_ids]
    batches = [
        (offset, pending[offset : offset + batch_size])
        for offset in range(0, len(pending), batch_size)
    ]
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = {
            executor.submit(_review_batch, adapter, batch, seed + offset): batch
            for offset, batch in batches
        }
        for future in as_completed(futures):
            ratings.extend(future.result())
            ratings = _ordered_ratings(packet, ratings)
            review = _review_artifact(packet, adapter, reviewer_id, created, ratings)
            if checkpoint_path is not None:
                checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
                checkpoint_path.write_text(
                    review.model_dump_json(indent=2) + "\n", encoding="utf-8"
                )
            if progress is not None:
                progress(len(ratings), len(packet.items))
    return _review_artifact(packet, adapter, reviewer_id, created, ratings)


def _review_artifact(
    packet: BlindedReviewPacket,
    adapter: ModelAdapter,
    reviewer_id: str,
    created_at: datetime,
    ratings: list[BlindedRating],
) -> BlindedReview:
    return BlindedReview(
        artifact_type="blinded_review",
        schema_version="1.0.0",
        packet_id=packet.packet_id,
        reviewer_id=reviewer_id,
        created_at=created_at,
        reviewer_type="model",
        provider=adapter.provider,
        model=adapter.model,
        ratings=ratings,
    )


def _review_batch(
    adapter: ModelAdapter,
    batch: list[BlindedReviewItem],
    seed: int,
) -> list[BlindedRating]:
    last_error: ValueError | None = None
    for attempt in range(3):
        retry_note = (
            "\n\nYour previous response was invalid. Return every item exactly once."
            if attempt
            else ""
        )
        response = adapter.generate(
            ModelRequest(
                system_prompt=REVIEWER_SYSTEM_PROMPT,
                user_prompt=_review_prompt(batch) + retry_note,
                provider=adapter.provider,
                model=adapter.model,
                seed=seed + attempt,
                temperature=0,
                top_p=1,
                max_output_tokens=max(512, 192 * len(batch)),
            )
        )
        try:
            parsed = ModelRatingBatch.model_validate_json(
                _extract_json_object(response.output_text)
            )
            expected_ids = {item.item_id for item in batch}
            actual_ids = {item.item_id for item in parsed.ratings}
            if actual_ids != expected_ids or len(parsed.ratings) != len(batch):
                raise ValueError(
                    "model review did not return exactly one rating per item"
                )
            ratings = []
            for rating in parsed.ratings:
                if rating.decision not in {"adheres", "violates", "unclear"}:
                    raise ValueError("model review returned an invalid decision")
                ratings.append(
                    BlindedRating(
                        item_id=rating.item_id,
                        decision=rating.decision,
                        task_success=rating.task_success,
                        memory_override=rating.memory_override,
                        unsupported_memory_claim=rating.unsupported_memory_claim,
                        notes=rating.notes,
                    )
                )
            return ratings
        except (ValueError, TypeError) as error:
            last_error = ValueError(str(error))
    assert last_error is not None
    raise last_error


def _ordered_ratings(
    packet: BlindedReviewPacket,
    ratings: list[BlindedRating],
) -> list[BlindedRating]:
    by_id = {rating.item_id: rating for rating in ratings}
    return [
        rating
        for packet_item in packet.items
        if (rating := by_id.get(packet_item.item_id)) is not None
    ]


def _review_prompt(items: list[BlindedReviewItem]) -> str:
    payload = [
        {
            "item_id": item.item_id,
            "current_request": item.current_request,
            "required_behavior": item.required_behavior,
            "violating_behaviors": item.violating_behaviors,
            "response": item.response,
        }
        for item in items
    ]
    return (
        "Rate every item. decision must be adheres only if the required behavior "
        "is present and no violating behavior occurs; otherwise use violates or "
        "unclear. task_success means the response substantively addresses the "
        "request. memory_override means historical context improperly overrode "
        "the current request. unsupported_memory_claim means the response claims "
        "a preference or fact not supported by the visible criteria. Return "
        '{"ratings":[{"item_id":"...","decision":"adheres|violates|unclear",'
        '"task_success":true,"memory_override":false,'
        '"unsupported_memory_claim":false,"notes":"brief reason"}]}.\n\n'
        + json.dumps(payload, ensure_ascii=False)
    )


def _extract_json_object(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        stripped = "\n".join(lines[1:-1]).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end < start:
        return stripped
    return stripped[start : end + 1]
