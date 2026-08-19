"""Core outcome economics models."""

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


class DomainModel(BaseModel):
    """Base model for validated domain records."""

    model_config = ConfigDict(extra="forbid")


class Variant(StrEnum):
    """Experiment assignment for a run or ticket."""

    CONTROL = "control"
    TREATMENT = "treatment"


class OutcomeStatus(StrEnum):
    """Lifecycle state of an outcome contract."""

    DRAFT = "draft"
    ACTIVE = "active"
    VERIFIED = "verified"
    REJECTED = "rejected"
    RETIRED = "retired"


class GovernanceAction(StrEnum):
    """Action selected by outcome governance."""

    APPROVE = "approve"
    REQUEST_REVIEW = "request_review"
    PAUSE = "pause"
    REJECT = "reject"


class Ticket(DomainModel):
    """Fictional support ticket with gold evaluation labels."""

    id: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    description: str = Field(min_length=1)
    gold_category: str = Field(min_length=1)
    gold_priority: str = Field(pattern=r"^P[1-4]$")
    gold_resolver_group: str = Field(min_length=1)
    created_at: AwareDatetime = Field(default_factory=utc_now)


class TriageResult(DomainModel):
    """Predicted routing labels for a support ticket."""

    run_id: str = Field(min_length=1)
    ticket_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    priority: str = Field(pattern=r"^P[1-4]$")
    resolver_group: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(min_length=1)
    created_at: AwareDatetime = Field(default_factory=utc_now)


class ReviewResult(DomainModel):
    """Human or automated review of a triage result."""

    run_id: str = Field(min_length=1)
    ticket_id: str = Field(min_length=1)
    approved: bool
    corrected_category: str | None = None
    corrected_priority: str | None = Field(default=None, pattern=r"^P[1-4]$")
    corrected_resolver_group: str | None = None
    notes: str = ""
    created_at: AwareDatetime = Field(default_factory=utc_now)


class OutcomeContract(DomainModel):
    """Measurable agreement used to evaluate an experiment outcome."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    variant: Variant
    status: OutcomeStatus = OutcomeStatus.DRAFT
    metric_name: str = Field(min_length=1)
    target_value: Decimal
    unit: str = Field(min_length=1)
    measurement_window_days: int = Field(gt=0)
    created_at: AwareDatetime = Field(default_factory=utc_now)


class VerificationResult(DomainModel):
    """Evidence-backed evaluation of an outcome contract."""

    id: str = Field(min_length=1)
    contract_id: str = Field(min_length=1)
    run_id: str | None = None
    passed: bool
    observed_value: Decimal
    evidence_count: int = Field(ge=0)
    reason: str = Field(min_length=1)
    verified_at: AwareDatetime = Field(default_factory=utc_now)


class PricingRecord(DomainModel):
    """Illustrative model-token pricing used for estimated costs."""

    id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    input_cost_per_million_tokens: Decimal = Field(ge=0)
    output_cost_per_million_tokens: Decimal = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    effective_at: AwareDatetime = Field(default_factory=utc_now)
    illustrative: Literal[True] = True


class EconomicsMetrics(DomainModel):
    """Estimated monetary metrics calculated from model usage."""

    run_id: str = Field(min_length=1)
    pricing_id: str = Field(min_length=1)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_input_cost: Decimal = Field(ge=0)
    estimated_output_cost: Decimal = Field(ge=0)
    estimated_total_cost: Decimal = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    monetary_values_are_estimated: Literal[True] = True
    calculated_at: AwareDatetime = Field(default_factory=utc_now)


class GovernanceDecision(DomainModel):
    """Recorded governance action for an outcome contract."""

    id: str = Field(min_length=1)
    contract_id: str = Field(min_length=1)
    action: GovernanceAction
    reason: str = Field(min_length=1)
    decided_by: str = Field(min_length=1)
    decided_at: AwareDatetime = Field(default_factory=utc_now)


class Outcome(DomainModel):
    """A measurable outcome and its economic inputs."""

    name: str = Field(min_length=1)
    baseline_value: Decimal = Field(ge=0)
    observed_value: Decimal = Field(ge=0)
    value_per_unit: Decimal = Field(ge=0)
    implementation_cost: Decimal = Field(ge=0)
    evidence: list[str] = Field(default_factory=list)


class EconomicAssessment(DomainModel):
    """Calculated value and verification state for an outcome."""

    outcome_name: str
    incremental_units: Decimal
    gross_value: Decimal
    net_value: Decimal
    return_on_investment: Decimal | None
    verified: bool