"""Outcome assessment workflow."""

from agent_framework import workflow

from maf_outcome_economics.domain import Outcome
from maf_outcome_economics.economics import assess_outcome
from maf_outcome_economics.reporting import render_assessment


@workflow
async def assessment_workflow(outcome: Outcome) -> str:
    """Assess and render an outcome through the functional workflow API."""
    return render_assessment(assess_outcome(outcome))