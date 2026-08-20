"""Compatibility exports for support-ticket scenario fixtures."""

from maf_outcome_economics.scenarios.ticket.seed import (
    DEMO_SCENARIO_TICKETS,
    FICTIONAL_TICKETS,
    DemoScenario,
    contract_id_for_variant,
    seed_demo_scenario,
    seed_fictional_tickets,
    seeded_contract,
)

__all__ = [
    "DEMO_SCENARIO_TICKETS",
    "FICTIONAL_TICKETS",
    "DemoScenario",
    "contract_id_for_variant",
    "seed_demo_scenario",
    "seed_fictional_tickets",
    "seeded_contract",
]