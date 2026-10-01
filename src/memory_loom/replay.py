from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any

from memory_loom.models import MemoryRecord, Scenario
from memory_loom.retrieval import LexicalRetriever
from memory_loom.store import MemoryStore


@dataclass(frozen=True)
class ReplayedContext:
    condition: str
    query_id: str
    context: str
    token_count: int
    included_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def replay_query_contexts(
    scenario: dict[str, Any], condition_manifest: dict[str, Any], query_id: str
) -> list[ReplayedContext]:
    return [
        replay_query_context(
            scenario, condition_manifest, query_id, condition, frozen_retrieval=True
        )
        for condition in ("B0", "B1", "B2", "B3")
    ]


def replay_query_contexts_live(
    scenario_document: dict[str, Any],
    condition_manifest: dict[str, Any],
    query_id: str,
) -> list[ReplayedContext]:
    scenario = Scenario.model_validate(scenario_document)
    query = next((item for item in scenario.queries if item.query_id == query_id), None)
    if query is None:
        raise ValueError(f"unknown query {query_id!r}")

    with MemoryStore() as store:
        store.load_scenario(scenario)
        result = LexicalRetriever(store).retrieve(
            query.query_id,
            query.content,
            query.scope,
            query.occurred_at,
        )

    replay_document = scenario.model_dump(mode="json")
    replay_document["retrieval_decisions"] = [
        decision
        for decision in replay_document["retrieval_decisions"]
        if decision["query_id"] != query_id
    ] + [decision.model_dump(mode="json") for decision in result.decisions]
    return replay_query_contexts(replay_document, condition_manifest, query_id)


def replay_query_context(
    scenario_document: dict[str, Any],
    condition_manifest: dict[str, Any],
    query_id: str,
    condition: str,
    *,
    frozen_retrieval: bool = False,
) -> ReplayedContext:
    scenario = Scenario.model_validate(scenario_document)
    query = next((item for item in scenario.queries if item.query_id == query_id), None)
    if query is None:
        raise ValueError(f"unknown query {query_id!r}")
    if condition not in {"B0", "B1", "B2", "B3"}:
        raise ValueError(f"unknown condition {condition!r}")

    replay_document = scenario.model_dump(mode="json")
    if condition == "B3" and not frozen_retrieval:
        with MemoryStore() as store:
            store.load_scenario(scenario)
            result = LexicalRetriever(store).retrieve(
                query.query_id,
                query.content,
                query.scope,
                query.occurred_at,
            )
        replay_document["retrieval_decisions"] = [
            decision
            for decision in replay_document["retrieval_decisions"]
            if decision["query_id"] != query_id
        ] + [decision.model_dump(mode="json") for decision in result.decisions]

    query_document = next(
        item for item in replay_document["queries"] if item["query_id"] == query_id
    )
    return _replay_condition(
        replay_document, condition_manifest, query_document, condition
    )


def count_tokens(text: str) -> int:
    return len(text.split())


def build_structured_memory_context(
    records: Sequence[MemoryRecord],
    header: str,
    budget: int,
) -> tuple[str, tuple[str, ...]]:
    included_records: list[dict[str, Any]] = []
    for record in records:
        record_document = record.model_dump(mode="json")
        candidate = [*included_records, record_document]
        context = _serialize_blocks(header, [_memory_block(item) for item in candidate])
        if count_tokens(context) > budget:
            break
        included_records = candidate

    if not included_records:
        return "", ()
    return (
        _serialize_blocks(header, [_memory_block(item) for item in included_records]),
        tuple(record["id"] for record in included_records),
    )


def _replay_condition(
    scenario: dict[str, Any],
    condition_manifest: dict[str, Any],
    query: dict[str, Any],
    condition: str,
) -> ReplayedContext:
    condition_config = condition_manifest["conditions"][condition]
    budget = condition_manifest["max_context_tokens"]
    kind = condition_config["kind"]

    if kind == "no_memory":
        context = ""
        included_ids: tuple[str, ...] = ()
    elif kind == "recent_history":
        context, included_ids = _recent_history_context(
            scenario, query, condition_config["header"], budget
        )
    elif kind == "rolling_summary":
        context, included_ids = _rolling_summary_context(
            scenario, query, condition_config["header"], budget
        )
    elif kind == "structured_memory":
        context, included_ids = _structured_memory_context(
            scenario, query, condition_config["header"], budget
        )
    else:
        raise ValueError(f"unsupported condition kind {kind!r}")

    token_count = count_tokens(context)
    if token_count > budget:
        raise ValueError(
            f"{condition} context uses {token_count} tokens, exceeding budget {budget}"
        )
    return ReplayedContext(
        condition, query["query_id"], context, token_count, included_ids
    )


