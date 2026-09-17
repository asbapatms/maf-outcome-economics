---
title: Net Value Gate
description: How GenericGovernanceEngine evaluates the net savings economics gate
---

**Enum value:** `GovernanceGate.NET_VALUE` (`"net_value"`)
**Category:** Economics gate (always evaluated; a `FAIL` returns `OPTIMIZE`)

## What it measures

Whether the treatment variant nets out to a positive (or policy-defined
minimum) savings versus the control variant, not merely a lower unit cost.
Net value combines the volume of verified outcomes with the per-outcome cost
difference, so a cheaper-but-much-smaller treatment run does not
automatically pass.

## How it is evaluated

In [core/governance.py](../../src/maf_outcome_economics/core/governance.py):

```python
net_value = comparison.net_savings
status = (
    GateStatus.UNKNOWN if net_value is None
    else GateStatus.PASS if net_value >= self._policy.minimum_net_value
    else GateStatus.FAIL
)
```

`minimum_net_value` comes from `GenericGovernancePolicy` and defaults to `0`
— meaning the treatment must save at least as much as it costs relative to
the control, with no built-in tolerance, unless the caller configures a
larger minimum.

* `PASS` — `comparison.net_savings` is at or above the policy minimum.
* `FAIL` — net savings falls below the policy minimum (including negative
  values, meaning the treatment is net more expensive).
* `UNKNOWN` — net savings cannot be computed (for example, insufficient
  evidence on one side of the comparison).

## What happens when it fails

A `FAIL` here (with no stop-gate failure or unknown) returns `OPTIMIZE`, with
the same generic recommendation as [unit cost](./unit_cost.md): "Improve
failed economic or token gates before scaling." No typed
`OptimizationRecommendation` is generated for this gate.

## Worked example (ticket demo)

The live ticket demo instantiates `GenericGovernanceEngine()` with the default
`GenericGovernancePolicy()`, so `minimum_net_value` is `0`. The dashboard's
"Net savings vs. control" KPI is the exact `comparison.net_savings` value this
gate checks.

## Related evidence

* `ProcessEconomicsComparison` in
  [core/comparison.py](../../src/maf_outcome_economics/core/comparison.py).
* [Governance gates index](./README.md) for economics-gate ordering.
