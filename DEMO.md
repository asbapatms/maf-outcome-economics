---
title: Two-Minute Live Demo
description: Timed sequence for demonstrating real traces, token usage, deterministic acceptance, and governance
ms.date: 2026-08-19
ms.topic: tutorial
---

## Before the Clock Starts

Use Python 3.11, synchronize the locked environment, copy `.env.example` to
`.env`, and set `AZURE_OPENAI_ENDPOINT` plus `AZURE_OPENAI_CHAT_MODEL`. Complete
Azure authentication and initialize the fictional dataset:

```powershell
az login
az account show --output table
uv sync --locked
uv run maf-outcome-economics seed
uv run maf-outcome-economics health
```

Seed approved current prices for every provider and response-model pair that
the live spans report. The application requires exact labels and never invents
pricing. Keep Application Insights or the Aspire Dashboard open when showing a
remote trace destination.

> [!IMPORTANT]
> The tickets are fictional. Sensitive telemetry is disabled, so traces contain
> correlation, model, timing, token, and deterministic verification metadata,
> but no prompt, response, or ticket text.

## 0:00 to 0:20: Establish Live Mode

Show the health table and point out that Azure OpenAI is configured. Application
Insights can be configured or omitted because SQLite trace storage is always
active.

```powershell
uv run maf-outcome-economics health
```

## 0:20 to 1:20: Execute Real Model Calls

Run the same two fictional tickets through baseline and optimized workflows:

```powershell
uv run maf-outcome-economics demo --provider live --limit 2
```

Every successful run refreshes `artifacts/hackathon-live-demo.html` with that
run's ticket evidence and the current persisted economics. Open the page in a
browser for the video or hackathon submission. Use a different destination when
you need to preserve multiple runs:

```powershell
uv run maf-outcome-economics demo --provider live --limit 2 `
	--html-output artifacts/demo-2026-08-19.html
```

`TKT-001` contains password-related content, so optimized review remains enabled
to demonstrate the safety gate. `TKT-002` is a routine billing ticket, so a
high-confidence result can skip review and demonstrate token savings.

As each workflow completes, call out these fields from the progress line:

* `trace=<32-character ID>` is the real OpenTelemetry trace identity
* `tokens=<N> in/<N> out` contains actual counters captured from chat spans
* `accepted=yes|no` comes from deterministic comparison with fictional gold labels
* `review=invoked|skipped` shows the optimized routing decision

No acceptance decision comes from model confidence or reviewer approval.

## 1:20 to 1:45: Inspect the Trace

Use the printed ticket identifier to show locally persisted safe spans:

```powershell
uv run maf-outcome-economics trace --ticket TKT-001
```

For Application Insights, replace the placeholder with the printed trace ID and
run this query after ingestion completes:

```kusto
union requests, dependencies
| where operation_Id == "<TRACE_ID>"
| order by timestamp asc
```

For Aspire Dashboard, paste the trace ID into the search field at
<http://localhost:18888>.

## 1:45 to 2:00: Explain the Decision

Return to the demo output. The comparison table reports baseline and optimized
quality, actual token totals, and estimated cost per accepted outcome. The final
panel applies deterministic contract gates and returns one action:

* `SCALE` when quality, critical recall, and unit cost all meet thresholds
* `OPTIMIZE` when quality gates pass but cost per accepted outcome exceeds budget
* `STOP` when quality or safety fails, or when zero outcomes are accepted

Reproduce the optimized decision from persisted evidence without another model
call:

```powershell
uv run maf-outcome-economics decide --variant optimized
```

## Optional: Show Every Governance Action

Use the deterministic fictional scenario suite when the video needs to explain
all three governance outcomes in one sequence:

```powershell
uv run maf-outcome-economics demo-scenarios
```

The final table shows `SCALE`, `OPTIMIZE`, and `STOP`. Open
`artifacts/demo-scenarios.html` to present the same three outcomes as a single
browser page, with links to each dataset's detailed evidence.
