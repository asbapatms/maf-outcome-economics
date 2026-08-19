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

> [!IMPORTANT]
> Every seeded support ticket is fictional. Sensitive telemetry capture is
> disabled in code, and prompt, response, ticket, tool-argument, and tool-result
> content is excluded from the SQLite and Azure Monitor exporters.

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
```

### Azure authentication

The live provider uses `DefaultAzureCredential`. Authenticate locally with the
Azure CLI and confirm the active subscription before starting the CLI:

```powershell
az login
az account show --output table
```

Use `az login --tenant <TENANT_ID>` when the Azure OpenAI resource belongs to a
specific tenant. The signed-in identity needs permission to invoke the model
deployment. In Azure-hosted environments, use managed identity instead of a
developer login. Never commit `.env`, tokens, or connection strings.

### Required environment variables

Set these values in the local `.env` file for live execution:

| Variable | Requirement | Purpose |
|----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Required | Azure OpenAI resource endpoint |
| `AZURE_OPENAI_CHAT_MODEL` | Required | Azure deployment name |
| `AZURE_OPENAI_API_VERSION` | Recommended | Responses API version, currently `preview` |
| `MAF_DATABASE_PATH` | Optional | SQLite path, defaults to `data/outcomes.db` |

`APPLICATIONINSIGHTS_CONNECTION_STRING`, console exporters, and OTLP export are
optional observability settings. Run the non-secret health check after editing
the file:

```powershell
uv run maf-outcome-economics health
```

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

## Console Workflow

Run each workflow variant over the same ordered labelled dataset, then compare
quality and economics:

```powershell
uv run maf-outcome-economics run --variant baseline --limit 20
uv run maf-outcome-economics run --variant optimized --limit 20
uv run maf-outcome-economics compare
uv run maf-outcome-economics trace --ticket TKT-001
uv run maf-outcome-economics decide --variant optimized
```

Live Azure OpenAI execution is the default. It requires
`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_CHAT_MODEL`, and local Azure
authentication. A completed live workflow must have captured semantic chat
usage in SQLite. The command fails instead of substituting token counts when
that telemetry is absent.

Live economics also requires an approved pricing record that exactly matches
the provider and response model captured by OpenTelemetry. If a model is
unpriced, the command prints a ready-to-run `seed` command with placeholders
for the approved current input and output prices. The application never invents
model pricing.

For a deterministic local rehearsal, select the fake provider explicitly:

```powershell
uv run maf-outcome-economics demo --provider fake --limit 20
```

The console marks fake runs as `REHEARSAL MODE`. Their provider, model, and
token counts are illustrative and cannot be interpreted as live telemetry.
The `demo` command runs baseline and optimized variants over the same ticket
set, prints trace IDs and token totals, compares quality and estimated
economics, and persists the optimized governance decision.

For live economics, seed a pricing record whose provider and model labels match
the normalized Azure OpenAI chat spans. Seeded values remain estimates and
must be supplied from an approved pricing source.

Execute the complete live comparison after authentication, configuration, and
pricing setup:

```powershell
uv run maf-outcome-economics demo --provider live --limit 1
```

The command prints progress for every fictional ticket, real trace IDs, actual
input and output token counts from model spans, deterministic acceptance, a
baseline-to-optimized economics comparison, and a `SCALE`, `OPTIMIZE`, or
`STOP` governance result. See [DEMO.md](DEMO.md) for the two-minute sequence.

## Application Insights Traces

SQLite trace persistence is always enabled. To send the same safe spans to an
Application Insights resource, copy its connection string from the Azure portal
and set it locally:

```dotenv
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...;IngestionEndpoint=...
```

Restart the CLI process after changing `.env`. The `health` command and the
live-mode panel report whether Application Insights export is configured,
without displaying the connection string:

```powershell
uv run maf-outcome-economics health
uv run maf-outcome-economics demo --provider live --limit 1
```

Azure Monitor receives spans asynchronously. Allow a few minutes for ingestion,
then search the Application Insights `requests` and `dependencies` tables by the
32-character trace ID printed by the CLI:

```kusto
union requests, dependencies
| where operation_Id == "<TRACE_ID>"
| order by timestamp asc
```

Prompt and ticket text remain disabled. Application Insights receives span
names, timing, status, trace correlation, model identity, token counts, and the
safe workflow attributes emitted by this application.

## Local Telemetry Exporters

### Console exporters

Enable Agent Framework console exporters for a local diagnostic run by setting
this value in `.env`:

```dotenv
ENABLE_CONSOLE_EXPORTERS=true
```

Run a one-ticket rehearsal or live workflow, then restore the setting to
`false` when the additional terminal output is no longer needed:

```powershell
uv run maf-outcome-economics run --variant optimized --provider fake --limit 1
```

Console output follows the same sensitive-data setting. The application always
passes `enable_sensitive_data=False` to Agent Framework telemetry setup.

### Optional Aspire Dashboard OTLP export

Start a standalone Aspire Dashboard with anonymous local OTLP ingestion. The
dashboard UI listens on port `18888`, and OTLP HTTP listens on host port `4318`:

```powershell
docker run --rm --name aspire-dashboard `
    -p 18888:18888 `
    -p 4317:18889 `
    -p 4318:18890 `
    -e DOTNET_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS=true `
    mcr.microsoft.com/dotnet/aspire-dashboard:latest
```

