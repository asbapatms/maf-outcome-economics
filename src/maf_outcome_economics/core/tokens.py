"""Framework-neutral token accounting and process efficiency comparison."""

from collections.abc import Iterable
from decimal import Decimal
from enum import StrEnum

from pydantic import Field, model_validator

from .comparison import EvidenceStatus
from .models import CoreModel, ReportingPeriod, TokenEntry, TokenPurpose, WorkUnit
from .verification import OutcomeVerificationSummary, WorkUnitVerification


class TokenSummary(CoreModel):
    """Token consumption and verified-outcome efficiency for one variant."""

    variant_id: str = Field(min_length=1)
    total_work_units: int = Field(ge=0)
    verified_outcomes: int = Field(ge=0)
    total_input_tokens: int = Field(ge=0)
    total_output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    tokens_per_verified_outcome: Decimal | None = Field(default=None, ge=0)
    purpose_breakdown: dict[TokenPurpose, int]
    evidence_status: EvidenceStatus

    @model_validator(mode="after")
    def validate_totals(self) -> "TokenSummary":
        """Reject token and outcome metrics inconsistent with their inputs."""
        if self.verified_outcomes > self.total_work_units:
            raise ValueError("verified_outcomes cannot exceed total_work_units")
        if self.total_tokens != self.total_input_tokens + self.total_output_tokens:
            raise ValueError("total_tokens must equal input plus output tokens")
        if self.total_tokens != sum(self.purpose_breakdown.values()):
            raise ValueError("total_tokens must equal the purpose breakdown total")
        expected = (
            Decimal(self.total_tokens) / self.verified_outcomes
            if self.verified_outcomes
            else None
        )
        if self.tokens_per_verified_outcome != expected:
            raise ValueError("tokens_per_verified_outcome is inconsistent")
        return self


class TokenEfficiencyComparison(CoreModel):
    """Normalized token efficiency for control and treatment variants."""

    period: ReportingPeriod
    control: TokenSummary
    treatment: TokenSummary
    comparable_control_tokens: Decimal | None = Field(default=None, ge=0)
    tokens_avoided: Decimal | None = None
    efficiency_improvement: Decimal | None = None

    @model_validator(mode="after")
    def validate_comparison(self) -> "TokenEfficiencyComparison":
        """Reject comparison values inconsistent with variant summaries."""
        control_unit_tokens = self.control.tokens_per_verified_outcome
        treatment_unit_tokens = self.treatment.tokens_per_verified_outcome
        if (
            control_unit_tokens is None
            or treatment_unit_tokens is None
            or not self.treatment.verified_outcomes
        ):
            if any(
                value is not None
                for value in (
                    self.comparable_control_tokens,
                    self.tokens_avoided,
                    self.efficiency_improvement,
                )
            ):
                raise ValueError("comparison values require verified outcomes")
            return self
        expected_control = control_unit_tokens * self.treatment.verified_outcomes
        if self.comparable_control_tokens != expected_control:
            raise ValueError("comparable_control_tokens is inconsistent")
        expected_avoided = expected_control - self.treatment.total_tokens
        if self.tokens_avoided != expected_avoided:
            raise ValueError("tokens_avoided is inconsistent")
        expected_improvement = Decimal(1) - (
            treatment_unit_tokens / control_unit_tokens
        )
        if self.efficiency_improvement != expected_improvement:
            raise ValueError("efficiency_improvement is inconsistent")
        return self


class ReviewOutcome(StrEnum):
    """Measured effect of review on independent outcome verification."""

    USEFUL_CORRECTION = "useful_correction"
    HARMFUL_CORRECTION = "harmful_correction"
    NON_CONTRIBUTING = "non_contributing"
    INCONCLUSIVE = "inconclusive"


