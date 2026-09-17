---
title: Business Outcome Gate
description: How GenericGovernanceEngine evaluates the business-outcome assurance stop gate
---

**Enum value:** `GovernanceGate.BUSINESS_OUTCOME` (`"business_outcome"`)
**Category:** Stop gate (a `FAIL` here returns `STOP`)

## What it measures

Whether the treatment variant actually delivers the business result the
process exists to produce — for example, an acceptable acceptance rate,
resolution rate, or another domain-specific success measure — independent of
cost or token efficiency. A process can be cheap and safe and still fail this
gate if it does not do its job often enough.

## How it is evaluated

`_assurance_result` applies the same three-state logic used by every
assurance gate
(in [core/governance.py](../../src/maf_outcome_economics/core/governance.py)):

* `PASS` — `GovernanceAssurance.business_outcome_passed` is `True`.
* `FAIL` — `business_outcome_passed` is `False`.
* `UNKNOWN` — `business_outcome_passed` is `None`.

## What happens when it fails

* `FAIL` — returns `STOP`.
* `UNKNOWN` (with no stop-gate `FAIL`) — returns `INSUFFICIENT_EVIDENCE`.

## Worked example (ticket demo)

`TicketEconomicsAnalyzer._assurance`
(in [scenarios/ticket/analysis.py](../../src/maf_outcome_economics/scenarios/ticket/analysis.py))
derives this from the acceptance rate of routed tickets:

```python
acceptance_rate = sum(item.accepted for item in verifications) / total
business_outcome_passed = acceptance_rate >= contract.minimum_acceptance_rate
```

If routed tickets are accepted often enough to clear
`contract.minimum_acceptance_rate`, this gate passes even when unit cost or
token efficiency still needs improvement — those are handled independently by
the economics gates below.

## Related evidence

* `GovernanceAssurance` model in
  [core/governance.py](../../src/maf_outcome_economics/core/governance.py).
* [Governance gates index](./README.md) for stop-gate ordering.
