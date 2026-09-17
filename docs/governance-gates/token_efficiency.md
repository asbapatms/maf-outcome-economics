---
title: Token Efficiency Gate
description: How GenericGovernanceEngine evaluates the minimum-efficiency-improvement gate
---

**Enum value:** `GovernanceGate.TOKEN_EFFICIENCY` (`"token_efficiency"`)
**Category:** Token economics gate (only evaluated when a `TokenGovernancePolicy`
is supplied; a `FAIL` returns `OPTIMIZE`)

## What it measures

Whether the treatment variant improves token efficiency by at least the
policy-required margin relative to a token-equivalent control run. This gate
is about relative improvement, not an absolute ceiling — it is the
complement of the [token budget gate](./token_budget.md), which only checks an
absolute limit.

## How it is evaluated

`_token_gate_results` and `_threshold_result`
(in [core/governance.py](../../src/maf_outcome_economics/core/governance.py))
compare `TokenEfficiencyComparison.efficiency_improvement` against
`TokenGovernancePolicy.minimum_efficiency_improvement`:

* `PASS` — efficiency improvement is at or above the minimum.
* `FAIL` — efficiency improvement is below the minimum.
* `UNKNOWN` — efficiency improvement cannot be computed (for example, the
  control has no comparable token baseline).

## What happens when it fails

A `FAIL` returns `OPTIMIZE` and generates a typed `OptimizationRecommendation`
with `lever=OptimizationLever.PROMPT_PROFILE`:

> Use the concise prompt profile for routine work and remeasure.

When every token gate passes instead, the engine still appends a
`REVIEW_THRESHOLD`-lever recommendation confirming the policy is met:

> Retain risk-based review triggers and monitor skipped routine work.

## Worked example (ticket demo)

The live ticket demo's `TokenGovernancePolicy`
(in [scenarios/ticket/analysis.py](../../src/maf_outcome_economics/scenarios/ticket/analysis.py))
sets `minimum_efficiency_improvement=Decimal("0.1")` (10%). The dashboard's
"Token efficiency improvement" KPI is the exact
`token_comparison.efficiency_improvement` value this gate checks.

## Related evidence

* `TokenEfficiencyComparison` in
  [core/tokens.py](../../src/maf_outcome_economics/core/tokens.py).
* [Governance gates index](./README.md) for token-economics gate ordering.
