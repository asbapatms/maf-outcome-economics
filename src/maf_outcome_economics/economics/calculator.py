"""Deterministic outcome economics calculations."""

from maf_outcome_economics.domain import EconomicAssessment, Outcome
from maf_outcome_economics.verification import verify_outcome


def assess_outcome(outcome: Outcome) -> EconomicAssessment:
    """Calculate incremental value, net value, and return on investment."""
    incremental_units = outcome.observed_value - outcome.baseline_value
    gross_value = incremental_units * outcome.value_per_unit
    net_value = gross_value - outcome.implementation_cost
    roi = net_value / outcome.implementation_cost if outcome.implementation_cost else None
    return EconomicAssessment(
        outcome_name=outcome.name,
        incremental_units=incremental_units,
        gross_value=gross_value,
        net_value=net_value,
        return_on_investment=roi,
        verified=verify_outcome(outcome),
    )