"""Tests for end-to-end generic ticket economics analysis."""

from decimal import Decimal

from maf_outcome_economics.config import Settings
from maf_outcome_economics.console_service import ConsoleProvider, ConsoleService
from maf_outcome_economics.core import (
    GateStatus,
    GenericGovernanceAction,
    GovernanceGate,
    OptimizationLever,
)
from maf_outcome_economics.domain import PricingRecord, WorkflowVariant
from maf_outcome_economics.persistence import OutcomeRepository, seed_fictional_tickets
from maf_outcome_economics.scenarios.ticket import TicketEconomicsAnalyzer


async def test_given_persisted_ticket_runs_when_analyzed_then_generic_core_is_used(
    tmp_path,
) -> None:
    # Arrange
    settings = Settings(database_path=tmp_path / "generic-ticket.db")
    repository = OutcomeRepository(settings.database_path)
    seed_fictional_tickets(repository)
    repository.save_pricing(
        PricingRecord(
            id="illustrative-pricing",
            provider="illustrative-provider",
            model="illustrative-model",
            input_cost_per_million_tokens=Decimal("2.5"),
            output_cost_per_million_tokens=Decimal("10"),
        )
    )
    service = ConsoleService(settings)
    for variant in WorkflowVariant:
        await service.run_variant(variant, 2, ConsoleProvider.FAKE)

    # Act
    analysis = await TicketEconomicsAnalyzer(repository).analyze()

    # Assert
    assert analysis.verification.total_work_units == 4
    assert analysis.verification.verified_outcomes == 4
    assert analysis.comparison.control.total_work_units == 2
    assert analysis.comparison.treatment.total_work_units == 2
    assert analysis.comparison.control.total_cost == Decimal("0.002")
    assert analysis.comparison.treatment.total_cost == Decimal("0.0016")
    assert analysis.comparison.net_savings == Decimal("0.0004")
    assert analysis.token_comparison.control.total_tokens == 500
    assert analysis.token_comparison.treatment.total_tokens == 400
    assert analysis.token_comparison.tokens_avoided == Decimal(100)
    assert analysis.token_comparison.efficiency_improvement == Decimal("0.2")
    assert analysis.control_review_attribution.reviews_invoked == 2
    assert analysis.control_review_attribution.total_review_tokens == 200
    assert analysis.treatment_review_attribution.reviews_invoked == 1
    assert analysis.treatment_review_attribution.total_review_tokens == 100
    assert analysis.decision.action is GenericGovernanceAction.MONITOR
    token_gates = {
        result.gate: result.status
        for result in analysis.decision.gate_results
        if result.gate
        in {
            GovernanceGate.TOKEN_BUDGET,
            GovernanceGate.TOKEN_EFFICIENCY,
            GovernanceGate.REVIEW_WASTE,
            GovernanceGate.RETRY_WASTE,
        }
    }
    assert set(token_gates.values()) == {GateStatus.PASS}
    assert analysis.decision.optimization_recommendations[0].lever is (
        OptimizationLever.REVIEW_THRESHOLD
    )