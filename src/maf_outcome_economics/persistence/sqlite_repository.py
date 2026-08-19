"""SQLite repositories for outcome economics records."""

import json
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from maf_outcome_economics.domain import (
    EconomicAssessment,
    GovernanceDecision,
    OutcomeContract,
    PricingRecord,
    ReviewResult,
    RoutingVerificationResult,
    Ticket,
    TriageResult,
    Variant,
    VerificationResult,
    WorkflowVariant,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class OutcomeRepository:
    """Store domain, run, telemetry, pricing, and governance records in SQLite."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        """Create the database schema when it does not exist."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        with self._connect() as connection:
            connection.executescript(schema)
            self._migrate_runs_table(connection)
            self._migrate_telemetry_tables(connection)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def table_names(self) -> set[str]:
        """Return application table names in the initialized database."""
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        return {str(row["name"]) for row in rows}

    def save_ticket(self, ticket: Ticket) -> None:
        """Insert or replace a support ticket."""
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO tickets
                (id, gold_category, gold_priority, gold_resolver_group, payload)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    ticket.id,
                    ticket.gold_category,
                    ticket.gold_priority,
                    ticket.gold_resolver_group,
                    ticket.model_dump_json(),
                ),
            )

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        """Load a support ticket by identifier."""
        row = self._fetch_one("SELECT payload FROM tickets WHERE id = ?", (ticket_id,))
        return Ticket.model_validate_json(row["payload"]) if row else None

    def list_tickets(self) -> list[Ticket]:
        """List support tickets in identifier order."""
        rows = self._fetch_all("SELECT payload FROM tickets ORDER BY id")
        return [Ticket.model_validate_json(row["payload"]) for row in rows]

    def save_outcome_contract(self, contract: OutcomeContract) -> None:
        """Insert or replace an outcome contract."""
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO outcome_contracts (id, variant, status, payload)
                VALUES (?, ?, ?, ?)""",
                (
                    contract.id,
                    contract.variant.value,
                    contract.status.value,
                    contract.model_dump_json(),
                ),
            )

    def get_outcome_contract(self, contract_id: str) -> OutcomeContract | None:
        """Load an outcome contract by identifier."""
        row = self._fetch_one(
            "SELECT payload FROM outcome_contracts WHERE id = ?", (contract_id,)
        )
        return OutcomeContract.model_validate_json(row["payload"]) if row else None

    def list_outcome_contracts(self) -> list[OutcomeContract]:
        """List outcome contracts in identifier order."""
        rows = self._fetch_all("SELECT payload FROM outcome_contracts ORDER BY id")
        return [OutcomeContract.model_validate_json(row["payload"]) for row in rows]

    def create_run(
        self,
        run_id: str,
        ticket_id: str,
        variant: Variant | WorkflowVariant,
        started_at: datetime | None = None,
        trace_id: str | None = None,
        business_task_id: str | None = None,
    ) -> None:
        """Create a pending experiment run for a ticket."""
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO runs
                (id, ticket_id, business_task_id, variant, trace_id, status, started_at)
                VALUES (?, ?, ?, ?, ?, 'running', ?)""",
                (
                    run_id,
                    ticket_id,
                    business_task_id,
                    variant.value,
                    trace_id,
                    (started_at or _utc_now()).isoformat(),
                ),
            )

    def complete_run(
        self,
        run_id: str,
        triage: TriageResult,
        review: ReviewResult | None,
        completed_at: datetime | None = None,
    ) -> None:
        """Complete a run with its triage and review results."""
        self.initialize()
        with self._connect() as connection:
            cursor = connection.execute(
                """UPDATE runs SET status = 'completed', completed_at = ?,
                triage_payload = ?, review_payload = ? WHERE id = ?""",
                (
                    (completed_at or _utc_now()).isoformat(),
                    triage.model_dump_json(),
                    review.model_dump_json() if review else None,
                    run_id,
                ),
            )
            if cursor.rowcount == 0:
                raise KeyError(f"Run not found: {run_id}")

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Load a run and deserialize its optional result payloads."""
        row = self._fetch_one("SELECT * FROM runs WHERE id = ?", (run_id,))
        if row is None:
            return None
        result = dict(row)
        variant = result["variant"]
        try:
            result["variant"] = WorkflowVariant(variant)
        except ValueError:
            result["variant"] = Variant(variant)
        result["triage"] = (
            TriageResult.model_validate_json(result.pop("triage_payload"))
            if result["triage_payload"]
            else None
        )
        result["review"] = (
            ReviewResult.model_validate_json(result.pop("review_payload"))
            if result["review_payload"]
            else None
        )
        return result

    def list_runs(self, variant: WorkflowVariant | None = None) -> list[dict[str, Any]]:
        """List runs, optionally filtered by workflow variant."""
        if variant is None:
            rows = self._fetch_all("SELECT * FROM runs ORDER BY started_at")
        else:
            rows = self._fetch_all(
                "SELECT * FROM runs WHERE variant = ? ORDER BY started_at",
                (variant.value,),
            )
        return [dict(row) for row in rows]

    @staticmethod
    def _migrate_runs_table(connection: sqlite3.Connection) -> None:
        columns = {
            str(row["name"])
            for row in connection.execute("PRAGMA table_info(runs)").fetchall()
        }
        if "trace_id" not in columns:
            connection.execute("ALTER TABLE runs ADD COLUMN trace_id TEXT")
        if "business_task_id" not in columns:
            connection.execute("ALTER TABLE runs ADD COLUMN business_task_id TEXT")
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_runs_trace_id ON runs(trace_id)"
        )
        connection.execute(
            """CREATE INDEX IF NOT EXISTS idx_runs_business_task_id
            ON runs(business_task_id)"""
        )

    def save_telemetry_span(
        self,
        span_id: str,
        run_id: str | None,
        name: str,
        trace_id: str,
        started_at: datetime,
        ended_at: datetime | None = None,
        attributes: Mapping[str, Any] | None = None,
        parent_span_id: str | None = None,
        status_code: str = "UNSET",
        status_description: str | None = None,
    ) -> None:
        """Insert or replace a telemetry span."""
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO telemetry_spans
                (id, run_id, trace_id, span_id, parent_span_id, name, started_at,
                ended_at, status_code, status_description, attributes_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    f"{trace_id}:{span_id}",
                    run_id,
                    trace_id,
                    span_id,
                    parent_span_id,
                    name,
                    started_at.isoformat(),
                    ended_at.isoformat() if ended_at else None,
                    status_code,
                    status_description,
                    json.dumps(dict(attributes or {}), sort_keys=True),
                ),
            )

    def list_telemetry_spans(self, run_id: str | None = None) -> list[dict[str, Any]]:
        """List deserialized telemetry spans, optionally filtered by run."""
        if run_id is None:
            rows = self._fetch_all("SELECT * FROM telemetry_spans ORDER BY started_at")
        else:
            rows = self._fetch_all(
                "SELECT * FROM telemetry_spans WHERE run_id = ? ORDER BY started_at", (run_id,)
            )
        spans = [dict(row) for row in rows]
        for span in spans:
            span["attributes"] = json.loads(span.pop("attributes_json"))
        return spans

    def get_telemetry_span(self, trace_id: str, span_id: str) -> dict[str, Any] | None:
        """Load one deserialized telemetry span by its OpenTelemetry identity."""
        row = self._fetch_one(
            "SELECT * FROM telemetry_spans WHERE trace_id = ? AND span_id = ?",
            (trace_id, span_id),
        )
        if row is None:
            return None
        span = dict(row)
        span["attributes"] = json.loads(span.pop("attributes_json"))
        return span

    def save_model_usage(
        self,
        usage_id: str,
        run_id: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        recorded_at: datetime | None = None,
    ) -> None:
        """Insert or replace nonnegative token usage for a run."""
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("Token counts cannot be negative")
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO model_usage
                (id, run_id, trace_id, span_id, provider, model, operation_name,
                input_tokens, output_tokens, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, 'manual', ?, ?, ?)""",
                (
                    usage_id,
                    run_id,
                    f"manual:{run_id}",
                    usage_id,
                    provider,
                    model,
                    input_tokens,
                    output_tokens,
                    (recorded_at or _utc_now()).isoformat(),
                ),
            )

    def list_model_usage(self, run_id: str) -> list[dict[str, Any]]:
        """List model usage records for a run."""
        rows = self._fetch_all(
            "SELECT * FROM model_usage WHERE run_id = ? ORDER BY recorded_at", (run_id,)
        )
        return [dict(row) for row in rows]

    def list_billable_model_usage(self) -> list[dict[str, Any]]:
        """List deduplicated chat model-call usage records."""
        rows = self._fetch_all(
            """SELECT model_usage.*, runs.business_task_id
            FROM model_usage LEFT JOIN runs ON runs.id = model_usage.run_id
            WHERE operation_name = 'chat' ORDER BY recorded_at"""
        )
        return [dict(row) for row in rows]

    def list_billable_model_usage_for_variant(
        self, variant: WorkflowVariant
    ) -> list[dict[str, Any]]:
        """List normalized chat calls associated with one workflow variant."""
        rows = self._fetch_all(
            """SELECT model_usage.*, runs.business_task_id
            FROM model_usage JOIN runs ON runs.id = model_usage.run_id
            WHERE model_usage.operation_name = 'chat' AND runs.variant = ?
            ORDER BY model_usage.recorded_at""",
            (variant.value,),
        )
        return [dict(row) for row in rows]

    def assign_model_usage_to_run(self, usage_ids: list[str], run_id: str) -> None:
        """Associate newly captured live model calls with a sequential CLI run."""
        if not usage_ids:
            return
        self.initialize()
        placeholders = ", ".join("?" for _ in usage_ids)
        with self._connect() as connection:
            connection.execute(
                f"UPDATE model_usage SET run_id = ? WHERE id IN ({placeholders})",
                (run_id, *usage_ids),
            )

    def save_rehearsal_model_call(
        self,
        *,
        usage_id: str,
        run_id: str,
        provider: str,
        model: str,
        agent_id: str,
        agent_name: str,
        input_tokens: int,
        output_tokens: int,
        recorded_at: datetime | None = None,
    ) -> None:
        """Persist an explicitly synthetic chat call for fake-provider rehearsals."""
        self.initialize()
        timestamp = (recorded_at or _utc_now()).isoformat()
        with self._connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO model_usage
                (id, run_id, trace_id, span_id, provider, model, request_model,
                response_model, operation_name, agent_id, agent_name, input_tokens,
                output_tokens, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'chat', ?, ?, ?, ?, ?)""",
                (
                    usage_id,
                    run_id,
                    f"rehearsal:{run_id}",
                    usage_id,
                    provider,
                    model,
                    model,
                    model,
                    agent_id,
                    agent_name,
                    input_tokens,
                    output_tokens,
                    timestamp,
                ),
            )

    def list_routing_verifications(
        self, variant: WorkflowVariant
    ) -> list[RoutingVerificationResult]:
        """List typed routing verifications for one workflow variant."""
        rows = self._fetch_all(
            """SELECT verifications.payload FROM verifications
            JOIN runs ON runs.id = verifications.run_id
            WHERE runs.variant = ? ORDER BY verifications.id""",
            (variant.value,),
        )
        return [
            RoutingVerificationResult.model_validate_json(row["payload"])
            for row in rows
        ]

    def save_pricing(self, pricing: PricingRecord) -> None:
        """Insert or replace illustrative model pricing."""
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO pricing
                (id, provider, model, effective_at, illustrative, payload)
                VALUES (?, ?, ?, ?, 1, ?)""",
                (
                    pricing.id,
                    pricing.provider,
                    pricing.model,
                    pricing.effective_at.isoformat(),
                    pricing.model_dump_json(),
                ),
            )

    def get_pricing(self, pricing_id: str) -> PricingRecord | None:
        """Load a pricing record by identifier."""
        row = self._fetch_one("SELECT payload FROM pricing WHERE id = ?", (pricing_id,))
        return PricingRecord.model_validate_json(row["payload"]) if row else None

    def list_pricing(self) -> list[PricingRecord]:
        """List illustrative pricing by effective date."""
        rows = self._fetch_all("SELECT payload FROM pricing ORDER BY effective_at")
        return [PricingRecord.model_validate_json(row["payload"]) for row in rows]

    def save_verification(self, verification: VerificationResult) -> None:
        """Insert or replace an outcome verification."""
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO verifications
                (id, contract_id, run_id, passed, payload) VALUES (?, ?, ?, ?, ?)""",
                (
                    verification.id,
                    verification.contract_id,
                    verification.run_id,
                    int(verification.passed),
                    verification.model_dump_json(),
                ),
            )

    def list_verifications(self, contract_id: str) -> list[VerificationResult]:
        """List verifications for an outcome contract."""
        rows = self._fetch_all(
            "SELECT payload FROM verifications WHERE contract_id = ? ORDER BY id", (contract_id,)
        )
        results: list[VerificationResult] = []
        for row in rows:
            payload = json.loads(row["payload"])
            model = (
                RoutingVerificationResult
                if "category_correct" in payload
                else VerificationResult
            )
            results.append(model.model_validate(payload))
        return results

    def save_governance_decision(self, decision: GovernanceDecision) -> None:
        """Insert or replace a governance decision."""
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO governance_decisions
                (id, contract_id, action, payload) VALUES (?, ?, ?, ?)""",
                (
                    decision.id,
                    decision.contract_id,
                    decision.action.value,
                    decision.model_dump_json(),
                ),
            )

    def list_governance_decisions(self, contract_id: str) -> list[GovernanceDecision]:
        """List governance decisions for an outcome contract."""
        rows = self._fetch_all(
            """SELECT payload FROM governance_decisions
            WHERE contract_id = ? ORDER BY id""",
            (contract_id,),
        )
        return [GovernanceDecision.model_validate_json(row["payload"]) for row in rows]

    def save(self, assessment: EconomicAssessment) -> None:
        """Insert or replace an assessment."""
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO assessments (outcome_name, payload) VALUES (?, ?)",
                (assessment.outcome_name, assessment.model_dump_json()),
            )

    def get(self, outcome_name: str) -> EconomicAssessment | None:
        """Load an assessment by outcome name."""
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM assessments WHERE outcome_name = ?", (outcome_name,)
            ).fetchone()
        return EconomicAssessment.model_validate_json(row[0]) if row else None

    def _fetch_one(self, query: str, parameters: tuple[Any, ...]) -> sqlite3.Row | None:
        self.initialize()
        with self._connect() as connection:
            return connection.execute(query, parameters).fetchone()

    def _fetch_all(
        self, query: str, parameters: tuple[Any, ...] = ()
    ) -> list[sqlite3.Row]:
        self.initialize()
        with self._connect() as connection:
            return connection.execute(query, parameters).fetchall()

    def _migrate_telemetry_tables(self, connection: sqlite3.Connection) -> None:
        telemetry_columns = self._table_columns(connection, "telemetry_spans")
        if "parent_span_id" not in telemetry_columns:
            connection.executescript(
                """ALTER TABLE telemetry_spans RENAME TO telemetry_spans_legacy;
                CREATE TABLE telemetry_spans (
                    id TEXT PRIMARY KEY,
                    run_id TEXT REFERENCES runs(id),
                    trace_id TEXT NOT NULL,
                    span_id TEXT NOT NULL,
                    parent_span_id TEXT,
                    name TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    status_code TEXT NOT NULL,
                    status_description TEXT,
                    attributes_json TEXT NOT NULL,
                    UNIQUE (trace_id, span_id)
                );
                INSERT INTO telemetry_spans
                    (id, run_id, trace_id, span_id, name, started_at, ended_at,
                    status_code, attributes_json)
                SELECT trace_id || ':' || span_id, run_id, trace_id, span_id, name,
                    started_at, ended_at, 'UNSET', attributes_json
                FROM telemetry_spans_legacy;
                DROP TABLE telemetry_spans_legacy;
                CREATE INDEX idx_spans_run_id ON telemetry_spans(run_id);"""
            )

        usage_columns = self._table_columns(connection, "model_usage")
        if "trace_id" not in usage_columns:
            connection.executescript(
                """ALTER TABLE model_usage RENAME TO model_usage_legacy;
                CREATE TABLE model_usage (
                    id TEXT PRIMARY KEY,
                    run_id TEXT REFERENCES runs(id),
                    trace_id TEXT NOT NULL,
                    span_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    request_model TEXT,
                    response_model TEXT,
                    operation_name TEXT NOT NULL,
                    agent_id TEXT,
                    agent_name TEXT,
                    workflow_id TEXT,
                    session_id TEXT,
                    executor_id TEXT,
                    message_source TEXT,
                    message_target TEXT,
                    error_type TEXT,
                    input_tokens INTEGER NOT NULL CHECK (input_tokens >= 0),
                    output_tokens INTEGER NOT NULL CHECK (output_tokens >= 0),
                    recorded_at TEXT NOT NULL,
                    UNIQUE (trace_id, span_id)
                );
                INSERT INTO model_usage
                    (id, run_id, trace_id, span_id, provider, model, operation_name,
                    input_tokens, output_tokens, recorded_at)
                SELECT id, run_id, 'legacy:' || id, id, provider, model, 'manual',
                    input_tokens, output_tokens, recorded_at
                FROM model_usage_legacy;
                DROP TABLE model_usage_legacy;
                CREATE INDEX idx_usage_run_id ON model_usage(run_id);"""
            )

    @staticmethod
    def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {str(row["name"]) for row in rows}