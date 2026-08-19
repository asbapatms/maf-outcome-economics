---
title: MAF Outcome Economics
description: Python service foundation for verified outcome economics using Microsoft Agent Framework
ms.date: 2026-08-19
ms.topic: overview
---

## Overview

`maf-outcome-economics` is a Python 3.11 foundation for evaluating the economic
impact of measurable outcomes. It combines deterministic calculations and
verification with Microsoft Agent Framework workflows and Azure OpenAI.

## Repository Structure

```text
maf-outcome-economics/
|-- src/maf_outcome_economics/
|   |-- agents/        # Azure OpenAI agent construction
|   |-- domain/        # Pydantic domain models
|   |-- workflows/     # Agent Framework orchestration
|   |-- telemetry/     # OpenTelemetry configuration
|   |-- persistence/   # SQLite repositories
|   |-- verification/  # Outcome evidence checks
|   |-- economics/     # Economic impact calculations
|   `-- reporting/     # Human-readable reports
|-- tests/             # Unit and integration tests
|-- .env.example       # Secret-free configuration template
|-- pyproject.toml     # Project and tool configuration
`-- uv.lock            # Locked dependency graph
```

## Setup

```powershell
uv sync --locked
Copy-Item .env.example .env
uv run maf-outcome-economics health
```

Use `az login` for local passwordless Azure authentication. In production, use
a managed identity. Never commit `.env`, API keys, tokens, or connection
strings.

The installed MAF `OpenAIChatClient` uses Azure's Responses API. Keep
`AZURE_OPENAI_API_VERSION=preview` unless the installed client documents a newer
supported Responses API version. `AZURE_OPENAI_CHAT_MODEL` must be the Azure
deployment name, not only the underlying catalog model name.

## Local Data

Initialize the SQLite schema and seed 20 fictional support tickets with gold
category, priority, and resolver-group labels:

```powershell
uv run maf-outcome-economics init-db
uv run maf-outcome-economics seed
```

The seed command accepts illustrative token prices for local scenarios:

```powershell
uv run maf-outcome-economics seed `
	--provider illustrative-provider `
	--model illustrative-model `
	--input-cost-per-million 2.50 `
	--output-cost-per-million 10.00
```

Seeded prices are illustrative, not vendor price quotes. Pricing-derived model
fields use the `estimated_` prefix, and `EconomicsMetrics` always sets
`monetary_values_are_estimated` to `true`.

On Windows ARM64, install and select x64 Python 3.11 before syncing. The Agent
Framework metapackage includes native dependencies that publish Windows x64,
but not Windows ARM64, wheels.

```powershell
uv python install cpython-3.11-windows-x86_64-none
uv venv --clear --python cpython-3.11-windows-x86_64-none
uv sync --locked
```

## Agent Framework APIs

The lockfile uses `agent-framework==1.11.0`, the newest stable release available
from the configured trusted Microsoft package mirror. Public PyPI advertised
`1.14.0` during setup, but its package artifacts were inaccessible from this
environment because HTTPS negotiation with `files.pythonhosted.org` failed.

The implementation uses the public `Agent`, `workflow`, `OpenAIChatClient`, and
`configure_otel_providers` APIs inspected from the installed `1.11.0` package.
It follows Microsoft's
[Python workflow samples](https://github.com/microsoft/agent-framework/tree/python-1.11.0/python/samples/03-workflows)
and [observability guidance](https://learn.microsoft.com/agent-framework/agents/observability).
OpenTelemetry exports through OTLP HTTP/protobuf by default.

## Support Agents

The live support flow creates two Azure OpenAI-backed Microsoft Agent Framework
agents with stable identities:

* `maf-outcome-economics.triage.v1` (`TriageAgent`)
* `maf-outcome-economics.review.v1` (`ReviewAgent`)

Both agents pass their Pydantic result type through the installed MAF
`response_format` option. Responses are validated as strict `TriageResult` or
`ReviewResult` objects. Plain JSON, a single JSON code fence, and a JSON object
inside surrounding text can be parsed defensively. Malformed output, schema
violations, or mismatched run and ticket identifiers trigger one corrective
retry. A second invalid response raises `MalformedAgentOutputError`.

The `baseline` prompt profile provides fuller classification and review
guidance. The `optimized` profile requests concise JSON only. Neither profile
includes seeded gold labels. The production `MAFAgentProvider` always invokes
real MAF agents. The deterministic fake provider exists only under `tests/` and
cannot be selected by the CLI.

After configuring Azure OpenAI and authenticating with `az login`, run one
fictional ticket through the live triage agent:

```powershell
uv run maf-outcome-economics agent-smoke-test --profile optimized
```

The command prints the validated response JSON, its trace ID, and input and
output token counts captured from billable MAF chat spans in SQLite. It uses
real Azure OpenAI execution and can incur model usage charges.

## Sequential Ticket Workflow

`create_ticket_workflow()` builds a sequential Microsoft Agent Framework
workflow from installed `Executor`, `WorkflowBuilder`, `WorkflowContext`, and
`handler` APIs. Each ticket moves through these executors in order:

1. `TicketInputExecutor` creates the run with its active trace ID.
2. `TriageAgentExecutor` invokes the triage agent.
3. `ReviewAgentExecutor` invokes or deterministically skips review.
4. `OutcomeVerifierExecutor` compares effective labels with fictional gold
	labels.
5. `ResultExecutor` completes persistence and yields `TicketWorkflowResult`.

Baseline runs invoke both agents for every ticket. Optimized runs invoke review
when triage confidence is below `0.8`, the request or ticket text is sensitive,
the priority is `P1`, or the category contains `Critical`. Other optimized
tickets continue through the sequential executor without a review model call.

`stream_ticket_workflow()` yields Agent Framework workflow events and produces
one typed final result. It keeps a parent `tokenomics.ticket` span active while
events stream and records `business_task_id`, `batch_id`, `contract_id`, and
`variant` attributes. The run stores the same 32-character trace ID so SQLite
spans and billable model usage can be associated with the business result.

## Telemetry

`configure_telemetry()` passes `SQLiteSpanExporter` to Agent Framework's
`configure_otel_providers()` initializer. Sensitive-data capture is explicitly
disabled, even if a local environment requests it. The SQLite exporter omits
known prompt, response, system-instruction, tool-argument, and tool-result
attributes.

SQLite telemetry works without an OpenTelemetry collector. Set
`OTEL_EXPORTER_OTLP_ENDPOINT` only when a collector is listening at that URL;
otherwise MAF will attempt additional trace, metric, and log exports and report
connection failures during provider flush.

Stored spans include trace, span, and parent identifiers; names; start and end
timestamps; status; status descriptions; and serialized safe attributes. The
normalizer extracts GenAI token usage, agent identity, request and response
models, operation name, workflow and session identity, executor identity,
message routing, and error type when available.

Only spans with `gen_ai.operation.name=chat` and a request or response model are
billable model calls. Both spans and billable usage are deduplicated by trace ID
and span ID.

Run the offline smoke test to emit a custom span, flush the OpenTelemetry
provider, and prove the record exists in the configured SQLite database:

```powershell
uv run maf-outcome-economics telemetry-smoke-test
```

## Quality Checks

```powershell
uv run pytest
uv run ruff check .
uv run pyright
```
