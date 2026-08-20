"""In-memory invoice adapter for the framework-neutral connector contracts."""

from maf_outcome_economics.core import (
    CostCategory,
    CostEntry,
    CostEvidenceStatus,
    EvidenceRecord,
    ReportingPeriod,
    WorkUnit,
)

from .models import InvoiceCostProfile, InvoiceRecord


class InvoiceScenarioConnector:
    """Normalize invoice records into work, evidence, and reconciled costs."""

    def __init__(
        self,
        invoices: list[InvoiceRecord],
        cost_profiles: list[InvoiceCostProfile],
    ) -> None:
        self._invoices = list(invoices)
        self._cost_profiles = {
            profile.process_variant_id: profile for profile in cost_profiles
        }

    async def load_work_units(self, period: ReportingPeriod) -> list[WorkUnit]:
        """Return invoice processing work completed in the reporting period."""
        return [
            WorkUnit(
                id=invoice.id,
                process_variant_id=invoice.process_variant_id,
                started_at=invoice.received_at,
                completed_at=invoice.completed_at,
                attributes={
                    "supplier_id": invoice.supplier_id,
                    "invoice_amount": str(invoice.amount),
                    "currency": invoice.currency,
                },
            )
            for invoice in self._invoices_in_period(period)
        ]

    async def load_evidence(self, period: ReportingPeriod) -> list[EvidenceRecord]:
        """Return independent posting, matching, and duplicate-check evidence."""
        records: list[EvidenceRecord] = []
        for invoice in self._invoices_in_period(period):
            observations = (
                ("posted", invoice.posted, "accounts-payable-ledger"),
                ("amount_matched", invoice.amount_matched, "three-way-match"),
                (
                    "duplicate_detected",
                    invoice.duplicate_detected,
                    "duplicate-control",
                ),
            )
            records.extend(
                EvidenceRecord(
                    id=f"evidence:{invoice.id}:{metric}",
                    work_unit_id=invoice.id,
                    metric=metric,
                    value=value,
                    source=source,
                    observed_at=invoice.completed_at,
                    provenance={"invoice_id": invoice.id},
                )
                for metric, value, source in observations
            )
        return records

    async def load_costs(self, period: ReportingPeriod) -> list[CostEntry]:
        """Return reconciled per-invoice costs by generic category."""
        entries: list[CostEntry] = []
        for invoice in self._invoices_in_period(period):
            profile = self._cost_profiles.get(invoice.process_variant_id)
            if profile is None:
                raise ValueError(
                    f"Missing invoice cost profile for {invoice.process_variant_id!r}"
                )
            amounts = (
                (CostCategory.HUMAN_PROCESSING, profile.human_processing),
                (CostCategory.PLATFORM, profile.platform),
                (CostCategory.MODEL, profile.model),
            )
            entries.extend(
                CostEntry(
                    id=f"cost:{invoice.id}:{category.value}",
                    process_variant_id=invoice.process_variant_id,
                    work_unit_id=invoice.id,
                    category=category,
                    amount=amount,
                    currency=invoice.currency,
                    source="invoice-cost-ledger",
                    status=CostEvidenceStatus.RECONCILED,
                    reconciliation_key=f"{invoice.id}:{category.value}",
                    incurred_at=invoice.completed_at,
                )
                for category, amount in amounts
                if amount > 0
            )
        return entries

    def _invoices_in_period(self, period: ReportingPeriod) -> list[InvoiceRecord]:
        return [
            invoice
            for invoice in self._invoices
            if period.start_at <= invoice.completed_at < period.end_at
        ]