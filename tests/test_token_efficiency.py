"""Tests for framework-neutral token efficiency comparison."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from maf_outcome_economics.core import (
    EvidenceOperator,
    EvidenceRecord,
    EvidenceRule,
    OutcomeContract,
    OutcomeVerifier,
    ReportingPeriod,
    ReviewOutcome,
    TokenEntry,
    TokenPurpose,
    WorkUnit,
    attribute_review_tokens,
    compare_token_efficiency,
)


def test_given_equal_outcomes_when_treatment_uses_fewer_tokens_then_improves() -> None:
    # Arrange
    timestamp = datetime(2026, 8, 20, tzinfo=UTC)
    period = ReportingPeriod(
        start_at=timestamp,
        end_at=timestamp + timedelta(hours=1),
    )
    work_units = [
        WorkUnit(
            id=f"{variant}-{index}",
            process_variant_id=variant,
            started_at=timestamp,
            completed_at=timestamp + timedelta(minutes=1),
        )
        for variant in ("control", "treatment")
        for index in range(2)
    ]
    evidence = [
        EvidenceRecord(
            id=f"evidence-{work_unit.id}",
            work_unit_id=work_unit.id,
            metric="accepted",
            value=True,
            source="verifier",
            observed_at=timestamp + timedelta(minutes=1),
        )
        for work_unit in work_units
    ]
    verification = OutcomeVerifier().verify(
        OutcomeContract(
            id="accepted-outcome",
            name="Accepted outcome",
            success_rules=[
                EvidenceRule(
                    metric="accepted",
                    operator=EvidenceOperator.EQUALS,
                    expected_value=True,
                )
            ],
            quality_gates=[],
            maximum_cost_per_verified_outcome=Decimal("1"),
            minimum_sample_size=2,
            currency="USD",
        ),
        work_units,
        evidence,
    )
    tokens = [
        TokenEntry(
            id=f"token-{work_unit.id}",
            process_variant_id=work_unit.process_variant_id,
            work_unit_id=work_unit.id,
            input_tokens=80 if work_unit.process_variant_id == "control" else 40,
            output_tokens=20,
            purpose=TokenPurpose.PRIMARY_WORK,
            source="model-telemetry",
            trace_id=f"trace-{work_unit.id}",
            span_id=f"span-{work_unit.id}",
            observed_at=timestamp + timedelta(minutes=1),
        )
        for work_unit in work_units
    ]

    # Act
    comparison = compare_token_efficiency(
        control_variant_id="control",
        treatment_variant_id="treatment",
        period=period,
        work_units=work_units,
        verification=verification,
        token_entries=tokens,
    )

    # Assert
    assert comparison.control.tokens_per_verified_outcome == Decimal(100)
    assert comparison.treatment.tokens_per_verified_outcome == Decimal(60)
    assert comparison.tokens_avoided == Decimal(80)
    assert comparison.efficiency_improvement == Decimal("0.4")


def test_given_duplicate_span_when_compared_then_tokens_are_counted_once() -> None:
    # Arrange
    timestamp = datetime(2026, 8, 20, tzinfo=UTC)
    period = ReportingPeriod(
        start_at=timestamp,
        end_at=timestamp + timedelta(hours=1),
    )
    work_units = [
        WorkUnit(
            id=variant,
            process_variant_id=variant,
            started_at=timestamp,
        )
        for variant in ("control", "treatment")
    ]
    evidence = [
        EvidenceRecord(
            id=f"evidence-{work_unit.id}",
            work_unit_id=work_unit.id,
            metric="accepted",
            value=True,
            source="verifier",
            observed_at=timestamp,
        )
        for work_unit in work_units
    ]
    verification = OutcomeVerifier().verify(
        OutcomeContract(
            id="accepted-outcome",
            name="Accepted outcome",
            success_rules=[
                EvidenceRule(
                    metric="accepted",
                    operator=EvidenceOperator.EQUALS,
                    expected_value=True,
                )
            ],
            quality_gates=[],
            maximum_cost_per_verified_outcome=Decimal("1"),
            minimum_sample_size=1,
            currency="USD",
        ),
        work_units,
        evidence,
    )
    control_token = TokenEntry(
        id="token-control",
        process_variant_id="control",
        work_unit_id="control",
        input_tokens=100,
        output_tokens=0,
        purpose=TokenPurpose.PRIMARY_WORK,
        source="model-telemetry",
        trace_id="trace-control",
        span_id="span-control",
        observed_at=timestamp,
    )
    treatment_token = control_token.model_copy(
        update={
            "id": "token-treatment",
            "process_variant_id": "treatment",
            "work_unit_id": "treatment",
            "input_tokens": 50,
            "trace_id": "trace-treatment",
            "span_id": "span-treatment",
        }
    )

    # Act
    comparison = compare_token_efficiency(
        control_variant_id="control",
        treatment_variant_id="treatment",
        period=period,
        work_units=work_units,
        verification=verification,
        token_entries=[control_token, control_token, treatment_token],
    )

    # Assert
    assert comparison.control.total_tokens == 100


def test_given_review_effects_when_attributed_then_useful_and_waste_are_separated() -> None:
    # Arrange
    timestamp = datetime(2026, 8, 20, tzinfo=UTC)
    entries = [
        TokenEntry(
            id=f"review-{index}",
            process_variant_id="treatment",
            work_unit_id=work_unit_id,
            agent_id="review",
            input_tokens=input_tokens,
            output_tokens=20,
            purpose=TokenPurpose.REVIEW,
            source="model-telemetry",
            trace_id=f"trace-{index}",
            span_id=f"span-{index}",
            observed_at=timestamp,
        )
        for index, (work_unit_id, input_tokens) in enumerate(
            (("useful", 80), ("unchanged", 30))
        )
    ]

    # Act
    attribution = attribute_review_tokens(
        entries,
        {
            "useful": ReviewOutcome.USEFUL_CORRECTION,
            "unchanged": ReviewOutcome.NON_CONTRIBUTING,
        },
    )

    # Assert
    assert attribution.useful_corrections == 1
    assert attribution.total_review_tokens == 150
    assert attribution.useful_review_tokens == 100
    assert attribution.non_contributing_review_tokens == 50
    assert attribution.review_tokens_per_useful_correction == Decimal(150)
    assert attribution.non_contributing_review_ratio == Decimal(1) / Decimal(3)