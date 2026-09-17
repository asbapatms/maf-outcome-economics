---
title: Retry Waste Gate
description: How GenericGovernanceEngine evaluates the retry-token ratio gate
---

**Enum value:** `GovernanceGate.RETRY_WASTE` (`"retry_waste"`)
**Category:** Token economics gate (only evaluated when a `TokenGovernancePolicy`
is supplied; a `FAIL` returns `OPTIMIZE`)

## What it measures

Whether repeated attempts at the same work — tokens tagged with
`TokenPurpose.RETRY` — consume too large a share of the treatment variant's
total tokens. A high retry ratio usually signals output validation failures
or flaky tool calls rather than genuinely new work.

## How it is evaluated

`_token_gate_results` and `_threshold_result`
(in [core/governance.py](../../src/maf_outcome_economics/core/governance.py))
compute:

```python
retry_ratio = (
    Decimal(treatment.purpose_breakdown[TokenPurpose.RETRY]) / total_tokens
    if treatment is not None and total_tokens
    else None
)
```

and compare it against `TokenGovernancePolicy.maximum_retry_token_ratio`:

* `PASS` — the retry-token ratio is at or below the maximum.
* `FAIL` — the ratio exceeds the maximum.
* `UNKNOWN` — no treatment token summary or no treatment tokens are available.

## What happens when it fails

A `FAIL` returns `OPTIMIZE` and generates a typed `OptimizationRecommendation`
with `lever=OptimizationLever.RETRY_POLICY`:

> Correct output validation failures before allowing another retry.

The recommendation's `evidence_metric` is `retry_token_ratio`, with
`observed_value` and `target_value` populated from the same ratio and policy
threshold used by the gate.

## Worked example (ticket demo)

The live ticket demo's `TokenGovernancePolicy`
(in [scenarios/ticket/analysis.py](../../src/maf_outcome_economics/scenarios/ticket/analysis.py))
sets `maximum_retry_token_ratio=Decimal("0.1")` (10%). The dashboard's "Token
efficiency: control vs. treatment" table's per-variant `total_tokens`, broken
down by `TokenPurpose` in `TokenSummary.purpose_breakdown`, is the source data
for this gate.

## Related evidence

* `TokenSummary.purpose_breakdown` and `TokenPurpose` in
  [core/tokens.py](../../src/maf_outcome_economics/core/tokens.py) and
  [core/models.py](../../src/maf_outcome_economics/core/models.py).
* [Governance gates index](./README.md) for token-economics gate ordering.
