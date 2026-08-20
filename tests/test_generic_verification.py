"""Tests for domain-independent outcome verification."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from maf_outcome_economics.core import (
    EvidenceOperator,
    EvidenceRecord,
    EvidenceRule,
    OutcomeContract,
    OutcomeVerifier,
    WorkUnit,
)

TIMESTAMP = datetime(2026, 8, 20, tzinfo=UTC)


def _work_unit(work_unit_id: str, *, variant_id: str) -> WorkUnit:
    return WorkUnit(
        id=work_unit_id,
        process_variant_id=variant_id,
        started_at=TIMESTAMP,
    )


def _evidence(
    work_unit_id: str,
    metric: str,
    value: bool | float,
    *,
    evidence_id: str | None = None,
    seconds: int = 0,
) -> EvidenceRecord:
    return EvidenceRecord(
        id=evidence_id or f"{work_unit_id}-{metric}",
        work_unit_id=work_unit_id,
        metric=metric,
        value=value,
        source="business-system",
        observed_at=TIMESTAMP + timedelta(seconds=seconds),
    )


def test_given_support_contract_when_verified_then_uses_generic_rules() -> None:
    # Arrange
    contract = OutcomeContract(
        id="support-outcome",
        name="Resolved support request",
        success_rules=[
            EvidenceRule(
                metric="routing_correct",
                operator=EvidenceOperator.EQUALS,
                expected_value=True,
            ),
            EvidenceRule(
                metric="resolved",
                operator=EvidenceOperator.EQUALS,
                expected_value=True,
            ),
            EvidenceRule(
                metric="reopened",
                operator=EvidenceOperator.EQUALS,
                expected_value=False,
            ),
        ],
        quality_gates=[],
        maximum_cost_per_verified_outcome=Decimal("5"),
        minimum_sample_size=1,
        currency="USD",
    )
    work_unit = _work_unit("ticket-001", variant_id="support-agent-v2")
    evidence = [
        _evidence(work_unit.id, "routing_correct", True),
        _evidence(work_unit.id, "resolved", True),
        _evidence(work_unit.id, "reopened", False),
    ]

    # Act
    result = OutcomeVerifier().verify(contract, [work_unit], evidence)

    # Assert
    assert result.verified_outcomes == 1
    assert result.minimum_sample_size_met is True
    assert result.results[0].passed is True


def test_given_invoice_contract_when_verified_then_uses_same_verifier() -> None:
    # Arrange
    contract = OutcomeContract(
        id="invoice-outcome",
        name="Accurate invoice processing",
        success_rules=[
            EvidenceRule(
                metric="duplicate_payment",
                operator=EvidenceOperator.EQUALS,
                expected_value=False,
            )
        ],
        quality_gates=[
            EvidenceRule(
                metric="field_accuracy",
                operator=EvidenceOperator.GREATER_THAN_OR_EQUAL,
                expected_value=0.99,
            )
        ],
        maximum_cost_per_verified_outcome=Decimal("2"),
        minimum_sample_size=1,
        currency="USD",
    )
    work_unit = _work_unit("invoice-001", variant_id="invoice-agent-v1")
    evidence = [
        _evidence(work_unit.id, "field_accuracy", 0.995),
        _evidence(work_unit.id, "duplicate_payment", False),
    ]

    # Act
    result = OutcomeVerifier().verify(contract, [work_unit], evidence)

    # Assert
    assert result.verified_outcomes == 1
    assert result.results[0].success_rules_passed is True
    assert result.results[0].quality_gates_passed is True


def test_given_latest_evidence_fails_when_verified_then_outcome_is_not_verified() -> None:
    # Arrange
    contract = OutcomeContract(
        id="support-outcome",
        name="Resolved support request",
        success_rules=[
            EvidenceRule(
                metric="reopened",
                operator=EvidenceOperator.EQUALS,
                expected_value=False,
            )
        ],
        quality_gates=[],
        maximum_cost_per_verified_outcome=Decimal("5"),
        minimum_sample_size=1,
        currency="USD",
    )
    work_unit = _work_unit("ticket-001", variant_id="support-agent-v2")
    evidence = [
        _evidence(work_unit.id, "reopened", False, evidence_id="first"),
        _evidence(
            work_unit.id,
            "reopened",
            True,
            evidence_id="latest",
            seconds=1,
        ),
    ]

    # Act
    result = OutcomeVerifier().verify(contract, [work_unit], evidence)

    # Assert
    assert result.verified_outcomes == 0
    assert result.results[0].evaluations[0].evidence_id == "latest"
    assert result.results[0].passed is False


def test_given_optional_evidence_is_missing_when_verified_then_rule_passes() -> None:
    # Arrange
    contract = OutcomeContract(
        id="invoice-outcome",
        name="Invoice processing",
        success_rules=[
            EvidenceRule(
                metric="approved",
                operator=EvidenceOperator.EQUALS,
                expected_value=True,
            ),
            EvidenceRule(
                metric="manual_note",
                operator=EvidenceOperator.NOT_EQUALS,
                expected_value=True,
                required=False,
            ),
        ],
        quality_gates=[],
        maximum_cost_per_verified_outcome=Decimal("2"),
        minimum_sample_size=2,
        currency="USD",
    )
    work_unit = _work_unit("invoice-001", variant_id="invoice-agent-v1")

    # Act
    result = OutcomeVerifier().verify(
        contract,
        [work_unit],
        [_evidence(work_unit.id, "approved", True)],
    )

    # Assert
    assert result.verified_outcomes == 1
    assert result.minimum_sample_size_met is False
    assert result.results[0].evaluations[1].evidence_found is False
    assert result.results[0].evaluations[1].passed is True