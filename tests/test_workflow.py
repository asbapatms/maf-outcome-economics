"""Tests for the Agent Framework workflow."""

from decimal import Decimal

import pytest

from maf_outcome_economics.domain import Outcome
from maf_outcome_economics.workflows import assessment_workflow


@pytest.mark.asyncio
async def test_given_outcome_when_workflow_runs_then_report_is_output() -> None:
    # Arrange
    outcome = Outcome(
        name="Throughput",
        baseline_value=Decimal("5"),
        observed_value=Decimal("7"),
        value_per_unit=Decimal("10"),
        implementation_cost=Decimal("5"),
        evidence=["measurement"],
    )

    # Act
    result = await assessment_workflow.run(outcome)

    # Assert
    assert result.get_outputs() == ["Throughput: net value 15.00, ROI 300.00%, verified=True"]