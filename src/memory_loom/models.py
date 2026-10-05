from __future__ import annotations

from collections import defaultdict
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)


ArtifactVersion = Annotated[str, StringConstraints(pattern=r"^1\.[0-9]+\.[0-9]+$")]
Identifier = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z0-9][a-z0-9._-]*$", min_length=1, max_length=128),
]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
ConditionName = Literal["B0", "B1", "B2", "B3"]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Scope(ContractModel):
    user_id: Identifier
    project_id: Identifier | None
    task_id: Identifier | None


class EvidenceEvent(ContractModel):
    id: UUID
    scenario_id: Identifier
    source_event_id: Identifier | None = None
    kind: Literal["explicit_preference", "direct_correction"]
    content: str | None
    content_state: Literal["present", "erased"]
    scope: Scope
    recorded_at: AwareDatetime
    consent: Literal["approved"]

    @model_validator(mode="after")
    def content_matches_state(self) -> EvidenceEvent:
        if self.content_state == "present" and not self.content:
            raise ValueError("present evidence must retain non-empty content")
        if self.content_state == "erased" and self.content is not None:
            raise ValueError("erased evidence content must be null")
        return self


class MemoryRecord(ContractModel):
    id: UUID
    rule_key: Identifier
    statement: str | None
    kind: Literal["preference", "correction"]
    scope: Scope
    status: Literal["active", "superseded", "deleted"]
    evidence_ids: list[UUID] = Field(min_length=1)
    created_at: AwareDatetime
    valid_from: AwareDatetime
    valid_until: AwareDatetime | None
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def statement_matches_state(self) -> MemoryRecord:
        if self.status == "deleted" and self.statement is not None:
            raise ValueError("deleted memory statement must be null")
        if self.status != "deleted" and not self.statement:
            raise ValueError("active or superseded memory requires a statement")
        if self.valid_until is not None and self.valid_until < self.valid_from:
            raise ValueError("valid_until cannot precede valid_from")
        _require_unique(self.evidence_ids, "evidence_ids")
        return self


class RevisionEvent(ContractModel):
    id: UUID
    memory_id: UUID
    operation: Literal["approve", "correct", "supersede", "delete"]
    from_version: int | None = Field(default=None, ge=1)
    to_version: int | None = Field(default=None, ge=1)
    evidence_ids: list[UUID]
    actor: Literal["user", "research_fixture"]
    reason_code: Identifier
    approval_event_id: Identifier | None = None
    created_at: AwareDatetime

    @model_validator(mode="after")
    def evidence_ids_are_unique(self) -> RevisionEvent:
        _require_unique(self.evidence_ids, "evidence_ids")
        if self.operation == "approve" and (
            self.from_version is not None or self.to_version is None
        ):
            raise ValueError("approval requires null from_version and a to_version")
        if self.operation == "correct" and (
            self.from_version is None
            or self.to_version is None
            or self.to_version != self.from_version + 1
        ):
            raise ValueError("correction requires consecutive versions")
        if self.operation in {"supersede", "delete"} and (
            self.from_version is None or self.to_version is not None
        ):
            raise ValueError(
                "supersession and deletion require from_version and null to_version"
            )
        return self


class RetrievalDecision(ContractModel):
    query_id: Identifier
    memory_id: UUID
    eligible: bool
    decision: Literal[
        "selected",
        "scope_filtered",
        "state_filtered",
        "specificity_filtered",
        "conflict_filtered",
        "lexical_filtered",
        "budget_filtered",
    ]
    lexical_score: float | None
    reason_code: Identifier
    position: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def decision_fields_are_consistent(self) -> RetrievalDecision:
        if self.decision == "selected":
            if not self.eligible or self.position is None or self.lexical_score is None:
                raise ValueError(
                    "selected decisions must be eligible, scored, and positioned"
                )
        elif self.position is not None:
            raise ValueError("filtered decisions cannot have a position")
        if self.decision in {"scope_filtered", "state_filtered"}:
            if self.eligible or self.lexical_score is not None:
                raise ValueError(
                    "scope and state filtered decisions are ineligible and unscored"
                )
        elif not self.eligible:
            raise ValueError("post-eligibility filters must remain eligible")
        if (
            self.decision
            in {
                "specificity_filtered",
                "conflict_filtered",
                "lexical_filtered",
            }
            and self.lexical_score is not None
        ):
            raise ValueError("pre-ranking and unmatched decisions must be unscored")
        if self.decision == "budget_filtered" and self.lexical_score is None:
            raise ValueError("budget-filtered decisions must retain their score")
        return self


