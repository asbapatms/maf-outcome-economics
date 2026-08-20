"""Generic cost connector for persisted Microsoft Agent Framework telemetry."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from maf_outcome_economics.core import (
    CostCategory,
    CostEntry,
    CostEvidenceStatus,
    ReportingPeriod,
    TokenEntry,
    TokenPurpose,
)
from maf_outcome_economics.domain import PricingRecord

if TYPE_CHECKING:
    from maf_outcome_economics.persistence.sqlite_repository import OutcomeRepository

MILLION_TOKENS = Decimal(1_000_000)


class MAFTelemetryTokenConnector:
    """Normalize captured MAF chat usage into generic token observations."""

    def __init__(
        self,
        repository: OutcomeRepository,
        variant_ids: dict[str, str],
    ) -> None:
        self._repository = repository
        self._variant_ids = variant_ids

    async def load_tokens(self, period: ReportingPeriod) -> list[TokenEntry]:
        """Return one attributed token entry per captured billable chat span."""
        entries: list[TokenEntry] = []
        seen_attempts: set[tuple[str, str]] = set()
        for row in self._repository.list_billable_model_usage():
            recorded_at = datetime.fromisoformat(str(row["recorded_at"]))
            if not period.start_at <= recorded_at < period.end_at:
                continue
            run_id = row.get("run_id")
            if not run_id:
                continue
            work_unit_id = str(run_id)
            run = self._repository.get_run(work_unit_id)
            if run is None:
                continue
            variant_id = self._variant_ids.get(str(run["variant"]))
            if variant_id is None:
                continue
            agent_id = self._agent_identity(row)
            attempt_key = (work_unit_id, agent_id or "unknown")
            purpose = self._purpose(
                agent_id,
                is_retry=attempt_key in seen_attempts,
                run_status=str(run["status"]),
            )
            seen_attempts.add(attempt_key)
            entries.append(
                TokenEntry(
                    id=f"maf:{row['trace_id']}:{row['span_id']}",
                    process_variant_id=variant_id,
                    work_unit_id=work_unit_id,
                    agent_id=agent_id,
                    input_tokens=int(row["input_tokens"]),
                    output_tokens=int(row["output_tokens"]),
                    purpose=purpose,
                    source="maf-opentelemetry",
                    trace_id=str(row["trace_id"]),
                    span_id=str(row["span_id"]),
                    observed_at=recorded_at,
                )
            )
        return entries

    @staticmethod
    def _agent_identity(row: dict[str, Any]) -> str | None:
        for key in ("agent_id", "agent_name", "executor_id"):
            value = row.get(key)
            if value:
                return str(value)
        return None

    @staticmethod
    def _purpose(
        agent_id: str | None,
        *,
        is_retry: bool,
        run_status: str,
    ) -> TokenPurpose:
        if run_status != "completed":
            return TokenPurpose.FAILED_WORK
        if is_retry:
            return TokenPurpose.RETRY
        identity = (agent_id or "").lower()
        if "review" in identity:
            return TokenPurpose.REVIEW
        if any(role in identity for role in ("critic", "aggregator", "coordinator")):
            return TokenPurpose.COORDINATION
        if "triage" in identity:
            return TokenPurpose.PRIMARY_WORK
        return TokenPurpose.UNKNOWN


class MAFTelemetryCostConnector:
    """Normalize captured MAF chat usage into generic estimated model costs."""

    def __init__(
        self,
        repository: OutcomeRepository,
        pricing: list[PricingRecord],
        variant_ids: dict[str, str],
    ) -> None:
        if not pricing:
            raise ValueError("At least one pricing record is required")
        currencies = {record.currency for record in pricing}
        if len(currencies) != 1:
            raise ValueError("All pricing records must use one currency")
        self._repository = repository
        self._pricing = {
            (record.provider, record.model): record for record in pricing
        }
        self._variant_ids = variant_ids

    async def load_costs(self, period: ReportingPeriod) -> list[CostEntry]:
        """Return one generic model-cost entry per captured billable chat span."""
        entries: list[CostEntry] = []
        for row in self._repository.list_billable_model_usage():
            recorded_at = datetime.fromisoformat(str(row["recorded_at"]))
            if not period.start_at <= recorded_at < period.end_at:
                continue
            run_id = row.get("run_id")
            if not run_id:
                continue
            run = self._repository.get_run(str(run_id))
            if run is None:
                continue
            variant_id = self._variant_ids.get(str(run["variant"]))
            if variant_id is None:
                continue
            entries.append(
                self._to_cost_entry(
                    row,
                    variant_id=variant_id,
                    work_unit_id=str(run_id),
                    recorded_at=recorded_at,
                )
            )
        return entries

    def _to_cost_entry(
        self,
        row: dict[str, Any],
        *,
        variant_id: str,
        work_unit_id: str,
        recorded_at: datetime,
    ) -> CostEntry:
        provider = str(row["provider"])
        model = str(row["model"])
        pricing = self._pricing.get((provider, model))
        if pricing is None:
            raise ValueError(
                f"Missing pricing for provider={provider!r}, model={model!r}"
            )
        amount = (
            Decimal(int(row["input_tokens"]))
            * pricing.input_cost_per_million_tokens
            + Decimal(int(row["output_tokens"]))
            * pricing.output_cost_per_million_tokens
        ) / MILLION_TOKENS
        return CostEntry(
            id=f"maf:{row['trace_id']}:{row['span_id']}",
            process_variant_id=variant_id,
            work_unit_id=work_unit_id,
            category=CostCategory.MODEL,
            amount=amount,
            currency=pricing.currency,
            source="maf-opentelemetry",
            status=CostEvidenceStatus.ESTIMATED,
            reconciliation_key=f"maf:{row['trace_id']}:{row['span_id']}",
            incurred_at=recorded_at,
        )