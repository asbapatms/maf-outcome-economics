"""Tests for framework-neutral connector contracts."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from maf_outcome_economics.connectors import (
    CostSource,
    EvidenceSource,
    TokenSource,
    WorkUnitSource,
)
from maf_outcome_economics.core import (
    CostCategory,
    CostEntry,
    CostEvidenceStatus,
    EvidenceRecord,
    ReportingPeriod,
    TokenEntry,
    TokenPurpose,
    WorkUnit,
)


class InMemoryConnector:
    """Test connector that returns already-normalized core records."""

    def __init__(
        self,
        work_units: list[WorkUnit],
        evidence: list[EvidenceRecord],
        costs: list[CostEntry],
        tokens: list[TokenEntry],
    ) -> None:
        self._work_units = work_units
        self._evidence = evidence
        self._costs = costs
        self._tokens = tokens

    async def load_work_units(self, period: ReportingPeriod) -> list[WorkUnit]:
        """Return normalized work units."""
        return self._work_units

    async def load_evidence(self, period: ReportingPeriod) -> list[EvidenceRecord]:
        """Return normalized evidence."""
        return self._evidence

    async def load_costs(self, period: ReportingPeriod) -> list[CostEntry]:
        """Return normalized costs."""
        return self._costs

    async def load_tokens(self, period: ReportingPeriod) -> list[TokenEntry]:
        """Return normalized tokens."""
        return self._tokens


async def load_all(
    work_source: WorkUnitSource,
    evidence_source: EvidenceSource,
    cost_source: CostSource,
    token_source: TokenSource,
    period: ReportingPeriod,
) -> tuple[list[WorkUnit], list[EvidenceRecord], list[CostEntry], list[TokenEntry]]:
    """Exercise structural conformance to all connector protocols."""
    return (
        await work_source.load_work_units(period),
        await evidence_source.load_evidence(period),
        await cost_source.load_costs(period),
        await token_source.load_tokens(period),
    )


@pytest.mark.asyncio
async def test_given_connector_when_loaded_then_returns_normalized_core_records() -> None:
    # Arrange
    start_at = datetime(2026, 8, 1, tzinfo=UTC)
    end_at = start_at + timedelta(days=31)
    period = ReportingPeriod(start_at=start_at, end_at=end_at)
    work_unit = WorkUnit(
        id="invoice-001",
        process_variant_id="invoice-agent-v1",
        started_at=start_at,
    )
    evidence = EvidenceRecord(
        id="evidence-001",
        work_unit_id=work_unit.id,
        metric="invoice.approved",
        value=True,
        source="finance-system",
        observed_at=start_at,
    )
    cost = CostEntry(
        id="cost-001",
        process_variant_id=work_unit.process_variant_id,
        work_unit_id=work_unit.id,
        category=CostCategory.PLATFORM,
        amount=Decimal("0.02"),
        currency="USD",
        source="cost-export",
        status=CostEvidenceStatus.RECONCILED,
        incurred_at=start_at,
    )
    token = TokenEntry(
        id="token-001",
        process_variant_id=work_unit.process_variant_id,
        work_unit_id=work_unit.id,
        agent_id="extractor",
        input_tokens=100,
        output_tokens=20,
        purpose=TokenPurpose.PRIMARY_WORK,
        source="model-telemetry",
        trace_id="trace-001",
        span_id="span-001",
        observed_at=start_at,
    )
    connector = InMemoryConnector([work_unit], [evidence], [cost], [token])

    # Act
    work_units, evidence_records, costs, tokens = await load_all(
        connector,
        connector,
        connector,
        connector,
        period,
    )

    # Assert
    assert work_units == [work_unit]
    assert evidence_records == [evidence]
    assert costs == [cost]
    assert tokens == [token]


@pytest.mark.parametrize(
    ("start_offset", "end_offset"),
    [(timedelta(), timedelta()), (timedelta(days=1), timedelta())],
)
def test_given_nonpositive_reporting_window_when_validated_then_rejects_period(
    start_offset: timedelta,
    end_offset: timedelta,
) -> None:
    # Arrange
    timestamp = datetime(2026, 8, 1, tzinfo=UTC)

    # Act and Assert
    with pytest.raises(ValidationError, match="end_at must be later than start_at"):
        ReportingPeriod(
            start_at=timestamp + start_offset,
            end_at=timestamp + end_offset,
        )