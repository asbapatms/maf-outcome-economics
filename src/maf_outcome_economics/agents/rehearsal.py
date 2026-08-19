"""Explicit deterministic agents for CLI tests and rehearsals only."""

from dataclasses import dataclass
from typing import Any, cast

from agent_framework import Agent

from maf_outcome_economics.domain import ReviewResult, Ticket, TriageResult

from .prompts import PromptProfile


class RehearsalTriageAgent:
    """Return ticket gold labels as deterministic rehearsal predictions."""

    async def run(
        self,
        ticket: Ticket,
        run_id: str,
        profile: PromptProfile = PromptProfile.BASELINE,
    ) -> TriageResult:
        """Return a schema-valid deterministic triage result."""
        del profile
        return TriageResult(
            run_id=run_id,
            ticket_id=ticket.id,
            category=ticket.gold_category,
            priority=ticket.gold_priority,
            resolver_group=ticket.gold_resolver_group,
            confidence=0.95,
            rationale="Deterministic fake-provider rehearsal output.",
        )


class RehearsalReviewAgent:
    """Approve deterministic rehearsal predictions without an LLM call."""

    async def run(
        self,
        ticket: Ticket,
        triage: TriageResult,
        profile: PromptProfile = PromptProfile.BASELINE,
    ) -> ReviewResult:
        """Return a schema-valid deterministic review result."""
        del profile
        return ReviewResult(
            run_id=triage.run_id,
            ticket_id=ticket.id,
            approved=True,
            notes="Deterministic fake-provider rehearsal approval.",
        )


@dataclass(slots=True)
class RehearsalAgentSuite:
    """Agent-like objects accepted by the shared ticket workflow."""

    triage: Any
    review: Any

    async def close(self) -> None:
        """Provide the same lifecycle shape as the live suite."""


def create_rehearsal_agent_suite() -> RehearsalAgentSuite:
    """Create explicit fake agents for tests and rehearsals."""
    return RehearsalAgentSuite(
        triage=cast(Agent, RehearsalTriageAgent()),
        review=cast(Agent, RehearsalReviewAgent()),
    )