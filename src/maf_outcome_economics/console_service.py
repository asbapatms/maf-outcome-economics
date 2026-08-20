"""Shared execution and reporting operations for the Typer console."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from opentelemetry import trace

from maf_outcome_economics.config import Settings
from maf_outcome_economics.domain import (
    BillableModelCall,
    GovernanceDecision,
    OutcomeEconomics,
    PricingRecord,
)
from maf_outcome_economics.economics import OutcomeEconomicsCalculator
from maf_outcome_economics.governance import GovernanceEngine
from maf_outcome_economics.persistence import (
    OutcomeRepository,
)
from maf_outcome_economics.scenarios.ticket import (
    TicketEconomicsAnalyzer,
    TicketGenericAnalysis,
    TicketScenario,
    TicketWorkflowInput,
    TicketWorkflowResult,
    WorkflowVariant,
)
from maf_outcome_economics.telemetry import configure_telemetry


class ConsoleProvider(StrEnum):
    """Execution provider exposed by the console."""

    LIVE = "live"
    FAKE = "fake"


class ConsoleSetupError(RuntimeError):
    """Raised when console prerequisites are missing."""


@dataclass(frozen=True, slots=True)
class VariantReport:
    """Persisted quality and economics for one workflow variant."""

    variant: WorkflowVariant
    runs: int
    trace_ids: tuple[str, ...]
    economics: OutcomeEconomics
    acceptance_rate: float
    average_quality: float
    critical_priority_recall: float


@dataclass(frozen=True, slots=True)
class TicketProgress:
    """Safe progress details emitted around one ticket workflow execution."""

    stage: Literal["started", "completed"]
    variant: WorkflowVariant
    ticket_id: str
    current: int
    total: int
    run_id: str | None = None
    trace_id: str | None = None
    accepted: bool | None = None
    review_invoked: bool | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class ConsoleService:
    """Run and report on live or explicitly fake workflow executions."""

    def __init__(
        self,
        settings: Settings,
        scenario: TicketScenario | None = None,
    ) -> None:
        self.settings = settings
        self.repository = OutcomeRepository(settings.database_path)
        self.scenario = scenario or TicketScenario()
        self._telemetry_configured = False

    async def run_variant(
        self,
        variant: WorkflowVariant,
        limit: int,
        provider: ConsoleProvider,
        progress: Callable[[TicketProgress], None] | None = None,
    ) -> list[TicketWorkflowResult]:
        """Run a labelled ticket subset and require usage for every live result."""
        if provider is ConsoleProvider.LIVE and not self.settings.azure_openai_configured:
            raise ConsoleSetupError(
                "Live mode requires AZURE_OPENAI_ENDPOINT and "
                "AZURE_OPENAI_CHAT_MODEL. Configure .env and run az login."
            )
        tickets = self.repository.list_tickets()[:limit]
        if not tickets:
            raise ConsoleSetupError("No tickets found. Run the seed command first.")
        contract_id = self.scenario.contract_id(variant)
        if self.repository.get_outcome_contract(contract_id) is None:
            raise ConsoleSetupError("Outcome contract missing. Run the seed command first.")

        if not self._telemetry_configured:
            configure_telemetry(
                self.settings.database_path,
                enable_application_insights=provider is ConsoleProvider.LIVE,
            )
            self._telemetry_configured = True
        suite = self.scenario.create_agent_suite(
            self.settings,
            live=provider is ConsoleProvider.LIVE,
        )
        results: list[TicketWorkflowResult] = []
        try:
            for index, ticket in enumerate(tickets, start=1):
                if progress is not None:
                    progress(
                        TicketProgress(
                            stage="started",
                            variant=variant,
                            ticket_id=ticket.id,
                            current=index,
                            total=len(tickets),
                        )
                    )
                before_ids = {
                    row["id"] for row in self.repository.list_billable_model_usage()
                }
                request = TicketWorkflowInput(
                    ticket=ticket,
                    business_task_id=f"{variant.value}:{ticket.id}",
                    batch_id=f"batch-{variant.value}-{uuid4()}",
                    contract_id=contract_id,
                    variant=variant,
                )
                output = None
                async for event in self.scenario.stream(
                    request,
                    self.repository,
                    suite,
                ):
                    if event.type == "output" and isinstance(
                        event.data, TicketWorkflowResult
                    ):
                        output = event.data
                if output is None:
                    raise RuntimeError("Workflow did not emit a typed result")
                if provider is ConsoleProvider.LIVE:
                    self._flush_telemetry()
                    new_usage = [
                        row
                        for row in self.repository.list_billable_model_usage()
                        if row["id"] not in before_ids
                    ]
                    if not new_usage:
                        raise RuntimeError(
                            "Live workflow captured no billable chat telemetry; "
                            "no synthetic usage was substituted."
                        )
                    self.repository.assign_model_usage_to_run(
                        [str(row["id"]) for row in new_usage], output.run_id
                    )
                    input_tokens = sum(int(row["input_tokens"]) for row in new_usage)
                    output_tokens = sum(int(row["output_tokens"]) for row in new_usage)
                else:
                    input_tokens, output_tokens = self._record_rehearsal_usage(output)
                results.append(output)
                if progress is not None:
                    progress(
                        TicketProgress(
                            stage="completed",
                            variant=variant,
                            ticket_id=ticket.id,
                            current=index,
                            total=len(tickets),
                            run_id=output.run_id,
                            trace_id=output.trace_id,
                            accepted=output.verification.accepted,
                            review_invoked=output.review_invoked,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                        )
                    )
        finally:
            await suite.close()
        return results

    def report(self, variant: WorkflowVariant) -> VariantReport:
        """Calculate quality and economics from persisted normalized records."""
        runs = self.repository.list_runs(variant)
        verifications = self.repository.list_routing_verifications(variant)
        usage = self.repository.list_billable_model_usage_for_variant(variant)
        if not runs or not verifications:
            raise ConsoleSetupError(f"No {variant.value} runs found. Run that variant first.")
        pricing = self.repository.list_pricing()
        if not pricing:
            raise ConsoleSetupError("No pricing found. Run the seed command first.")
        self.require_pricing(usage, pricing)
        economics = OutcomeEconomicsCalculator(pricing).calculate(
            [self._model_call(row) for row in usage],
            verifications,
        )
        total = len(verifications)
        critical = [item for item in verifications if item.critical_priority_expected]
        return VariantReport(
            variant=variant,
            runs=len(runs),
            trace_ids=tuple(str(row["trace_id"]) for row in runs if row["trace_id"]),
            economics=economics,
            acceptance_rate=sum(item.accepted for item in verifications) / total,
            average_quality=sum(float(item.quality_score) for item in verifications) / total,
            critical_priority_recall=(
                sum(item.critical_priority_recalled is True for item in critical)
                / len(critical)
                if critical
                else 1.0
            ),
        )

    async def analyze_generic(self) -> TicketGenericAnalysis:
        """Analyze all persisted ticket runs through the generic core pipeline."""
        pricing = self.repository.list_pricing()
        if not pricing:
            raise ConsoleSetupError("No pricing found. Run the seed command first.")
        self.require_pricing(self.repository.list_billable_model_usage(), pricing)
        try:
            return await TicketEconomicsAnalyzer(self.repository).analyze()
        except ValueError as error:
            raise ConsoleSetupError(str(error)) from error

    def validate_variant_pricing(self, variant: WorkflowVariant) -> None:
        """Require approved pricing for every captured call in one variant."""
        pricing = self.repository.list_pricing()
        if not pricing:
            raise ConsoleSetupError("No pricing found. Run the seed command first.")
        self.require_pricing(
            self.repository.list_billable_model_usage_for_variant(variant),
            pricing,
        )

    @staticmethod
    def require_pricing(
        usage: list[dict[str, Any]], pricing: list[PricingRecord]
    ) -> None:
        """Raise actionable guidance for captured provider/model pairs without pricing."""
        priced_models = {(record.provider, record.model) for record in pricing}
        unpriced_models = sorted(
            {
                (str(row["provider"]), str(row["model"]))
                for row in usage
                if (str(row["provider"]), str(row["model"])) not in priced_models
            }
        )
        if unpriced_models:
            provider, model = unpriced_models[0]
            raise ConsoleSetupError(
                f"Missing approved pricing for provider={provider!r}, model={model!r}. "
                "Seed the current prices, then rerun the demo:\n"
                f"uv run maf-outcome-economics seed --provider {provider} "
                f"--model {model} --input-cost-per-million <INPUT_PRICE> "
                "--output-cost-per-million <OUTPUT_PRICE>"
            )

    def decide(self, variant: WorkflowVariant) -> GovernanceDecision:
        """Evaluate and persist governance for one variant's current evidence."""
        report = self.report(variant)
        contract = self.repository.get_outcome_contract(self.scenario.contract_id(variant))
        if contract is None:
            raise ConsoleSetupError("Outcome contract missing. Run the seed command first.")
        return GovernanceEngine(self.repository).evaluate(
            decision_id=f"decision-{variant.value}-{uuid4()}",
            contract=contract,
            economics=report.economics,
            verifications=self.repository.list_routing_verifications(variant),
            decided_by="maf-outcome-economics-cli",
        )

    def ticket_trace(self, ticket_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Return runs and safe spans for a ticket identifier."""
        runs = [row for row in self.repository.list_runs() if row["ticket_id"] == ticket_id]
        spans = [
            span
            for run in runs
            for span in self.repository.list_telemetry_spans(str(run["id"]))
        ]
        return runs, spans

    @staticmethod
    def _model_call(row: dict[str, Any]) -> BillableModelCall:
        business_task_id = row.get("business_task_id")
        if not business_task_id:
            raise RuntimeError("Billable usage is missing business_task_id attribution")
        return BillableModelCall(
            trace_id=str(row["trace_id"]),
            span_id=str(row["span_id"]),
            business_task_id=str(business_task_id),
            provider=str(row["provider"]),
            model=str(row["model"]),
            operation_name=str(row["operation_name"]),
            input_tokens=int(row["input_tokens"]),
            output_tokens=int(row["output_tokens"]),
            agent_id=row.get("agent_id"),
            agent_name=row.get("agent_name"),
            executor_id=row.get("executor_id"),
            recorded_at=datetime.fromisoformat(str(row["recorded_at"])),
        )

    def _record_rehearsal_usage(self, result: TicketWorkflowResult) -> tuple[int, int]:
        calls = [("triage", "TriageAgent", 120, 30)]
        if result.review_invoked:
            calls.append(("review", "ReviewAgent", 80, 20))
        for index, (agent_id, agent_name, input_tokens, output_tokens) in enumerate(calls):
            self.repository.save_rehearsal_model_call(
                usage_id=f"rehearsal-{result.run_id}-{index}",
                run_id=result.run_id,
                provider="illustrative-provider",
                model="illustrative-model",
                agent_id=agent_id,
                agent_name=agent_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        return (
            sum(call[2] for call in calls),
            sum(call[3] for call in calls),
        )

    @staticmethod
    def _flush_telemetry() -> None:
        provider = trace.get_tracer_provider()
        force_flush = getattr(provider, "force_flush", None)
        if not callable(force_flush) or not force_flush(timeout_millis=10_000):
            raise RuntimeError("OpenTelemetry provider did not flush live agent spans")