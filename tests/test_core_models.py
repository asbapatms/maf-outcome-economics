"""Tests for framework-neutral outcome economics records."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from maf_outcome_economics.core import (
    CostCategory,
    CostEntry,
    CostEvidenceStatus,
    EvidenceRecord,
    ProcessDefinition,
    ProcessVariant,
    ProcessVariantRole,
    TokenEntry,
    TokenPurpose,
    WorkUnit,
)


def test_given_generic_process_records_when_validated_then_preserves_relationship_ids() -> None:
    # Arrange
    started_at = datetime(2026, 8, 20, 9, tzinfo=UTC)
    completed_at = started_at + timedelta(minutes=4)
    process = ProcessDefinition(
        id="invoice-processing",
        name="Invoice processing",
        process_type="finance",
    )
    variant = ProcessVariant(
        id="invoice-agent-v1",
        process_id=process.id,
        role=ProcessVariantRole.TREATMENT,
        version="1.0",
    )

    # Act
    work_unit = WorkUnit(
        id="invoice-001",
        process_variant_id=variant.id,
        started_at=started_at,
        completed_at=completed_at,
        attributes={"supplier": "fictional", "page_count": 2},
    )
    evidence = EvidenceRecord(
        id="evidence-001",
        work_unit_id=work_unit.id,
        metric="fields_correct",
        value=True,
        source="accounts-payable-system",
        observed_at=completed_at,
        provenance={"record_id": "validation-001"},
    )
    cost = CostEntry(
        id="cost-001",
        process_variant_id=variant.id,
        work_unit_id=work_unit.id,
        category=CostCategory.MODEL,
        amount=Decimal("0.015"),
        currency="USD",
        source="model-telemetry",
        status=CostEvidenceStatus.ESTIMATED,
        incurred_at=started_at,
    )

    # Assert
    assert (evidence.work_unit_id, cost.work_unit_id) == (work_unit.id, work_unit.id)


def test_given_completion_before_start_when_validated_then_rejects_work_unit() -> None:
    # Arrange
    started_at = datetime(2026, 8, 20, 9, tzinfo=UTC)

    # Act and Assert
    with pytest.raises(ValidationError, match="completed_at must not be earlier"):
        WorkUnit(
            id="work-001",
            process_variant_id="variant-001",
            started_at=started_at,
            completed_at=started_at - timedelta(seconds=1),
        )


@pytest.mark.parametrize("amount", [Decimal("-0.01"), Decimal("-1")])
def test_given_negative_cost_when_validated_then_rejects_entry(amount: Decimal) -> None:
    # Act and Assert
    with pytest.raises(ValidationError):
        CostEntry(
            id="cost-invalid",
            process_variant_id="variant-001",
            category=CostCategory.PLATFORM,
            amount=amount,
            currency="USD",
            source="cost-export",
            status=CostEvidenceStatus.RECONCILED,
            incurred_at=datetime(2026, 8, 20, tzinfo=UTC),
        )


def test_given_naive_timestamp_when_validated_then_rejects_record() -> None:
    # Act and Assert
    with pytest.raises(ValidationError):
        EvidenceRecord(
            id="evidence-invalid",
            work_unit_id="work-001",
            metric="outcome.accepted",
            value=True,
            source="verifier",
            observed_at=datetime(2026, 8, 20),
        )


def test_given_unknown_field_when_validated_then_rejects_core_record() -> None:
    # Act and Assert
    with pytest.raises(ValidationError):
        ProcessDefinition.model_validate(
            {
                "id": "process-001",
                "name": "Generic process",
                "process_type": "generic",
                "ticket_type": "incident",
            }
        )


def test_given_token_observation_when_validated_then_reports_total_tokens() -> None:
    # Arrange
    observed_at = datetime(2026, 8, 20, 9, tzinfo=UTC)

    # Act
    entry = TokenEntry(
        id="token-001",
        process_variant_id="invoice-agent-v1",
        work_unit_id="invoice-001",
        agent_id="extractor",
        input_tokens=120,
        output_tokens=30,
        purpose=TokenPurpose.PRIMARY_WORK,
        source="model-telemetry",
        trace_id="trace-001",
        span_id="span-001",
        observed_at=observed_at,
    )

    # Assert
    assert entry.total_tokens == 150


@pytest.mark.parametrize(("input_tokens", "output_tokens"), [(-1, 0), (0, -1)])
def test_given_negative_token_count_when_validated_then_rejects_entry(
    input_tokens: int,
    output_tokens: int,
) -> None:
    # Act and Assert
    with pytest.raises(ValidationError):
        TokenEntry(
            id="token-invalid",
            process_variant_id="variant-001",
            work_unit_id="work-001",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            purpose=TokenPurpose.UNKNOWN,
            source="model-telemetry",
            trace_id="trace-001",
            span_id="span-001",
            observed_at=datetime(2026, 8, 20, tzinfo=UTC),
        )