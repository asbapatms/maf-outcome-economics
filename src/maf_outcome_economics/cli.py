"""Command-line interface."""

import asyncio
import platform
import sqlite3
from dataclasses import dataclass
from decimal import Decimal
from importlib.metadata import version
from typing import Annotated
from uuid import uuid4

import typer
from opentelemetry import trace
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from maf_outcome_economics.agents import PromptProfile, create_support_agent_suite
from maf_outcome_economics.config import Settings
from maf_outcome_economics.console_service import (
    ConsoleProvider,
    ConsoleService,
    ConsoleSetupError,
    TicketProgress,
    VariantReport,
)
from maf_outcome_economics.domain import (
    GovernanceDecision,
    PricingRecord,
    TicketWorkflowResult,
    TriageResult,
    WorkflowVariant,
)
from maf_outcome_economics.persistence import (
    FICTIONAL_TICKETS,
    OutcomeRepository,
    seed_fictional_tickets,
)
from maf_outcome_economics.telemetry import configure_telemetry

app = typer.Typer(help="Analyze and verify outcome economics.", no_args_is_help=True)
console = Console()


@dataclass(frozen=True, slots=True)
class AgentSmokeResult:
    """Observable result from one live agent invocation."""

    response: TriageResult
    trace_id: str
    input_tokens: int
    output_tokens: int


@app.callback()
def main() -> None:
    """Analyze and verify outcome economics."""


@app.command()
def health() -> None:
    """Check local runtime dependencies and non-secret configuration."""
    settings = Settings.from_env()
    table = Table(title="MAF Outcome Economics Health")
    table.add_column("Check")
    table.add_column("Status")
    table.add_row("Python", platform.python_version())
    table.add_row("SQLite", sqlite3.sqlite_version)
    table.add_row("Agent Framework", version("agent-framework"))
    azure_status = "configured" if settings.azure_openai_configured else "not configured"
    table.add_row("Azure OpenAI", azure_status)
    app_insights_status = (
        "configured" if settings.applicationinsights_configured else "not configured"
    )
    table.add_row("Application Insights", app_insights_status)
    table.add_row("Database", str(settings.database_path))
    console.print(table)


@app.command("init-db")
def init_db() -> None:
    """Initialize the configured SQLite database schema."""
    settings = Settings.from_env()
    repository = OutcomeRepository(settings.database_path)
    repository.initialize()
    console.print(f"Initialized SQLite database at {settings.database_path}")


@app.command()
def seed(
    provider: str = typer.Option("illustrative-provider", help="Illustrative provider label."),
    model: str = typer.Option("illustrative-model", help="Illustrative model label."),
    input_cost_per_million: float = typer.Option(
        2.50, min=0, help="Illustrative input-token price per million."
    ),
    output_cost_per_million: float = typer.Option(
        10.00, min=0, help="Illustrative output-token price per million."
    ),
) -> None:
    """Seed fictional tickets and configurable illustrative pricing."""
    settings = Settings.from_env()
    repository = OutcomeRepository(settings.database_path)
    ticket_count = seed_fictional_tickets(repository)
    pricing = PricingRecord(
        id=f"pricing:{provider}:{model}",
        provider=provider,
        model=model,
        input_cost_per_million_tokens=Decimal(str(input_cost_per_million)),
        output_cost_per_million_tokens=Decimal(str(output_cost_per_million)),
    )
    repository.save_pricing(pricing)
    console.print(f"Seeded {ticket_count} fictional support tickets.")
    console.print(
        "Seeded illustrative pricing. All monetary outputs derived from it are estimated."
    )


def _provider_panel(provider: ConsoleProvider, settings: Settings) -> Panel:
    telemetry_destination = (
        "SQLite + Application Insights"
        if settings.applicationinsights_configured
        else "SQLite only"
    )
    if provider is ConsoleProvider.FAKE:
        return Panel(
            "Deterministic fake agents and illustrative token counts are in use. "
            "These are rehearsal results, not live telemetry.\n"
            f"Telemetry destination: {telemetry_destination}.",
            title="REHEARSAL MODE",
            border_style="yellow",
        )
    return Panel(
        "Azure OpenAI agents are active. Token counts must come from captured chat spans.\n"
        f"Telemetry destination: {telemetry_destination}.",
        title="LIVE MODE",
        border_style="green",
    )


