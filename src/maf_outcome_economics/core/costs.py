"""Deterministic aggregation and reconciliation of normalized process costs."""

from collections.abc import Iterable
from decimal import Decimal

from pydantic import Field, model_validator

from .models import (
    CoreModel,
    CostCategory,
    CostEntry,
    CostEvidenceStatus,
    ReportingPeriod,
)


class CostSummary(CoreModel):
    """Financial totals for one process variant and reporting period."""

    variant_id: str = Field(min_length=1)
    period: ReportingPeriod
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    category_costs: dict[CostCategory, Decimal]
    total_cost: Decimal = Field(ge=0)
    source_entry_count: int = Field(ge=0)
    effective_entry_count: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_total(self) -> "CostSummary":
        """Reject summaries whose total differs from their category amounts."""
        if self.total_cost != sum(self.category_costs.values(), start=Decimal(0)):
            raise ValueError("total_cost must equal the category cost total")
        return self


class CostLedger:
    """Summarize normalized costs without double-counting reconciled estimates."""

    def summarize(
        self,
        entries: Iterable[CostEntry],
        *,
        variant_id: str,
        period: ReportingPeriod,
    ) -> CostSummary:
        """Aggregate costs for one variant in the half-open reporting period."""
        selected = self._select_unique(entries, variant_id=variant_id, period=period)
        effective = self._reconcile(selected)
        currencies = {entry.currency for entry in effective}
        if len(currencies) > 1:
            raise ValueError("All effective cost entries must use one currency")

        category_costs = {category: Decimal(0) for category in CostCategory}
        for entry in effective:
            category_costs[entry.category] += entry.amount

        return CostSummary(
            variant_id=variant_id,
            period=period,
            currency=next(iter(currencies), None),
            category_costs=category_costs,
            total_cost=sum(category_costs.values(), start=Decimal(0)),
            source_entry_count=len(selected),
            effective_entry_count=len(effective),
        )

    @staticmethod
    def _select_unique(
        entries: Iterable[CostEntry],
        *,
        variant_id: str,
        period: ReportingPeriod,
    ) -> list[CostEntry]:
        unique: dict[str, CostEntry] = {}
        for entry in entries:
            if entry.process_variant_id != variant_id:
                continue
            if not period.start_at <= entry.incurred_at < period.end_at:
                continue
            unique.setdefault(entry.id, entry)
        return list(unique.values())

    @staticmethod
    def _reconcile(entries: list[CostEntry]) -> list[CostEntry]:
        reconciled_keys = {
            (entry.category, entry.reconciliation_key)
            for entry in entries
            if entry.status is CostEvidenceStatus.RECONCILED
            and entry.reconciliation_key is not None
        }
        return [
            entry
            for entry in entries
            if not (
                entry.status is CostEvidenceStatus.ESTIMATED
                and entry.reconciliation_key is not None
                and (entry.category, entry.reconciliation_key) in reconciled_keys
            )
        ]
