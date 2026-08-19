"""Sequential Microsoft Agent Framework workflow for support tickets."""

from collections.abc import AsyncIterator
from typing import Never
from uuid import uuid4

from agent_framework import (
    Executor,
    Workflow,
    WorkflowBuilder,
    WorkflowContext,
    WorkflowEvent,
    handler,
)
from opentelemetry import trace
from opentelemetry.trace import Tracer

from maf_outcome_economics.agents import PromptProfile, ReviewAgent, TriageAgent
from maf_outcome_economics.domain import (
    ReviewResult,
    TicketWorkflowInput,
    TicketWorkflowResult,
    TicketWorkflowState,
    TriageResult,
    WorkflowVariant,
)
from maf_outcome_economics.persistence import OutcomeRepository
from maf_outcome_economics.verification import verify_routing_outcome

LOW_CONFIDENCE_THRESHOLD = 0.8
SENSITIVE_TERMS = frozenset(
    {"credential", "password", "payment", "privacy", "security", "sensitive"}
)


def _prompt_profile(variant: WorkflowVariant) -> PromptProfile:
    return PromptProfile(variant.value)


def _requires_optimized_review(state: TicketWorkflowState) -> tuple[bool, str]:
    triage = state.triage
    if triage is None:
        raise ValueError("Triage must complete before review routing")
    ticket_text = f"{state.request.ticket.subject} {state.request.ticket.description}".lower()
    if triage.confidence < LOW_CONFIDENCE_THRESHOLD:
        return True, "low-confidence"
    if state.request.sensitive or any(term in ticket_text for term in SENSITIVE_TERMS):
        return True, "sensitive"
    if triage.priority == "P1" or "critical" in triage.category.lower():
        return True, "critical"
    return False, "high-confidence non-sensitive non-critical ticket"


class TicketInputExecutor(Executor):
    """Persist the ticket and initialize its traced run state."""

    def __init__(self, repository: OutcomeRepository) -> None:
        super().__init__(id="ticket-input")
        self.repository = repository

    @handler
    async def handle(
        self,
        request: TicketWorkflowInput,
        ctx: WorkflowContext[TicketWorkflowState],
    ) -> None:
        """Create the run using the active ticket span identity."""
        span_context = trace.get_current_span().get_span_context()
        if not span_context.is_valid:
            raise RuntimeError("Ticket workflow requires an active tokenomics.ticket span")
        trace_id = format(span_context.trace_id, "032x")
        run_id = f"run-{uuid4()}"
        self.repository.save_ticket(request.ticket)
        self.repository.create_run(
            run_id,
            request.ticket.id,
            request.variant,
            trace_id=trace_id,
            business_task_id=request.business_task_id,
        )
        await ctx.send_message(
            TicketWorkflowState(request=request, run_id=run_id, trace_id=trace_id)
        )


class TriageAgentExecutor(Executor):
    """Invoke the triage agent exactly once for a ticket."""

    def __init__(self, triage_agent: TriageAgent) -> None:
        super().__init__(id="triage-agent")
        self.triage_agent = triage_agent

    @handler
    async def handle(
        self,
        state: TicketWorkflowState,
        ctx: WorkflowContext[TicketWorkflowState],
    ) -> None:
        """Attach typed triage output to workflow state."""
        triage = await self.triage_agent.run(
            state.request.ticket,
            state.run_id,
            _prompt_profile(state.request.variant),
        )
        await ctx.send_message(state.model_copy(update={"triage": triage}))


class ReviewAgentExecutor(Executor):
    """Invoke or deterministically skip ticket review."""

    def __init__(self, review_agent: ReviewAgent) -> None:
        super().__init__(id="review-agent")
        self.review_agent = review_agent

    @handler
    async def handle(
        self,
        state: TicketWorkflowState,
        ctx: WorkflowContext[TicketWorkflowState],
    ) -> None:
        """Review all baseline tickets and only risky optimized tickets."""
        if state.triage is None:
            raise ValueError("Triage result is required before review")
        invoke_review = state.request.variant is WorkflowVariant.BASELINE
        reason = "baseline always reviews"
        if not invoke_review:
            invoke_review, reason = _requires_optimized_review(state)
        if not invoke_review:
            await ctx.send_message(
                state.model_copy(
                    update={
                        "review_invoked": False,
                        "review_skip_reason": reason,
                    }
                )
            )
            return
        review = await self.review_agent.run(
            state.request.ticket,
            state.triage,
            _prompt_profile(state.request.variant),
        )
        await ctx.send_message(
            state.model_copy(
                update={
                    "review": review,
                    "review_invoked": True,
                    "review_skip_reason": None,
                }
            )
        )


