from __future__ import annotations

import json
from datetime import UTC, datetime

from memory_loom.model_reviewer import review_packet_with_model
from memory_loom.models import BlindedReviewPacket
from memory_loom.runner import ModelRequest, ModelResponse


class FakeReviewAdapter:
    provider = "test"
    model = "blind-reviewer"

    def generate(self, request: ModelRequest) -> ModelResponse:
        payload = json.loads(request.user_prompt.split("\n\n", 1)[1])
        return ModelResponse(
            output_text=json.dumps(
                {
                    "ratings": [
                        {
                            "item_id": item["item_id"],
                            "decision": "adheres",
                            "task_success": True,
                            "memory_override": False,
                            "unsupported_memory_claim": False,
                            "notes": "Required behavior is present.",
                        }
                        for item in payload
                    ]
                }
            )
        )


def test_model_reviewer_never_receives_condition_labels() -> None:
    packet = BlindedReviewPacket.model_validate(
        {
            "artifact_type": "blinded_review_packet",
            "schema_version": "1.0.0",
            "packet_id": "pilot-001",
            "created_at": "2026-10-05T12:00:00Z",
            "dataset_version": "development-0.1.0",
            "instructions": "Review blindly.",
            "items": [
                {
                    "item_id": "item-001",
                    "scenario_id": "scenario-001",
                    "query_id": "query-001",
                    "repeat": 1,
                    "current_request": "Review this code.",
                    "required_behavior": "Lead with correctness.",
                    "violating_behaviors": ["Lead with style."],
                    "response": "Correctness issue: unsafe indexing.",
                }
            ],
        }
    )

    review = review_packet_with_model(
        packet.model_dump(mode="json"),
        FakeReviewAdapter(),
        reviewer_id="model-reviewer",
        created_at=datetime(2026, 10, 5, 12, 1, tzinfo=UTC),
    )

    assert review.reviewer_type == "model"
    assert review.provider == "test"
    assert review.model == "blind-reviewer"
    assert review.ratings[0].decision == "adheres"


def test_model_reviewer_resumes_existing_ratings() -> None:
    packet = _packet()
    first = review_packet_with_model(
        packet.model_dump(mode="json"),
        FakeReviewAdapter(),
        reviewer_id="model-reviewer",
        created_at=datetime(2026, 10, 5, 12, 1, tzinfo=UTC),
    )

    resumed = review_packet_with_model(
        packet.model_dump(mode="json"),
        FakeReviewAdapter(),
        reviewer_id="model-reviewer",
        existing_review_document=first.model_dump(mode="json"),
    )

    assert resumed == first


def _packet() -> BlindedReviewPacket:
    return BlindedReviewPacket.model_validate(
        {
            "artifact_type": "blinded_review_packet",
            "schema_version": "1.0.0",
            "packet_id": "pilot-001",
            "created_at": "2026-10-05T12:00:00Z",
            "dataset_version": "development-0.1.0",
            "instructions": "Review blindly.",
            "items": [
                {
                    "item_id": "item-001",
                    "scenario_id": "scenario-001",
                    "query_id": "query-001",
                    "repeat": 1,
                    "current_request": "Review this code.",
                    "required_behavior": "Lead with correctness.",
                    "violating_behaviors": ["Lead with style."],
                    "response": "Correctness issue: unsafe indexing.",
                }
            ],
        }
    )
