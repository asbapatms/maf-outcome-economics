---
title: "OutcomeMeter: From AI Activity to Verified Business Value"
description: "Executive pitch for outcome-based AI economics, token governance, and evidence-backed scale decisions"
ms.date: 2026-09-16
ms.topic: overview
keywords:
  - outcome economics
  - agentic AI
  - token efficiency
  - deterministic governance
  - Microsoft Agent Framework
---

## Suggested Title

OutcomeMeter: From AI Activity to Verified Business Value

> **Tagline:** Measure what AI spends. Verify what it achieves. Decide what to
> scale.

## Executive Summary

Enterprises can measure AI calls, tokens, latency, and spend, but these metrics
do not prove business value. A workflow may use fewer tokens while producing
more errors, or add expensive review steps that rarely improve an outcome.
Leaders need to know whether each AI-assisted process delivers an independently
verified result at an acceptable cost and risk.

OutcomeMeter connects AI telemetry to business evidence. It compares a control
process with an optimized treatment, calculates cost and tokens per verified
outcome, identifies avoidable review and retry consumption, and produces a
deterministic recommendation: **scale, monitor, optimize, stop, or collect more
evidence**.

OutcomeMeter is the decision layer executives are missing. It turns raw agent
activity into a live, auditable answer to one question: **Should this AI
workflow scale?** The prototype proves that answer with Azure OpenAI execution,
safe telemetry, independent verification, token-waste attribution, governance
gates, and a live dashboard that refreshes from the same evidence database.

The result is a practical investment and governance layer for enterprise AI.
OutcomeMeter helps organizations scale workflows that create measurable value,
improve workflows that waste resources, and stop workflows that compromise
quality or safety.

## The Problem

Most AI reporting focuses on activity rather than outcomes. Token totals and
model costs show what a system consumed, but not whether the business received
a correct, useful, and acceptable result.

This creates four common problems:

* Low token usage can be mistaken for efficiency even when quality falls
* Review, retries, rework, and failed calls are hidden inside aggregate usage
* Estimated savings can be presented without independently verified outcomes
* Teams make inconsistent scale decisions because assurance and economic
  thresholds are not encoded as policy

Without a shared outcome-based measure, organizations risk scaling AI activity
instead of business value.

## The Solution

OutcomeMeter measures AI economics using the independently verified outcome as
the denominator.

For each unit of work, it connects four forms of evidence:

* The business work completed
* Independent evidence showing whether the outcome was acceptable
* Monetary costs associated with the process
* Input and output tokens consumed by primary work, review, retries, and rework

It then compares a baseline process with an optimized workflow using the same
outcome contract and eligible workload. Core measures include:

* Verified outcome rate
* Quality and critical-case performance
* Cost per verified outcome
* Tokens per verified outcome
* Token efficiency improvement
* Non-contributing review tokens
* Retry and rework consumption

This prevents a cheaper but lower-quality workflow from appearing successful.
The objective is not to minimize tokens at any cost. It is to minimize the
resources required to produce a trusted business outcome.

The full comparison runs from the command line against a real Azure OpenAI
deployment, then renders the same decision in the dashboard:

```powershell
uv run maf-outcome-economics init-db
uv run maf-outcome-economics seed
uv run maf-outcome-economics demo --provider live --limit 3
uv run maf-outcome-economics dashboard --database data/dashboard-sample.db
```

`demo` executes the control and treatment variants through Microsoft Agent
Framework, verifies each ticket's route against the labeled outcome, prints
cost and token tables per variant, and closes with the governance decision.
`dashboard` opens the Streamlit executive view against any SQLite evidence
database, live or curated.

## Demo Scenario

The demo uses support-ticket triage because it is familiar, high-volume, and
easy to verify without exposing sensitive content. Each ticket has a known
expected route, so OutcomeMeter can compare a baseline process with an optimized
agent workflow and count only tickets routed correctly under the declared
outcome contract.

The pain point is common across enterprise AI programs. A team can reduce
tokens, shorten responses, or add a reviewer, yet still fail the business if
the ticket lands in the wrong queue or if review consumes tokens without
changing the outcome. Ticket triage makes this visible in seconds: every token
spent by the agent, reviewer, retry path, or coordination step is measured
against a verified routing result.

This scenario is relevant to token and outcome governance because it separates
three questions that are often blended together:

* Did the AI workflow complete the work correctly?
* How many tokens and dollars were required per verified outcome?
* Did review and retry activity improve the result or consume avoidable budget?

The same verification pattern applies wherever an AI workflow makes a decision
that can be checked against a known-correct outcome. The ticket scenario is the
fastest way to show the metric model before applying it to the other processes
described under Example Applications.