def _recent_history_context(
    scenario: dict[str, Any],
    query: dict[str, Any],
    header: str,
    budget: int,
) -> tuple[str, tuple[str, ...]]:
    messages = [
        event
        for event in scenario["timeline"]
        if event["type"] == "message" and event["sequence"] <= query["after_sequence"]
    ]
    selected: list[dict[str, Any]] = []
    for message in reversed(messages):
        candidate = [message, *selected]
        context = _serialize_blocks(
            header, [_message_block(item) for item in candidate]
        )
        if count_tokens(context) > budget:
            break
        selected = candidate
    if not selected:
        return "", ()
    return (
        _serialize_blocks(header, [_message_block(item) for item in selected]),
        tuple(item["event_id"] for item in selected),
    )


def _rolling_summary_context(
    scenario: dict[str, Any],
    query: dict[str, Any],
    header: str,
    budget: int,
) -> tuple[str, tuple[str, ...]]:
    snapshots = [
        snapshot
        for snapshot in scenario["summary_snapshots"]
        if snapshot["through_sequence"] <= query["after_sequence"]
    ]
    if not snapshots:
        return "", ()
    snapshot = max(snapshots, key=lambda item: item["through_sequence"])
    context = _serialize_blocks(header, [snapshot["content"]])
    if count_tokens(context) > budget:
        raise ValueError(
            f"summary {snapshot['snapshot_id']!r} does not fit the context budget"
        )
    return context, (snapshot["snapshot_id"],)


def _structured_memory_context(
    scenario: dict[str, Any],
    query: dict[str, Any],
    header: str,
    budget: int,
) -> tuple[str, tuple[str, ...]]:
    selected_decisions = sorted(
        (
            decision
            for decision in scenario["retrieval_decisions"]
            if decision["query_id"] == query["query_id"]
            and decision["decision"] == "selected"
        ),
        key=lambda item: item["position"],
    )
    records_by_id: dict[str, list[dict[str, Any]]] = {}
    for record in scenario["memory_records"]:
        records_by_id.setdefault(record["id"], []).append(record)

    selected_records: list[MemoryRecord] = []
    for decision in selected_decisions:
        record = max(
            records_by_id[decision["memory_id"]], key=lambda item: item["version"]
        )
        if record["status"] != "active" or record["statement"] is None:
            raise ValueError(f"selected memory {record['id']!r} is not active")
        if not _scope_matches(record["scope"], query["scope"]):
            raise ValueError(f"selected memory {record['id']!r} is out of scope")
        selected_records.append(MemoryRecord.model_validate(record))

    return build_structured_memory_context(selected_records, header, budget)


def _scope_matches(record_scope: dict[str, Any], query_scope: dict[str, Any]) -> bool:
    if record_scope["user_id"] != query_scope["user_id"]:
        return False
    if record_scope["project_id"] not in (None, query_scope["project_id"]):
        return False
    return record_scope["task_id"] in (None, query_scope["task_id"])


def _message_block(message: dict[str, Any]) -> str:
    return (
        f'<message role="{message["role"]}" event_id="{message["event_id"]}">\n'
        f"{message['content']}\n"
        "</message>"
    )


def _memory_block(record: dict[str, Any]) -> str:
    scope = record["scope"]
    return "\n".join(
        [
            f'<memory id="{record["id"]}" rule_key="{record["rule_key"]}">',
            f"scope: user={scope['user_id']} project={scope['project_id']} task={scope['task_id']}",
            f"statement: {record['statement']}",
            f"evidence_ids: {','.join(record['evidence_ids'])}",
            "</memory>",
        ]
    )


def _serialize_blocks(header: str, blocks: list[str]) -> str:
    if not blocks:
        return ""
    return "\n\n".join([header, *blocks]).strip()
