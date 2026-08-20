"""Tests for generic control-versus-treatment economics comparison."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from maf_outcome_economics.core import (
    CostCategory,
    CostEntry,
    CostEvidenceStatus,
    EvidenceStatus,
    OutcomeVerificationSummary,
    ReportingPeriod,
    WorkUnit,
    WorkUnitVerification,
    compare_processes,
)

START_AT = datetime(2026, 8, 1, tzinfo=UTC)
PERIOD = ReportingPeriod(start_at=START_AT, end_at=START_AT + timedelta(days=31))


def _work_unit(work_unit_id: str, variant_id: str) -> WorkUnit:
    return WorkUnit(
        id=work_unit_id,
        process_variant_id=variant_id,
        started_at=START_AT,
        completed_at=START_AT + timedelta(hours=1),
    )


def _verification(work_unit_id: str, *, passed: bool) -> WorkUnitVerification:
    return WorkUnitVerification(
        work_unit_id=work_unit_id,
        passed=passed,
        success_rules_passed=passed,
        quality_gates_passed=True,
        evaluations=[],
    )


def _cost(
    entry_id: str,
    variant_id: str,
    amount: str,
    *,
    category: CostCategory = CostCategory.HUMAN_PROCESSING,
    currency: str = "USD",
) -> CostEntry:
    return CostEntry(
        id=entry_id,
        process_variant_id=variant_id,
        category=category,
        amount=Decimal(amount),
        currency=currency,
        source="test-costs",
        status=CostEvidenceStatus.MEASURED,
        incurred_at=START_AT,
    )


def _verification_summary(
    results: list[WorkUnitVerification],
    *,
    minimum_sample_size: int = 2,
) -> OutcomeVerificationSummary:
    return OutcomeVerificationSummary(
        contract_id="generic-outcome",
        total_work_units=len(results),
        verified_outcomes=sum(result.passed for result in results),
        minimum_sample_size=minimum_sample_size,
        minimum_sample_size_met=len(results) >= minimum_sample_size,
        results=results,
    )


def test_given_control_and_treatment_when_compared_then_normalizes_success_volume() -> None:
    # Arrange
    work_units = [
        _work_unit("control-1", "manual-support-v1"),
        _work_unit("control-2", "manual-support-v1"),
        _work_unit("treatment-1", "support-agent-v2"),
        _work_unit("treatment-2", "support-agent-v2"),
        _work_unit("treatment-3", "support-agent-v2"),
    ]
    verification = _verification_summary(
        [
            _verification("control-1", passed=True),
            _verification("control-2", passed=True),
            _verification("treatment-1", passed=True),
            _verification("treatment-2", passed=True),
            _verification("treatment-3", passed=False),
        ]
    )
    costs = [
        _cost("control-labor", "manual-support-v1", "20"),
        _cost("treatment-platform", "support-agent-v2", "3", category=CostCategory.PLATFORM),
        _cost("treatment-model", "support-agent-v2", "5", category=CostCategory.MODEL),
    ]

    # Act
    comparison = compare_processes(
        control_variant_id="manual-support-v1",
        treatment_variant_id="support-agent-v2",
        period=PERIOD,
        work_units=work_units,
        verification=verification,
        cost_entries=costs,
    )

    # Assert
    assert comparison.control.cost_per_verified_outcome == Decimal("10")
    assert comparison.treatment.cost_per_verified_outcome == Decimal("4")
    assert comparison.control_unit_cost == Decimal("10")
    assert comparison.comparable_control_cost == Decimal("20")
    assert comparison.net_savings == Decimal("12")
    assert comparison.treatment.cost_breakdown[CostCategory.MODEL] == Decimal("5")
    assert comparison.control.evidence_status is EvidenceStatus.SUFFICIENT
    assert comparison.treatment.evidence_status is EvidenceStatus.SUFFICIENT
    assert comparison.currency == "USD"


def test_given_incomplete_variant_evidence_when_compared_then_marks_insufficient() -> None:
    # Arrange
    work_units = [
        _work_unit("control-1", "control-v1"),
        _work_unit("control-2", "control-v1"),
        _work_unit("treatment-1", "treatment-v1"),
        _work_unit("treatment-2", "treatment-v1"),
    ]
    verification = _verification_summary(
        [
            _verification("control-1", passed=True),
            _verification("control-2", passed=True),
            _verification("treatment-1", passed=True),
        ]
    )

    # Act
    comparison = compare_processes(
        control_variant_id="control-v1",
        treatment_variant_id="treatment-v1",
        period=PERIOD,
        work_units=work_units,
        verification=verification,
        cost_entries=[],
    )

    # Assert
    assert comparison.control.evidence_status is EvidenceStatus.SUFFICIENT
    assert comparison.treatment.evidence_status is EvidenceStatus.INSUFFICIENT


def test_given_no_control_verified_outcomes_when_compared_then_savings_are_undefined() -> None:
    # Arrange
    work_units = [
        _work_unit("control-1", "control-v1"),
        _work_unit("treatment-1", "treatment-v1"),
    ]
    verification = _verification_summary(
        [
            _verification("control-1", passed=False),
            _verification("treatment-1", passed=True),
        ],
        minimum_sample_size=1,
    )

    # Act
    comparison = compare_processes(
        control_variant_id="control-v1",
        treatment_variant_id="treatment-v1",
        period=PERIOD,
        work_units=work_units,
        verification=verification,
        cost_entries=[_cost("control", "control-v1", "10")],
    )

    # Assert
    assert comparison.control_unit_cost is None
    assert comparison.comparable_control_cost is None
    assert comparison.net_savings is None


def test_given_different_currencies_when_compared_then_raises() -> None:
    # Arrange
    work_units = [
        _work_unit("control-1", "control-v1"),
        _work_unit("treatment-1", "treatment-v1"),
    ]
    verification = _verification_summary(
        [
            _verification("control-1", passed=True),
            _verification("treatment-1", passed=True),
        ],
        minimum_sample_size=1,
    )
    costs = [
        _cost("control", "control-v1", "10", currency="USD"),
        _cost("treatment", "treatment-v1", "8", currency="EUR"),
    ]

    # Act and Assert
    with pytest.raises(ValueError, match="one currency"):
        compare_processes(
            control_variant_id="control-v1",
            treatment_variant_id="treatment-v1",
            period=PERIOD,
            work_units=work_units,
            verification=verification,
            cost_entries=costs,
        )