def _result_table(
    results: list[TicketWorkflowResult], provider: ConsoleProvider
) -> Table:
    table = Table(title=f"{results[0].variant.value.title()} workflow results")
    table.add_column("Ticket")
    table.add_column("Run")
    table.add_column("Trace ID")
    table.add_column("Accepted")
    table.add_column("Review")
    table.add_column("Usage")
    usage_label = "illustrative" if provider is ConsoleProvider.FAKE else "captured"
    for result in results:
        table.add_row(
            result.triage.ticket_id,
            result.run_id,
            result.trace_id,
            "yes" if result.verification.accepted else "no",
            "invoked" if result.review_invoked else "skipped",
            usage_label,
        )
    return table


def _comparison_table(reports: list[VariantReport]) -> Table:
    table = Table(title="Quality and outcome economics")
    table.add_column("Metric")
    for report in reports:
        table.add_column(report.variant.value.title(), justify="right")
    metrics = (
        ("Runs", lambda item: str(item.runs)),
        ("Acceptance rate", lambda item: f"{item.acceptance_rate:.1%}"),
        ("Average quality", lambda item: f"{item.average_quality:.1%}"),
        ("Critical recall", lambda item: f"{item.critical_priority_recall:.1%}"),
        ("Input tokens", lambda item: str(item.economics.total_input_tokens)),
        ("Output tokens", lambda item: str(item.economics.total_output_tokens)),
        (
            "Estimated model cost",
            lambda item: f"{item.economics.estimated_model_cost:.6f} {item.economics.currency}",
        ),
        (
            "Cost / accepted",
            lambda item: (
                f"{item.economics.cost_per_accepted_outcome:.6f}"
                if item.economics.cost_per_accepted_outcome is not None
                else "n/a"
            ),
        ),
        (
            "Tokens / accepted",
            lambda item: (
                f"{item.economics.tokens_per_accepted_outcome:.2f}"
                if item.economics.tokens_per_accepted_outcome is not None
                else "n/a"
            ),
        ),
    )
    for label, formatter in metrics:
        table.add_row(label, *(formatter(report) for report in reports))
    return table


def _decision_panel(decision: GovernanceDecision) -> Panel:
    reason_codes = ", ".join(code.value for code in decision.reason_codes)
    actions = "\n".join(f"- {action}" for action in decision.recommended_actions)
    return Panel(
        f"{decision.reason}\nReason codes: {reason_codes}\n{actions}",
        title=f"Governance: {decision.action.value}",
    )


def _print_ticket_progress(event: TicketProgress) -> None:
    prefix = f"{event.variant.value} {event.current}/{event.total}:"
    if event.stage == "started":
        console.print(f"[cyan]{prefix}[/cyan] Starting {event.ticket_id}...")
        return
    review = "invoked" if event.review_invoked else "skipped"
    accepted = "yes" if event.accepted else "no"
    console.print(
        f"[green]{prefix}[/green] Completed {event.ticket_id} | "
        f"accepted={accepted} | review={review} | "
        f"tokens={event.input_tokens} in/{event.output_tokens} out | "
        f"trace={event.trace_id}"
    )


@app.command("run")
def run_workflow(
    variant: Annotated[WorkflowVariant, typer.Option(help="Workflow variant to run.")],
    limit: Annotated[int, typer.Option(min=1, help="Maximum labelled tickets.")] = 20,
    provider: Annotated[
        ConsoleProvider,
        typer.Option(help="Live Azure agents or explicit fake rehearsal agents."),
    ] = ConsoleProvider.LIVE,
) -> None:
    """Run a workflow variant over labelled tickets."""
    settings = Settings.from_env()
    console.print(_provider_panel(provider, settings))
    console.print(
        f"Starting {variant.value} variant with up to {limit} tickets "
        f"using {provider.value} provider."
    )
    try:
        results = asyncio.run(
            ConsoleService(settings).run_variant(
                variant, limit, provider, _print_ticket_progress
            )
        )
    except ConsoleSetupError as error:
        console.print(f"[red]Setup error:[/red] {error}")
        raise typer.Exit(code=2) from error
    except Exception as error:
        console.print(f"[red]Run failed:[/red] {error}")
        raise typer.Exit(code=1) from error
    console.print(_result_table(results, provider))


