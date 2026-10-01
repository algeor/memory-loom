from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from threading import Lock
from uuid import UUID, uuid4

from pydantic import AwareDatetime, Field, model_validator

from memory_loom.mcp_models import ChangeRequest
from memory_loom.models import ContractModel, Scope


class ProposalNotFoundError(ValueError):
    pass


class ProposalExpiredError(ValueError):
    pass


class PendingProposal(ContractModel):
    proposal_id: UUID
    change: ChangeRequest
    scope: Scope
    target_version: int | None = Field(default=None, ge=1)
    created_at: AwareDatetime
    expires_at: AwareDatetime

    @model_validator(mode="after")
    def target_version_matches_operation(self) -> PendingProposal:
        if self.change.operation == "create" and self.target_version is not None:
            raise ValueError("create proposal cannot have a target version")
        if self.change.operation != "create" and self.target_version is None:
            raise ValueError("revision proposal requires a target version")
        return self


class ProposalStore:
    def __init__(
        self,
        *,
        ttl: timedelta = timedelta(minutes=15),
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if ttl <= timedelta(0):
            raise ValueError("proposal TTL must be positive")

        self._ttl = ttl
        self._clock = clock or (lambda: datetime.now(UTC))
        self._proposals: dict[UUID, PendingProposal] = {}
        self._lock = Lock()

    def create(
        self,
        change: ChangeRequest,
        scope: Scope,
        *,
        target_version: int | None = None,
    ) -> PendingProposal:
        now = self._now()
        proposal = PendingProposal(
            proposal_id=uuid4(),
            change=change,
            scope=scope,
            target_version=target_version,
            created_at=now,
            expires_at=now + self._ttl,
        )

        with self._lock:
            self._purge_expired(now)
            self._proposals[proposal.proposal_id] = proposal.model_copy(deep=True)

        return proposal.model_copy(deep=True)

    def get(self, proposal_id: UUID) -> PendingProposal:
        now = self._now()

        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if proposal is None:
                raise ProposalNotFoundError(f"unknown proposal {proposal_id}")
            if proposal.expires_at <= now:
                del self._proposals[proposal_id]
                raise ProposalExpiredError(f"expired proposal {proposal_id}")
            return proposal.model_copy(deep=True)

    def take(self, proposal_id: UUID) -> PendingProposal:
        now = self._now()

        with self._lock:
            proposal = self._proposals.pop(proposal_id, None)
            if proposal is None:
                raise ProposalNotFoundError(f"unknown proposal {proposal_id}")
            if proposal.expires_at <= now:
                raise ProposalExpiredError(f"expired proposal {proposal_id}")
            return proposal.model_copy(deep=True)

    def restore(self, proposal: PendingProposal) -> bool:
        now = self._now()
        if proposal.expires_at <= now:
            return False

        with self._lock:
            if proposal.proposal_id in self._proposals:
                return False
            self._proposals[proposal.proposal_id] = proposal.model_copy(deep=True)
            return True

    def discard(self, proposal_id: UUID) -> bool:
        with self._lock:
            return self._proposals.pop(proposal_id, None) is not None

    def _now(self) -> datetime:
        now = self._clock()
        if now.utcoffset() is None:
            raise ValueError("proposal clock must return a timezone-aware datetime")
        return now

    def _purge_expired(self, now: datetime) -> None:
        expired = [
            proposal_id
            for proposal_id, proposal in self._proposals.items()
            if proposal.expires_at <= now
        ]
        for proposal_id in expired:
            del self._proposals[proposal_id]


proposal_store = ProposalStore()
