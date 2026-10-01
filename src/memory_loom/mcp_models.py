from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, Field

from memory_loom.models import ContractModel, Identifier, Scope


class McpScope(ContractModel):
    project_id: Identifier | None = None
    task_id: Identifier | None = None


class SelectedMemory(ContractModel):
    memory_id: UUID
    rule_key: Identifier
    statement: str = Field(min_length=1)
    kind: Literal["preference", "correction"]
    scope: Scope
    version: int = Field(ge=1)
    reason_code: Identifier


class RetrieveResponse(ContractModel):
    query_id: Identifier
    scope: Scope
    context: str
    selected: list[SelectedMemory]


MemoryKind = Literal["preference", "correction"]
ScopeLevel = Literal["user", "project", "task"]


class SourceEventInput(ContractModel):
    event_id: Identifier
    content: str = Field(min_length=1)


class CreateChangeRequest(ContractModel):
    operation: Literal["create"]
    kind: MemoryKind
    rule_key: Identifier
    statement: str = Field(min_length=1)
    scope_level: ScopeLevel
    source_event: SourceEventInput


class CorrectChangeRequest(ContractModel):
    operation: Literal["correct"]
    target_memory_id: UUID
    statement: str = Field(min_length=1)
    source_event: SourceEventInput


class DeleteChangeRequest(ContractModel):
    operation: Literal["delete"]
    target_memory_id: UUID


ChangeRequest = Annotated[
    CreateChangeRequest | CorrectChangeRequest | DeleteChangeRequest,
    Field(discriminator="operation"),
]


class ProposeChangeResponse(ContractModel):
    proposal_id: UUID
    operation: Literal["create", "correct", "delete"]
    summary: str = Field(min_length=1)
    confirmation_prompt: str = Field(min_length=1)
    durable: Literal[False]
    expires_at: AwareDatetime