@app.command()
def compare() -> None:
    """Compare persisted baseline and optimized quality and economics."""
    service = ConsoleService(Settings.from_env())
    try:
        reports = [service.report(variant) for variant in WorkflowVariant]
    except ConsoleSetupError as error:
        console.print(f"[red]Comparison unavailable:[/red] {error}")
        raise typer.Exit(code=2) from error
    console.print(_comparison_table(reports))


@app.command("trace")
def show_trace(
    ticket_id: Annotated[str, typer.Option("--ticket", help="Ticket identifier.")],
) -> None:
    """Show safe run and span metadata for one ticket."""
    runs, spans = ConsoleService(Settings.from_env()).ticket_trace(ticket_id)
    if not runs:
        console.print(f"[red]No runs found for ticket {ticket_id}.[/red]")
        raise typer.Exit(code=2)
    run_table = Table(title=f"Runs for {ticket_id}")
    run_table.add_column("Run")
    run_table.add_column("Variant")
    run_table.add_column("Status")
    run_table.add_column("Trace ID")
    for run in runs:
        run_table.add_row(
            str(run["id"]),
            str(run["variant"]),
            str(run["status"]),
            str(run["trace_id"] or "n/a"),
        )
    console.print(run_table)
    span_table = Table(title="Safe telemetry metadata")
    span_table.add_column("Name")
    span_table.add_column("Trace ID")
    span_table.add_column("Span ID")
    span_table.add_column("Status")
    for span in spans:
        span_table.add_row(
            str(span["name"]),
            str(span["trace_id"]),
            str(span["span_id"]),
            str(span["status_code"]),
        )
    console.print(span_table)


@app.command()
def decide(
    variant: Annotated[WorkflowVariant, typer.Option(help="Workflow variant to govern.")],
) -> None:
    """Evaluate and persist a deterministic governance decision."""
    try:
        decision = ConsoleService(Settings.from_env()).decide(variant)
    except ConsoleSetupError as error:
        console.print(f"[red]Decision unavailable:[/red] {error}")
        raise typer.Exit(code=2) from error
    console.print(_decision_panel(decision))


@app.command()
def demo(
    limit: Annotated[int, typer.Option(min=1, help="Tickets per variant.")] = 20,
    provider: Annotated[
        ConsoleProvider,
        typer.Option(help="Live Azure agents or explicit fake rehearsal agents."),
    ] = ConsoleProvider.LIVE,
) -> None:
    """Run both variants on the same data and print economics and governance."""
    settings = Settings.from_env()
    repository = OutcomeRepository(settings.database_path)
    seed_fictional_tickets(repository)
    if not repository.list_pricing():
        repository.save_pricing(
            PricingRecord(
                id="pricing:illustrative-provider:illustrative-model",
                provider="illustrative-provider",
                model="illustrative-model",
                input_cost_per_million_tokens=Decimal("2.50"),
                output_cost_per_million_tokens=Decimal("10.00"),
            )
        )
    console.print(_provider_panel(provider, settings))
    service = ConsoleService(settings)
    try:
        for variant in WorkflowVariant:
            console.print(
                f"\n[bold]Starting {variant.value} variant[/bold]: "
                f"up to {limit} tickets using {provider.value} provider."
            )
            results = asyncio.run(
                service.run_variant(variant, limit, provider, _print_ticket_progress)
            )
            console.print(_result_table(results, provider))
            service.validate_variant_pricing(variant)
            console.print(f"Completed {variant.value} variant.")
        console.print("\n[bold]Calculating quality and outcome economics...[/bold]")
        reports = [service.report(variant) for variant in WorkflowVariant]
        console.print("Evaluating optimized governance decision...")
        decision = service.decide(WorkflowVariant.OPTIMIZED)
    except ConsoleSetupError as error:
        console.print(f"[red]Demo setup error:[/red] {error}")
        raise typer.Exit(code=2) from error
    except Exception as error:
        console.print(f"[red]Demo failed:[/red] {error}")
        raise typer.Exit(code=1) from error
    console.print(_comparison_table(reports))
    console.print(_decision_panel(decision))


