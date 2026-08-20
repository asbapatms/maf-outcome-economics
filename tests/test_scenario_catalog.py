"""Tests for generic scenario discovery metadata."""

from maf_outcome_economics.scenarios import (
    SCENARIO_CATALOG,
    ScenarioId,
    get_scenario_descriptor,
)


def test_given_reference_scenarios_when_catalog_loaded_then_ids_are_unique() -> None:
    # Act
    scenario_ids = [item.id for item in SCENARIO_CATALOG]

    # Assert
    assert scenario_ids == [
        ScenarioId.TICKET_TRIAGE,
        ScenarioId.INVOICE_PROCESSING,
    ]
    assert len(scenario_ids) == len(set(scenario_ids))


def test_given_scenario_id_when_descriptor_requested_then_shortcut_is_returned() -> None:
    # Act
    descriptor = get_scenario_descriptor(ScenarioId.INVOICE_PROCESSING)

    # Assert
    assert descriptor.name == "Invoice processing"
    assert descriptor.shortcut == "invoice-demo"