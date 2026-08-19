"""Deterministic outcome economics calculations."""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from decimal import Decimal

from maf_outcome_economics.domain import (
    BillableModelCall,
    EconomicAssessment,
    Outcome,
    OutcomeEconomics,
    PricingRecord,
    RoutingVerificationResult,
)
from maf_outcome_economics.verification import verify_outcome

MILLION_TOKENS = Decimal(1_000_000)
COORDINATION_ROLES = ("review", "critic", "aggregator")


def assess_outcome(outcome: Outcome) -> EconomicAssessment:
    """Calculate incremental value, net value, and return on investment."""
    incremental_units = outcome.observed_value - outcome.baseline_value
    gross_value = incremental_units * outcome.value_per_unit
    net_value = gross_value - outcome.implementation_cost
    roi = net_value / outcome.implementation_cost if outcome.implementation_cost else None
    return EconomicAssessment(
        outcome_name=outcome.name,
        incremental_units=incremental_units,
        gross_value=gross_value,
        net_value=net_value,
        return_on_investment=roi,
        verified=verify_outcome(outcome),
    )


class OutcomeEconomicsCalculator:
    """Calculate economics from normalized unique chat model calls."""

    def __init__(self, pricing: Sequence[PricingRecord]) -> None:
        if not pricing:
            raise ValueError("At least one pricing record is required")
        currencies = {record.currency for record in pricing}
        if len(currencies) != 1:
            raise ValueError("All pricing records must use one currency")
        self._pricing = {(record.provider, record.model): record for record in pricing}
        self._currency = pricing[0].currency

    def calculate(
        self,
        model_calls: Iterable[BillableModelCall],
        verifications: Iterable[RoutingVerificationResult],
    ) -> OutcomeEconomics:
        """Aggregate usage, accepted outcomes, and operational cost taxes."""
        calls = self._unique_billable_calls(model_calls)
        unique_verifications = {result.id: result for result in verifications}
        accepted_outcomes = sum(
            result.accepted for result in unique_verifications.values()
        )
        total_input_tokens = sum(call.input_tokens for call in calls)
        total_output_tokens = sum(call.output_tokens for call in calls)
        total_tokens = total_input_tokens + total_output_tokens
        call_costs = {self._call_key(call): self._cost(call) for call in calls}
        estimated_model_cost = sum(call_costs.values(), start=Decimal(0))

        contribution: defaultdict[str, Decimal] = defaultdict(Decimal)
        for call in calls:
            contribution[self._agent_identity(call)] += call_costs[self._call_key(call)]

        retry_tax = self._retry_tax(calls, call_costs)
        coordination_tax = sum(
            (
                call_costs[self._call_key(call)]
                for call in calls
                if self._is_coordination(call)
            ),
            start=Decimal(0),
        )
        return OutcomeEconomics(
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            estimated_model_cost=estimated_model_cost,
            accepted_outcomes=accepted_outcomes,
            cost_per_accepted_outcome=(
                estimated_model_cost / accepted_outcomes
                if accepted_outcomes
                else None
            ),
            tokens_per_accepted_outcome=(
                Decimal(total_tokens) / accepted_outcomes
                if accepted_outcomes
                else None
            ),
            agent_contribution_cost=dict(sorted(contribution.items())),
            retry_tax=retry_tax,
            coordination_tax=coordination_tax,
            currency=self._currency,
        )

    @staticmethod
    def _call_key(call: BillableModelCall) -> tuple[str, str]:
        return call.trace_id, call.span_id

    def _unique_billable_calls(
        self, model_calls: Iterable[BillableModelCall]
    ) -> list[BillableModelCall]:
        unique: dict[tuple[str, str], BillableModelCall] = {}
        for call in model_calls:
            if call.operation_name != "chat":
                continue
            unique.setdefault(self._call_key(call), call)
        return sorted(
            unique.values(),
            key=lambda call: (call.recorded_at, call.trace_id, call.span_id),
        )

    def _cost(self, call: BillableModelCall) -> Decimal:
        pricing = self._pricing.get((call.provider, call.model))
        if pricing is None:
            raise ValueError(
                f"Missing pricing for provider={call.provider!r}, model={call.model!r}"
            )
        input_cost = (
            Decimal(call.input_tokens)
            * pricing.input_cost_per_million_tokens
            / MILLION_TOKENS
        )
        output_cost = (
            Decimal(call.output_tokens)
            * pricing.output_cost_per_million_tokens
            / MILLION_TOKENS
        )
        return input_cost + output_cost

    @staticmethod
    def _agent_identity(call: BillableModelCall) -> str:
        return call.agent_id or call.agent_name or call.executor_id or "unknown"

    def _retry_tax(
        self,
        calls: Sequence[BillableModelCall],
        call_costs: dict[tuple[str, str], Decimal],
    ) -> Decimal:
        attempts: defaultdict[tuple[str, str], int] = defaultdict(int)
        retry_tax = Decimal(0)
        for call in calls:
            key = (call.business_task_id, self._agent_identity(call))
            attempts[key] += 1
            if attempts[key] > 1:
                retry_tax += call_costs[self._call_key(call)]
        return retry_tax

    @staticmethod
    def _is_coordination(call: BillableModelCall) -> bool:
        identity = " ".join(
            value
            for value in (call.agent_id, call.agent_name, call.executor_id)
            if value
        ).lower()
        return any(role in identity for role in COORDINATION_ROLES)