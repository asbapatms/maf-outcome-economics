"""Generic record adapter for persisted support-ticket scenario evidence."""

from datetime import datetime

from maf_outcome_economics.core import (
    EvidenceRecord,
    ReportingPeriod,
    ReviewOutcome,
    WorkUnit,
)
from maf_outcome_economics.domain import WorkflowVariant
from maf_outcome_economics.persistence.sqlite_repository import OutcomeRepository

from .verification import RoutingVerificationResult

TICKET_VARIANT_IDS = {
    WorkflowVariant.BASELINE: "ticket-baseline-v1",
    WorkflowVariant.OPTIMIZED: "ticket-optimized-v1",
}


class TicketScenarioConnector:
    """Normalize ticket runs and deterministic verification into generic records."""

    def __init__(self, repository: OutcomeRepository) -> None:
        self._repository = repository

    async def load_work_units(self, period: ReportingPeriod) -> list[WorkUnit]:
        """Return completed ticket runs as generic work units."""
        work_units: list[WorkUnit] = []
        for row in self._repository.list_runs():
            completed_at_value = row.get("completed_at")
            if row.get("status") != "completed" or not completed_at_value:
                continue
            completed_at = datetime.fromisoformat(str(completed_at_value))
            if not period.start_at <= completed_at < period.end_at:
                continue
            variant = WorkflowVariant(str(row["variant"]))
            work_units.append(
                WorkUnit(
                    id=str(row["id"]),
                    process_variant_id=TICKET_VARIANT_IDS[variant],
                    started_at=datetime.fromisoformat(str(row["started_at"])),
                    completed_at=completed_at,
                    attributes={
                        "ticket_id": str(row["ticket_id"]),
                        "business_task_id": str(row.get("business_task_id") or ""),
                        "trace_id": str(row.get("trace_id") or ""),
                    },
                )
            )
        return work_units

    async def load_evidence(self, period: ReportingPeriod) -> list[EvidenceRecord]:
        """Return generic facts derived from deterministic routing verification."""
        records: list[EvidenceRecord] = []
        runs_by_id = {
            str(row["id"]): row for row in self._repository.list_runs()
        }
        for variant in WorkflowVariant:
            for verification in self._repository.list_routing_verifications(variant):
                run_id = verification.run_id
                if run_id is None or run_id not in runs_by_id:
                    continue
                run = runs_by_id[run_id]
                completed_at_value = run.get("completed_at")
                if not completed_at_value:
                    continue
                completed_at = datetime.fromisoformat(str(completed_at_value))
                if not period.start_at <= completed_at < period.end_at:
                    continue
                records.extend(self._verification_evidence(verification, completed_at))
        return records

    async def load_review_outcomes(
        self,
        period: ReportingPeriod,
    ) -> dict[str, ReviewOutcome]:
        """Classify invoked reviews by their effect on verified routing."""
        tickets = {ticket.id: ticket for ticket in self._repository.list_tickets()}
        verifications = {
            verification.run_id: verification
            for variant in WorkflowVariant
            for verification in self._repository.list_routing_verifications(variant)
            if verification.run_id is not None
        }
        outcomes: dict[str, ReviewOutcome] = {}
        for row in self._repository.list_runs():
            run_id = str(row["id"])
            run = self._repository.get_run(run_id)
            if run is None or run.get("review") is None:
                continue
            completed_at_value = run.get("completed_at")
            if not completed_at_value:
                continue
            completed_at = datetime.fromisoformat(str(completed_at_value))
            if not period.start_at <= completed_at < period.end_at:
                continue
            triage = run.get("triage")
            ticket = tickets.get(str(run["ticket_id"]))
            verification = verifications.get(run_id)
            if triage is None or ticket is None or verification is None:
                outcomes[run_id] = ReviewOutcome.INCONCLUSIVE
                continue
            triage_passed = (
                triage.category == ticket.gold_category
                and triage.priority == ticket.gold_priority
                and triage.resolver_group == ticket.gold_resolver_group
            )
            if not triage_passed and verification.accepted:
                outcomes[run_id] = ReviewOutcome.USEFUL_CORRECTION
            elif triage_passed and not verification.accepted:
                outcomes[run_id] = ReviewOutcome.HARMFUL_CORRECTION
            else:
                outcomes[run_id] = ReviewOutcome.NON_CONTRIBUTING
        return outcomes

    @staticmethod
    def _verification_evidence(
        verification: RoutingVerificationResult,
        observed_at: datetime,
    ) -> list[EvidenceRecord]:
        values: list[tuple[str, bool | float]] = [
            ("routing_accepted", verification.accepted),
            ("quality_score", float(verification.quality_score)),
        ]
        if verification.critical_priority_recalled is not None:
            values.append(
                (
                    "critical_priority_recalled",
                    verification.critical_priority_recalled,
                )
            )
        return [
            EvidenceRecord(
                id=f"ticket:{verification.id}:{metric}",
                work_unit_id=verification.run_id or "unknown",
                metric=metric,
                value=value,
                source="deterministic-routing-verifier",
                observed_at=observed_at,
                provenance={
                    "verification_id": verification.id,
                    "contract_id": verification.contract_id,
                },
            )
            for metric, value in values
        ]