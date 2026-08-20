"""Framework-neutral process economics comparison."""

from collections.abc import Iterable
from decimal import Decimal
from enum import StrEnum

from pydantic import Field, model_validator

from .costs import CostLedger
from .models import CoreModel, CostCategory, CostEntry, ReportingPeriod, WorkUnit
from .verification import OutcomeVerificationSummary, WorkUnitVerification


class EvidenceStatus(StrEnum):
    """Whether a process summary has enough complete verification evidence."""

    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"


class ProcessEconomicsSummary(CoreModel):
    """Cost and verified-outcome economics for one process variant."""

    variant_id: str = Field(min_length=1)
    total_work_units: int = Field(ge=0)
    verified_outcomes: int = Field(ge=0)
    total_cost: Decimal = Field(ge=0)
    cost_per_verified_outcome: Decimal | None = Field(default=None, ge=0)
    cost_breakdown: dict[CostCategory, Decimal]
    evidence_status: EvidenceStatus
    currency: str | None = Field(default=None, min_length=3, max_length=3)

    @model_validator(mode="after")
    def validate_economics(self) -> "ProcessEconomicsSummary":
        """Reject counts and unit economics inconsistent with aggregate values."""
        if self.verified_outcomes > self.total_work_units:
            raise ValueError("verified_outcomes cannot exceed total_work_units")
        expected_unit_cost = (
            self.total_cost / self.verified_outcomes
            if self.verified_outcomes
            else None
        )
        if self.cost_per_verified_outcome != expected_unit_cost:
            raise ValueError("cost_per_verified_outcome is inconsistent")
        if self.total_cost != sum(self.cost_breakdown.values(), start=Decimal(0)):
            raise ValueError("total_cost must equal the cost breakdown total")
        return self


class ProcessEconomicsComparison(CoreModel):
    """Normalized control-versus-treatment process economics."""

    period: ReportingPeriod
    control: ProcessEconomicsSummary
    treatment: ProcessEconomicsSummary
    control_unit_cost: Decimal | None = Field(default=None, ge=0)
    comparable_control_cost: Decimal | None = Field(default=None, ge=0)
    net_savings: Decimal | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)

    @model_validator(mode="after")
    def validate_comparison(self) -> "ProcessEconomicsComparison":
        """Reject comparison values inconsistent with the process summaries."""
        if self.control_unit_cost != self.control.cost_per_verified_outcome:
            raise ValueError("control_unit_cost is inconsistent")
        if self.control_unit_cost is None or not self.treatment.verified_outcomes:
            if self.comparable_control_cost is not None or self.net_savings is not None:
                raise ValueError("comparison values require verified outcomes")
            return self
        expected_control_cost = (
            self.control_unit_cost * self.treatment.verified_outcomes
        )
        if self.comparable_control_cost != expected_control_cost:
            raise ValueError("comparable_control_cost is inconsistent")
        if self.net_savings != expected_control_cost - self.treatment.total_cost:
            raise ValueError("net_savings is inconsistent")
        return self


def compare_processes(
    *,
    control_variant_id: str,
    treatment_variant_id: str,
    period: ReportingPeriod,
    work_units: Iterable[WorkUnit],
    verification: OutcomeVerificationSummary,
    cost_entries: Iterable[CostEntry],
) -> ProcessEconomicsComparison:
    """Compare any control and treatment using only normalized core records."""
    if control_variant_id == treatment_variant_id:
        raise ValueError("Control and treatment variant IDs must differ")

    all_work_units = list(work_units)
    all_cost_entries = list(cost_entries)
    verification_by_work_unit = {
        result.work_unit_id: result for result in verification.results
    }
    control = _summarize_process(
        variant_id=control_variant_id,
        period=period,
        work_units=all_work_units,
        verification_by_work_unit=verification_by_work_unit,
        minimum_sample_size=verification.minimum_sample_size,
        cost_entries=all_cost_entries,
    )
    treatment = _summarize_process(
        variant_id=treatment_variant_id,
        period=period,
        work_units=all_work_units,
        verification_by_work_unit=verification_by_work_unit,
        minimum_sample_size=verification.minimum_sample_size,
        cost_entries=all_cost_entries,
    )
    currencies = {
        currency for currency in (control.currency, treatment.currency) if currency
    }
    if len(currencies) > 1:
        raise ValueError("Control and treatment costs must use one currency")

    control_unit_cost = control.cost_per_verified_outcome
    comparable_control_cost = None
    if control_unit_cost is not None and treatment.verified_outcomes > 0:
        comparable_control_cost = control_unit_cost * treatment.verified_outcomes
    return ProcessEconomicsComparison(
        period=period,
        control=control,
        treatment=treatment,
        control_unit_cost=control_unit_cost,
        comparable_control_cost=comparable_control_cost,
        net_savings=(
            comparable_control_cost - treatment.total_cost
            if comparable_control_cost is not None
            else None
        ),
        currency=next(iter(currencies), None),
    )


def _summarize_process(
    *,
    variant_id: str,
    period: ReportingPeriod,
    work_units: list[WorkUnit],
    verification_by_work_unit: dict[str, WorkUnitVerification],
    minimum_sample_size: int,
    cost_entries: list[CostEntry],
) -> ProcessEconomicsSummary:
    selected_work_units = {
        work_unit.id: work_unit
        for work_unit in work_units
        if work_unit.process_variant_id == variant_id
        and period.start_at
        <= (work_unit.completed_at or work_unit.started_at)
        < period.end_at
    }
    selected_results = [
        verification_by_work_unit[work_unit_id]
        for work_unit_id in selected_work_units
        if work_unit_id in verification_by_work_unit
    ]
    total_work_units = len(selected_work_units)
    verified_outcomes = sum(result.passed for result in selected_results)
    evidence_status = (
        EvidenceStatus.SUFFICIENT
        if total_work_units >= minimum_sample_size
        and len(selected_results) == total_work_units
        else EvidenceStatus.INSUFFICIENT
    )
    cost_summary = CostLedger().summarize(
        cost_entries,
        variant_id=variant_id,
        period=period,
    )
    return ProcessEconomicsSummary(
        variant_id=variant_id,
        total_work_units=total_work_units,
        verified_outcomes=verified_outcomes,
        total_cost=cost_summary.total_cost,
        cost_per_verified_outcome=(
            cost_summary.total_cost / verified_outcomes
            if verified_outcomes
            else None
        ),
        cost_breakdown=cost_summary.category_costs,
        evidence_status=evidence_status,
        currency=cost_summary.currency,
    )
