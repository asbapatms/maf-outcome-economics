---
title: Quality Gate
description: How GenericGovernanceEngine evaluates the quality assurance stop gate
---

**Enum value:** `GovernanceGate.QUALITY` (`"quality"`)
**Category:** Stop gate (a `FAIL` here returns `STOP`)

## What it measures

Whether the treatment variant's output quality clears the caller-supplied
assurance threshold. Unlike the economics gates, this gate does not compute
anything itself — it trusts a boolean (or unknown) verdict supplied by the
caller through `GovernanceAssurance.quality_passed`.

## How it is evaluated

`GenericGovernanceEngine` treats every assurance gate identically through
`_assurance_result`
(in [core/governance.py](../../src/maf_outcome_economics/core/governance.py)):

```python
status = (
    GateStatus.UNKNOWN if passed is None
    else GateStatus.PASS if passed
    else GateStatus.FAIL
)
```

* `PASS` — `quality_passed` is `True`.
* `FAIL` — `quality_passed` is `False`.
* `UNKNOWN` — `quality_passed` is `None` (no quality assessment was supplied).

The engine itself never inspects prompts, responses, or scoring rubrics; the
caller (a scenario connector or a domain-specific analyzer) is responsible for
producing `quality_passed` from its own verified evidence.

## What happens when it fails

* `FAIL` — combined with any other stop-gate failure, returns `STOP` with the
  recommendation: "Stop rollout and remediate failed outcome or assurance
  gates."
* `UNKNOWN` (with no stop gate `FAIL`) — returns `INSUFFICIENT_EVIDENCE` with
  the recommendation: "Complete quality, safety, compliance, and outcome
  assessment."

## Worked example (ticket demo)

`TicketEconomicsAnalyzer._assurance`
(in [scenarios/ticket/analysis.py](../../src/maf_outcome_economics/scenarios/ticket/analysis.py))
derives `quality_passed` from routing verification records:

```python
average_quality = sum(item.quality_score for item in verifications) / total
quality_passed = average_quality >= contract.minimum_quality_score
```

The `demo-scenarios` `STOP` dataset intentionally fails hidden-label quality
checks so this gate reports `FAIL`, driving the `STOP` action end to end.

## Related evidence

* `GovernanceAssurance` model in
  [core/governance.py](../../src/maf_outcome_economics/core/governance.py).
* [Governance gates index](./README.md) for stop-gate ordering relative to
  safety, compliance, and business outcome.