class MessageEvent(ContractModel):
    event_id: Identifier
    sequence: int = Field(ge=1)
    occurred_at: AwareDatetime
    type: Literal["message"]
    role: Literal["user", "assistant"]
    scope: Scope
    content: str = Field(min_length=1)


class ApprovalTimelineEvent(ContractModel):
    event_id: Identifier
    sequence: int = Field(ge=1)
    occurred_at: AwareDatetime
    type: Literal["approval"]
    memory_id: UUID
    evidence_ids: list[UUID] = Field(min_length=1)
    actor: Literal["research_fixture"]


class RevisionTimelineEvent(ContractModel):
    event_id: Identifier
    sequence: int = Field(ge=1)
    occurred_at: AwareDatetime
    type: Literal["revision"]
    memory_id: UUID
    revision_id: UUID
    operation: Literal["correct", "supersede", "delete"]
    actor: Literal["research_fixture"]


TimelineEvent = Annotated[
    MessageEvent | ApprovalTimelineEvent | RevisionTimelineEvent,
    Field(discriminator="type"),
]


class SummarySnapshot(ContractModel):
    snapshot_id: Identifier
    through_sequence: int = Field(ge=1)
    created_at: AwareDatetime
    generator: Identifier
    content: str = Field(min_length=1)


class QueryLabels(ContractModel):
    memory_needed: bool
    relevant_memory_ids: list[UUID]
    acceptable_memory_ids: list[UUID]
    forbidden_memory_ids: list[UUID]
    required_behavior: str = Field(min_length=1)
    violating_behaviors: list[Annotated[str, StringConstraints(min_length=1)]]
    abstention_correct: bool

    @model_validator(mode="after")
    def memory_labels_are_consistent(self) -> QueryLabels:
        relevant = set(self.relevant_memory_ids)
        acceptable = set(self.acceptable_memory_ids)
        forbidden = set(self.forbidden_memory_ids)
        _require_unique(self.relevant_memory_ids, "relevant_memory_ids")
        _require_unique(self.acceptable_memory_ids, "acceptable_memory_ids")
        _require_unique(self.forbidden_memory_ids, "forbidden_memory_ids")
        if not relevant.issubset(acceptable):
            raise ValueError("relevant memories must also be acceptable")
        if acceptable & forbidden:
            raise ValueError("acceptable and forbidden memories cannot overlap")
        if self.memory_needed != bool(relevant):
            raise ValueError(
                "memory_needed must match the presence of relevant memories"
            )
        return self


class ScenarioQuery(ContractModel):
    query_id: Identifier
    after_sequence: int = Field(ge=1)
    occurred_at: AwareDatetime
    content: str = Field(min_length=1)
    scope: Scope
    labels: QueryLabels


