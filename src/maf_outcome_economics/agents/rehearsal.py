"""Explicit deterministic agents for CLI tests and rehearsals only."""

from dataclasses import dataclass
from typing import Any, cast

from agent_framework import Agent

from maf_outcome_economics.domain import ReviewResult, Ticket, TriageResult

from .prompts import PromptProfile

_CORRECTABLE_TRIAGE_IDS = frozenset({"TKT-022", "TKT-025", "TKT-028", "TKT-031"})
_HARMFUL_REVIEW_IDS = frozenset({"TKT-015"})


class RehearsalTriageAgent:
    """Return deterministic rehearsal predictions with representative variation."""

    async def run(
        self,
        ticket: Ticket,
        run_id: str,
        profile: PromptProfile = PromptProfile.BASELINE,
    ) -> TriageResult:
        """Return a schema-valid deterministic triage result."""
        del profile
        if ticket.id.startswith("STOP-"):
            return TriageResult(
                run_id=run_id,
                ticket_id=ticket.id,
                category="Service request",
                priority="P3",
                resolver_group="Service Desk",
                confidence=0.95,
                rationale="Intentional mismatch for deterministic STOP rehearsal.",
            )
        if ticket.id in _CORRECTABLE_TRIAGE_IDS:
            return TriageResult(
                run_id=run_id,
                ticket_id=ticket.id,
                category="Service request",
                priority="P3",
                resolver_group="Service Desk",
                confidence=0.65,
                rationale="Intentional correctable mismatch for rehearsal attribution.",
            )
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
    """Return deterministic mixed review outcomes without an LLM call."""

    async def run(
        self,
        ticket: Ticket,
        triage: TriageResult,
        profile: PromptProfile = PromptProfile.BASELINE,
    ) -> ReviewResult:
        """Return a schema-valid deterministic review result."""
        del profile
        if ticket.id in _HARMFUL_REVIEW_IDS:
            return ReviewResult(
                run_id=triage.run_id,
                ticket_id=ticket.id,
                approved=False,
                corrected_category="Service request",
                corrected_priority="P3",
                corrected_resolver_group="Service Desk",
                notes="Intentional harmful correction for rehearsal attribution.",
            )
        triage_matches_gold = (
            triage.category == ticket.gold_category
            and triage.priority == ticket.gold_priority
            and triage.resolver_group == ticket.gold_resolver_group
        )
        if not triage_matches_gold:
            return ReviewResult(
                run_id=triage.run_id,
                ticket_id=ticket.id,
                approved=False,
                corrected_category=ticket.gold_category,
                corrected_priority=ticket.gold_priority,
                corrected_resolver_group=ticket.gold_resolver_group,
                notes="Deterministic useful correction for rehearsal attribution.",
            )
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