---
title: Token Budget Gate
description: How GenericGovernanceEngine evaluates the tokens-per-verified-outcome budget gate
---

**Enum value:** `GovernanceGate.TOKEN_BUDGET` (`"token_budget"`)
**Category:** Token economics gate (only evaluated when a `TokenGovernancePolicy`
is supplied; a `FAIL` returns `OPTIMIZE`)

## What it measures

Whether the treatment variant's token consumption per independently verified
outcome stays within a hard budget, regardless of dollar cost. This catches
runaway prompt or output growth even when per-token pricing happens to be
cheap.

## How it is evaluated

`_token_gate_results` and `_threshold_result`
(in [core/governance.py](../../src/maf_outcome_economics/core/governance.py))
compare `treatment.tokens_per_verified_outcome` against
`TokenGovernancePolicy.maximum_tokens_per_verified_outcome`:

* `PASS` — tokens per verified outcome is at or below the maximum.
* `FAIL` — tokens per verified outcome exceeds the maximum.
* `UNKNOWN` — no verified outcomes exist yet, so the ratio is undefined.

## What happens when it fails

A `FAIL` returns `OPTIMIZE` and generates a typed `OptimizationRecommendation`
with `lever=OptimizationLever.OUTPUT_LIMIT`:

> Reduce response limits or prompt context before scaling.

The recommendation's `evidence_metric` is `tokens_per_verified_outcome`, with
`observed_value` and `target_value` populated directly from the comparison
and policy so the recommendation is traceable to the same numbers shown in
the gate table.

## Worked example (ticket demo)

The live ticket demo's `TokenGovernancePolicy`
(in [scenarios/ticket/analysis.py](../../src/maf_outcome_economics/scenarios/ticket/analysis.py))
sets `maximum_tokens_per_verified_outcome=300`. If the treatment variant
consumes, for example, 350 tokens per verified outcome, this gate fails and
the dashboard's "Optimization recommendations" table shows the `Output Limit`
lever with observed `350` against target `300`.

## Related evidence

* `TokenEfficiencyComparison` and `TokenSummary` in
  [core/tokens.py](../../src/maf_outcome_economics/core/tokens.py).
* [Governance gates index](./README.md) for token-economics gate ordering.