## How It Creates Value

### Better Investment Decisions

Executives can compare AI initiatives using verified unit economics rather than
usage proxies. Funding and scaling decisions become tied to measurable business
results.

### Lower Operational Waste

Teams can see where tokens are spent on reviews that do not improve outcomes,
retries that do not recover, excessive output, or repeated coordination. Each
failed efficiency gate maps to an actionable optimization.

### Stronger Assurance

Quality, safety, compliance, and business-outcome gates are evaluated before
economics. A workflow cannot earn permission to scale merely by being cheaper.

### Faster Experimentation

Teams can change a prompt, model, review threshold, retry policy, or workflow
design and compare it with the control under the same evidence contract.

### Reusable Enterprise Capability

Generic contracts allow the same measurement and governance engine to support
customer service, invoice processing, claims, software delivery, compliance,
maintenance, and other AI-assisted processes.

### Demonstrated, Not Simulated

The evidence is demonstrated rather than described. A live Azure OpenAI run in
the terminal is followed by the Streamlit dashboard reading a curated
representative evidence database, showing the same governance model with
stable executive metrics, including verified outcomes, cost per verified
outcome, token efficiency, tokens avoided, and review-waste attribution.

## Independent Verification

OutcomeMeter does not allow an agent to declare its own success. Model
confidence, rationale, and reviewer approval may be useful signals, but they do
not independently prove correctness.

Each process defines an outcome contract containing required evidence and
acceptance rules. Evidence may come from authoritative labels, deterministic
validation, downstream system status, human acceptance, audit results, or
service-level measurements.

This separation makes the economics credible. Cost and token savings count only
when the resulting work passes the business-defined outcome contract.

## End-to-End Flow and the Golden Dataset

```text
[Ticket, no labels]
        |
        v
[Triage Agent predicts category, priority, resolver]
        |
        v
[Review: AI today, human-swappable] --> approve or correct
        |
        v
[Outcome Verifier: final labels vs gold dataset]
        |
        v
[Governance Engine: 11 ordered gates, cost + token records in]
        |
        v
[Action: SCALE / OPTIMIZE / STOP / MONITOR / INSUFFICIENT_EVIDENCE]
```

Human review sits at exactly one seam: the `RA` decision node. The agent
never sees or influences it. `ReviewAgentExecutor` only requires a
`ReviewResult(approved, corrected_category, corrected_priority,
corrected_resolver_group)`; today an AI reviewer produces it, and a
higher-risk domain can route that same node to a human queue with no change
to triage, verification, or governance.

The golden dataset is a small, independently authored ground-truth set that
the agent never sees. In the ticket scenario, each of the 20 fictional
seed tickets carries three human-authored labels the triage and review
agents cannot access: `gold_category`, `gold_priority` (`P1` to `P4`), and
`gold_resolver_group`. The verifier compares the final category, priority,
and resolver group against these three gold labels, producing a
`quality_score` out of three and a pass or fail acceptance flag; a `P1`
gold ticket additionally checks whether critical priority was recalled. The
invoice scenario uses the same principle with a different evidence source:
instead of per-item gold labels, it checks the agent's output against the
accounts-payable ledger and three-way match, because that is the
independent record of truth for a posted invoice. Either way, correctness
is proven against evidence the agent cannot see or influence, never against
the agent's own confidence or rationale.

## Review Value and Token Waste

Secondary review is often treated as automatically valuable. OutcomeMeter
measures whether it actually changed the result.

Review activity is classified as:

* A useful correction that turns an incorrect result into a verified result
* A harmful correction that changes a correct result into an incorrect result
* A non-contributing review that consumes resources without improving
  correctness
* An inconclusive review where the available evidence cannot establish impact

This supports risk-based review. Critical, sensitive, or uncertain work can
retain additional assurance, while routine work that consistently passes
verification can avoid unnecessary review.

## Executive Governance

OutcomeMeter converts evidence into one of five deterministic actions:

| Action | Executive meaning |
| ------ | ----------------- |
| `SCALE` | Outcomes, assurance, economics, and evidence maturity pass |
| `MONITOR` | Gates pass, but estimated costs or another uncertainty remain |
| `OPTIMIZE` | Assurance passes, but economic or token-efficiency targets fail |
| `STOP` | Quality, safety, compliance, or business-outcome requirements fail |
| `INSUFFICIENT_EVIDENCE` | Required evidence is missing or inconclusive |

The decision order is deliberate. Missing evidence prevents unsupported claims,
and hard assurance failures override favorable economics. Recommendations are
advisory and auditable; OutcomeMeter never changes production policy
automatically.

