"""Deterministic governance decisions for verified outcome economics."""

from collections.abc import Iterable
from decimal import Decimal

from maf_outcome_economics.domain import (
    GovernanceAction,
    GovernanceDecision,
    GovernanceEvidence,
    GovernanceReasonCode,
    OutcomeContract,
    OutcomeEconomics,
    RoutingVerificationResult,
)
from maf_outcome_economics.persistence import OutcomeRepository


class GovernanceEngine:
    """Evaluate quality, safety, and budget gates in deterministic order."""

    def __init__(self, repository: OutcomeRepository | None = None) -> None:
        self.repository = repository

    def evaluate(
        self,
        *,
        decision_id: str,
        contract: OutcomeContract,
        economics: OutcomeEconomics,
        verifications: Iterable[RoutingVerificationResult],
        decided_by: str = "governance-engine",
    ) -> GovernanceDecision:
        """Return and optionally persist a SCALE, OPTIMIZE, or STOP decision."""
        evidence = self._evidence(contract, economics, verifications)
        reason_codes = self._stop_reasons(contract, evidence)
        if reason_codes:
            action = GovernanceAction.STOP
            recommended_actions = self._stop_actions(reason_codes)
        elif evidence.cost_per_accepted_outcome is None:
            raise ValueError("Accepted outcomes require a cost per accepted outcome")
        elif evidence.cost_per_accepted_outcome > (
            contract.maximum_cost_per_accepted_outcome
        ):
            action = GovernanceAction.OPTIMIZE
            reason_codes = [GovernanceReasonCode.COST_EXCEEDS_BUDGET]
            recommended_actions = [
                "Reduce retries, coordination calls, or model cost before scaling."
            ]
        else:
            action = GovernanceAction.SCALE
            reason_codes = [GovernanceReasonCode.THRESHOLDS_MET]
            recommended_actions = [
                "Scale the workflow while monitoring quality, safety, and unit cost."
            ]
        decision = GovernanceDecision(
            id=decision_id,
            contract_id=contract.id,
            action=action,
            reason=", ".join(code.value for code in reason_codes),
            reason_codes=reason_codes,
            evidence_metrics=evidence,
            recommended_actions=recommended_actions,
            decided_by=decided_by,
        )
        if self.repository is not None:
            self.repository.save_governance_decision(decision)
        return decision

    @staticmethod
    def _evidence(
        contract: OutcomeContract,
        economics: OutcomeEconomics,
        verifications: Iterable[RoutingVerificationResult],
    ) -> GovernanceEvidence:
        if economics.currency != contract.budget_currency:
            raise ValueError("Economics and contract budget currencies must match")
        unique = {result.id: result for result in verifications}
        results = list(unique.values())
        total_outcomes = len(results)
        accepted_outcomes = sum(result.accepted for result in results)
        if accepted_outcomes != economics.accepted_outcomes:
            raise ValueError("Economics accepted outcomes must match verification evidence")
        acceptance_rate = (
            Decimal(accepted_outcomes) / total_outcomes
            if total_outcomes
            else Decimal(0)
        )
        correct_fields = sum(
            (
                result.category_correct
                + result.priority_correct
                + result.resolver_group_correct
            )
            for result in results
        )
        average_quality_score = (
            Decimal(correct_fields) / Decimal(total_outcomes * 3)
            if total_outcomes
            else Decimal(0)
        )
        critical_results = [
            result for result in results if result.critical_priority_expected
        ]
        critical_recalled = sum(
            result.critical_priority_recalled is True for result in critical_results
        )
        critical_priority_recall = (
            Decimal(critical_recalled) / len(critical_results)
            if critical_results
            else Decimal(1)
        )
        return GovernanceEvidence(
            total_outcomes=total_outcomes,
            accepted_outcomes=accepted_outcomes,
            acceptance_rate=acceptance_rate,
            average_quality_score=average_quality_score,
            critical_outcomes=len(critical_results),
            critical_priority_recall=critical_priority_recall,
            cost_per_accepted_outcome=economics.cost_per_accepted_outcome,
            maximum_cost_per_accepted_outcome=(
                contract.maximum_cost_per_accepted_outcome
            ),
            currency=economics.currency,
        )

    @staticmethod
    def _stop_reasons(
        contract: OutcomeContract,
        evidence: GovernanceEvidence,
    ) -> list[GovernanceReasonCode]:
        reasons: list[GovernanceReasonCode] = []
        if evidence.accepted_outcomes == 0:
            reasons.append(GovernanceReasonCode.NO_ACCEPTED_OUTCOMES)
        if evidence.acceptance_rate < contract.minimum_acceptance_rate:
            reasons.append(GovernanceReasonCode.ACCEPTANCE_BELOW_MINIMUM)
        if evidence.average_quality_score < contract.minimum_quality_score:
            reasons.append(GovernanceReasonCode.QUALITY_BELOW_MINIMUM)
        if (
            evidence.critical_priority_recall
            < contract.minimum_critical_priority_recall
        ):
            reasons.append(GovernanceReasonCode.CRITICAL_RECALL_BELOW_MINIMUM)
        return reasons

    @staticmethod
    def _stop_actions(reason_codes: Iterable[GovernanceReasonCode]) -> list[str]:
        reasons = set(reason_codes)
        actions = ["Stop rollout and investigate failed governance gates."]
        if GovernanceReasonCode.CRITICAL_RECALL_BELOW_MINIMUM in reasons:
            actions.append("Correct Critical-priority under-classification before retrying.")
        if GovernanceReasonCode.NO_ACCEPTED_OUTCOMES in reasons:
            actions.append("Collect accepted outcomes before reconsidering deployment.")
        return actions