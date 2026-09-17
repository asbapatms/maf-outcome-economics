---
title: Unit Cost Gate
description: How GenericGovernanceEngine evaluates the per-verified-outcome cost economics gate
---

**Enum value:** `GovernanceGate.UNIT_COST` (`"unit_cost"`)
**Category:** Economics gate (always evaluated; a `FAIL` returns `OPTIMIZE`)

## What it measures

Whether the treatment variant's cost per independently verified outcome stays
within the contract's ceiling. This is computed directly by the engine from
`ProcessEconomicsComparison`, unlike the assurance gates above, which rely on
caller-supplied verdicts.

## How it is evaluated

In [core/governance.py](../../src/maf_outcome_economics/core/governance.py):

```python
unit_cost = treatment.cost_per_verified_outcome
status = (
    GateStatus.UNKNOWN if unit_cost is None
    else GateStatus.PASS if unit_cost <= contract.maximum_cost_per_verified_outcome
    else GateStatus.FAIL
)
```

* `PASS` — unit cost is at or below `OutcomeContract.maximum_cost_per_verified_outcome`.
* `FAIL` — unit cost exceeds the contract maximum.
* `UNKNOWN` — no verified outcomes exist yet, so `cost_per_verified_outcome`
  is `None` (division by zero is avoided upstream in `ProcessEconomicsComparison`).

## What happens when it fails

A `FAIL` here (with no stop-gate failure or unknown) returns `OPTIMIZE`. The
generic recommendation is: "Improve failed economic or token gates before
scaling." This gate does not currently produce a typed
`OptimizationRecommendation` — those are only generated for the four
token-economics gates
([token budget](./token_budget.md), [token efficiency](./token_efficiency.md),
[review waste](./review_waste.md), [retry waste](./retry_waste.md)).

## Worked example (ticket demo)

The generic contract built in
`TicketEconomicsAnalyzer._generic_contract`
(in [scenarios/ticket/analysis.py](../../src/maf_outcome_economics/scenarios/ticket/analysis.py))
sets `maximum_cost_per_verified_outcome` directly from the ticket-specific
seed data's `maximum_cost_per_accepted_outcome`. In the live dashboard KPI
row, "Cost / verified outcome" is the exact `unit_cost` value this gate
checks.

## Related evidence

* `ProcessEconomicsComparison` in
  [core/comparison.py](../../src/maf_outcome_economics/core/comparison.py).
* [Governance gates index](./README.md) for economics-gate ordering.