class Scenario(ContractModel):
    artifact_type: Literal["scenario"]
    schema_version: ArtifactVersion
    scenario_id: Identifier
    template_family: Identifier
    split: Literal["development", "held_out"]
    synthetic: Literal[True]
    timeline: list[TimelineEvent] = Field(min_length=1)
    summary_snapshots: list[SummarySnapshot]
    evidence_events: list[EvidenceEvent] = Field(min_length=1)
    memory_records: list[MemoryRecord] = Field(min_length=1)
    revision_events: list[RevisionEvent] = Field(min_length=1)
    retrieval_decisions: list[RetrievalDecision]
    queries: list[ScenarioQuery] = Field(min_length=1)

    @model_validator(mode="after")
    def references_and_lifecycle_are_consistent(self) -> Scenario:
        sequences = [event.sequence for event in self.timeline]
        if sequences != sorted(sequences):
            raise ValueError("timeline events must be ordered by sequence")
        _require_unique(sequences, "timeline sequence values")
        _require_unique(
            [event.event_id for event in self.timeline], "timeline event IDs"
        )
        _require_unique(
            [event.id for event in self.evidence_events], "evidence event IDs"
        )
        _require_unique(
            [(record.id, record.version) for record in self.memory_records],
            "memory ID and version pairs",
        )
        _require_unique(
            [event.id for event in self.revision_events], "revision event IDs"
        )
        _require_unique([query.query_id for query in self.queries], "query IDs")

        evidence_by_id = {event.id: event for event in self.evidence_events}
        memory_ids = {memory.id for memory in self.memory_records}
        revision_ids = {revision.id for revision in self.revision_events}
        query_by_id = {query.query_id: query for query in self.queries}

        for evidence in self.evidence_events:
            if evidence.scenario_id != self.scenario_id:
                raise ValueError("evidence scenario_id must match the scenario")

        evidence_owners: dict[UUID, set[UUID]] = defaultdict(set)
        for memory in self.memory_records:
            for evidence_id in memory.evidence_ids:
                if evidence_id not in evidence_by_id:
                    raise ValueError(f"unknown evidence {evidence_id} in memory record")
                evidence_owners[evidence_id].add(memory.id)
                if (
                    memory.status == "deleted"
                    and evidence_by_id[evidence_id].content_state != "erased"
                ):
                    raise ValueError(
                        f"deleted memory references present evidence {evidence_id}"
                    )
        if any(len(owner_ids) > 1 for owner_ids in evidence_owners.values()):
            raise ValueError("evidence cannot belong to multiple memory lineages")

        for revision in self.revision_events:
            if revision.memory_id not in memory_ids:
                raise ValueError(f"unknown memory {revision.memory_id} in revision")
            if any(item not in evidence_by_id for item in revision.evidence_ids):
                raise ValueError("revision references unknown evidence")

        for event in self.timeline:
            if (
                isinstance(event, (ApprovalTimelineEvent, RevisionTimelineEvent))
                and event.memory_id not in memory_ids
            ):
                raise ValueError(f"unknown memory {event.memory_id} in timeline")
            if isinstance(event, ApprovalTimelineEvent) and any(
                item not in evidence_by_id for item in event.evidence_ids
            ):
                raise ValueError("approval references unknown evidence")
            if (
                isinstance(event, RevisionTimelineEvent)
                and event.revision_id not in revision_ids
            ):
                raise ValueError(f"unknown revision {event.revision_id} in timeline")

        max_sequence = max(sequences)
        if any(
            snapshot.through_sequence > max_sequence
            for snapshot in self.summary_snapshots
        ):
            raise ValueError("summary snapshot exceeds the timeline")

        for query in self.queries:
            if query.after_sequence > max_sequence:
                raise ValueError(f"query {query.query_id} exceeds the timeline")
            labeled_ids = set().union(
                query.labels.relevant_memory_ids,
                query.labels.acceptable_memory_ids,
                query.labels.forbidden_memory_ids,
            )
            if not labeled_ids.issubset(memory_ids):
                raise ValueError(f"query {query.query_id} labels unknown memories")

        decisions_by_query: dict[str, list[RetrievalDecision]] = defaultdict(list)
        for decision in self.retrieval_decisions:
            if decision.query_id not in query_by_id:
                raise ValueError(f"unknown query {decision.query_id} in retrieval")
            if decision.memory_id not in memory_ids:
                raise ValueError(f"unknown memory {decision.memory_id} in retrieval")
            decisions_by_query[decision.query_id].append(decision)

        for query_id, decisions in decisions_by_query.items():
            _require_unique(
                [decision.memory_id for decision in decisions],
                f"retrieval memory IDs for query {query_id}",
            )
            selected = [item for item in decisions if item.decision == "selected"]
            positions = sorted(item.position for item in selected if item.position)
            if positions != list(range(1, len(selected) + 1)):
                raise ValueError(
                    f"selected positions for query {query_id} must be contiguous"
                )
            forbidden_ids = set(query_by_id[query_id].labels.forbidden_memory_ids)
            if {item.memory_id for item in selected} & forbidden_ids:
                raise ValueError(f"query {query_id} selects forbidden memories")
        return self


class NoMemoryCondition(ContractModel):
    kind: Literal["no_memory"]
    header: Literal[""]


class RecentHistoryCondition(ContractModel):
    kind: Literal["recent_history"]
    header: str = Field(min_length=1)
    selection: Literal["newest-complete-contiguous-suffix"]
    serialization_order: Literal["chronological"]
    partial_messages: Literal[False]