Examples of recommendations include:

* Narrow review triggers to high-risk work
* Use a concise prompt profile for routine cases
* Reduce unnecessary response length
* Investigate retry and rework behavior
* Improve telemetry or outcome-evidence coverage

## Why It Is Different

OutcomeMeter goes beyond conventional observability because traces, tokens,
latency, and spend are inputs rather than the final answer.

It goes beyond model evaluation because it measures completed business work,
not only benchmark responses. It goes beyond FinOps because its denominator is
a verified outcome, and economic optimization is constrained by assurance. It
also goes beyond free-form AI recommendations because governance actions are
deterministic, threshold-based, and reproducible.

Its central differentiator is simple:

> **OutcomeMeter measures the resources required to create trusted value, not
> merely the resources consumed by AI.**

## Generic Architecture

The framework-neutral core uses four normalized records:

* `WorkUnit` represents completed business work
* `EvidenceRecord` represents an independently observed fact
* `CostEntry` represents model, labor, infrastructure, or service cost
* `TokenEntry` represents input and output token consumption

Each record is a typed Pydantic model with validation, so a connector cannot
submit an evidence-free cost or an unattributed token count:

```python
class WorkUnit(CoreModel):
    id: str
    process_variant_id: str
    started_at: AwareDatetime
    completed_at: AwareDatetime | None = None
    attributes: dict[str, JsonValue] = {}

class EvidenceRecord(CoreModel):
    id: str
    work_unit_id: str
    metric: str
    value: JsonValue
    source: str
    observed_at: AwareDatetime

class CostEntry(CoreModel):
    id: str
    process_variant_id: str
    category: CostCategory
    amount: Decimal
    currency: str
    status: CostEvidenceStatus

class TokenEntry(CoreModel):
    id: str
    process_variant_id: str
    work_unit_id: str
    input_tokens: int
    output_tokens: int
    purpose: TokenPurpose
    trace_id: str
    span_id: str
```

Connectors translate workflow telemetry into cost and token records. Scenario
adapters translate business systems into work and evidence records. The same
verification, comparison, and governance services can therefore operate across
models, frameworks, and domains.

```text
AI workflow + business systems
              |
              v
Connectors and scenario adapters
              |
              v
Work + evidence + cost + token records
              |
              v
Independent outcome verification
              |
              v
Control-to-treatment comparison
              |
              v
Deterministic executive governance
```

### The Plug-In Contract

Connectors satisfy four `Protocol` interfaces, structural types with no base
class and no framework import required:

```python
class WorkUnitSource(Protocol):
    async def load_work_units(self, period) -> list[WorkUnit]: ...

class EvidenceSource(Protocol):
    async def load_evidence(self, period) -> list[EvidenceRecord]: ...

class CostSource(Protocol):
    async def load_costs(self, period) -> list[CostEntry]: ...

class TokenSource(Protocol):
    async def load_tokens(self, period) -> list[TokenEntry]: ...
```

Two domains already implement this contract with zero shared code beyond
these four records:

* `TicketScenarioConnector`: a work unit is one completed ticket run,
  evidence comes from a deterministic routing verifier, and cost comes from
  MAF telemetry spans plus human-review labor.
* `InvoiceScenarioConnector`: a work unit is one completed invoice, evidence
  comes from the accounts-payable ledger and three-way match, and cost comes
  from a reconciled ledger split across human, platform, and model spend.

Adding a third scenario means writing one adapter class with these four
methods; verification, comparison, and governance below do not change.

```text
1. Scenario Connectors      (Ticket, Invoice, MAF telemetry)
              |
              v
2. Normalized Records       (WorkUnit, EvidenceRecord, CostEntry, TokenEntry)
              |
              v
3. Outcome Verification     (OutcomeContract + EvidenceRule)
              |
              v
4. Economics + Token Comparison   (control vs treatment)
              |
              v
5. Deterministic Governance  (11 gates -> 5 actions)
```

### Where Humans Stay in the Loop

There is no single approve button. Human judgment enters at five seams:

* **Contract authoring** - a domain owner writes the `OutcomeContract`: which
  evidence proves a correct outcome and the maximum defensible cost.
* **The review seam** - `ReviewAgentExecutor` only depends on getting back a
  `ReviewResult(approved, corrected_*)`. A higher-risk domain can swap in a
  human approval queue without touching triage, verification, or governance.
* **Assurance sign-off** - `GovernanceAssurance.quality_passed`,
  `safety_passed`, `compliance_passed`, and `business_outcome_passed` are
  booleans the engine consumes, supplied by human or automated evaluators; it
  never infers them itself.
