---
title: Evidence Gate
description: How GenericGovernanceEngine confirms control and treatment evidence is sufficient before any other gate runs
---

**Enum value:** `GovernanceGate.EVIDENCE` (`"evidence"`)
**Category:** Evidence (runs first, gates every other check)

## What it measures

Whether both the control and treatment process variants have enough
independently verified work to support a decision at all. This gate exists so
that no other gate — quality, cost, or token efficiency — can be evaluated
against a variant that has not produced sufficient evidence.

## How it is evaluated

In [core/governance.py](../../src/maf_outcome_economics/core/governance.py),
`_gate_results` computes:

```python
evidence_passed = (
    comparison.control.evidence_status is EvidenceStatus.SUFFICIENT
    and treatment.evidence_status is EvidenceStatus.SUFFICIENT
)
```

`EvidenceStatus` comes from `ProcessEconomicsComparison`
(in [core/comparison.py](../../src/maf_outcome_economics/core/comparison.py))
and reflects whether each variant's sample size and independent verification
meet the reporting requirements set on the `OutcomeContract`.

* `PASS` — both control and treatment evidence is `SUFFICIENT`.
* `FAIL` — control or treatment evidence is incomplete. This is the only gate
  with no `UNKNOWN` state; it is always a boolean pass/fail.

## What happens when it fails

A failed evidence gate short-circuits the entire decision: the engine returns
`INSUFFICIENT_EVIDENCE` immediately and does not evaluate the stop or
economics gates at all. The recommended action is always:

> Collect complete control and treatment evidence before deciding.

## Worked example (ticket demo)

The live ticket demo's generic `OutcomeContract`
(in [scenarios/ticket/analysis.py](../../src/maf_outcome_economics/scenarios/ticket/analysis.py))
sets `minimum_sample_size=1`, so a single independently verified work unit per
variant is enough to pass this gate. In the three-scenario demo
(`demo-scenarios`), every scenario supplies enough verified tickets to pass
evidence; the `SCALE`, `OPTIMIZE`, and `STOP` outcomes are differentiated by
the gates below it, not by evidence sufficiency.

## Related evidence

* `OutcomeVerifier` and `EvidenceStatus`
  in [core/verification.py](../../src/maf_outcome_economics/core/verification.py)
  and [core/comparison.py](../../src/maf_outcome_economics/core/comparison.py).
* [Governance gates index](./README.md) for how this gate relates to the
  others.
