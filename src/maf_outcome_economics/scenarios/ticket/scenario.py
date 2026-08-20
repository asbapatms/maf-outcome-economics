"""Composition root for the support-ticket triage reference scenario."""

from collections.abc import AsyncIterator
from dataclasses import dataclass

from agent_framework import WorkflowEvent
from opentelemetry.trace import Tracer

from maf_outcome_economics.agents import (
    RehearsalAgentSuite,
    SupportAgentSuite,
    create_rehearsal_agent_suite,
    create_support_agent_suite,
)
from maf_outcome_economics.config import Settings
from maf_outcome_economics.domain import (
    TicketWorkflowInput,
    WorkflowVariant,
)
from maf_outcome_economics.persistence.sqlite_repository import OutcomeRepository

from .seed import (
    DemoScenario,
    contract_id_for_variant,
    seed_demo_scenario,
    seed_fictional_tickets,
)
from .workflow import stream_ticket_workflow


@dataclass(frozen=True, slots=True)
class TicketScenario:
    """Own ticket-specific data, agents, contracts, and workflow dispatch."""

    id: str = "ticket-triage"
    name: str = "Support ticket triage"
    variants: tuple[WorkflowVariant, ...] = tuple(WorkflowVariant)

    @staticmethod
    def seed(
        repository: OutcomeRepository,
        dataset: DemoScenario | None = None,
    ) -> int:
        """Seed the standard or deterministic ticket dataset."""
        if dataset is None:
            return seed_fictional_tickets(repository)
        return seed_demo_scenario(repository, dataset)

    @staticmethod
    def contract_id(variant: WorkflowVariant) -> str:
        """Return the ticket scenario's contract for a workflow variant."""
        return contract_id_for_variant(variant)

    @staticmethod
    def create_agent_suite(
        settings: Settings,
        *,
        live: bool,
    ) -> SupportAgentSuite | RehearsalAgentSuite:
        """Create live or deterministic agents for the ticket scenario."""
        if live:
            return create_support_agent_suite(settings)
        return create_rehearsal_agent_suite()

    @staticmethod
    def stream(
        request: TicketWorkflowInput,
        repository: OutcomeRepository,
        suite: SupportAgentSuite | RehearsalAgentSuite,
        *,
        tracer: Tracer | None = None,
    ) -> AsyncIterator[WorkflowEvent[object]]:
        """Dispatch one ticket through the scenario workflow."""
        return stream_ticket_workflow(
            request,
            repository,
            suite.triage,
            suite.review,
            tracer=tracer,
        )