"""Configurable, domain-independent governance for verified process economics."""

from decimal import Decimal
from enum import StrEnum

from pydantic import Field

from .comparison import EvidenceStatus, ProcessEconomicsComparison
from .models import CoreModel, TokenPurpose
from .tokens import ReviewTokenAttribution, TokenEfficiencyComparison
from .verification import OutcomeContract


class GovernanceGate(StrEnum):
    """Independent evidence and economics dimensions used for governance."""

    EVIDENCE = "evidence"
    QUALITY = "quality"
    SAFETY = "safety"
    COMPLIANCE = "compliance"
    BUSINESS_OUTCOME = "business_outcome"
    UNIT_COST = "unit_cost"
    NET_VALUE = "net_value"
    TOKEN_BUDGET = "token_budget"
    TOKEN_EFFICIENCY = "token_efficiency"
    REVIEW_WASTE = "review_waste"
    RETRY_WASTE = "retry_waste"


class GateStatus(StrEnum):
    """Evaluation state of one governance gate."""

    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class GenericGovernanceAction(StrEnum):
    """Action selected by the generic governance engine."""

    SCALE = "scale"
    OPTIMIZE = "optimize"
    STOP = "stop"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    MONITOR = "monitor"


class GovernanceAssurance(CoreModel):
    """Domain-neutral assurance gate observations supplied by evaluators."""

    quality_passed: bool | None
    safety_passed: bool | None
    compliance_passed: bool | None
    business_outcome_passed: bool | None
    reconciled_costs_available: bool


class GenericGovernancePolicy(CoreModel):
    """Configurable financial boundary for generic governance."""

    minimum_net_value: Decimal = Decimal(0)


class TokenGovernancePolicy(CoreModel):
    """Token efficiency boundaries applied to AI-enabled process variants."""

    maximum_tokens_per_verified_outcome: Decimal = Field(gt=0)
    minimum_efficiency_improvement: Decimal
    maximum_review_token_ratio: Decimal = Field(ge=0, le=1)
    maximum_retry_token_ratio: Decimal = Field(ge=0, le=1)


class OptimizationLever(StrEnum):
    """Operational control that can improve process token efficiency."""

    REVIEW_THRESHOLD = "review_threshold"
    RETRY_POLICY = "retry_policy"
    OUTPUT_LIMIT = "output_limit"
    PROMPT_PROFILE = "prompt_profile"


class OptimizationRecommendation(CoreModel):
    """Evidence-backed deterministic process optimization recommendation."""

    lever: OptimizationLever
    reason: str = Field(min_length=1)
    evidence_metric: str = Field(min_length=1)
    observed_value: Decimal
    target_value: Decimal
    suggested_action: str = Field(min_length=1)


class GovernanceGateResult(CoreModel):
    """Auditable result for one generic governance gate."""

    gate: GovernanceGate
    status: GateStatus
    reason: str = Field(min_length=1)


class GenericGovernanceDecision(CoreModel):
    """Deterministic governance decision with complete gate evidence."""

    id: str = Field(min_length=1)
    contract_id: str = Field(min_length=1)
    treatment_variant_id: str = Field(min_length=1)
    action: GenericGovernanceAction
    gate_results: list[GovernanceGateResult]
    recommended_actions: list[str]
    optimization_recommendations: list[OptimizationRecommendation] = Field(
        default_factory=list
    )


