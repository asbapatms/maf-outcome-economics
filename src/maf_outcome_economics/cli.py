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
from rich.table import Table

from maf_outcome_economics.agents import PromptProfile, create_support_agent_suite
from maf_outcome_economics.config import Settings
from maf_outcome_economics.domain import PricingRecord, TriageResult
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
        id="illustrative-default",
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