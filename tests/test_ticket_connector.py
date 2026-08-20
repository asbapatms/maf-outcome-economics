"""Tests for generic ticket work and evidence normalization."""

from datetime import UTC, datetime, timedelta

from maf_outcome_economics.core import ReportingPeriod, ReviewOutcome
from maf_outcome_economics.domain import (
    ReviewResult,
    Ticket,
    TriageResult,
    WorkflowVariant,
)
from maf_outcome_economics.persistence import OutcomeRepository
from maf_outcome_economics.scenarios.ticket import (
    TICKET_VARIANT_IDS,
    TicketScenarioConnector,
    seeded_contract,
    verify_routing_outcome,
)


async def test_given_verified_ticket_run_when_loaded_then_generic_records_are_returned(
    tmp_path,
) -> None:
    # Arrange
    timestamp = datetime(2026, 8, 20, tzinfo=UTC)
    repository = OutcomeRepository(tmp_path / "ticket.db")
    ticket = Ticket(
        id="TKT-001",
        subject="Fictional ticket",
        description="Generic adapter test.",
        gold_category="Application",
        gold_priority="P1",
        gold_resolver_group="Business Applications",
    )
    repository.save_ticket(ticket)
    repository.create_run(
        "run-1",
        ticket.id,
        WorkflowVariant.OPTIMIZED,
        started_at=timestamp,
        trace_id="1" * 32,
        business_task_id="optimized:TKT-001",
    )
    repository.complete_run(
        "run-1",
        TriageResult(
            run_id="run-1",
            ticket_id=ticket.id,
            category="Access",
            priority="P1",
            resolver_group="Identity Operations",
            confidence=0.95,
            rationale="Matched fictional labels.",
        ),
        ReviewResult(
            run_id="run-1",
            ticket_id=ticket.id,
            approved=False,
            corrected_category="Application",
            corrected_priority="P1",
            corrected_resolver_group="Business Applications",
            notes="Corrected fictional routing labels.",
        ),
        completed_at=timestamp + timedelta(minutes=1),
    )
    repository.save_outcome_contract(seeded_contract(WorkflowVariant.OPTIMIZED))
    repository.save_verification(
        verify_routing_outcome(
            verification_id="verification-1",
            contract_id="contract-optimized",
            run_id="run-1",
            ticket=ticket,
            final_category="Application",
            final_priority="P1",
            final_resolver_group="Business Applications",
        )
    )
    connector = TicketScenarioConnector(repository)
    period = ReportingPeriod(
        start_at=timestamp - timedelta(minutes=1),
        end_at=timestamp + timedelta(minutes=2),
    )

    # Act
    work_units = await connector.load_work_units(period)
    evidence = await connector.load_evidence(period)
    review_outcomes = await connector.load_review_outcomes(period)

    # Assert
    assert len(work_units) == 1
    assert work_units[0].id == "run-1"
    assert work_units[0].process_variant_id == TICKET_VARIANT_IDS[WorkflowVariant.OPTIMIZED]
    assert {record.metric for record in evidence} == {
        "routing_accepted",
        "quality_score",
        "critical_priority_recalled",
    }
    assert all(record.work_unit_id == "run-1" for record in evidence)
    assert review_outcomes == {"run-1": ReviewOutcome.USEFUL_CORRECTION}