@app.command("telemetry-smoke-test")
def telemetry_smoke_test() -> None:
    """Export a custom span and verify its SQLite record."""
    settings = Settings.from_env()
    configure_telemetry(settings.database_path)
    marker = str(uuid4())
    tracer = trace.get_tracer("maf-outcome-economics.telemetry-smoke-test")
    with tracer.start_as_current_span("telemetry.smoke_test") as span:
        span.set_attribute("smoke_test.id", marker)

    provider = trace.get_tracer_provider()
    force_flush = getattr(provider, "force_flush", None)
    if not callable(force_flush) or not force_flush(timeout_millis=10_000):
        raise typer.Exit(code=1)

    repository = OutcomeRepository(settings.database_path)
    persisted = next(
        (
            stored_span
            for stored_span in repository.list_telemetry_spans()
            if stored_span["attributes"].get("smoke_test.id") == marker
        ),
        None,
    )
    if persisted is None:
        console.print("Telemetry smoke test failed: span was not written to SQLite.")
        raise typer.Exit(code=1)

    console.print(
        "Telemetry smoke test passed: "
        f"trace_id={persisted['trace_id']} span_id={persisted['span_id']}"
    )


async def _run_agent_smoke_test(
    settings: Settings,
    profile: PromptProfile,
) -> AgentSmokeResult:
    """Run one real MAF triage call and load its captured usage from SQLite."""
    configure_telemetry(settings.database_path)
    suite = create_support_agent_suite(settings)
    run_id = f"smoke-{uuid4()}"
    tracer = trace.get_tracer("maf-outcome-economics.agent-smoke-test")
    try:
        with tracer.start_as_current_span("agent.smoke_test") as span:
            trace_id = format(span.get_span_context().trace_id, "032x")
            response = await suite.triage.run(FICTIONAL_TICKETS[0], run_id, profile)
    finally:
        await suite.close()

    provider = trace.get_tracer_provider()
    force_flush = getattr(provider, "force_flush", None)
    if not callable(force_flush) or not force_flush(timeout_millis=10_000):
        raise RuntimeError("OpenTelemetry provider did not flush agent spans")

    usage = [
        record
        for record in OutcomeRepository(settings.database_path).list_billable_model_usage()
        if record["trace_id"] == trace_id
    ]
    if not usage:
        raise RuntimeError("No billable MAF chat span was captured for the smoke-test trace")
    return AgentSmokeResult(
        response=response,
        trace_id=trace_id,
        input_tokens=sum(int(record["input_tokens"]) for record in usage),
        output_tokens=sum(int(record["output_tokens"]) for record in usage),
    )


@app.command("agent-smoke-test")
def agent_smoke_test(
    profile: Annotated[
        PromptProfile,
        typer.Option(help="Prompt profile used for the live triage call."),
    ] = PromptProfile.OPTIMIZED,
) -> None:
    """Run one fictional ticket through a live Azure OpenAI-backed MAF agent."""
    settings = Settings.from_env()
    if not settings.azure_openai_configured:
        console.print(
            "Agent smoke test requires AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_CHAT_MODEL."
        )
        raise typer.Exit(code=2)
    try:
        result = asyncio.run(_run_agent_smoke_test(settings, profile))
    except Exception as error:
        console.print(f"Agent smoke test failed: {error}")
        raise typer.Exit(code=1) from error

    console.print(f"response={result.response.model_dump_json()}")
    console.print(f"trace_id={result.trace_id}")
    console.print(
        f"captured_tokens input={result.input_tokens} output={result.output_tokens}"
    )


if __name__ == "__main__":
    app()