class ReviewTokenAttribution(CoreModel):
    """Review token allocation by independently measured outcome effect."""

    reviews_invoked: int = Field(ge=0)
    useful_corrections: int = Field(ge=0)
    harmful_corrections: int = Field(ge=0)
    non_contributing_reviews: int = Field(ge=0)
    inconclusive_reviews: int = Field(ge=0)
    total_review_tokens: int = Field(ge=0)
    useful_review_tokens: int = Field(ge=0)
    harmful_review_tokens: int = Field(ge=0)
    non_contributing_review_tokens: int = Field(ge=0)
    inconclusive_review_tokens: int = Field(ge=0)
    review_tokens_per_useful_correction: Decimal | None = Field(default=None, ge=0)
    non_contributing_review_ratio: Decimal | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def validate_attribution(self) -> "ReviewTokenAttribution":
        """Reject review counts and token allocations that do not reconcile."""
        classified_reviews = (
            self.useful_corrections
            + self.harmful_corrections
            + self.non_contributing_reviews
            + self.inconclusive_reviews
        )
        if self.reviews_invoked != classified_reviews:
            raise ValueError("reviews_invoked must equal classified review outcomes")
        classified_tokens = (
            self.useful_review_tokens
            + self.harmful_review_tokens
            + self.non_contributing_review_tokens
            + self.inconclusive_review_tokens
        )
        if self.total_review_tokens != classified_tokens:
            raise ValueError("total_review_tokens must equal classified review tokens")
        expected_per_correction = (
            Decimal(self.total_review_tokens) / self.useful_corrections
            if self.useful_corrections
            else None
        )
        if self.review_tokens_per_useful_correction != expected_per_correction:
            raise ValueError("review_tokens_per_useful_correction is inconsistent")
        expected_ratio = (
            Decimal(self.non_contributing_review_tokens) / self.total_review_tokens
            if self.total_review_tokens
            else None
        )
        if self.non_contributing_review_ratio != expected_ratio:
            raise ValueError("non_contributing_review_ratio is inconsistent")
        return self


def attribute_review_tokens(
    token_entries: Iterable[TokenEntry],
    review_outcomes: dict[str, ReviewOutcome],
) -> ReviewTokenAttribution:
    """Allocate review-purpose tokens to measured work-unit review outcomes."""
    unique_review_tokens = {
        (entry.trace_id, entry.span_id): entry
        for entry in token_entries
        if entry.purpose is TokenPurpose.REVIEW
    }.values()
    tokens_by_outcome = {outcome: 0 for outcome in ReviewOutcome}
    for entry in unique_review_tokens:
        outcome = review_outcomes.get(entry.work_unit_id, ReviewOutcome.INCONCLUSIVE)
        tokens_by_outcome[outcome] += entry.total_tokens
    counts = {outcome: 0 for outcome in ReviewOutcome}
    for outcome in review_outcomes.values():
        counts[outcome] += 1
    total_review_tokens = sum(tokens_by_outcome.values())
    useful_corrections = counts[ReviewOutcome.USEFUL_CORRECTION]
    return ReviewTokenAttribution(
        reviews_invoked=len(review_outcomes),
        useful_corrections=useful_corrections,
        harmful_corrections=counts[ReviewOutcome.HARMFUL_CORRECTION],
        non_contributing_reviews=counts[ReviewOutcome.NON_CONTRIBUTING],
        inconclusive_reviews=counts[ReviewOutcome.INCONCLUSIVE],
        total_review_tokens=total_review_tokens,
        useful_review_tokens=tokens_by_outcome[ReviewOutcome.USEFUL_CORRECTION],
        harmful_review_tokens=tokens_by_outcome[ReviewOutcome.HARMFUL_CORRECTION],
        non_contributing_review_tokens=tokens_by_outcome[
            ReviewOutcome.NON_CONTRIBUTING
        ],
        inconclusive_review_tokens=tokens_by_outcome[ReviewOutcome.INCONCLUSIVE],
        review_tokens_per_useful_correction=(
            Decimal(total_review_tokens) / useful_corrections
            if useful_corrections
            else None
        ),
        non_contributing_review_ratio=(
            Decimal(tokens_by_outcome[ReviewOutcome.NON_CONTRIBUTING])
            / total_review_tokens
            if total_review_tokens
            else None
        ),
    )


