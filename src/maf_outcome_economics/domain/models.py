"""Core outcome economics models."""

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


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


class WorkflowVariant(StrEnum):
    """Ticket workflow strategy used for agent invocation."""

    BASELINE = "baseline"
    OPTIMIZED = "optimized"


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
    SCALE = "scale"
    OPTIMIZE = "optimize"
    STOP = "stop"


class GovernanceReasonCode(StrEnum):
    """Machine-readable reason for a governance decision."""

    THRESHOLDS_MET = "thresholds_met"
    COST_EXCEEDS_BUDGET = "cost_exceeds_budget"
    NO_ACCEPTED_OUTCOMES = "no_accepted_outcomes"
    ACCEPTANCE_BELOW_MINIMUM = "acceptance_below_minimum"
    QUALITY_BELOW_MINIMUM = "quality_below_minimum"
    CRITICAL_RECALL_BELOW_MINIMUM = "critical_recall_below_minimum"


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
    minimum_acceptance_rate: Decimal = Field(ge=0, le=1)
    minimum_quality_score: Decimal = Field(ge=0, le=1)
    minimum_critical_priority_recall: Decimal = Field(ge=0, le=1)
    maximum_cost_per_accepted_outcome: Decimal = Field(ge=0)
    budget_currency: str = Field(default="USD", min_length=3, max_length=3)
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


class RoutingVerificationResult(VerificationResult):
    """Deterministic field-level verification of final routing labels."""

    category_correct: bool
    priority_correct: bool
    resolver_group_correct: bool
    accepted: bool
    correction_required: bool
    quality_score: Decimal = Field(ge=0, le=1)
    critical_priority_expected: bool
    critical_priority_recalled: bool | None = None

    @model_validator(mode="after")
    def validate_consistency(self) -> "RoutingVerificationResult":
        """Reject contradictory correctness and acceptance values."""
        all_correct = (
            self.category_correct
            and self.priority_correct
            and self.resolver_group_correct
        )
        expected_score = Decimal(
            sum(
                (
                    self.category_correct,
                    self.priority_correct,
                    self.resolver_group_correct,
                )
            )
        ) / Decimal(3)
        if self.accepted != all_correct or self.passed != all_correct:
            raise ValueError("Acceptance and passed require all routing fields to match")
        if self.correction_required == all_correct:
            raise ValueError("correction_required must be the inverse of acceptance")
        if self.quality_score != expected_score or self.observed_value != expected_score:
            raise ValueError("Quality scores must equal the fraction of correct fields")
        if self.critical_priority_expected:
            if self.critical_priority_recalled is not self.priority_correct:
                raise ValueError("Critical-priority recall must reflect priority correctness")
        elif self.critical_priority_recalled is not None:
            raise ValueError("Critical-priority recall applies only to critical gold labels")
        return self


class TicketWorkflowInput(DomainModel):
    """Business metadata and ticket supplied to one workflow run."""

    ticket: Ticket
    business_task_id: str = Field(min_length=1)
    batch_id: str = Field(min_length=1)
    contract_id: str = Field(min_length=1)
    variant: WorkflowVariant
    sensitive: bool = False


class TicketWorkflowState(DomainModel):
    """Typed message passed between sequential ticket executors."""

    request: TicketWorkflowInput
    run_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=32, max_length=32)
    triage: TriageResult | None = None
    review: ReviewResult | None = None
    review_invoked: bool = False
    review_skip_reason: str | None = None
    verification: RoutingVerificationResult | None = None


class TicketWorkflowResult(DomainModel):
    """Final typed output from one ticket workflow run."""

    business_task_id: str = Field(min_length=1)
    batch_id: str = Field(min_length=1)
    contract_id: str = Field(min_length=1)
    variant: WorkflowVariant
    run_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=32, max_length=32)
    triage: TriageResult
    review: ReviewResult | None = None
    review_invoked: bool
    review_skip_reason: str | None = None
    verification: RoutingVerificationResult


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


class BillableModelCall(DomainModel):
    """One normalized semantic chat model call used for economics."""

    trace_id: str = Field(min_length=1)
    span_id: str = Field(min_length=1)
    business_task_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    operation_name: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    agent_id: str | None = None
    agent_name: str | None = None
    executor_id: str | None = None
    recorded_at: AwareDatetime


class OutcomeEconomics(DomainModel):
    """Aggregated token and estimated-cost economics for verified outcomes."""

    total_input_tokens: int = Field(ge=0)
    total_output_tokens: int = Field(ge=0)
    estimated_model_cost: Decimal = Field(ge=0)
    accepted_outcomes: int = Field(ge=0)
    cost_per_accepted_outcome: Decimal | None
    tokens_per_accepted_outcome: Decimal | None
    agent_contribution_cost: dict[str, Decimal]
    retry_tax: Decimal = Field(ge=0)
    coordination_tax: Decimal = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    monetary_values_are_estimated: Literal[True] = True
    calculated_at: AwareDatetime = Field(default_factory=utc_now)


class GovernanceEvidence(DomainModel):
    """Metrics evaluated against an outcome contract's governance thresholds."""

    total_outcomes: int = Field(ge=0)
    accepted_outcomes: int = Field(ge=0)
    acceptance_rate: Decimal = Field(ge=0, le=1)
    average_quality_score: Decimal = Field(ge=0, le=1)
    critical_outcomes: int = Field(ge=0)
    critical_priority_recall: Decimal = Field(ge=0, le=1)
    cost_per_accepted_outcome: Decimal | None = Field(default=None, ge=0)
    maximum_cost_per_accepted_outcome: Decimal = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)


class GovernanceDecision(DomainModel):
    """Recorded governance action for an outcome contract."""

    id: str = Field(min_length=1)
    contract_id: str = Field(min_length=1)
    action: GovernanceAction
    reason: str = Field(min_length=1)
    reason_codes: list[GovernanceReasonCode] = Field(default_factory=list)
    evidence_metrics: GovernanceEvidence | None = None
    recommended_actions: list[str] = Field(default_factory=list)
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