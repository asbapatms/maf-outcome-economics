"""Structured support-ticket triage and review agents."""

from typing import Generic, TypeVar, cast

from agent_framework import Agent
from pydantic import BaseModel

from maf_outcome_economics.domain import ReviewResult, Ticket, TriageResult

from .prompts import PromptProfile, render_review_prompt, render_triage_prompt, retry_prompt
from .provider import AgentProvider, MalformedAgentOutputError, parse_json_output

ResultT = TypeVar("ResultT", bound=BaseModel)


class StructuredSupportAgent(Generic[ResultT]):
    """Run a schema-bound agent with one malformed-output retry."""

    def __init__(
        self,
        agent: Agent,
        provider: AgentProvider,
        response_type: type[ResultT],
    ) -> None:
        self.agent = agent
        self.provider = provider
        self.response_type = response_type

    async def _complete(
        self,
        prompt: str,
        *,
        run_id: str,
        ticket_id: str,
    ) -> ResultT:
        current_prompt = prompt
        for attempt in range(2):
            try:
                output = await self.provider.complete(
                    self.agent,
                    current_prompt,
                    self.response_type,
                )
                if isinstance(output, self.response_type):
                    result = output
                elif isinstance(output, str):
                    result = parse_json_output(output, self.response_type)
                else:
                    raise MalformedAgentOutputError(
                        f"Provider returned {type(output).__name__}, expected text or "
                        f"{self.response_type.__name__}"
                    )
                if (
                    getattr(result, "run_id", None) != run_id
                    or getattr(result, "ticket_id", None) != ticket_id
                ):
                    raise MalformedAgentOutputError(
                        "Response run_id or ticket_id did not match the request"
                    )
                return result
            except MalformedAgentOutputError:
                if attempt == 1:
                    raise
                current_prompt = retry_prompt(
                    current_prompt,
                    cast(type[TriageResult] | type[ReviewResult], self.response_type),
                )
        raise AssertionError("Bounded retry loop exited unexpectedly")


class TriageAgent(StructuredSupportAgent[TriageResult]):
    """Classify and route fictional support tickets."""

    ID = "maf-outcome-economics.triage.v1"
    NAME = "TriageAgent"

    def __init__(self, agent: Agent, provider: AgentProvider) -> None:
        super().__init__(agent, provider, TriageResult)

    async def run(
        self,
        ticket: Ticket,
        run_id: str,
        profile: PromptProfile = PromptProfile.BASELINE,
    ) -> TriageResult:
        """Triage a ticket using the selected prompt profile."""
        return await self._complete(
            render_triage_prompt(ticket, run_id, profile),
            run_id=run_id,
            ticket_id=ticket.id,
        )


class ReviewAgent(StructuredSupportAgent[ReviewResult]):
    """Review a proposed fictional support-ticket triage."""

    ID = "maf-outcome-economics.review.v1"
    NAME = "ReviewAgent"

    def __init__(self, agent: Agent, provider: AgentProvider) -> None:
        super().__init__(agent, provider, ReviewResult)

    async def run(
        self,
        ticket: Ticket,
        triage: TriageResult,
        profile: PromptProfile = PromptProfile.BASELINE,
    ) -> ReviewResult:
        """Review a triage result using the selected prompt profile."""
        return await self._complete(
            render_review_prompt(ticket, triage, profile),
            run_id=triage.run_id,
            ticket_id=ticket.id,
        )