class OutcomeVerifierExecutor(Executor):
    """Verify final routing labels against fictional gold labels."""

    def __init__(self, repository: OutcomeRepository) -> None:
        super().__init__(id="outcome-verifier")
        self.repository = repository

    @handler
    async def handle(
        self,
        state: TicketWorkflowState,
        ctx: WorkflowContext[TicketWorkflowState],
    ) -> None:
        """Persist deterministic ticket outcome verification."""
        if state.triage is None:
            raise ValueError("Triage result is required before verification")
        category, priority, resolver_group = self._effective_labels(
            state.triage,
            state.review,
        )
        ticket = state.request.ticket
        verification = verify_routing_outcome(
            verification_id=f"verification-{state.run_id}",
            contract_id=state.request.contract_id,
            run_id=state.run_id,
            ticket=ticket,
            final_category=category,
            final_priority=priority,
            final_resolver_group=resolver_group,
        )
        self.repository.save_verification(verification)
        await ctx.send_message(state.model_copy(update={"verification": verification}))

    @staticmethod
    def _effective_labels(
        triage: TriageResult,
        review: ReviewResult | None,
    ) -> tuple[str, str, str]:
        if review is None or review.approved:
            return triage.category, triage.priority, triage.resolver_group
        return (
            review.corrected_category or triage.category,
            review.corrected_priority or triage.priority,
            review.corrected_resolver_group or triage.resolver_group,
        )


class ResultExecutor(Executor):
    """Persist and yield the final typed workflow result."""

    def __init__(self, repository: OutcomeRepository) -> None:
        super().__init__(id="result")
        self.repository = repository

    @handler
    async def handle(
        self,
        state: TicketWorkflowState,
        ctx: WorkflowContext[Never, TicketWorkflowResult],
    ) -> None:
        """Complete the run and emit its terminal result."""
        if state.triage is None or state.verification is None:
            raise ValueError("Triage and verification are required for a final result")
        self.repository.complete_run(state.run_id, state.triage, state.review)
        await ctx.yield_output(
            TicketWorkflowResult(
                business_task_id=state.request.business_task_id,
                batch_id=state.request.batch_id,
                contract_id=state.request.contract_id,
                variant=state.request.variant,
                run_id=state.run_id,
                trace_id=state.trace_id,
                triage=state.triage,
                review=state.review,
                review_invoked=state.review_invoked,
                review_skip_reason=state.review_skip_reason,
                verification=state.verification,
            )
        )


def create_ticket_workflow(
    repository: OutcomeRepository,
    triage_agent: TriageAgent,
    review_agent: ReviewAgent,
) -> Workflow:
    """Build a fresh sequential workflow for one ticket run."""
    executors = [
        TicketInputExecutor(repository),
        TriageAgentExecutor(triage_agent),
        ReviewAgentExecutor(review_agent),
        OutcomeVerifierExecutor(repository),
        ResultExecutor(repository),
    ]
    return (
        WorkflowBuilder(
            start_executor=executors[0],
            name="tokenomics-ticket-v1",
            output_from=[executors[-1]],
        )
        .add_chain(executors)
        .build()
    )


async def stream_ticket_workflow(
    request: TicketWorkflowInput,
    repository: OutcomeRepository,
    triage_agent: TriageAgent,
    review_agent: ReviewAgent,
    *,
    tracer: Tracer | None = None,
) -> AsyncIterator[WorkflowEvent[object]]:
    """Stream workflow events under one business-context parent span."""
    ticket_tracer = tracer or trace.get_tracer("maf-outcome-economics.ticket-workflow")
    with ticket_tracer.start_as_current_span(
        "tokenomics.ticket",
        attributes={
            "business_task_id": request.business_task_id,
            "batch_id": request.batch_id,
            "contract_id": request.contract_id,
            "variant": request.variant.value,
        },
    ) as ticket_span:
        workflow = create_ticket_workflow(repository, triage_agent, review_agent)
        async for event in workflow.run(request, stream=True):
            if event.type == "output" and isinstance(event.data, TicketWorkflowResult):
                verification = event.data.verification
                ticket_span.set_attributes(
                    {
                        "tokenomics.verification.accepted": verification.accepted,
                        "tokenomics.verification.correction_required": (
                            verification.correction_required
                        ),
                        "tokenomics.verification.quality_score": float(
                            verification.quality_score
                        ),
                        "tokenomics.verification.critical_priority_expected": (
                            verification.critical_priority_expected
                        ),
                    }
                )
                if verification.critical_priority_recalled is not None:
                    ticket_span.set_attribute(
                        "tokenomics.verification.critical_priority_recalled",
                        verification.critical_priority_recalled,
                    )
            yield event