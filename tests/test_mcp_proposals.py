from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from memory_loom.mcp_models import CreateChangeRequest, SourceEventInput
from memory_loom.mcp_proposals import ProposalExpiredError, ProposalStore
from memory_loom.models import Scope


def test_proposal_expires_without_persistence() -> None:
    current_time = [datetime(2026, 10, 1, 12, 0, tzinfo=UTC)]
    store = ProposalStore(
        ttl=timedelta(minutes=15),
        clock=lambda: current_time[0],
    )
    proposal = store.create(_change(), _scope())

    current_time[0] += timedelta(minutes=15)

    with pytest.raises(ProposalExpiredError):
        store.get(proposal.proposal_id)
    assert store.discard(proposal.proposal_id) is False


def test_proposal_store_returns_defensive_copies() -> None:
    store = ProposalStore()
    proposal = store.create(_change(), _scope())

    proposal.change.statement = "Mutated outside the store."

    stored = store.get(proposal.proposal_id)
    assert stored.change.statement == "Lead with correctness issues."


def _change() -> CreateChangeRequest:
    return CreateChangeRequest(
        operation="create",
        kind="preference",
        rule_key="review.priority",
        statement="Lead with correctness issues.",
        scope_level="user",
        source_event=SourceEventInput(
            event_id="message-001",
            content="Lead with correctness issues.",
        ),
    )


def _scope() -> Scope:
    return Scope(user_id="user-a", project_id=None, task_id=None)
