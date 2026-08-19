"""Tests for deterministic economic calculations."""

from decimal import Decimal

from maf_outcome_economics.domain import Outcome
from maf_outcome_economics.economics import assess_outcome


def test_given_verified_outcome_when_assessed_then_returns_net_value() -> None:
    # Arrange
    outcome = Outcome(
        name="Cycle time reduction",
        baseline_value=Decimal("10"),
        observed_value=Decimal("14"),
        value_per_unit=Decimal("100"),
        implementation_cost=Decimal("200"),
        evidence=["experiment-42"],
    )

    # Act
    assessment = assess_outcome(outcome)

    # Assert
    assert assessment.net_value == Decimal("200")
    assert assessment.verified is True