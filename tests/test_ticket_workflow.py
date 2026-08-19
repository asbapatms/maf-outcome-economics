"""Mocked tests for the sequential ticket workflow."""

import asyncio
from decimal import Decimal

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from maf_outcome_economics.agents import ReviewAgent, TriageAgent
from maf_outcome_economics.domain import (
    OutcomeContract,
    OutcomeStatus,
    ReviewResult,
    Ticket,
    TicketWorkflowInput,
    TicketWorkflowResult,
    TriageResult,
    Variant,
    WorkflowVariant,
)
from maf_outcome_economics.persistence import OutcomeRepository
from maf_outcome_economics.workflows import stream_ticket_workflow


def _ticket() -> Ticket:
    return Ticket(
        id="TKT-WORKFLOW",
        subject="Routine analytics export issue",
        description="A fictional analyst cannot export one report.",
        gold_category="Application",
        gold_priority="P3",
        gold_resolver_group="Business Applications",
    )


def _triage(
    *,
    confidence: float = 0.95,
    priority: str = "P3",
    category: str = "Application",
) -> TriageResult:
    return TriageResult(
        run_id="placeholder",
        ticket_id="TKT-WORKFLOW",
        category=category,
        priority=priority,
        resolver_group="Business Applications",
        confidence=confidence,
        rationale="The fictional issue affects one analytics export.",
    )


def _review(run_id: str) -> ReviewResult:
    return ReviewResult(
        run_id=run_id,
        ticket_id="TKT-WORKFLOW",
        approved=True,
        notes="Routing is consistent with the fictional ticket.",
    )


def _repository(tmp_path) -> OutcomeRepository:
    repository = OutcomeRepository(tmp_path / "workflow.db")
    repository.save_outcome_contract(
        OutcomeContract(
            id="contract-routing",
            name="Routing accuracy",
            description="Verify fictional ticket routing labels.",
            variant=Variant.TREATMENT,
            status=OutcomeStatus.ACTIVE,
            metric_name="routing_accuracy",
            target_value=Decimal("1"),
            unit="ratio",
            measurement_window_days=1,
            minimum_acceptance_rate=Decimal("1"),
            minimum_quality_score=Decimal("1"),
            minimum_critical_priority_recall=Decimal("1"),
            maximum_cost_per_accepted_outcome=Decimal("1"),
        )
    )
    return repository


def _agents(mocker, triage: TriageResult):
    triage_agent = mocker.MagicMock(spec=TriageAgent)
    review_agent = mocker.MagicMock(spec=ReviewAgent)

    async def run_triage(ticket, run_id, profile):
        del ticket, profile
        return triage.model_copy(update={"run_id": run_id})

    async def run_review(ticket, triage_result, profile):
        del ticket, profile
        return _review(triage_result.run_id)

    triage_agent.run = mocker.AsyncMock(side_effect=run_triage)
    review_agent.run = mocker.AsyncMock(side_effect=run_review)
    return triage_agent, review_agent


async def _stream(
    request: TicketWorkflowInput,
    repository: OutcomeRepository,
    triage_agent: TriageAgent,
    review_agent: ReviewAgent,
):
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    events = [
        event
        async for event in stream_ticket_workflow(
            request,
            repository,
            triage_agent,
            review_agent,
            tracer=provider.get_tracer("ticket-workflow-tests"),
        )
    ]
    return events, exporter.get_finished_spans()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (RuntimeError("agent failed"), "failed"),
        (asyncio.CancelledError(), "interrupted"),
    ],
)
async def test_given_execution_terminates_when_streamed_then_run_is_terminal(
    tmp_path,
    mocker,
    error: BaseException,
    expected_status: str,
) -> None:
    # Arrange
    repository = _repository(tmp_path)
    triage_agent, review_agent = _agents(mocker, _triage())
    triage_agent.run.side_effect = error
    request = TicketWorkflowInput(
        ticket=_ticket(),
        business_task_id="task-terminated",
        batch_id="batch-terminated",
        contract_id="contract-routing",
        variant=WorkflowVariant.BASELINE,
    )

    # Act and assert
    with pytest.raises(type(error)):
        await _stream(request, repository, triage_agent, review_agent)

    runs = repository.list_runs()
    assert len(runs) == 1
    assert runs[0]["status"] == expected_status
    assert runs[0]["completed_at"] is not None


