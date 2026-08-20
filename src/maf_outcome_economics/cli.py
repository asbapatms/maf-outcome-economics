"""Command-line interface."""

import asyncio
import platform
import sqlite3
from dataclasses import dataclass
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path
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
from maf_outcome_economics.core import (
    GenericGovernanceAction,
    GenericGovernanceDecision,
)
from maf_outcome_economics.demo_report import write_demo_report, write_scenario_index
from maf_outcome_economics.domain import (
    GovernanceAction,
    GovernanceDecision,
    GovernanceReasonCode,
    PricingRecord,
)
from maf_outcome_economics.persistence import OutcomeRepository
from maf_outcome_economics.scenarios import (
    SCENARIO_CATALOG,
    InvoiceProcessingScenario,
    ScenarioId,
)
from maf_outcome_economics.scenarios.invoice import InvoiceScenarioResult
from maf_outcome_economics.scenarios.ticket import (
    FICTIONAL_TICKETS,
    DemoScenario,
    TicketGenericAnalysis,
    TicketScenario,
    TicketWorkflowResult,
    TriageResult,
    WorkflowVariant,
)
from maf_outcome_economics.telemetry import configure_telemetry

app = typer.Typer(help="Analyze and verify outcome economics.", no_args_is_help=True)
console = Console()