class GenericGovernanceEngine:
    """Select a generic action from assurance and process economics gates."""

    def __init__(self, policy: GenericGovernancePolicy | None = None) -> None:
        self._policy = policy or GenericGovernancePolicy()

    def evaluate(
        self,
        *,
        decision_id: str,
        contract: OutcomeContract,
        comparison: ProcessEconomicsComparison,
        assurance: GovernanceAssurance,
        token_policy: TokenGovernancePolicy | None = None,
        token_comparison: TokenEfficiencyComparison | None = None,
        review_attribution: ReviewTokenAttribution | None = None,
    ) -> GenericGovernanceDecision:
        """Evaluate gates in evidence, hard-stop, economics, and maturity order."""
        self._validate_currency(contract, comparison)
        results = self._gate_results(
            contract,
            comparison,
            assurance,
            token_policy=token_policy,
            token_comparison=token_comparison,
            review_attribution=review_attribution,
        )
        by_gate = {result.gate: result for result in results}

        evidence = by_gate[GovernanceGate.EVIDENCE]
        stop_results = [
            by_gate[gate]
            for gate in (
                GovernanceGate.QUALITY,
                GovernanceGate.SAFETY,
                GovernanceGate.COMPLIANCE,
                GovernanceGate.BUSINESS_OUTCOME,
            )
        ]
        economics_results = [
            by_gate[GovernanceGate.UNIT_COST],
            by_gate[GovernanceGate.NET_VALUE],
        ]
        economics_results.extend(
            result
            for result in results
            if result.gate
            in (
                GovernanceGate.TOKEN_BUDGET,
                GovernanceGate.TOKEN_EFFICIENCY,
                GovernanceGate.REVIEW_WASTE,
                GovernanceGate.RETRY_WASTE,
            )
        )

        if evidence.status is not GateStatus.PASS:
            action = GenericGovernanceAction.INSUFFICIENT_EVIDENCE
            recommendations = [
                "Collect complete control and treatment evidence before deciding."
            ]
        elif any(result.status is GateStatus.FAIL for result in stop_results):
            action = GenericGovernanceAction.STOP
            recommendations = [
                "Stop rollout and remediate failed outcome or assurance gates."
            ]
        elif any(result.status is GateStatus.UNKNOWN for result in stop_results):
            action = GenericGovernanceAction.INSUFFICIENT_EVIDENCE
            recommendations = [
                "Complete quality, safety, compliance, and outcome assessment."
            ]
        elif any(result.status is GateStatus.UNKNOWN for result in economics_results):
            action = GenericGovernanceAction.INSUFFICIENT_EVIDENCE
            recommendations = [
                "Collect enough cost, control, and token evidence to calculate economics."
            ]
        elif any(result.status is GateStatus.FAIL for result in economics_results):
            action = GenericGovernanceAction.OPTIMIZE
            recommendations = ["Improve failed economic or token gates before scaling."]
        elif not assurance.reconciled_costs_available:
            action = GenericGovernanceAction.MONITOR
            recommendations = [
                "Monitor estimated economics until reconciled costs are available."
            ]
        else:
            action = GenericGovernanceAction.SCALE
            recommendations = [
                "Scale while continuing to monitor assurance and economic gates."
            ]

        optimization_recommendations = self._optimization_recommendations(
            results,
            token_policy=token_policy,
            token_comparison=token_comparison,
            review_attribution=review_attribution,
        )
        if optimization_recommendations and action is GenericGovernanceAction.OPTIMIZE:
            recommendations = [
                recommendation.suggested_action
                for recommendation in optimization_recommendations
            ]
        return GenericGovernanceDecision(
            id=decision_id,
            contract_id=contract.id,
            treatment_variant_id=comparison.treatment.variant_id,
            action=action,
            gate_results=results,
            recommended_actions=recommendations,
            optimization_recommendations=optimization_recommendations,
        )

    def _gate_results(
        self,
        contract: OutcomeContract,
        comparison: ProcessEconomicsComparison,
        assurance: GovernanceAssurance,
        *,
        token_policy: TokenGovernancePolicy | None,
        token_comparison: TokenEfficiencyComparison | None,
        review_attribution: ReviewTokenAttribution | None,
    ) -> list[GovernanceGateResult]:
        treatment = comparison.treatment
        evidence_passed = (
            comparison.control.evidence_status is EvidenceStatus.SUFFICIENT
            and treatment.evidence_status is EvidenceStatus.SUFFICIENT
        )
        unit_cost = treatment.cost_per_verified_outcome
        net_value = comparison.net_savings
        results = [
            self._boolean_result(
                GovernanceGate.EVIDENCE,
                evidence_passed,
                "Control and treatment evidence is sufficient.",
                "Control or treatment evidence is incomplete.",
            ),
            self._assurance_result(
                GovernanceGate.QUALITY,
                assurance.quality_passed,
            ),
            self._assurance_result(
                GovernanceGate.SAFETY,
                assurance.safety_passed,
            ),
            self._assurance_result(
                GovernanceGate.COMPLIANCE,
                assurance.compliance_passed,
            ),
            self._assurance_result(
                GovernanceGate.BUSINESS_OUTCOME,
                assurance.business_outcome_passed,
            ),
            GovernanceGateResult(
                gate=GovernanceGate.UNIT_COST,
                status=(
                    GateStatus.UNKNOWN
                    if unit_cost is None
                    else GateStatus.PASS
                    if unit_cost <= contract.maximum_cost_per_verified_outcome
                    else GateStatus.FAIL
                ),
                reason=(
                    "Unit cost is unavailable."
                    if unit_cost is None
                    else "Unit cost is within the contract maximum."
                    if unit_cost <= contract.maximum_cost_per_verified_outcome
                    else "Unit cost exceeds the contract maximum."
                ),
            ),
            GovernanceGateResult(
                gate=GovernanceGate.NET_VALUE,
                status=(
                    GateStatus.UNKNOWN
                    if net_value is None
                    else GateStatus.PASS
                    if net_value >= self._policy.minimum_net_value
                    else GateStatus.FAIL
                ),
                reason=(
                    "Net value is unavailable."
                    if net_value is None
                    else "Net value meets the policy minimum."
                    if net_value >= self._policy.minimum_net_value
                    else "Net value is below the policy minimum."
                ),
            ),
        ]
        if token_policy is not None:
            results.extend(
                self._token_gate_results(
                    token_policy,
                    token_comparison,
                    review_attribution,
                )
            )
        return results

    @staticmethod
    def _token_gate_results(
        policy: TokenGovernancePolicy,
        comparison: TokenEfficiencyComparison | None,
        review_attribution: ReviewTokenAttribution | None,
    ) -> list[GovernanceGateResult]:
        treatment = comparison.treatment if comparison is not None else None
        tokens_per_outcome = (
            treatment.tokens_per_verified_outcome if treatment is not None else None
        )
        efficiency = comparison.efficiency_improvement if comparison is not None else None
        total_tokens = treatment.total_tokens if treatment is not None else 0
        review_ratio = (
            Decimal(review_attribution.non_contributing_review_tokens) / total_tokens
            if review_attribution is not None and total_tokens
            else None
        )
        retry_ratio = (
            Decimal(treatment.purpose_breakdown[TokenPurpose.RETRY]) / total_tokens
            if treatment is not None and total_tokens
            else None
        )
        return [
            GenericGovernanceEngine._threshold_result(
                GovernanceGate.TOKEN_BUDGET,
                tokens_per_outcome,
                policy.maximum_tokens_per_verified_outcome,
                maximum=True,
            ),
            GenericGovernanceEngine._threshold_result(
                GovernanceGate.TOKEN_EFFICIENCY,
                efficiency,
                policy.minimum_efficiency_improvement,
                maximum=False,
            ),
            GenericGovernanceEngine._threshold_result(
                GovernanceGate.REVIEW_WASTE,
                review_ratio,
                policy.maximum_review_token_ratio,
                maximum=True,
            ),
            GenericGovernanceEngine._threshold_result(
                GovernanceGate.RETRY_WASTE,
                retry_ratio,
                policy.maximum_retry_token_ratio,
                maximum=True,
            ),
        ]

    @staticmethod
    def _threshold_result(
        gate: GovernanceGate,
        observed: Decimal | None,
        target: Decimal,
        *,
        maximum: bool,
    ) -> GovernanceGateResult:
        passed = observed is not None and (
            observed <= target if maximum else observed >= target
        )
        return GovernanceGateResult(
            gate=gate,
            status=(
                GateStatus.UNKNOWN
                if observed is None
                else GateStatus.PASS
                if passed
                else GateStatus.FAIL
            ),
            reason=(
                f"{gate.value} evidence is unavailable."
                if observed is None
                else f"Observed {observed} against target {target}."
            ),
        )

    @staticmethod
    def _optimization_recommendations(
        results: list[GovernanceGateResult],
        *,
        token_policy: TokenGovernancePolicy | None,
        token_comparison: TokenEfficiencyComparison | None,
        review_attribution: ReviewTokenAttribution | None,
    ) -> list[OptimizationRecommendation]:
        if token_policy is None or token_comparison is None:
            return []
        failed = {
            result.gate
            for result in results
            if result.status is GateStatus.FAIL
        }
        treatment = token_comparison.treatment
        recommendations: list[OptimizationRecommendation] = []
        if GovernanceGate.TOKEN_BUDGET in failed:
            recommendations.append(
                OptimizationRecommendation(
                    lever=OptimizationLever.OUTPUT_LIMIT,
                    reason="Treatment exceeds its token budget per verified outcome.",
                    evidence_metric="tokens_per_verified_outcome",
                    observed_value=treatment.tokens_per_verified_outcome or Decimal(0),
                    target_value=token_policy.maximum_tokens_per_verified_outcome,
                    suggested_action=(
                        "Reduce response limits or prompt context before scaling."
                    ),
                )
            )
        if GovernanceGate.TOKEN_EFFICIENCY in failed:
            recommendations.append(
                OptimizationRecommendation(
                    lever=OptimizationLever.PROMPT_PROFILE,
                    reason="Treatment does not meet the required efficiency gain.",
                    evidence_metric="token_efficiency_improvement",
                    observed_value=(
                        token_comparison.efficiency_improvement or Decimal(0)
                    ),
                    target_value=token_policy.minimum_efficiency_improvement,
                    suggested_action=(
                        "Use the concise prompt profile for routine work and remeasure."
                    ),
                )
            )
        if GovernanceGate.REVIEW_WASTE in failed and review_attribution is not None:
            observed_ratio = (
                Decimal(review_attribution.total_review_tokens)
                / treatment.total_tokens
                if treatment.total_tokens
                else Decimal(0)
            )
            recommendations.append(
                OptimizationRecommendation(
                    lever=OptimizationLever.REVIEW_THRESHOLD,
                    reason="Review consumes too much of treatment token usage.",
                    evidence_metric="review_token_ratio",
                    observed_value=observed_ratio,
                    target_value=token_policy.maximum_review_token_ratio,
                    suggested_action=(
                        "Narrow review triggers while retaining sensitive and critical gates."
                    ),
                )
            )
        if GovernanceGate.RETRY_WASTE in failed:
            retry_ratio = (
                Decimal(treatment.purpose_breakdown[TokenPurpose.RETRY])
                / treatment.total_tokens
                if treatment.total_tokens
                else Decimal(0)
            )
            recommendations.append(
                OptimizationRecommendation(
                    lever=OptimizationLever.RETRY_POLICY,
                    reason="Retry tokens exceed the allowed treatment ratio.",
                    evidence_metric="retry_token_ratio",
                    observed_value=retry_ratio,
                    target_value=token_policy.maximum_retry_token_ratio,
                    suggested_action=(
                        "Correct output validation failures before allowing another retry."
                    ),
                )
            )
        if not failed and token_comparison.efficiency_improvement is not None:
            recommendations.append(
                OptimizationRecommendation(
                    lever=OptimizationLever.REVIEW_THRESHOLD,
                    reason="Treatment meets its token efficiency policy.",
                    evidence_metric="token_efficiency_improvement",
                    observed_value=token_comparison.efficiency_improvement,
                    target_value=token_policy.minimum_efficiency_improvement,
                    suggested_action=(
                        "Retain risk-based review triggers and monitor skipped routine work."
                    ),
                )
            )
        return recommendations

    @staticmethod
    def _assurance_result(
        gate: GovernanceGate,
        passed: bool | None,
    ) -> GovernanceGateResult:
        status = (
            GateStatus.UNKNOWN
            if passed is None
            else GateStatus.PASS
            if passed
            else GateStatus.FAIL
        )
        return GovernanceGateResult(
            gate=gate,
            status=status,
            reason=f"{gate.value} assurance is {status.value}.",
        )

    @staticmethod
    def _boolean_result(
        gate: GovernanceGate,
        passed: bool,
        pass_reason: str,
        fail_reason: str,
    ) -> GovernanceGateResult:
        return GovernanceGateResult(
            gate=gate,
            status=GateStatus.PASS if passed else GateStatus.FAIL,
            reason=pass_reason if passed else fail_reason,
        )

    @staticmethod
    def _validate_currency(
        contract: OutcomeContract,
        comparison: ProcessEconomicsComparison,
    ) -> None:
        if comparison.currency is not None and comparison.currency != contract.currency:
            raise ValueError("Comparison and contract currencies must match")
