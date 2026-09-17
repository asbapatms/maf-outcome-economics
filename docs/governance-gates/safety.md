---
title: Safety Gate
description: How GenericGovernanceEngine evaluates the safety assurance stop gate
---

**Enum value:** `GovernanceGate.SAFETY` (`"safety"`)
**Category:** Stop gate (a `FAIL` here returns `STOP`)

## What it measures

Whether the treatment variant meets its safety-critical assurance bar, most
commonly a recall requirement on high-severity or critical-priority cases. As
with the [quality gate](./quality.md), the engine only evaluates a
caller-supplied verdict; it does not compute a safety score itself.

## How it is evaluated

`_assurance_result` applies the same three-state logic used by every
assurance gate
(in [core/governance.py](../../src/maf_outcome_economics/core/governance.py)):

* `PASS` — `GovernanceAssurance.safety_passed` is `True`.
* `FAIL` — `safety_passed` is `False`.
* `UNKNOWN` — `safety_passed` is `None`.

## What happens when it fails

* `FAIL` — returns `STOP`. Safety failures are never downgraded to
  `OPTIMIZE`; the engine treats safety and quality with equal severity.
* `UNKNOWN` (with no stop-gate `FAIL`) — returns `INSUFFICIENT_EVIDENCE`.

## Worked example (ticket demo)

`TicketEconomicsAnalyzer._assurance`
(in [scenarios/ticket/analysis.py](../../src/maf_outcome_economics/scenarios/ticket/analysis.py))
computes safety from critical-priority recall:

```python
critical_recall = (
    Decimal(sum(item.critical_priority_recalled is True for item in critical))
    / Decimal(len(critical))
    if critical
    else Decimal(1)
)
safety_passed = critical_recall >= contract.minimum_critical_priority_recall
```

If no critical-priority tickets were observed in the reporting period,
`critical_recall` defaults to `1` (perfect recall by vacuous truth) rather than
`UNKNOWN`, so the gate does not block a decision purely because no critical
case occurred. The `demo-scenarios` `STOP` dataset intentionally fails
critical-priority recall alongside quality to drive its `STOP` outcome.

## Related evidence

* `GovernanceAssurance` model in
  [core/governance.py](../../src/maf_outcome_economics/core/governance.py).
* [Governance gates index](./README.md) for stop-gate ordering.