GovernanceDisplayDecision = GovernanceDecision | GenericGovernanceDecision


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
    ticket_count = TicketScenario().seed(repository)
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
        if provider is ConsoleProvider.LIVE
        and settings.applicationinsights_configured
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
    table.add_column("Labels")
    table.add_column("Accepted")
    table.add_column("Review")
    table.add_column("Usage")
    usage_label = "illustrative" if provider is ConsoleProvider.FAKE else "captured"
    for result in results:
        verification = result.verification
        matched_labels = sum(
            (
                verification.category_correct,
                verification.priority_correct,
                verification.resolver_group_correct,
            )
        )
        table.add_row(
            result.triage.ticket_id,
            result.run_id,
            result.trace_id,
            f"{matched_labels}/3",
            "yes" if verification.accepted else "no",
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


def _tokenomics_table(analysis: TicketGenericAnalysis) -> Table:
    """Render token efficiency and review attribution from generic analysis."""
    comparison = analysis.token_comparison
    table = Table(title="Verified Outcome Tokenomics")
    table.add_column("Metric")
    table.add_column("Baseline", justify="right")
    table.add_column("Optimized", justify="right")
    rows = (
        (
            "Verified outcomes",
            str(comparison.control.verified_outcomes),
            str(comparison.treatment.verified_outcomes),
        ),
        (
            "Total tokens",
            f"{comparison.control.total_tokens:,}",
            f"{comparison.treatment.total_tokens:,}",
        ),
        (
            "Tokens / verified outcome",
            _decimal_text(comparison.control.tokens_per_verified_outcome),
            _decimal_text(comparison.treatment.tokens_per_verified_outcome),
        ),
        (
            "Review tokens",
            f"{analysis.control_review_attribution.total_review_tokens:,}",
            f"{analysis.treatment_review_attribution.total_review_tokens:,}",
        ),
        (
            "Non-contributing review tokens",
            f"{analysis.control_review_attribution.non_contributing_review_tokens:,}",
            f"{analysis.treatment_review_attribution.non_contributing_review_tokens:,}",
        ),
        (
            "Token efficiency improvement",
            "-",
            (
                f"{comparison.efficiency_improvement:.1%}"
                if comparison.efficiency_improvement is not None
                else "n/a"
            ),
        ),
    )
    for row in rows:
        table.add_row(*row)
    return table


def _decimal_text(value: Decimal | None) -> str:
    return f"{value:,.2f}" if value is not None else "n/a"


def _decision_panel(decision: GovernanceDisplayDecision) -> Panel:
    if isinstance(decision, GenericGovernanceDecision):
        gates = "\n".join(
            f"- {result.gate.value}: {result.status.value} ({result.reason})"
            for result in decision.gate_results
        )
        actions = "\n".join(
            f"- {action}" for action in decision.recommended_actions
        )
        optimizations = "\n".join(
            f"- {recommendation.suggested_action} "
            f"({recommendation.evidence_metric}: "
            f"{recommendation.observed_value} vs "
            f"{recommendation.target_value})"
            for recommendation in decision.optimization_recommendations
        )
        optimization_section = (
            f"\n\n[bold]Token optimization[/bold]\n{optimizations}"
            if optimizations
            else ""
        )
        border_style = {
            GenericGovernanceAction.SCALE: "green",
            GenericGovernanceAction.MONITOR: "cyan",
            GenericGovernanceAction.OPTIMIZE: "yellow",
            GenericGovernanceAction.STOP: "red",
            GenericGovernanceAction.INSUFFICIENT_EVIDENCE: "yellow",
        }[decision.action]
        return Panel(
            f"[bold]Generic gates[/bold]\n{gates}\n\n"
            f"[bold]Recommended action[/bold]\n{actions}"
            f"{optimization_section}",
            title=f"Governance Decision: {decision.action.value.upper()}",
            border_style=border_style,
        )
    explanations = {
        GovernanceReasonCode.THRESHOLDS_MET: (
            "Quality and safety gates passed, and cost per accepted outcome is "
            "within budget."
        ),
        GovernanceReasonCode.COST_EXCEEDS_BUDGET: (
            "Quality passed, but cost per accepted outcome exceeds the approved budget."
        ),
        GovernanceReasonCode.NO_ACCEPTED_OUTCOMES: (
            "No outcomes passed deterministic verification."
        ),
        GovernanceReasonCode.ACCEPTANCE_BELOW_MINIMUM: (
            "The verified acceptance rate is below the contract minimum."
        ),
        GovernanceReasonCode.QUALITY_BELOW_MINIMUM: (
            "Average deterministic quality is below the contract minimum."
        ),
        GovernanceReasonCode.CRITICAL_RECALL_BELOW_MINIMUM: (
            "Critical-priority recall is below the safety threshold."
        ),
    }
    reason_codes = ", ".join(code.value for code in decision.reason_codes)
    reasons = "\n".join(f"- {explanations[code]}" for code in decision.reason_codes)
    actions = "\n".join(f"- {action}" for action in decision.recommended_actions)
    return Panel(
        f"[bold]Why[/bold]\n{reasons}\n\n"
        f"[bold]Recommended action[/bold]\n{actions}\n\n"
        f"[dim]Audit codes: {reason_codes}[/dim]",
        title=f"Governance Decision: {decision.action.value.upper()}",
        border_style="green" if decision.action is GovernanceAction.SCALE else "yellow",
    )


def _demo_intro_panel(limit: int, provider: ConsoleProvider) -> Panel:
    usage_source = (
        "actual MAF OpenTelemetry spans"
        if provider is ConsoleProvider.LIVE
        else "illustrative rehearsal records"
    )
    return Panel(
        "[bold]Question[/bold]: Can risk-based review preserve routing quality "
        "while reducing token cost?\n\n"
        f"[bold]Experiment[/bold]: Run the same {limit} fictional ticket(s) through "
        "both workflow designs.\n"
        "[bold]Baseline[/bold]: Triage + review every ticket.\n"
        "[bold]Optimized[/bold]: Triage every ticket; review only low-confidence, "
        "sensitive, or critical results.\n"
        "[bold]Acceptance[/bold]: Category, priority, and resolver group must all "
        "match hidden gold labels.\n"
        f"[bold]Usage evidence[/bold]: {usage_source}.",
        title="OutcomeMeter Experiment",
        border_style="cyan",
    )


def _variant_strategy_panel(variant: WorkflowVariant) -> Panel:
    if variant is WorkflowVariant.BASELINE:
        message = (
            "Control workflow: every triage result receives a second model review. "
            "This maximizes oversight but adds coordination tokens."
        )
    else:
        message = (
            "Treatment workflow: deterministic risk rules invoke review only for "
            "confidence < 0.8, sensitive content, P1 priority, or a critical category."
        )
    return Panel(message, title=f"{variant.value.title()} Strategy", border_style="blue")


def _outcome_panel(
    reports: list[VariantReport],
    decision: GovernanceDisplayDecision,
) -> Panel:
    baseline, optimized = reports
    baseline_tokens = (
        baseline.economics.total_input_tokens
        + baseline.economics.total_output_tokens
    )
    optimized_tokens = (
        optimized.economics.total_input_tokens
        + optimized.economics.total_output_tokens
    )
    token_delta = optimized_tokens - baseline_tokens
    token_change = (
        Decimal(token_delta) / Decimal(baseline_tokens)
        if baseline_tokens
        else Decimal(0)
    )
    cost_delta = (
        optimized.economics.estimated_model_cost
        - baseline.economics.estimated_model_cost
    )
    quality_delta = optimized.average_quality - baseline.average_quality
    if token_delta < 0:
        interpretation = (
            "The optimized workflow preserved measured quality with fewer tokens."
            if quality_delta >= 0
            else "The optimized workflow used fewer tokens but reduced measured quality."
        )
    elif token_delta == 0:
        interpretation = (
            "This sample triggered the same review work in both variants, so no token "
            "saving was observed."
        )
    else:
        interpretation = "The optimized workflow used more tokens in this sample."
    return Panel(
        f"[bold]Token change[/bold]: {token_delta:+,} "
        f"({token_change:+.1%}; {baseline_tokens:,} baseline -> "
        f"{optimized_tokens:,} optimized)\n"
        f"[bold]Estimated cost change[/bold]: {cost_delta:+.6f} "
        f"{optimized.economics.currency}\n"
        f"[bold]Average quality change[/bold]: {quality_delta:+.1%}\n"
        f"[bold]Interpretation[/bold]: {interpretation}\n\n"
        f"[bold]Decision[/bold]: {decision.action.value.upper()} based on the "
        "optimized workflow's quality, safety, and unit-cost gates.",
        title="What Changed and Why It Matters",
        border_style="magenta",
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


async def _run_demo_variants(
    service: ConsoleService,
    limit: int,
    provider: ConsoleProvider,
) -> tuple[
    list[VariantReport],
    GovernanceDisplayDecision,
    list[TicketProgress],
    TicketGenericAnalysis | None,
]:
    """Run both demo variants on one event loop and calculate the decision."""
    progress_events: list[TicketProgress] = []

    def record_progress(event: TicketProgress) -> None:
        progress_events.append(event)
        _print_ticket_progress(event)

    for variant in WorkflowVariant:
        console.print(_variant_strategy_panel(variant))
        console.print(
            f"\n[bold]Starting {variant.value} variant[/bold]: "
            f"up to {limit} tickets using {provider.value} provider."
        )
        results = await service.run_variant(
            variant, limit, provider, record_progress
        )
        console.print(_result_table(results, provider))
        service.validate_variant_pricing(variant)
        console.print(f"Completed {variant.value} variant.")
    console.print("\n[bold]Calculating quality and outcome economics...[/bold]")
    reports = [service.report(variant) for variant in WorkflowVariant]
    console.print("Evaluating optimized governance decision...")
    decision: GovernanceDisplayDecision
    generic_analysis: TicketGenericAnalysis | None = None
    if provider is ConsoleProvider.LIVE:
        generic_analysis = await service.analyze_generic()
        decision = generic_analysis.decision
    else:
        decision = service.decide(WorkflowVariant.OPTIMIZED)
    return reports, decision, progress_events, generic_analysis


def _execute_demo(
    settings: Settings,
    limit: int,
    provider: ConsoleProvider,
    html_output: Path,
    scenario: DemoScenario | None = None,
) -> tuple[list[VariantReport], GovernanceDisplayDecision]:
    repository = OutcomeRepository(settings.database_path)
    TicketScenario().seed(repository, scenario)
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
    if scenario is not None:
        console.print(
            Panel(
                f"Fictional evidence designed to exercise the "
                f"{scenario.value.upper()} governance path. The deterministic "
                "engine still calculates the action from quality, safety, and cost.",
                title=f"Scenario Dataset: {scenario.value.upper()}",
                border_style="cyan",
            )
        )
    console.print(_demo_intro_panel(limit, provider))
    service = ConsoleService(settings)
    reports, decision, progress_events, generic_analysis = asyncio.run(
        _run_demo_variants(service, limit, provider)
    )
    console.print(_comparison_table(reports))
    if generic_analysis is not None:
        console.print(_tokenomics_table(generic_analysis))
    console.print(_outcome_panel(reports, decision))
    console.print(_decision_panel(decision))
    report_path = write_demo_report(
        html_output,
        reports,
        decision,
        provider,
        progress_events,
        limit,
        generic_analysis,
    )
    console.print(f"[bold green]HTML report:[/bold green] {report_path}")
    return reports, decision


def _scenario_summary(
    results: list[tuple[DemoScenario, VariantReport, GovernanceDecision, Path]],
) -> Table:
    table = Table(title="All Three Governance Outcomes")
    table.add_column("Dataset")
    table.add_column("Quality", justify="right")
    table.add_column("Critical recall", justify="right")
    table.add_column("Cost / accepted", justify="right")
    table.add_column("Budget", justify="right")
    table.add_column("Decision")
    table.add_column("HTML report")
    for scenario, report, decision, report_path in results:
        cost = report.economics.cost_per_accepted_outcome
        evidence = decision.evidence_metrics
        budget = (
            evidence.maximum_cost_per_accepted_outcome
            if evidence is not None
            else None
        )
        table.add_row(
            scenario.value.upper(),
            f"{report.average_quality:.1%}",
            f"{report.critical_priority_recall:.1%}",
            f"{cost:.6f}" if cost is not None else "n/a",
            f"{budget:.6f}" if budget is not None else "n/a",
            decision.action.value.upper(),
            str(report_path),
        )
    return table


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
    except KeyboardInterrupt as error:
        console.print("[yellow]Run interrupted.[/yellow]")
        raise typer.Exit(code=130) from error
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
    html_output: Annotated[
        Path,
        typer.Option(
            help="Self-contained HTML report written after each successful demo."
        ),
    ] = Path("artifacts/hackathon-live-demo.html"),
    scenario: Annotated[
        DemoScenario | None,
        typer.Option(
            help="Use an isolated rehearsal dataset for a governance outcome."
        ),
    ] = None,
) -> None:
    """Run both variants and render console plus HTML economics evidence."""
    settings = Settings.from_env()
    if scenario is not None:
        if provider is not ConsoleProvider.FAKE:
            console.print(
                "[red]Scenario datasets require --provider fake so the expected "
                "governance path is reproducible.[/red]"
            )
            raise typer.Exit(code=2)
        scenario_path = Path("data") / f"demo-{scenario.value}.db"
        scenario_path.unlink(missing_ok=True)
        settings = settings.model_copy(update={"database_path": scenario_path})
        limit = min(limit, 3)
        if html_output == Path("artifacts/hackathon-live-demo.html"):
            html_output = Path("artifacts") / f"demo-{scenario.value}.html"
    try:
        _execute_demo(
            settings,
            limit,
            provider,
            html_output,
            scenario,
        )
    except ConsoleSetupError as error:
        console.print(f"[red]Demo setup error:[/red] {error}")
        raise typer.Exit(code=2) from error
    except KeyboardInterrupt as error:
        console.print("[yellow]Demo interrupted.[/yellow]")
        raise typer.Exit(code=130) from error
    except Exception as error:
        console.print(f"[red]Demo failed:[/red] {error}")
        raise typer.Exit(code=1) from error


@app.command("demo-scenarios")
def demo_scenarios() -> None:
    """Run isolated fictional datasets for SCALE, OPTIMIZE, and STOP."""
    base_settings = Settings.from_env()
    results: list[
        tuple[DemoScenario, VariantReport, GovernanceDecision, Path]
    ] = []
    try:
        for scenario in DemoScenario:
            database_path = Path("data") / f"demo-{scenario.value}.db"
            database_path.unlink(missing_ok=True)
            html_output = Path("artifacts") / f"demo-{scenario.value}.html"
            settings = base_settings.model_copy(update={"database_path": database_path})
            console.rule(f"[bold]{scenario.value.upper()} DATASET[/bold]")
            reports, decision = _execute_demo(
                settings,
                3,
                ConsoleProvider.FAKE,
                html_output,
                scenario,
            )
            if not isinstance(decision, GovernanceDecision):
                raise RuntimeError("Rehearsal scenarios require legacy governance")
            optimized = next(
                report
                for report in reports
                if report.variant is WorkflowVariant.OPTIMIZED
            )
            results.append((scenario, optimized, decision, html_output.resolve()))
    except KeyboardInterrupt as error:
        console.print("[yellow]Scenario demo interrupted.[/yellow]")
        raise typer.Exit(code=130) from error
    except Exception as error:
        console.print(f"[red]Scenario demo failed:[/red] {error}")
        raise typer.Exit(code=1) from error
    console.print(_scenario_summary(results))
    index_path = write_scenario_index(
        Path("artifacts/demo-scenarios.html"),
        [
            (scenario.value, report, decision, report_path)
            for scenario, report, decision, report_path in results
        ],
    )
    console.print(f"[bold green]Scenario index:[/bold green] {index_path}")


def _print_invoice_scenario(result: InvoiceScenarioResult) -> None:
    """Render normalized invoice economics and governance."""
    table = Table(title="Invoice Processing Outcome Economics")
    table.add_column("Metric")
    table.add_column("Manual", justify="right")
    table.add_column("Automated", justify="right")
    table.add_row(
        "Verified invoices",
        str(result.comparison.control.verified_outcomes),
        str(result.comparison.treatment.verified_outcomes),
    )
    table.add_row(
        "Total cost",
        f"{result.comparison.control.total_cost:.2f} USD",
        f"{result.comparison.treatment.total_cost:.2f} USD",
    )
    table.add_row(
        "Cost / verified invoice",
        f"{result.comparison.control.cost_per_verified_outcome:.2f} USD",
        f"{result.comparison.treatment.cost_per_verified_outcome:.2f} USD",
    )
    console.print(table)
    console.print(
        Panel(
            f"[bold]Net savings[/bold]: {result.comparison.net_savings:.2f} USD\n"
            f"[bold]Governance action[/bold]: {result.decision.action.value.upper()}\n\n"
            "Invoice records were normalized through generic connector contracts; "
            "verification, cost comparison, and governance contain no invoice logic.",
            title="Generic Architecture Proof",
            border_style="green",
        )
    )


@app.command("list-scenarios")
def list_scenarios() -> None:
    """List runnable reference scenarios and their shortcut commands."""
    table = Table(title="Available Outcome Economics Scenarios")
    table.add_column("Scenario ID")
    table.add_column("Name")
    table.add_column("Shortcut")
    for descriptor in SCENARIO_CATALOG:
        table.add_row(
            descriptor.id.value,
            descriptor.name,
            descriptor.shortcut,
        )
    console.print(table)


@app.command("run-scenario")
def run_scenario(
    scenario: Annotated[
        ScenarioId,
        typer.Argument(help="Stable scenario identifier from list-scenarios."),
    ],
) -> None:
    """Run a reference scenario through its deterministic local path."""
    console.rule(f"[bold]{scenario.value}[/bold]")
    if scenario is ScenarioId.INVOICE_PROCESSING:
        _print_invoice_scenario(asyncio.run(InvoiceProcessingScenario().run()))
        return

    database_path = Path("data") / "scenario-ticket-triage.db"
    database_path.unlink(missing_ok=True)
    settings = Settings.from_env().model_copy(update={"database_path": database_path})
    try:
        _execute_demo(
            settings,
            3,
            ConsoleProvider.FAKE,
            Path("artifacts") / "ticket-triage.html",
        )
    except KeyboardInterrupt as error:
        console.print("[yellow]Scenario interrupted.[/yellow]")
        raise typer.Exit(code=130) from error
    except Exception as error:
        console.print(f"[red]Scenario failed:[/red] {error}")
        raise typer.Exit(code=1) from error


@app.command("invoice-demo")
def invoice_demo() -> None:
    """Run the generic invoice-processing economics scenario."""
    _print_invoice_scenario(asyncio.run(InvoiceProcessingScenario().run()))


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
    except KeyboardInterrupt as error:
        console.print("Agent smoke test interrupted.")
        raise typer.Exit(code=130) from error
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