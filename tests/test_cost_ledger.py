"""Tests for generic cost aggregation and reconciliation."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from maf_outcome_economics.core import (
    CostCategory,
    CostEntry,
    CostEvidenceStatus,
    CostLedger,
    ReportingPeriod,
)

START_AT = datetime(2026, 8, 1, tzinfo=UTC)
PERIOD = ReportingPeriod(start_at=START_AT, end_at=START_AT + timedelta(days=31))


def _entry(
    entry_id: str,
    amount: str,
    *,
    category: CostCategory = CostCategory.MODEL,
    status: CostEvidenceStatus = CostEvidenceStatus.ESTIMATED,
    reconciliation_key: str | None = None,
    variant_id: str = "agent-v1",
    currency: str = "USD",
    incurred_at: datetime = START_AT,
) -> CostEntry:
    return CostEntry(
        id=entry_id,
        process_variant_id=variant_id,
        category=category,
        amount=Decimal(amount),
        currency=currency,
        source="test-source",
        status=status,
        reconciliation_key=reconciliation_key,
        incurred_at=incurred_at,
    )


def test_given_process_costs_when_summarized_then_retains_category_breakdown() -> None:
    # Arrange
    entries = [
        _entry("model", "0.20"),
        _entry("platform", "0.05", category=CostCategory.PLATFORM),
        _entry("human", "1.50", category=CostCategory.HUMAN_PROCESSING),
        _entry("review", "0.40", category=CostCategory.HUMAN_REVIEW),
        _entry("retry", "0.10", category=CostCategory.RETRY),
        _entry("other", "0.25", category=CostCategory.OTHER),
        _entry("other-variant", "99", variant_id="agent-v2"),
        _entry("outside-period", "99", incurred_at=PERIOD.end_at),
    ]

    # Act
    summary = CostLedger().summarize(
        entries,
        variant_id="agent-v1",
        period=PERIOD,
    )

    # Assert
    assert summary.category_costs[CostCategory.MODEL] == Decimal("0.20")
    assert summary.category_costs[CostCategory.PLATFORM] == Decimal("0.05")
    assert summary.category_costs[CostCategory.HUMAN_PROCESSING] == Decimal("1.50")
    assert summary.category_costs[CostCategory.HUMAN_REVIEW] == Decimal("0.40")
    assert summary.category_costs[CostCategory.RETRY] == Decimal("0.10")
    assert summary.category_costs[CostCategory.OTHER] == Decimal("0.25")
    assert summary.total_cost == Decimal("2.50")
    assert summary.currency == "USD"


def test_given_reconciled_model_cost_when_summarized_then_replaces_estimates() -> None:
    # Arrange
    entries = [
        _entry("estimate-1", "0.20", reconciliation_key="deployment-august"),
        _entry("estimate-2", "0.30", reconciliation_key="deployment-august"),
        _entry(
            "actual",
            "0.42",
            status=CostEvidenceStatus.RECONCILED,
            reconciliation_key="deployment-august",
        ),
    ]

    # Act
    summary = CostLedger().summarize(
        entries,
        variant_id="agent-v1",
        period=PERIOD,
    )

    # Assert
    assert summary.category_costs[CostCategory.MODEL] == Decimal("0.42")
    assert summary.total_cost == Decimal("0.42")
    assert summary.source_entry_count == 3
    assert summary.effective_entry_count == 1


def test_given_only_estimated_model_costs_when_summarized_then_includes_all() -> None:
    # Arrange
    entries = [
        _entry("estimate-1", "0.20", reconciliation_key="deployment-august"),
        _entry("estimate-2", "0.30", reconciliation_key="deployment-august"),
    ]

    # Act
    summary = CostLedger().summarize(
        entries,
        variant_id="agent-v1",
        period=PERIOD,
    )

    # Assert
    assert summary.total_cost == Decimal("0.50")
    assert summary.effective_entry_count == 2


def test_given_duplicate_entry_ids_when_summarized_then_counts_cost_once() -> None:
    # Arrange
    entry = _entry("duplicate", "0.20")

    # Act
    summary = CostLedger().summarize(
        [entry, entry],
        variant_id="agent-v1",
        period=PERIOD,
    )

    # Assert
    assert summary.total_cost == Decimal("0.20")
    assert summary.source_entry_count == 1


def test_given_mixed_effective_currencies_when_summarized_then_raises() -> None:
    # Arrange
    entries = [_entry("usd", "1"), _entry("eur", "1", currency="EUR")]

    # Act and Assert
    with pytest.raises(ValueError, match="one currency"):
        CostLedger().summarize(entries, variant_id="agent-v1", period=PERIOD)