"""Typed discovery catalog for runnable outcome-economics scenarios."""

from enum import StrEnum

from pydantic import Field

from maf_outcome_economics.core.models import CoreModel


class ScenarioId(StrEnum):
    """Stable identifier accepted by generic scenario commands."""

    TICKET_TRIAGE = "ticket-triage"
    INVOICE_PROCESSING = "invoice-processing"


class ScenarioDescriptor(CoreModel):
    """User-facing metadata for one runnable reference scenario."""

    id: ScenarioId
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    shortcut: str = Field(min_length=1)


SCENARIO_CATALOG = (
    ScenarioDescriptor(
        id=ScenarioId.TICKET_TRIAGE,
        name="Support ticket triage",
        description="Compare review-all and risk-based agent workflows.",
        shortcut="demo --provider fake",
    ),
    ScenarioDescriptor(
        id=ScenarioId.INVOICE_PROCESSING,
        name="Invoice processing",
        description="Compare manual and automated invoice processing costs.",
        shortcut="invoice-demo",
    ),
)


def get_scenario_descriptor(scenario_id: ScenarioId) -> ScenarioDescriptor:
    """Return catalog metadata for a stable scenario identifier."""
    return next(item for item in SCENARIO_CATALOG if item.id is scenario_id)