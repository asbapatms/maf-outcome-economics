"""Tests for the support-ticket scenario composition root."""

from maf_outcome_economics.config import Settings
from maf_outcome_economics.domain import WorkflowVariant
from maf_outcome_economics.persistence import DemoScenario, OutcomeRepository
from maf_outcome_economics.scenarios import TicketScenario


def test_given_standard_dataset_when_scenario_seeds_then_contracts_and_tickets_exist(
    tmp_path,
) -> None:
    # Arrange
    repository = OutcomeRepository(tmp_path / "scenario.db")
    scenario = TicketScenario()

    # Act
    count = scenario.seed(repository)

    # Assert
    assert count == 20
    assert len(repository.list_tickets()) == 20
    assert repository.get_outcome_contract(
        scenario.contract_id(WorkflowVariant.BASELINE)
    ) is not None


def test_given_named_dataset_when_scenario_seeds_then_isolated_fixture_is_used(
    tmp_path,
) -> None:
    # Arrange
    repository = OutcomeRepository(tmp_path / "scenario.db")

    # Act
    count = TicketScenario().seed(repository, DemoScenario.STOP)

    # Assert
    assert count == 3
    assert {ticket.id for ticket in repository.list_tickets()} == {
        "STOP-001",
        "STOP-002",
        "STOP-003",
    }


def test_given_rehearsal_mode_when_suite_created_then_fake_agents_are_returned(
    tmp_path,
) -> None:
    # Arrange
    settings = Settings(database_path=tmp_path / "scenario.db")

    # Act
    suite = TicketScenario().create_agent_suite(settings, live=False)

    # Assert
    assert type(suite).__name__ == "RehearsalAgentSuite"