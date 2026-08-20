"""Tests for generic evidence and economics governance."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from maf_outcome_economics.core import (
    CostCategory,
    EvidenceOperator,
    EvidenceRule,
    EvidenceStatus,
    GateStatus,
    GenericGovernanceAction,
    GenericGovernanceEngine,
    GenericGovernancePolicy,
    GovernanceAssurance,
    GovernanceGate,
    OptimizationLever,
    OutcomeContract,
    ProcessEconomicsComparison,
    ProcessEconomicsSummary,
    ReportingPeriod,
    ReviewTokenAttribution,
    TokenEfficiencyComparison,
    TokenGovernancePolicy,
    TokenPurpose,
    TokenSummary,
)

PERIOD = ReportingPeriod(
    start_at=datetime(2026, 8, 1, tzinfo=UTC),
    end_at=datetime(2026, 9, 1, tzinfo=UTC),
)


def _contract(*, maximum_unit_cost: str = "5") -> OutcomeContract:
    return OutcomeContract(
        id="generic-contract",
        name="Generic verified outcome",
        success_rules=[
            EvidenceRule(
                metric="outcome_achieved",
                operator=EvidenceOperator.EQUALS,
                expected_value=True,
            )
        ],
        quality_gates=[],
        maximum_cost_per_verified_outcome=Decimal(maximum_unit_cost),
        minimum_sample_size=2,
        currency="USD",
    )


def _summary(
    variant_id: str,
    *,
    total_cost: str,
    verified_outcomes: int = 2,
    evidence_status: EvidenceStatus = EvidenceStatus.SUFFICIENT,
) -> ProcessEconomicsSummary:
    cost = Decimal(total_cost)
    return ProcessEconomicsSummary(
        variant_id=variant_id,
        total_work_units=2,
        verified_outcomes=verified_outcomes,
        total_cost=cost,
        cost_per_verified_outcome=(cost / verified_outcomes if verified_outcomes else None),
        cost_breakdown={CostCategory.OTHER: cost},
        evidence_status=evidence_status,
        currency="USD",
    )


def _comparison(
    *,
    treatment_cost: str = "8",
    treatment_verified: int = 2,
    treatment_evidence: EvidenceStatus = EvidenceStatus.SUFFICIENT,
    control_evidence: EvidenceStatus = EvidenceStatus.SUFFICIENT,
) -> ProcessEconomicsComparison:
    control = _summary(
        "control-v1",
        total_cost="20",
        evidence_status=control_evidence,
    )
    treatment = _summary(
        "treatment-v1",
        total_cost=treatment_cost,
        verified_outcomes=treatment_verified,
        evidence_status=treatment_evidence,
    )
    comparable_control_cost = (
        control.cost_per_verified_outcome * treatment_verified
        if control.cost_per_verified_outcome is not None and treatment_verified
        else None
    )
    return ProcessEconomicsComparison(
        period=PERIOD,
        control=control,
        treatment=treatment,
        control_unit_cost=control.cost_per_verified_outcome,
        comparable_control_cost=comparable_control_cost,
        net_savings=(
            comparable_control_cost - treatment.total_cost
            if comparable_control_cost is not None
            else None
        ),
        currency="USD",
    )


def _assurance(
    *,
    quality: bool | None = True,
    safety: bool | None = True,
    compliance: bool | None = True,
    business_outcome: bool | None = True,
    reconciled: bool = True,
) -> GovernanceAssurance:
    return GovernanceAssurance(
        quality_passed=quality,
        safety_passed=safety,
        compliance_passed=compliance,
        business_outcome_passed=business_outcome,
        reconciled_costs_available=reconciled,
    )


def _token_comparison() -> TokenEfficiencyComparison:
    purpose_breakdown = {purpose: 0 for purpose in TokenPurpose}
    control_breakdown = purpose_breakdown | {TokenPurpose.PRIMARY_WORK: 400}
    treatment_breakdown = purpose_breakdown | {
        TokenPurpose.PRIMARY_WORK: 40,
        TokenPurpose.REVIEW: 160,
    }
    control = TokenSummary(
        variant_id="control-v1",
        total_work_units=2,
        verified_outcomes=2,
        total_input_tokens=320,
        total_output_tokens=80,
        total_tokens=400,
        tokens_per_verified_outcome=Decimal(200),
        purpose_breakdown=control_breakdown,
        evidence_status=EvidenceStatus.SUFFICIENT,
    )
    treatment = TokenSummary(
        variant_id="treatment-v1",
        total_work_units=2,
        verified_outcomes=2,
        total_input_tokens=160,
        total_output_tokens=40,
        total_tokens=200,
        tokens_per_verified_outcome=Decimal(100),
        purpose_breakdown=treatment_breakdown,
        evidence_status=EvidenceStatus.SUFFICIENT,
    )
    return TokenEfficiencyComparison(
        period=PERIOD,
        control=control,
        treatment=treatment,
        comparable_control_tokens=Decimal(400),
        tokens_avoided=Decimal(200),
        efficiency_improvement=Decimal("0.5"),
    )


def _review_attribution() -> ReviewTokenAttribution:
    return ReviewTokenAttribution(
        reviews_invoked=1,
        useful_corrections=0,
        harmful_corrections=0,
        non_contributing_reviews=1,
        inconclusive_reviews=0,
        total_review_tokens=160,
        useful_review_tokens=0,
        harmful_review_tokens=0,
        non_contributing_review_tokens=160,
        inconclusive_review_tokens=0,
        review_tokens_per_useful_correction=None,
        non_contributing_review_ratio=Decimal(1),
    )


def _token_policy() -> TokenGovernancePolicy:
    return TokenGovernancePolicy(
        maximum_tokens_per_verified_outcome=Decimal(150),
        minimum_efficiency_improvement=Decimal("0.2"),
        maximum_review_token_ratio=Decimal("0.25"),
        maximum_retry_token_ratio=Decimal("0.1"),
    )


def test_given_all_gates_pass_with_reconciled_costs_when_evaluated_then_scales() -> None:
    # Act
    decision = GenericGovernanceEngine().evaluate(
        decision_id="scale",
        contract=_contract(),
        comparison=_comparison(),
        assurance=_assurance(),
    )

    # Assert
    assert decision.action is GenericGovernanceAction.SCALE
    assert all(result.status is GateStatus.PASS for result in decision.gate_results)


@pytest.mark.parametrize(
    ("comparison", "policy"),
    [
        (_comparison(treatment_cost="12"), GenericGovernancePolicy()),
        (_comparison(), GenericGovernancePolicy(minimum_net_value=Decimal("13"))),
    ],
)
def test_given_economics_gate_fails_when_evaluated_then_optimizes(
    comparison: ProcessEconomicsComparison,
    policy: GenericGovernancePolicy,
) -> None:
    # Act
    decision = GenericGovernanceEngine(policy).evaluate(
        decision_id="optimize",
        contract=_contract(),
        comparison=comparison,
        assurance=_assurance(),
    )

    # Assert
    assert decision.action is GenericGovernanceAction.OPTIMIZE


@pytest.mark.parametrize("failed_gate", ["quality", "safety", "compliance", "business"])
def test_given_hard_gate_fails_when_evaluated_then_stops(failed_gate: str) -> None:
    # Arrange
    values = {
        "quality": True,
        "safety": True,
        "compliance": True,
        "business": True,
    }
    values[failed_gate] = False

    # Act
    decision = GenericGovernanceEngine().evaluate(
        decision_id="stop",
        contract=_contract(),
        comparison=_comparison(),
        assurance=_assurance(
            quality=values["quality"],
            safety=values["safety"],
            compliance=values["compliance"],
            business_outcome=values["business"],
        ),
    )

    # Assert
    assert decision.action is GenericGovernanceAction.STOP


@pytest.mark.parametrize(
    ("comparison", "assurance"),
    [
        (
            _comparison(treatment_evidence=EvidenceStatus.INSUFFICIENT),
            _assurance(),
        ),
        (_comparison(), _assurance(safety=None)),
        (_comparison(treatment_verified=0, treatment_cost="0"), _assurance()),
    ],
)
def test_given_incomplete_gate_evidence_when_evaluated_then_reports_insufficient(
    comparison: ProcessEconomicsComparison,
    assurance: GovernanceAssurance,
) -> None:
    # Act
    decision = GenericGovernanceEngine().evaluate(
        decision_id="insufficient",
        contract=_contract(),
        comparison=comparison,
        assurance=assurance,
    )

    # Assert
    assert decision.action is GenericGovernanceAction.INSUFFICIENT_EVIDENCE


def test_given_estimates_pass_without_reconciled_costs_when_evaluated_then_monitors() -> None:
    # Act
    decision = GenericGovernanceEngine().evaluate(
        decision_id="monitor",
        contract=_contract(),
        comparison=_comparison(),
        assurance=_assurance(reconciled=False),
    )

    # Assert
    assert decision.action is GenericGovernanceAction.MONITOR
    assert next(
        result
        for result in decision.gate_results
        if result.gate is GovernanceGate.UNIT_COST
    ).status is GateStatus.PASS


def test_given_review_token_ratio_fails_when_evaluated_then_recommends_threshold() -> None:
    # Act
    decision = GenericGovernanceEngine().evaluate(
        decision_id="token-optimize",
        contract=_contract(),
        comparison=_comparison(),
        assurance=_assurance(),
        token_policy=_token_policy(),
        token_comparison=_token_comparison(),
        review_attribution=_review_attribution(),
    )

    # Assert
    assert decision.action is GenericGovernanceAction.OPTIMIZE
    assert decision.optimization_recommendations[0].lever is (
        OptimizationLever.REVIEW_THRESHOLD
    )
    assert "Narrow review triggers" in decision.recommended_actions[0]


def test_given_quality_fails_when_tokens_improve_then_hard_gate_still_stops() -> None:
    # Act
    decision = GenericGovernanceEngine().evaluate(
        decision_id="token-stop",
        contract=_contract(),
        comparison=_comparison(),
        assurance=_assurance(quality=False),
        token_policy=_token_policy(),
        token_comparison=_token_comparison(),
        review_attribution=_review_attribution(),
    )

    # Assert
    assert decision.action is GenericGovernanceAction.STOP


def test_given_token_policy_without_token_evidence_then_evidence_is_insufficient() -> None:
    # Act
    decision = GenericGovernanceEngine().evaluate(
        decision_id="token-missing",
        contract=_contract(),
        comparison=_comparison(),
        assurance=_assurance(),
        token_policy=_token_policy(),
    )

    # Assert
    assert decision.action is GenericGovernanceAction.INSUFFICIENT_EVIDENCE
    token_results = [
        result
        for result in decision.gate_results
        if result.gate
        in {
            GovernanceGate.TOKEN_BUDGET,
            GovernanceGate.TOKEN_EFFICIENCY,
            GovernanceGate.REVIEW_WASTE,
            GovernanceGate.RETRY_WASTE,
        }
    ]
    assert {result.status for result in token_results} == {GateStatus.UNKNOWN}