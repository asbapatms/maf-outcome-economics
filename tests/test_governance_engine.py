"""Boundary tests for deterministic outcome governance."""

from decimal import Decimal

import pytest

from maf_outcome_economics.domain import (
    GovernanceAction,
    GovernanceReasonCode,
    OutcomeContract,
    OutcomeEconomics,
    OutcomeStatus,
    Ticket,
    Variant,
)
from maf_outcome_economics.governance import GovernanceEngine
from maf_outcome_economics.persistence import OutcomeRepository
from maf_outcome_economics.verification import verify_routing_outcome


def _contract() -> OutcomeContract:
    return OutcomeContract(
        id="contract-governance",
        name="Routing governance",
        description="Govern fictional ticket-routing outcomes.",
        variant=Variant.TREATMENT,
        status=OutcomeStatus.ACTIVE,
        metric_name="routing_quality",
        target_value=Decimal("0.8"),
        unit="ratio",
        measurement_window_days=7,
        minimum_acceptance_rate=Decimal("0.5"),
        minimum_quality_score=Decimal(5) / Decimal(6),
        minimum_critical_priority_recall=Decimal("1"),
        maximum_cost_per_accepted_outcome=Decimal("0.50"),
    )


def _economics(
    *,
    accepted_outcomes: int = 1,
    cost_per_accepted_outcome: Decimal | None = Decimal("0.50"),
) -> OutcomeEconomics:
    return OutcomeEconomics(
        total_input_tokens=100,
        total_output_tokens=20,
        estimated_model_cost=Decimal("0.50"),
        accepted_outcomes=accepted_outcomes,
        cost_per_accepted_outcome=cost_per_accepted_outcome,
        tokens_per_accepted_outcome=(Decimal("120") if accepted_outcomes else None),
        agent_contribution_cost={"triage-agent": Decimal("0.50")},
        retry_tax=Decimal("0"),
        coordination_tax=Decimal("0"),
        currency="USD",
    )


def _verification(
    identifier: str,
    *,
    accepted: bool = True,
    critical: bool = False,
):
    ticket = Ticket(
        id=f"ticket-{identifier}",
        subject="Fictional governance ticket",
        description="A fictional ticket used for governance boundaries.",
        gold_category="Application",
        gold_priority="P1" if critical else "P3",
        gold_resolver_group="Business Applications",
    )
    return verify_routing_outcome(
        verification_id=f"verification-{identifier}",
        contract_id="contract-governance",
        run_id=f"run-{identifier}",
        ticket=ticket,
        final_category="Application" if accepted else "Network",
        final_priority=("P1" if critical and accepted else "P2" if critical else "P3"),
        final_resolver_group="Business Applications",
    )


def test_given_all_metrics_at_threshold_when_evaluated_then_scales() -> None:
    # Arrange
    engine = GovernanceEngine()
    verifications = [
        _verification("accepted", critical=True),
        _verification("rejected", accepted=False),
    ]

    # Act
    decision = engine.evaluate(
        decision_id="decision-scale",
        contract=_contract(),
        economics=_economics(),
        verifications=verifications,
    )

    # Assert
    assert decision.action is GovernanceAction.SCALE
    assert decision.reason_codes == [GovernanceReasonCode.THRESHOLDS_MET]
    assert decision.evidence_metrics is not None
    assert decision.evidence_metrics.acceptance_rate == Decimal("0.5")
    assert decision.evidence_metrics.average_quality_score == Decimal(5) / Decimal(6)
    assert decision.evidence_metrics.critical_priority_recall == Decimal("1")
    assert decision.evidence_metrics.cost_per_accepted_outcome == Decimal("0.50")
    assert decision.recommended_actions


def test_given_quality_passes_and_cost_exceeds_budget_when_evaluated_then_optimizes() -> None:
    # Arrange
    engine = GovernanceEngine()

    # Act
    decision = engine.evaluate(
        decision_id="decision-optimize",
        contract=_contract(),
        economics=_economics(cost_per_accepted_outcome=Decimal("0.5001")),
        verifications=[_verification("accepted")],
    )

    # Assert
    assert decision.action is GovernanceAction.OPTIMIZE
    assert decision.reason_codes == [GovernanceReasonCode.COST_EXCEEDS_BUDGET]
    assert "Reduce" in decision.recommended_actions[0]


@pytest.mark.parametrize(
    ("contract_update", "verifications", "reason_code"),
    [
        (
            {"minimum_acceptance_rate": Decimal("0.5001")},
            [_verification("accepted"), _verification("rejected", accepted=False)],
            GovernanceReasonCode.ACCEPTANCE_BELOW_MINIMUM,
        ),
        (
            {"minimum_quality_score": Decimal("0.834")},
            [_verification("accepted"), _verification("rejected", accepted=False)],
            GovernanceReasonCode.QUALITY_BELOW_MINIMUM,
        ),
        (
            {},
            [_verification("critical", accepted=False, critical=True)],
            GovernanceReasonCode.CRITICAL_RECALL_BELOW_MINIMUM,
        ),
    ],
)
def test_given_quality_or_safety_below_boundary_when_evaluated_then_stops(
    contract_update,
    verifications,
    reason_code: GovernanceReasonCode,
) -> None:
    # Arrange
    accepted = sum(result.accepted for result in verifications)
    contract = _contract().model_copy(update=contract_update)
    economics = _economics(
        accepted_outcomes=accepted,
        cost_per_accepted_outcome=(Decimal("0.50") if accepted else None),
    )

    # Act
    decision = GovernanceEngine().evaluate(
        decision_id=f"decision-{reason_code.value}",
        contract=contract,
        economics=economics,
        verifications=verifications,
    )

    # Assert
    assert decision.action is GovernanceAction.STOP
    assert reason_code in decision.reason_codes


def test_given_no_accepted_outcomes_when_evaluated_then_stops() -> None:
    # Act
    decision = GovernanceEngine().evaluate(
        decision_id="decision-none",
        contract=_contract(),
        economics=_economics(accepted_outcomes=0, cost_per_accepted_outcome=None),
        verifications=[_verification("rejected", accepted=False)],
    )

    # Assert
    assert decision.action is GovernanceAction.STOP
    assert GovernanceReasonCode.NO_ACCEPTED_OUTCOMES in decision.reason_codes


def test_given_repository_when_evaluated_then_decision_is_persisted(tmp_path) -> None:
    # Arrange
    repository = OutcomeRepository(tmp_path / "governance.db")
    contract = _contract()
    repository.save_outcome_contract(contract)
    engine = GovernanceEngine(repository)

    # Act
    decision = engine.evaluate(
        decision_id="decision-persisted",
        contract=contract,
        economics=_economics(),
        verifications=[_verification("accepted")],
    )

    # Assert
    assert repository.list_governance_decisions(contract.id) == [decision]


def test_given_economics_disagrees_with_evidence_when_evaluated_then_raises() -> None:
    # Act and assert
    with pytest.raises(ValueError, match="accepted outcomes"):
        GovernanceEngine().evaluate(
            decision_id="decision-invalid",
            contract=_contract(),
            economics=_economics(accepted_outcomes=0, cost_per_accepted_outcome=None),
            verifications=[_verification("accepted")],
        )