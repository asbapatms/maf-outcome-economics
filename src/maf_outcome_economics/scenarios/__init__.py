"""Runnable reference scenarios built on the generic economics core."""

from .catalog import (
	SCENARIO_CATALOG,
	ScenarioDescriptor,
	ScenarioId,
	get_scenario_descriptor,
)
from .invoice import InvoiceProcessingScenario
from .ticket import TicketScenario

__all__ = [
	"SCENARIO_CATALOG",
	"InvoiceProcessingScenario",
	"ScenarioDescriptor",
	"ScenarioId",
	"TicketScenario",
	"get_scenario_descriptor",
]