Set the collector endpoint in `.env`, restart the CLI process, and open
<http://localhost:18888>:

```dotenv
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
```

Remove `OTEL_EXPORTER_OTLP_ENDPOINT` when the dashboard is not running. Leaving
an unavailable endpoint configured causes expected exporter connection errors.

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
real MAF agents. The console also provides deterministic fake agents for tests
and explicitly selected rehearsals. Fake mode never acts as an implicit
fallback for missing live configuration or telemetry.

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

Outcome verification deterministically compares the final category, priority,
and resolver group with the ticket-owned gold labels. Acceptance requires all
three fields to match; review approval never determines correctness. Persisted
results include per-field correctness, `correction_required`, a three-field
quality score, and separate `P1` critical-priority recall. The parent span
records only verification booleans and numeric quality, never ticket text.

## Outcome Economics

`OutcomeEconomicsCalculator` consumes normalized model calls, deterministic
verification results, and provider/model pricing. It bills only semantic chat
calls and defensively deduplicates them by trace ID and span ID, preventing
outer agent spans or repeated exports from inflating cost.

The result reports input and output tokens, estimated model cost, accepted
outcomes, cost and tokens per accepted outcome, and estimated contribution cost
by agent. Per-accepted-outcome values are `None` when no outcome is accepted.
Retry tax includes calls after the first attempt for the same business task and
agent. Coordination tax includes reviewer, critic, and aggregator calls;
`ReviewAgent` is a coordination role for this MVP. Taxes are analytical subsets
of total model cost and can overlap when a coordination call is also a retry.

## Governance

`GovernanceEngine` reads minimum acceptance, average quality, Critical-priority
recall, and maximum cost-per-accepted-outcome thresholds from the
`OutcomeContract`. It returns typed evidence metrics, machine-readable reason
codes, and recommended actions, and can persist the decision through
`OutcomeRepository`.

Decision precedence is deterministic. Any failed quality or safety gate, or no
accepted outcomes, returns `STOP`. When all quality and safety gates pass but
unit cost is above budget, the engine returns `OPTIMIZE`. It returns `SCALE`
when every threshold is met; equality counts as meeting a threshold.

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

A chat span is billable only when it contains explicit, valid, nonnegative
input and output token attributes. Spans with missing or malformed token
counters remain available for diagnostics but are excluded from economics.
Failed, cancelled, interrupted, or partially consumed workflow streams
terminalize created runs as `failed` or `interrupted` rather than leaving them
in `running` state.

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
