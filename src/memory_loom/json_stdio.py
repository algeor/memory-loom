from __future__ import annotations

import json
import sys
from typing import Any, Literal, TextIO
from uuid import UUID

from pydantic import Field, ValidationError

from memory_loom.mcp_models import (
    ChangeRequest,
    DiscardReason,
)
from memory_loom.mcp_proposals import (
    ProposalExpiredError,
    ProposalNotFoundError,
)
from memory_loom.mcp_server import (
    commit_change,
    discard_change,
    inspect_memory,
    propose_change,
    retrieve_memory,
)
from memory_loom.models import ContractModel, Identifier


Method = Literal[
    "memory_loom_retrieve",
    "memory_loom_propose_change",
    "memory_loom_commit_change",
    "memory_loom_discard_change",
    "memory_loom_inspect",
]


class JsonRequest(ContractModel):
    id: Identifier
    method: Method
    params: dict[str, Any] = Field(default_factory=dict)


class RetrieveParams(ContractModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class ProposeParams(ContractModel):
    change: ChangeRequest


class CommitParams(ContractModel):
    proposal_id: UUID
    approval_event_id: Identifier
    approved_by: Literal["user"]


class DiscardParams(ContractModel):
    proposal_id: UUID
    reason: DiscardReason


class InspectParams(ContractModel):
    memory_id: UUID | None = None
    include_inactive: bool = False
    cursor: UUID | None = None
    limit: int = Field(default=50, ge=1, le=100)


def serve_json_lines(
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
) -> int:
    for line in input_stream:
        if not line.strip():
            continue
        response = handle_json_line(line)
        output_stream.write(json.dumps(response, separators=(",", ":")) + "\n")
        output_stream.flush()
    return 0


def handle_json_line(line: str) -> dict[str, Any]:
    request_id: str | None = None
    try:
        document = json.loads(line)
        if isinstance(document, dict) and isinstance(document.get("id"), str):
            request_id = document["id"]
        request = JsonRequest.model_validate(document)
        request_id = request.id
        result = _dispatch(request)
        return {
            "id": request.id,
            "ok": True,
            "result": result.model_dump(mode="json"),
        }
    except json.JSONDecodeError:
        return _error(request_id, "invalid_request", "request is not valid JSON")
    except ValidationError:
        return _error(
            request_id,
            "invalid_request",
            "request does not satisfy the JSON CLI contract",
        )
    except ProposalExpiredError:
        return _error(request_id, "proposal_expired", "proposal has expired")
    except ProposalNotFoundError:
        return _error(request_id, "not_found", "proposal was not found")
    except ValueError as error:
        message = str(error)
        code = (
            "scope_denied"
            if "scope" in message or "unavailable" in message
            else "invalid_transition"
        )
        return _error(request_id, code, "operation is unavailable in the active scope")
    except Exception:
        return _error(request_id, "internal_error", "operation failed")


def _dispatch(request: JsonRequest):
    if request.method == "memory_loom_retrieve":
        params = RetrieveParams.model_validate(request.params)
        return retrieve_memory(params.query, params.limit)
    if request.method == "memory_loom_propose_change":
        params = ProposeParams.model_validate(request.params)
        return propose_change(params.change)
    if request.method == "memory_loom_commit_change":
        params = CommitParams.model_validate(request.params)
        return commit_change(
            params.proposal_id,
            params.approval_event_id,
            params.approved_by,
        )
    if request.method == "memory_loom_discard_change":
        params = DiscardParams.model_validate(request.params)
        return discard_change(params.proposal_id, params.reason)

    params = InspectParams.model_validate(request.params)
    return inspect_memory(
        params.memory_id,
        params.include_inactive,
        params.cursor,
        params.limit,
    )


def _error(
    request_id: str | None,
    code: str,
    message: str,
) -> dict[str, Any]:
    return {
        "id": request_id,
        "ok": False,
        "error": {"code": code, "message": message},
    }
