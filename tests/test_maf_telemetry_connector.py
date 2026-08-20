"""Tests for generic costs normalized from persisted MAF telemetry."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from maf_outcome_economics.connectors import (
    MAFTelemetryCostConnector,
    MAFTelemetryTokenConnector,
)
from maf_outcome_economics.core import (
    CostEvidenceStatus,
    ReportingPeriod,
    TokenPurpose,
)
from maf_outcome_economics.domain import (
    PricingRecord,
    Ticket,
    TriageResult,
    WorkflowVariant,
)
from maf_outcome_economics.persistence import OutcomeRepository


async def test_given_maf_chat_usage_when_loaded_then_generic_cost_is_returned(
    tmp_path,
) -> None:
    # Arrange
    timestamp = datetime(2026, 8, 20, tzinfo=UTC)
    repository = OutcomeRepository(tmp_path / "telemetry.db")
    repository.save_ticket(
        Ticket(
            id="TKT-001",
            subject="Fictional ticket",
            description="Generic telemetry connector test.",
            gold_category="Application",
            gold_priority="P3",
            gold_resolver_group="Business Applications",
        )
    )
    repository.create_run(
        "run-1",
        "TKT-001",
        WorkflowVariant.OPTIMIZED,
        started_at=timestamp,
        business_task_id="optimized:TKT-001",
    )
    repository.save_rehearsal_model_call(
        usage_id="usage-1",
        run_id="run-1",
        provider="azure.ai.openai",
        model="deployment-v1",
        agent_id="triage",
        agent_name="TriageAgent",
        input_tokens=100_000,
        output_tokens=10_000,
        recorded_at=timestamp,
    )
    connector = MAFTelemetryCostConnector(
        repository,
        [
            PricingRecord(
                id="pricing-1",
                provider="azure.ai.openai",
                model="deployment-v1",
                input_cost_per_million_tokens=Decimal("2"),
                output_cost_per_million_tokens=Decimal("8"),
            )
        ],
        {WorkflowVariant.OPTIMIZED.value: "ticket-optimized-v1"},
    )

    # Act
    costs = await connector.load_costs(
        ReportingPeriod(
            start_at=timestamp - timedelta(minutes=1),
            end_at=timestamp + timedelta(minutes=1),
        )
    )

    # Assert
    assert len(costs) == 1
    assert costs[0].amount == Decimal("0.28")
    assert costs[0].process_variant_id == "ticket-optimized-v1"
    assert costs[0].work_unit_id == "run-1"
    assert costs[0].status is CostEvidenceStatus.ESTIMATED
    assert costs[0].source == "maf-opentelemetry"


async def test_given_maf_agents_when_loaded_then_tokens_have_business_purpose(
    tmp_path,
) -> None:
    # Arrange
    timestamp = datetime(2026, 8, 20, tzinfo=UTC)
    repository = OutcomeRepository(tmp_path / "tokens.db")
    repository.save_ticket(
        Ticket(
            id="TKT-001",
            subject="Fictional ticket",
            description="Generic token connector test.",
            gold_category="Application",
            gold_priority="P3",
            gold_resolver_group="Business Applications",
        )
    )
    repository.create_run(
        "run-1",
        "TKT-001",
        WorkflowVariant.BASELINE,
        started_at=timestamp,
        business_task_id="baseline:TKT-001",
    )
    repository.complete_run(
        "run-1",
        TriageResult(
            run_id="run-1",
            ticket_id="TKT-001",
            category="Application",
            priority="P3",
            resolver_group="Business Applications",
            confidence=0.95,
            rationale="Matched fictional labels.",
        ),
        None,
        completed_at=timestamp,
    )
    for index, agent_id in enumerate(("triage", "review", "review")):
        repository.save_rehearsal_model_call(
            usage_id=f"usage-{index}",
            run_id="run-1",
            provider="azure.ai.openai",
            model="deployment-v1",
            agent_id=agent_id,
            agent_name=f"{agent_id.title()}Agent",
            input_tokens=100,
            output_tokens=20,
            recorded_at=timestamp + timedelta(seconds=index),
        )
    connector = MAFTelemetryTokenConnector(
        repository,
        {WorkflowVariant.BASELINE.value: "ticket-baseline-v1"},
    )

    # Act
    tokens = await connector.load_tokens(
        ReportingPeriod(
            start_at=timestamp - timedelta(minutes=1),
            end_at=timestamp + timedelta(minutes=1),
        )
    )

    # Assert
    assert [entry.purpose for entry in tokens] == [
        TokenPurpose.PRIMARY_WORK,
        TokenPurpose.REVIEW,
        TokenPurpose.RETRY,
    ]
    assert sum(entry.total_tokens for entry in tokens) == 360