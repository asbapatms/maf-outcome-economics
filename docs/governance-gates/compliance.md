---
title: Compliance Gate
description: How GenericGovernanceEngine evaluates the compliance assurance stop gate
---

**Enum value:** `GovernanceGate.COMPLIANCE` (`"compliance"`)
**Category:** Stop gate (a `FAIL` here returns `STOP`)

## What it measures

Whether the treatment variant satisfies regulatory, policy, or contractual
compliance requirements outside of quality and safety scoring — for example,
required disclosures, data-handling rules, or audit-trail completeness. Like
every assurance gate, the engine only evaluates a caller-supplied verdict.

## How it is evaluated

`_assurance_result` applies the same three-state logic used by every
assurance gate
(in [core/governance.py](../../src/maf_outcome_economics/core/governance.py)):

* `PASS` — `GovernanceAssurance.compliance_passed` is `True`.
* `FAIL` — `compliance_passed` is `False`.
* `UNKNOWN` — `compliance_passed` is `None`.

## What happens when it fails

* `FAIL` — returns `STOP`.
* `UNKNOWN` (with no stop-gate `FAIL`) — returns `INSUFFICIENT_EVIDENCE`.

## Worked example (ticket demo)

The ticket scenario has no compliance-specific check implemented yet.
`TicketEconomicsAnalyzer._assurance`
(in [scenarios/ticket/analysis.py](../../src/maf_outcome_economics/scenarios/ticket/analysis.py))
hardcodes `compliance_passed=True` for every run, so this gate always passes
in the shipped demo. This is a deliberate scope boundary, not a hidden
assumption: a real deployment integrating this engine should replace the
hardcoded value with an actual compliance verdict (for example, from an audit
log check or a policy-as-code evaluator) before relying on this gate.

## Related evidence

* `GovernanceAssurance` model in
  [core/governance.py](../../src/maf_outcome_economics/core/governance.py).
* [Governance gates index](./README.md) for stop-gate ordering.
