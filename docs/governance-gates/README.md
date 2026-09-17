---
title: Governance Gates Reference
description: One page per GenericGovernanceEngine gate, its evaluation logic, and the actions it can trigger
---

`GenericGovernanceEngine` (in
[core/governance.py](../../src/maf_outcome_economics/core/governance.py))
evaluates every governed process variant through eleven independent gates
before it selects one of five deterministic actions:

* `SCALE` — every gate passes and reconciled costs are available.
* `MONITOR` — every gate passes but costs remain estimated (unreconciled).
* `OPTIMIZE` — evidence and assurance gates pass but an economics gate fails.
* `STOP` — a quality, safety, compliance, or business-outcome gate fails.
* `INSUFFICIENT_EVIDENCE` — a required gate result is unknown.

## Evaluation order

The engine never lets a favorable cost or token estimate override missing or
failed outcome assurance. Gates are grouped and evaluated in this order:

1. **Evidence gate.** If [evidence](./evidence.md) does not pass, the decision
   is `INSUFFICIENT_EVIDENCE` immediately; no other gate is consulted.
2. **Stop gates.** [Quality](./quality.md), [safety](./safety.md),
   [compliance](./compliance.md), and
   [business outcome](./business_outcome.md). Any `FAIL` returns `STOP`. Any
   `UNKNOWN` (with no `FAIL`) returns `INSUFFICIENT_EVIDENCE`.
3. **Economics gates.** [Unit cost](./unit_cost.md) and
   [net value](./net_value.md) always run. When a `TokenGovernancePolicy` is
   supplied, four token-economics gates join them:
   [token budget](./token_budget.md), [token efficiency](./token_efficiency.md),
   [review waste](./review_waste.md), and [retry waste](./retry_waste.md). Any
   `UNKNOWN` returns `INSUFFICIENT_EVIDENCE`; any `FAIL` returns `OPTIMIZE`
   with a typed `OptimizationRecommendation` per failed gate.
4. **Maturity check.** If every gate passes but
   `GovernanceAssurance.reconciled_costs_available` is `False`, the decision is
   `MONITOR`. Otherwise it is `SCALE`.

## Gate summary

| Gate             | Category        | Always evaluated | Can trigger                         |
|------------------|-----------------|-------------------|--------------------------------------|
| Evidence         | Evidence        | Yes               | `INSUFFICIENT_EVIDENCE`             |
| Quality          | Stop            | Yes               | `STOP`, `INSUFFICIENT_EVIDENCE`     |
| Safety           | Stop            | Yes               | `STOP`, `INSUFFICIENT_EVIDENCE`     |
| Compliance       | Stop            | Yes               | `STOP`, `INSUFFICIENT_EVIDENCE`     |
| Business outcome | Stop            | Yes               | `STOP`, `INSUFFICIENT_EVIDENCE`     |
| Unit cost        | Economics       | Yes               | `OPTIMIZE`, `INSUFFICIENT_EVIDENCE` |
| Net value        | Economics       | Yes               | `OPTIMIZE`, `INSUFFICIENT_EVIDENCE` |
| Token budget     | Token economics | Only with policy  | `OPTIMIZE`, `INSUFFICIENT_EVIDENCE` |
| Token efficiency | Token economics | Only with policy  | `OPTIMIZE`, `INSUFFICIENT_EVIDENCE` |
| Review waste     | Token economics | Only with policy  | `OPTIMIZE`, `INSUFFICIENT_EVIDENCE` |
| Retry waste      | Token economics | Only with policy  | `OPTIMIZE`, `INSUFFICIENT_EVIDENCE` |

Every gate result is auditable: `GovernanceGateResult` records the gate, its
`GateStatus` (`pass`, `fail`, or `unknown`), and a human-readable reason. The
[live dashboard](../../README.md#governance) and the `decide`/`demo` console
commands render this same list, so a reviewer never sees an action without
the full gate-by-gate evidence behind it.

## Worked reference

The live ticket demo
([scenarios/ticket/analysis.py](../../src/maf_outcome_economics/scenarios/ticket/analysis.py))
supplies a concrete `TokenGovernancePolicy`:

* Maximum tokens per verified outcome: `300`
* Minimum efficiency improvement: `10%`
* Maximum review-token ratio: `40%`
* Maximum retry-token ratio: `10%`

Each per-gate page below reuses these exact thresholds in its worked example.
