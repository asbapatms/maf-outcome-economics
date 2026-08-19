"""Tests for domain model validation."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from maf_outcome_economics.domain import (
    EconomicsMetrics,
    GovernanceAction,
    GovernanceDecision,
    OutcomeContract,
    OutcomeStatus,
    PricingRecord,
    ReviewResult,
    Ticket,
    TriageResult,
    Variant,
    VerificationResult,
)


def test_requested_models_accept_valid_records() -> None:
    timestamp = datetime(2026, 8, 19, tzinfo=UTC)
    ticket = Ticket(
        id="TKT-001",
        subject="Fictional issue",
        description="A fictional support issue.",
        gold_category="Application",
        gold_priority="P2",
        gold_resolver_group="Application Support",
        created_at=timestamp,
    )
    triage = TriageResult(
        run_id="RUN-001",
        ticket_id=ticket.id,
        category="Application",
        priority="P2",
        resolver_group="Application Support",
        confidence=0.95,
        rationale="The issue concerns application behavior.",
        created_at=timestamp,
    )
    review = ReviewResult(
        run_id="RUN-001",
        ticket_id=ticket.id,
        approved=True,
        created_at=timestamp,
    )
    contract = OutcomeContract(
        id="CONTRACT-001",
        name="Routing accuracy",
        description="Measure correct fictional ticket routing.",
        variant=Variant.TREATMENT,
        status=OutcomeStatus.ACTIVE,
        metric_name="accuracy",
        target_value=Decimal("0.90"),
        unit="ratio",
        measurement_window_days=30,
        minimum_acceptance_rate=Decimal("0.90"),
        minimum_quality_score=Decimal("0.90"),
        minimum_critical_priority_recall=Decimal("1"),
        maximum_cost_per_accepted_outcome=Decimal("1"),
        created_at=timestamp,
    )
    verification = VerificationResult(
        id="VERIFY-001",
        contract_id=contract.id,
        run_id="RUN-001",
        passed=True,
        observed_value=Decimal("0.95"),
        evidence_count=20,
        reason="The illustrative target was met.",
        verified_at=timestamp,
    )
    pricing = PricingRecord(
        id="PRICE-001",
        provider="illustrative-provider",
        model="illustrative-model",
        input_cost_per_million_tokens=Decimal("2.50"),
        output_cost_per_million_tokens=Decimal("10.00"),
        effective_at=timestamp,
    )
    economics = EconomicsMetrics(
        run_id="RUN-001",
        pricing_id=pricing.id,
        input_tokens=100,
        output_tokens=50,
        estimated_input_cost=Decimal("0.00025"),
        estimated_output_cost=Decimal("0.00050"),
        estimated_total_cost=Decimal("0.00075"),
        calculated_at=timestamp,
    )
    decision = GovernanceDecision(
        id="DECISION-001",
        contract_id=contract.id,
        action=GovernanceAction.APPROVE,
        reason="The verified outcome meets the illustrative threshold.",
        decided_by="governance-test",
        decided_at=timestamp,
    )

    assert triage.ticket_id == review.ticket_id
    assert verification.contract_id == decision.contract_id
    assert pricing.illustrative is True
    assert economics.monetary_values_are_estimated is True


@pytest.mark.parametrize("priority", ["high", "P0", "P5"])
def test_ticket_rejects_invalid_gold_priority(priority: str) -> None:
    with pytest.raises(ValidationError):
        Ticket(
            id="TKT-INVALID",
            subject="Invalid priority",
            description="A fictional invalid record.",
            gold_category="Application",
            gold_priority=priority,
            gold_resolver_group="Application Support",
        )


def test_pricing_rejects_negative_or_nonillustrative_values() -> None:
    with pytest.raises(ValidationError):
        PricingRecord(
            id="PRICE-INVALID",
            provider="provider",
            model="model",
            input_cost_per_million_tokens=Decimal("-1"),
            output_cost_per_million_tokens=Decimal("1"),
        )

    with pytest.raises(ValidationError):
        PricingRecord.model_validate(
            {
                "id": "PRICE-INVALID",
                "provider": "provider",
                "model": "model",
                "input_cost_per_million_tokens": "1",
                "output_cost_per_million_tokens": "1",
                "illustrative": False,
            }
        )


def test_economics_metrics_cannot_remove_estimate_label() -> None:
    with pytest.raises(ValidationError):
        EconomicsMetrics.model_validate(
            {
                "run_id": "RUN-001",
                "pricing_id": "PRICE-001",
                "input_tokens": 10,
                "output_tokens": 5,
                "estimated_input_cost": "0.01",
                "estimated_output_cost": "0.02",
                "estimated_total_cost": "0.03",
                "monetary_values_are_estimated": False,
            }
        )