* **Cost reconciliation** - `reconciled_costs_available` gates `SCALE`
  against `MONITOR`, so a scale call only fires once finance has confirmed
  actual invoiced costs, not estimates.
* **Acting on the recommendation** - the engine returns a string, never a
  side effect; a process owner decides what happens next.

## Microsoft Technology

The working prototype uses Microsoft Agent Framework and Azure OpenAI for agent
execution. OpenTelemetry captures trace correlation and token usage, while
Python, Pydantic, and SQLite provide typed processing and portable evidence
storage. A Streamlit dashboard reads the configured SQLite evidence store and
renders the executive governance decision, gate results, token comparisons,
review attribution, and recent runs.

Microsoft technology demonstrates an enterprise-relevant implementation, while
the normalized core avoids permanent dependency on one orchestration framework
or business scenario.

## Responsible AI and Privacy

OutcomeMeter treats efficiency as one objective, not the only objective.
Quality, safety, compliance, critical populations, and declared business
outcomes are evaluated before cost and token gates.

The prototype excludes prompts, responses, ticket text, system instructions,
and tool payloads from telemetry. It retains the correlation, model, timing,
token, workflow, and verification metadata required for analysis. The included
scenarios use fictional data.

The governance engine remains a decision aid. Human owners define contracts,
approve thresholds, assess risks, and authorize changes. Recommendations do not
autonomously modify prompts, routing, review, or retry policies.

## Example Applications

* Customer service: tokens and cost per correctly routed or resolved case
* Finance: resources per accepted invoice or reconciled transaction
* Insurance: cost per correctly processed claim with critical controls intact
* Software engineering: resources per change that passes tests and security
  checks
* Security operations: tokens per validated alert disposition while preserving
  critical recall
* Compliance: resources per accepted review with required human accountability

Each domain answers the same questions: What outcome was achieved? What proves
it? What did it cost? Where was consumption avoidable? What action should follow?

This combination reframes AI value from model usage to verified business
outcomes, makes token efficiency accountable to quality and safety gates, and
exposes hidden waste in reviews, retries, rework, failed calls, and excessive
outputs. Instead of ending with an informal recommendation, it produces a
deterministic executive decision backed by live Azure OpenAI execution,
refreshed dashboard evidence, and reusable contracts for work, evidence, cost,
and tokens.

## Prototype Evidence

The repository contains a working Python 3.11 prototype that demonstrates:

* Microsoft Agent Framework workflows with Azure OpenAI execution
* Safe OpenTelemetry capture and work-level trace correlation
* Generic connectors and domain adapters
* Independent outcome verification
* Cost and token ledgers with trace and span deduplication
* Control-to-treatment economics and token-efficiency comparison
* Review-value attribution
* Deterministic governance with typed recommendations
* Live Streamlit executive dashboard with explicit database selection
* Command-line and self-contained HTML executive reporting
* Governance-gate reference documentation for evidence, assurance, economics,
  token efficiency, review waste, and retry waste
* Approved-pricing resolution for Azure OpenAI response-model names that include
  dated deployment suffixes

Support-ticket and invoice scenarios demonstrate that the core is not tied to a
single domain. Automated tests, strict type checking, and linting support the
prototype's technical quality. Monetary results remain explicitly estimated
until reconciled billing evidence is available.

The curated dashboard sample shows a credible executive portfolio for recording:
`MONITOR` governance action, 20 verified treatment outcomes, 0.0011 USD per
verified outcome, 0.0314 USD in net savings, 60.8% token-efficiency improvement,
7,300 tokens avoided, and review-waste gate input at 12.8% of treatment tokens.

## Business Impact

OutcomeMeter gives executives, finance, engineering, operations, and risk teams
a shared language for AI value. It can improve portfolio allocation, reduce
avoidable model consumption, protect critical outcomes, and shorten the path
from experimentation to accountable scale.

The immediate value is better optimization of individual workflows. The larger
opportunity is a portfolio-level control plane that compares AI investments
across departments using consistent evidence, economics, and governance.

## Scale Potential

The next phase would add enterprise data connectors, reconciled billing and
labor costs, policy versioning, access control, portfolio dashboards, trend and
cohort analysis, and approval workflows.

Because domain and framework details remain at the edges, each new use case is
primarily an adapter and outcome-contract exercise rather than a new governance
implementation.

## Closing Pitch

The next phase of enterprise AI will not be defined by whoever generates the
most agent activity. It will be defined by organizations that can prove which
workflows create trusted outcomes, understand what those outcomes cost, remove
consumption that adds no value, and scale with discipline.

OutcomeMeter provides that missing decision layer.

**Measure what AI spends. Verify what it achieves. Decide what to scale.**
