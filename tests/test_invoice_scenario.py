"""Tests for the generic invoice-processing reference scenario."""

from decimal import Decimal

from maf_outcome_economics.connectors import CostSource, EvidenceSource, WorkUnitSource
from maf_outcome_economics.core import CostCategory, GenericGovernanceAction
from maf_outcome_economics.scenarios import InvoiceProcessingScenario


async def test_given_invoice_records_when_scenario_runs_then_generic_pipeline_scales() -> None:
    # Arrange
    scenario = InvoiceProcessingScenario()

    # Act
    result = await scenario.run()

    # Assert
    assert result.verification.total_work_units == 4
    assert result.verification.verified_outcomes == 4
    assert result.comparison.control.cost_per_verified_outcome == Decimal("12")
    assert result.comparison.treatment.cost_per_verified_outcome == Decimal("3")
    assert result.comparison.net_savings == Decimal("18")
    assert result.decision.action is GenericGovernanceAction.SCALE


async def test_given_invoice_connector_when_loaded_then_contracts_are_structural() -> None:
    # Arrange
    scenario = InvoiceProcessingScenario()
    work_source: WorkUnitSource = scenario.connector
    evidence_source: EvidenceSource = scenario.connector
    cost_source: CostSource = scenario.connector
    period = (await scenario.run()).period

    # Act
    work_units = await work_source.load_work_units(period)
    evidence = await evidence_source.load_evidence(period)
    costs = await cost_source.load_costs(period)

    # Assert
    assert len(work_units) == 4
    assert len(evidence) == 12
    assert sum(cost.amount for cost in costs) == Decimal("30")
    assert {cost.category for cost in costs} == {
        CostCategory.HUMAN_PROCESSING,
        CostCategory.PLATFORM,
        CostCategory.MODEL,
    }