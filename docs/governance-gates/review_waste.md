---
title: Review Waste Gate
description: How GenericGovernanceEngine evaluates the non-contributing review-token ratio gate
---

**Enum value:** `GovernanceGate.REVIEW_WASTE` (`"review_waste"`)
**Category:** Token economics gate (only evaluated when a `TokenGovernancePolicy`
is supplied; a `FAIL` returns `OPTIMIZE`)

## What it measures

Whether review tokens — the tokens spent on a reviewer, critic, or aggregator
pass — are earning their keep. A review call that neither corrects a wrong
outcome nor confirms a right one is waste: it consumed tokens without
delivering assurance value. This gate caps the *ratio* of such
non-contributing review tokens to total treatment tokens.

## How it is evaluated

`_token_gate_results` and `_threshold_result`
(in [core/governance.py](../../src/maf_outcome_economics/core/governance.py))
compute:

```python
review_ratio = (
    Decimal(review_attribution.non_contributing_review_tokens) / total_tokens
    if review_attribution is not None and total_tokens
    else None
)
```

and compare it against `TokenGovernancePolicy.maximum_review_token_ratio`:

* `PASS` — the non-contributing review-token ratio is at or below the maximum.
* `FAIL` — the ratio exceeds the maximum.
* `UNKNOWN` — no review attribution or no treatment tokens are available.

`ReviewTokenAttribution`
(in [core/tokens.py](../../src/maf_outcome_economics/core/tokens.py)) classifies
every review token as a useful correction, a harmful correction, a
non-contributing review, or inconclusive — only the non-contributing bucket
feeds this gate.

## What happens when it fails

A `FAIL` returns `OPTIMIZE` and generates a typed `OptimizationRecommendation`
with `lever=OptimizationLever.REVIEW_THRESHOLD`:

> Narrow review triggers while retaining sensitive and critical gates.

The recommendation's `evidence_metric` is `review_token_ratio`, using the
*total* review-token ratio (not just the non-contributing share) as the
observed value against the same policy target.

## Worked example (ticket demo)

The live ticket demo's `TokenGovernancePolicy`
(in [scenarios/ticket/analysis.py](../../src/maf_outcome_economics/scenarios/ticket/analysis.py))
sets `maximum_review_token_ratio=Decimal("0.4")` (40%). The dashboard's
"Review token attribution" table and its "Non-contributing review token
ratio" caption show the same evidence this gate consumes.

## Related evidence

* `ReviewTokenAttribution` and `attribute_review_tokens` in
  [core/tokens.py](../../src/maf_outcome_economics/core/tokens.py).
* [Governance gates index](./README.md) for token-economics gate ordering.
