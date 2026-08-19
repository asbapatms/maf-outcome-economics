"""Persistence adapters."""

from .seed import (
	DEMO_SCENARIO_TICKETS,
	FICTIONAL_TICKETS,
	DemoScenario,
	contract_id_for_variant,
	seed_demo_scenario,
	seed_fictional_tickets,
	seeded_contract,
)
from .sqlite_repository import OutcomeRepository

__all__ = [
	"DEMO_SCENARIO_TICKETS",
	"FICTIONAL_TICKETS",
	"DemoScenario",
	"OutcomeRepository",
	"contract_id_for_variant",
	"seed_demo_scenario",
	"seed_fictional_tickets",
	"seeded_contract",
]