@pytest.mark.asyncio
async def test_given_baseline_when_streamed_then_both_agents_run_and_result_is_typed(
    tmp_path,
    mocker,
) -> None:
    # Arrange
    repository = _repository(tmp_path)
    triage_agent, review_agent = _agents(mocker, _triage())
    request = TicketWorkflowInput(
        ticket=_ticket(),
        business_task_id="task-001",
        batch_id="batch-001",
        contract_id="contract-routing",
        variant=WorkflowVariant.BASELINE,
    )

    # Act
    events, spans = await _stream(request, repository, triage_agent, review_agent)
    output = next(event.data for event in events if event.type == "output")

    # Assert
    assert isinstance(output, TicketWorkflowResult)
    assert output.review_invoked is True
    assert output.verification.accepted is True
    assert output.verification.correction_required is False
    triage_agent.run.assert_awaited_once()
    review_agent.run.assert_awaited_once()
    persisted = repository.get_run(output.run_id)
    assert persisted is not None
    assert persisted["trace_id"] == output.trace_id
    assert repository.list_verifications("contract-routing") == [output.verification]
    parent = next(span for span in spans if span.name == "tokenomics.ticket")
    assert parent.attributes is not None
    assert parent.attributes["business_task_id"] == "task-001"
    assert parent.attributes["batch_id"] == "batch-001"
    assert parent.attributes["contract_id"] == "contract-routing"
    assert parent.attributes["variant"] == "baseline"
    assert parent.attributes["tokenomics.verification.accepted"] is True
    assert parent.attributes["tokenomics.verification.correction_required"] is False
    assert parent.attributes["tokenomics.verification.quality_score"] == 1.0
    assert request.ticket.subject not in parent.attributes.values()
    assert request.ticket.description not in parent.attributes.values()


@pytest.mark.asyncio
async def test_given_review_approves_wrong_labels_when_verified_then_gold_labels_reject(
    tmp_path,
    mocker,
) -> None:
    # Arrange
    repository = _repository(tmp_path)
    triage_agent, review_agent = _agents(
        mocker,
        _triage(category="Network"),
    )
    request = TicketWorkflowInput(
        ticket=_ticket(),
        business_task_id="task-wrong-labels",
        batch_id="batch-001",
        contract_id="contract-routing",
        variant=WorkflowVariant.BASELINE,
    )

    # Act
    events, spans = await _stream(request, repository, triage_agent, review_agent)
    output = next(event.data for event in events if event.type == "output")

    # Assert
    assert isinstance(output, TicketWorkflowResult)
    assert output.review is not None
    assert output.review.approved is True
    assert output.verification.category_correct is False
    assert output.verification.accepted is False
    assert output.verification.correction_required is True
    parent = next(span for span in spans if span.name == "tokenomics.ticket")
    assert parent.attributes is not None
    assert parent.attributes["tokenomics.verification.accepted"] is False


@pytest.mark.asyncio
async def test_given_optimized_routine_ticket_when_streamed_then_review_skips_without_call(
    tmp_path,
    mocker,
) -> None:
    # Arrange
    repository = _repository(tmp_path)
    triage_agent, review_agent = _agents(mocker, _triage())
    request = TicketWorkflowInput(
        ticket=_ticket(),
        business_task_id="task-002",
        batch_id="batch-001",
        contract_id="contract-routing",
        variant=WorkflowVariant.OPTIMIZED,
    )

    # Act
    events, _ = await _stream(request, repository, triage_agent, review_agent)
    output = next(event.data for event in events if event.type == "output")

    # Assert
    assert isinstance(output, TicketWorkflowResult)
    assert output.review_invoked is False
    assert output.review is None
    assert output.review_skip_reason == "high-confidence non-sensitive non-critical ticket"
    review_agent.run.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("confidence", "priority", "category", "sensitive"),
    [
        (0.79, "P3", "Application", False),
        (0.95, "P3", "Application", True),
        (0.95, "P1", "Application", False),
        (0.95, "P3", "Critical Incident", False),
    ],
)
async def test_given_optimized_review_trigger_when_streamed_then_review_agent_runs(
    tmp_path,
    mocker,
    confidence: float,
    priority: str,
    category: str,
    sensitive: bool,
) -> None:
    # Arrange
    repository = _repository(tmp_path)
    triage_agent, review_agent = _agents(
        mocker,
        _triage(confidence=confidence, priority=priority, category=category),
    )
    request = TicketWorkflowInput(
        ticket=_ticket(),
        business_task_id="task-trigger",
        batch_id="batch-001",
        contract_id="contract-routing",
        variant=WorkflowVariant.OPTIMIZED,
        sensitive=sensitive,
    )

    # Act
    events, _ = await _stream(request, repository, triage_agent, review_agent)
    output = next(event.data for event in events if event.type == "output")

    # Assert
    assert isinstance(output, TicketWorkflowResult)
    assert output.review_invoked is True
    review_agent.run.assert_awaited_once()