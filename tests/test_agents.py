"""Tests for structured support-ticket agents."""

import pytest
from agent_framework import Agent
from fake_agent_provider import DeterministicFakeProvider

from maf_outcome_economics.agents import (
    MalformedAgentOutputError,
    PromptProfile,
    ReviewAgent,
    TriageAgent,
)
from maf_outcome_economics.agents.prompts import render_triage_prompt
from maf_outcome_economics.domain import Ticket


@pytest.fixture()
def ticket() -> Ticket:
    """Return a fictional ticket with labels that prompts must not expose."""
    return Ticket(
        id="TKT-001",
        subject="Account locked after password reset",
        description="A fictional user cannot sign in after completing a password reset.",
        gold_category="SECRET-GOLD-CATEGORY",
        gold_priority="P1",
        gold_resolver_group="SECRET-GOLD-GROUP",
    )


def test_given_profiles_when_rendering_triage_then_optimized_is_shorter_and_labels_are_hidden(
    ticket: Ticket,
) -> None:
    # Act
    baseline = render_triage_prompt(ticket, "run-test", PromptProfile.BASELINE)
    optimized = render_triage_prompt(ticket, "run-test", PromptProfile.OPTIMIZED)

    # Assert
    assert len(optimized) < len(baseline)
    assert "SECRET-GOLD" not in baseline + optimized


@pytest.mark.asyncio
async def test_given_deterministic_fake_when_triage_runs_then_returns_typed_result(
    ticket: Ticket,
    mocker,
) -> None:
    # Arrange
    provider = DeterministicFakeProvider()
    agent = mocker.MagicMock(spec=Agent)
    triage_agent = TriageAgent(agent, provider)

    # Act
    result = await triage_agent.run(ticket, "run-test")

    # Assert
    assert result.ticket_id == ticket.id
    assert result.priority == "P2"


@pytest.mark.asyncio
async def test_given_fenced_json_when_triage_runs_then_parses_without_retry(
    ticket: Ticket,
    mocker,
) -> None:
    # Arrange
    output = """```json
{"run_id":"run-test","ticket_id":"TKT-001","category":"Identity","priority":"P2",
"resolver_group":"Identity Operations","confidence":0.9,"rationale":"Account lockout."}
```"""
    provider = DeterministicFakeProvider([output])
    triage_agent = TriageAgent(mocker.MagicMock(spec=Agent), provider)

    # Act
    result = await triage_agent.run(ticket, "run-test")

    # Assert
    assert result.category == "Identity"
    assert len(provider.prompts) == 1


@pytest.mark.asyncio
async def test_given_malformed_then_valid_json_when_triage_runs_then_retries_once(
    ticket: Ticket,
    mocker,
) -> None:
    # Arrange
    valid = (
        '{"run_id":"run-test","ticket_id":"TKT-001","category":"Identity",'
        '"priority":"P2","resolver_group":"Identity Operations","confidence":0.9,'
        '"rationale":"Account lockout."}'
    )
    provider = DeterministicFakeProvider(["not json", valid])
    triage_agent = TriageAgent(mocker.MagicMock(spec=Agent), provider)

    # Act
    result = await triage_agent.run(ticket, "run-test")

    # Assert
    assert result.run_id == "run-test"
    assert len(provider.prompts) == 2
    assert "previous response was malformed" in provider.prompts[1]


@pytest.mark.asyncio
async def test_given_two_malformed_outputs_when_triage_runs_then_raises(
    ticket: Ticket,
    mocker,
) -> None:
    # Arrange
    provider = DeterministicFakeProvider(["not json", "still not json"])
    triage_agent = TriageAgent(mocker.MagicMock(spec=Agent), provider)

    # Act & Assert
    with pytest.raises(MalformedAgentOutputError):
        await triage_agent.run(ticket, "run-test")
    assert len(provider.prompts) == 2


def test_agents_have_stable_names_and_ids() -> None:
    # Assert
    assert TriageAgent.ID == "maf-outcome-economics.triage.v1"
    assert TriageAgent.NAME == "TriageAgent"
    assert ReviewAgent.ID == "maf-outcome-economics.review.v1"
    assert ReviewAgent.NAME == "ReviewAgent"