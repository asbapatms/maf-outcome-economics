"""Tests for normalized model-call outcome economics."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from maf_outcome_economics.domain import (
    BillableModelCall,
    PricingRecord,
    Ticket,
)
from maf_outcome_economics.economics import OutcomeEconomicsCalculator
from maf_outcome_economics.verification import verify_routing_outcome

TIMESTAMP = datetime(2026, 8, 19, tzinfo=UTC)


def _pricing(
    *,
    provider: str = "provider",
    model: str = "model",
    currency: str = "USD",
) -> PricingRecord:
    return PricingRecord(
        id=f"price-{provider}-{model}",
        provider=provider,
        model=model,
        input_cost_per_million_tokens=Decimal("2"),
        output_cost_per_million_tokens=Decimal("8"),
        currency=currency,
    )


def _call(
    span_id: str,
    *,
    business_task_id: str = "task-1",
    input_tokens: int = 100_000,
    output_tokens: int = 10_000,
    agent_id: str = "triage-agent",
    agent_name: str | None = "TriageAgent",
    operation_name: str = "chat",
    seconds: int = 0,
    provider: str = "provider",
    model: str = "model",
) -> BillableModelCall:
    return BillableModelCall(
        trace_id=f"trace-{span_id}",
        span_id=span_id,
        business_task_id=business_task_id,
        provider=provider,
        model=model,
        operation_name=operation_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        agent_id=agent_id,
        agent_name=agent_name,
        recorded_at=TIMESTAMP + timedelta(seconds=seconds),
    )


def _verification(*, accepted: bool):
    ticket = Ticket(
        id="ticket-accepted" if accepted else "ticket-rejected",
        subject="Fictional economics ticket",
        description="A fictional ticket for deterministic economics tests.",
        gold_category="Application",
        gold_priority="P3",
        gold_resolver_group="Business Applications",
    )
    return verify_routing_outcome(
        verification_id=f"verification-{ticket.id}",
        contract_id="contract-economics",
        run_id=f"run-{ticket.id}",
        ticket=ticket,
        final_category="Application" if accepted else "Network",
        final_priority="P3",
        final_resolver_group="Business Applications",
    )


def test_given_unique_chat_calls_when_calculated_then_reports_all_economics() -> None:
    # Arrange
    calculator = OutcomeEconomicsCalculator([_pricing()])
    first_attempt = _call("span-1")
    retry = _call(
        "span-2",
        input_tokens=50_000,
        output_tokens=5_000,
        seconds=1,
    )
    review = _call(
        "span-3",
        input_tokens=20_000,
        output_tokens=2_000,
        agent_id="review-agent",
        agent_name="ReviewAgent",
        seconds=2,
    )
    other_task = _call(
        "span-4",
        business_task_id="task-2",
        input_tokens=30_000,
        output_tokens=3_000,
        seconds=3,
    )

    # Act
    result = calculator.calculate(
        [first_attempt, retry, review, other_task],
        [
            _verification(accepted=True),
            _verification(accepted=True),
            _verification(accepted=False),
        ],
    )

    # Assert
    assert result.total_input_tokens == 200_000
    assert result.total_output_tokens == 20_000
    assert result.estimated_model_cost == Decimal("0.560")
    assert result.accepted_outcomes == 1
    assert result.cost_per_accepted_outcome == Decimal("0.560")
    assert result.tokens_per_accepted_outcome == Decimal("220000")
    assert result.agent_contribution_cost == {
        "review-agent": Decimal("0.056"),
        "triage-agent": Decimal("0.504"),
    }
    assert result.retry_tax == Decimal("0.140")
    assert result.coordination_tax == Decimal("0.056")


def test_given_duplicate_chat_and_agent_span_when_calculated_then_bills_chat_once() -> None:
    # Arrange
    calculator = OutcomeEconomicsCalculator([_pricing()])
    chat = _call("same-span")
    duplicate_chat = chat.model_copy(update={"input_tokens": 999_999})
    agent_span = _call(
        "agent-span",
        operation_name="invoke_agent",
        input_tokens=900_000,
        output_tokens=900_000,
    )

    # Act
    result = calculator.calculate(
        [chat, duplicate_chat, agent_span],
        [_verification(accepted=True)],
    )

    # Assert
    assert result.total_input_tokens == 100_000
    assert result.total_output_tokens == 10_000
    assert result.estimated_model_cost == Decimal("0.280")
    assert result.retry_tax == Decimal("0")


def test_given_no_accepted_outcomes_when_calculated_then_per_outcome_values_are_none() -> None:
    # Arrange
    calculator = OutcomeEconomicsCalculator([_pricing()])

    # Act
    result = calculator.calculate([_call("span-1")], [_verification(accepted=False)])

    # Assert
    assert result.accepted_outcomes == 0
    assert result.cost_per_accepted_outcome is None
    assert result.tokens_per_accepted_outcome is None


def test_given_same_agent_on_distinct_tasks_when_calculated_then_not_retry_tax() -> None:
    # Arrange
    calculator = OutcomeEconomicsCalculator([_pricing()])

    # Act
    result = calculator.calculate(
        [
            _call("span-1", business_task_id="task-1"),
            _call("span-2", business_task_id="task-2", seconds=1),
        ],
        [],
    )

    # Assert
    assert result.retry_tax == Decimal("0")


@pytest.mark.parametrize(
    "agent_name",
    ["ReviewerAgent", "PolicyCritic", "ResultAggregator"],
)
def test_given_coordination_role_when_calculated_then_call_cost_is_coordination_tax(
    agent_name: str,
) -> None:
    # Arrange
    calculator = OutcomeEconomicsCalculator([_pricing()])

    # Act
    result = calculator.calculate(
        [_call("span-1", agent_id="coordinator", agent_name=agent_name)],
        [],
    )

    # Assert
    assert result.coordination_tax == Decimal("0.280")


def test_given_unpriced_model_when_calculated_then_raises() -> None:
    # Arrange
    calculator = OutcomeEconomicsCalculator([_pricing()])

    # Act and assert
    with pytest.raises(ValueError, match="Missing pricing"):
        calculator.calculate([_call("span-1", model="unpriced")], [])


def test_given_mixed_pricing_currencies_when_created_then_raises() -> None:
    # Act and assert
    with pytest.raises(ValueError, match="one currency"):
        OutcomeEconomicsCalculator(
            [_pricing(), _pricing(provider="other", currency="EUR")]
        )