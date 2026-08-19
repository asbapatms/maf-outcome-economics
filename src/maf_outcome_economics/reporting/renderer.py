"""Plain-text assessment reporting."""

from maf_outcome_economics.domain import EconomicAssessment


def render_assessment(assessment: EconomicAssessment) -> str:
    """Render a concise assessment summary."""
    roi = (
        "n/a"
        if assessment.return_on_investment is None
        else f"{assessment.return_on_investment:.2%}"
    )
    return (
        f"{assessment.outcome_name}: net value {assessment.net_value:.2f}, "
        f"ROI {roi}, verified={assessment.verified}"
    )