def compare_token_efficiency(
    *,
    control_variant_id: str,
    treatment_variant_id: str,
    period: ReportingPeriod,
    work_units: Iterable[WorkUnit],
    verification: OutcomeVerificationSummary,
    token_entries: Iterable[TokenEntry],
) -> TokenEfficiencyComparison:
    """Compare token use per verified outcome for control and treatment."""
    if control_variant_id == treatment_variant_id:
        raise ValueError("Control and treatment variant IDs must differ")
    all_work_units = list(work_units)
    unique_tokens = {
        (entry.trace_id, entry.span_id): entry for entry in token_entries
    }.values()
    all_tokens = list(unique_tokens)
    verification_by_work_unit = {
        result.work_unit_id: result for result in verification.results
    }
    control = _summarize_tokens(
        variant_id=control_variant_id,
        period=period,
        work_units=all_work_units,
        verification_by_work_unit=verification_by_work_unit,
        minimum_sample_size=verification.minimum_sample_size,
        token_entries=all_tokens,
    )
    treatment = _summarize_tokens(
        variant_id=treatment_variant_id,
        period=period,
        work_units=all_work_units,
        verification_by_work_unit=verification_by_work_unit,
        minimum_sample_size=verification.minimum_sample_size,
        token_entries=all_tokens,
    )
    comparable_control_tokens = None
    tokens_avoided = None
    efficiency_improvement = None
    if (
        control.tokens_per_verified_outcome is not None
        and treatment.tokens_per_verified_outcome is not None
    ):
        comparable_control_tokens = (
            control.tokens_per_verified_outcome * treatment.verified_outcomes
        )
        tokens_avoided = comparable_control_tokens - treatment.total_tokens
        efficiency_improvement = Decimal(1) - (
            treatment.tokens_per_verified_outcome
            / control.tokens_per_verified_outcome
        )
    return TokenEfficiencyComparison(
        period=period,
        control=control,
        treatment=treatment,
        comparable_control_tokens=comparable_control_tokens,
        tokens_avoided=tokens_avoided,
        efficiency_improvement=efficiency_improvement,
    )


def _summarize_tokens(
    *,
    variant_id: str,
    period: ReportingPeriod,
    work_units: list[WorkUnit],
    verification_by_work_unit: dict[str, WorkUnitVerification],
    minimum_sample_size: int,
    token_entries: list[TokenEntry],
) -> TokenSummary:
    selected_work_units = {
        work_unit.id
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
    selected_tokens = [
        entry
        for entry in token_entries
        if entry.process_variant_id == variant_id
        and entry.work_unit_id in selected_work_units
        and period.start_at <= entry.observed_at < period.end_at
    ]
    total_work_units = len(selected_work_units)
    verified_outcomes = sum(result.passed for result in selected_results)
    input_tokens = sum(entry.input_tokens for entry in selected_tokens)
    output_tokens = sum(entry.output_tokens for entry in selected_tokens)
    total_tokens = input_tokens + output_tokens
    purpose_breakdown = {purpose: 0 for purpose in TokenPurpose}
    for entry in selected_tokens:
        purpose_breakdown[entry.purpose] += entry.total_tokens
    return TokenSummary(
        variant_id=variant_id,
        total_work_units=total_work_units,
        verified_outcomes=verified_outcomes,
        total_input_tokens=input_tokens,
        total_output_tokens=output_tokens,
        total_tokens=total_tokens,
        tokens_per_verified_outcome=(
            Decimal(total_tokens) / verified_outcomes if verified_outcomes else None
        ),
        purpose_breakdown=purpose_breakdown,
        evidence_status=(
            EvidenceStatus.SUFFICIENT
            if total_work_units >= minimum_sample_size
            and len(selected_results) == total_work_units
            else EvidenceStatus.INSUFFICIENT
        ),
    )