class SummaryGeneration(ContractModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    prompt_hash: Sha256
    temperature: float = Field(ge=0)
    seed: int = Field(ge=0)
    update_schedule: str = Field(min_length=1)


class RollingSummaryCondition(ContractModel):
    kind: Literal["rolling_summary"]
    header: str = Field(min_length=1)
    summary_generation: SummaryGeneration


class StructuredMemoryCondition(ContractModel):
    kind: Literal["structured_memory"]
    header: str = Field(min_length=1)
    selection_source: Literal["retrieval_decisions"]
    include_raw_approval_messages: Literal[False]


class TokenizerConfig(ContractModel):
    name: Literal["whitespace"]
    version: Literal["1"]


class SerializerConfig(ContractModel):
    name: Literal["memory-loom-context"]
    version: Literal["1"]


class Conditions(ContractModel):
    B0: NoMemoryCondition
    B1: RecentHistoryCondition
    B2: RollingSummaryCondition
    B3: StructuredMemoryCondition


class ConditionManifest(ContractModel):
    artifact_type: Literal["condition_manifest"]
    schema_version: ArtifactVersion
    manifest_id: Identifier
    tokenizer: TokenizerConfig
    serializer: SerializerConfig
    max_context_tokens: int = Field(ge=1)
    conditions: Conditions


class AnalysisConfig(ContractModel):
    repeat_aggregation: str = Field(min_length=1)
    scenario_weighting: str = Field(min_length=1)
    independent_unit: Literal["scenario", "template_family"]
    interval_method: str = Field(min_length=1)
    multiplicity_method: str = Field(min_length=1)
    h1_decision_rule: str = Field(min_length=1)


class PromptHashes(ContractModel):
    system: Sha256
    user: Sha256


class DecodingConfig(ContractModel):
    temperature: float = Field(ge=0, le=2)
    top_p: float = Field(gt=0, le=1)
    max_output_tokens: int = Field(ge=1)


class RunManifest(ContractModel):
    artifact_type: Literal["run_manifest"]
    schema_version: ArtifactVersion
    run_id: Identifier
    created_at: AwareDatetime
    protocol_version: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    code_revision: str = Field(min_length=1)
    condition_manifest_id: Identifier
    scenario_ids: list[Identifier] = Field(min_length=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    prompt_hashes: PromptHashes
    condition_order: list[ConditionName]
    condition_order_strategy: Literal["fixed", "deterministic-shuffle"] = "fixed"
    decoding: DecodingConfig
    seed: int = Field(ge=0)
    repeats: int = Field(ge=1)
    analysis: AnalysisConfig
    status: Literal["prepared", "running", "completed", "failed"]

    @model_validator(mode="after")
    def scenario_ids_are_unique(self) -> RunManifest:
        _require_unique(self.scenario_ids, "run scenario IDs")
        if sorted(self.condition_order) != ["B0", "B1", "B2", "B3"]:
            raise ValueError("condition_order must contain B0, B1, B2, and B3 once")
        return self


class RunFailure(ContractModel):
    stage: Literal["context_assembly", "model_invocation", "output_capture"]
    error_type: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ConditionRunResult(ContractModel):
    scenario_id: Identifier
    query_id: Identifier
    condition: ConditionName
    repeat: int = Field(ge=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    seed: int = Field(ge=0)
    system_prompt: str = Field(min_length=1)
    user_prompt: str | None
    injected_context: str | None
    context_token_count: int | None = Field(default=None, ge=0)
    included_ids: list[str] | None
    status: Literal["completed", "failed"]
    raw_output: str | None
    latency_ms: float | None = Field(default=None, ge=0)
    provider_response_id: str | None = None
    provider_model: str | None = None
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    failure: RunFailure | None

    @model_validator(mode="after")
    def outcome_fields_are_consistent(self) -> ConditionRunResult:
        prompt_fields = (
            self.user_prompt,
            self.injected_context,
            self.context_token_count,
            self.included_ids,
        )
        if self.failure is not None and self.failure.stage == "context_assembly":
            if any(value is not None for value in prompt_fields):
                raise ValueError(
                    "context failures cannot contain assembled prompt data"
                )
        elif any(value is None for value in prompt_fields):
            raise ValueError("assembled runs require prompt and context data")

        if self.status == "completed":
            if (
                self.raw_output is None
                or self.latency_ms is None
                or self.failure is not None
            ):
                raise ValueError(
                    "completed runs require output and latency without failure"
                )
        elif self.failure is None or self.raw_output is not None:
            raise ValueError("failed runs require failure details and no output")
        if self.failure is not None and self.failure.stage != "context_assembly":
            if self.latency_ms is None:
                raise ValueError("post-assembly failures require latency")
        return self


class RunArtifact(ContractModel):
    artifact_type: Literal["run_artifact"]
    schema_version: ArtifactVersion
    run_manifest: RunManifest
    condition_manifest: ConditionManifest
    started_at: AwareDatetime
    completed_at: AwareDatetime
    status: Literal["completed", "completed_with_failures", "failed"]
    results: list[ConditionRunResult] = Field(min_length=1)

    @model_validator(mode="after")
    def configuration_and_status_are_consistent(self) -> RunArtifact:
        if self.completed_at < self.started_at:
            raise ValueError("completed_at cannot precede started_at")
        if (
            self.run_manifest.condition_manifest_id
            != self.condition_manifest.manifest_id
        ):
            raise ValueError("run and condition manifests do not match")
        completed = sum(result.status == "completed" for result in self.results)
        expected_status = (
            "completed"
            if completed == len(self.results)
            else "failed"
            if completed == 0
            else "completed_with_failures"
        )
        if self.status != expected_status:
            raise ValueError(f"run status must be {expected_status}")
        return self


class BlindedReviewItem(ContractModel):
    item_id: Identifier
    scenario_id: Identifier
    query_id: Identifier
    repeat: int = Field(ge=1)
    current_request: str = Field(min_length=1)
    required_behavior: str = Field(min_length=1)
    violating_behaviors: list[str]
    response: str = Field(min_length=1)


class BlindedReviewPacket(ContractModel):
    artifact_type: Literal["blinded_review_packet"]
    schema_version: ArtifactVersion
    packet_id: Identifier
    created_at: AwareDatetime
    dataset_version: str = Field(min_length=1)
    instructions: str = Field(min_length=1)
    items: list[BlindedReviewItem] = Field(min_length=1)

    @model_validator(mode="after")
    def item_ids_are_unique(self) -> BlindedReviewPacket:
        _require_unique([item.item_id for item in self.items], "review item IDs")
        return self


class BlindingKeyItem(ContractModel):
    item_id: Identifier
    scenario_id: Identifier
    template_family: Identifier
    query_id: Identifier
    repeat: int = Field(ge=1)
    condition: ConditionName
    memory_needed: bool
    relevant_memory_ids: list[UUID]
    forbidden_memory_ids: list[UUID]
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    provider_model: str | None = None


class BlindingKey(ContractModel):
    artifact_type: Literal["blinding_key"]
    schema_version: ArtifactVersion
    packet_id: Identifier
    created_at: AwareDatetime
    seed_hash: Sha256
    items: list[BlindingKeyItem] = Field(min_length=1)

    @model_validator(mode="after")
    def item_ids_are_unique(self) -> BlindingKey:
        _require_unique([item.item_id for item in self.items], "blinding key item IDs")
        return self


class BlindedRating(ContractModel):
    item_id: Identifier
    decision: Literal["adheres", "violates", "unclear", "unreviewed"]
    task_success: bool | None = None
    memory_override: bool | None = None
    unsupported_memory_claim: bool | None = None
    notes: str | None = None


class BlindedReview(ContractModel):
    artifact_type: Literal["blinded_review"]
    schema_version: ArtifactVersion
    packet_id: Identifier
    reviewer_id: Identifier
    created_at: AwareDatetime
    reviewer_type: Literal["human", "model"]
    provider: str | None = None
    model: str | None = None
    ratings: list[BlindedRating] = Field(min_length=1)

    @model_validator(mode="after")
    def reviewer_and_ratings_are_consistent(self) -> BlindedReview:
        _require_unique([item.item_id for item in self.ratings], "review rating IDs")
        if self.reviewer_type == "model" and (
            self.provider is None or self.model is None
        ):
            raise ValueError("model reviews require provider and model")
        if self.reviewer_type == "human" and (
            self.provider is not None or self.model is not None
        ):
            raise ValueError("human reviews cannot declare provider or model")
        return self


class ConditionPilotMetrics(ContractModel):
    condition: ConditionName
    scored_items: int = Field(ge=0)
    unclear_items: int = Field(ge=0)
    preference_adherence: float | None = Field(default=None, ge=0, le=1)
    task_success: float | None = Field(default=None, ge=0, le=1)
    mean_context_tokens: float | None = Field(default=None, ge=0)
    mean_latency_ms: float | None = Field(default=None, ge=0)
    memory_override_count: int = Field(ge=0)
    unsupported_memory_claim_count: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)


class PilotContrast(ContractModel):
    comparison: Literal["B3-B0", "B3-B1", "B3-B2"]
    estimate: float
    simultaneous_ci_low: float
    simultaneous_ci_high: float


class FamilyPilotMetrics(ContractModel):
    template_family: Identifier
    condition: ConditionName
    scored_items: int = Field(ge=0)
    preference_adherence: float | None = Field(default=None, ge=0, le=1)
    task_success: float | None = Field(default=None, ge=0, le=1)


class PilotAnalysis(ContractModel):
    artifact_type: Literal["pilot_analysis"]
    schema_version: ArtifactVersion
    packet_id: Identifier
    created_at: AwareDatetime
    status: Literal["exploratory_pilot"]
    reviewer_types: list[Literal["human", "model"]]
    generation_models: list[str]
    reviewer_models: list[str]
    reviewed_items: int = Field(ge=0)
    reviewer_disagreements: int = Field(ge=0)
    failed_runs: int = Field(ge=0)
    memory_override_count: int = Field(ge=0)
    unsupported_memory_claim_count: int = Field(ge=0)
    forbidden_context_count: int = Field(ge=0)
    no_memory_false_positive_count: int = Field(ge=0)
    bootstrap_samples: int = Field(ge=1)
    condition_metrics: list[ConditionPilotMetrics]
    family_metrics: list[FamilyPilotMetrics]
    contrasts: list[PilotContrast]
    limitations: list[str] = Field(min_length=1)


class RetrievalEvaluationQueryResult(ContractModel):
    scenario_id: Identifier
    template_family: Identifier
    split: Literal["development", "held_out"]
    query_id: Identifier
    memory_needed: bool
    abstention_expected: bool
    relevant_memory_ids: list[UUID]
    acceptable_memory_ids: list[UUID]
    forbidden_memory_ids: list[UUID]
    selected_memory_ids: list[UUID]
    included_memory_ids: list[UUID]
    irrelevant_selected_ids: list[UUID]
    forbidden_hits: list[UUID]
    recall_at_k: float | None = Field(default=None, ge=0, le=1)
    precision_at_k: float | None = Field(default=None, ge=0, le=1)
    reciprocal_rank: float | None = Field(default=None, ge=0, le=1)
    ndcg_at_k: float | None = Field(default=None, ge=0, le=1)
    abstention_match: bool | None
    no_memory_false_positive: bool
    context_token_count: int = Field(ge=0)


class RetrievalAggregateMetrics(ContractModel):
    total_scenarios: int = Field(ge=1)
    total_queries: int = Field(ge=1)
    memory_needed_queries: int = Field(ge=0)
    abstention_queries: int = Field(ge=0)
    recall_at_k: float | None = Field(default=None, ge=0, le=1)
    precision_at_k: float | None = Field(default=None, ge=0, le=1)
    mean_reciprocal_rank: float | None = Field(default=None, ge=0, le=1)
    mean_ndcg_at_k: float | None = Field(default=None, ge=0, le=1)
    abstention_accuracy: float | None = Field(default=None, ge=0, le=1)
    no_memory_false_positive_rate: float | None = Field(default=None, ge=0, le=1)
    forbidden_hit_count: int = Field(ge=0)
    forbidden_query_count: int = Field(ge=0)
    mean_context_tokens: float = Field(ge=0)


class RetrievalEvaluationArtifact(ContractModel):
    artifact_type: Literal["retrieval_evaluation"]
    schema_version: ArtifactVersion
    evaluator: Literal["sqlite-fts5-lexical-v1"]
    dataset_path: str = Field(min_length=1)
    condition_manifest_id: Identifier
    limit: int = Field(ge=1)
    scenario_ids: list[Identifier] = Field(min_length=1)
    query_results: list[RetrievalEvaluationQueryResult] = Field(min_length=1)
    metrics: RetrievalAggregateMetrics

    @model_validator(mode="after")
    def contents_are_consistent(self) -> RetrievalEvaluationArtifact:
        _require_unique(self.scenario_ids, "retrieval evaluation scenario IDs")
        query_keys = [
            (result.scenario_id, result.query_id) for result in self.query_results
        ]
        _require_unique(query_keys, "retrieval evaluation query keys")
        if set(self.scenario_ids) != {
            result.scenario_id for result in self.query_results
        }:
            raise ValueError("scenario IDs must match retrieval query results")
        if self.metrics.total_scenarios != len(self.scenario_ids):
            raise ValueError("total_scenarios must match scenario IDs")
        if self.metrics.total_queries != len(self.query_results):
            raise ValueError("total_queries must match query results")
        return self


def _require_unique(values: list[object], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")
