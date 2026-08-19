"""Deterministic evidence verification."""

from maf_outcome_economics.domain import Outcome


def verify_outcome(outcome: Outcome) -> bool:
    """Require evidence and an observed value different from the baseline."""
    return bool(outcome.evidence) and outcome.observed_value != outcome.baseline_value