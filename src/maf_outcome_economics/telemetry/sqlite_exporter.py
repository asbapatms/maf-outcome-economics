"""OpenTelemetry span exporter backed by SQLite."""

import json
import logging
import sqlite3
from collections.abc import Sequence
from contextlib import closing
from pathlib import Path

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from maf_outcome_economics.persistence import OutcomeRepository

from .normalizer import MAFSpanNormalizer, NormalizedSpan

logger = logging.getLogger(__name__)


class SQLiteSpanExporter(SpanExporter):
    """Persist normalized spans and deduplicated billable chat calls to SQLite."""

    def __init__(
        self,
        database_path: Path,
        normalizer: MAFSpanNormalizer | None = None,
    ) -> None:
        self.database_path = database_path
        self.normalizer = normalizer or MAFSpanNormalizer()
        OutcomeRepository(database_path).initialize()

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Persist a batch of completed spans."""
        try:
            with closing(sqlite3.connect(self.database_path)) as connection, connection:
                connection.execute("PRAGMA foreign_keys = ON")
                for span in spans:
                    normalized = self.normalizer.normalize(span)
                    self._insert_span(connection, normalized)
                    if normalized.is_billable_model_call:
                        self._insert_billable_usage(connection, normalized)
        except (OSError, sqlite3.Error, TypeError, ValueError):
            logger.exception("Failed to export OpenTelemetry spans to SQLite")
            return SpanExportResult.FAILURE
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        """Release exporter resources."""

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Return immediately because exports commit synchronously."""
        return True

    @staticmethod
    def _insert_span(connection: sqlite3.Connection, span: NormalizedSpan) -> None:
        connection.execute(
            """INSERT OR IGNORE INTO telemetry_spans
            (id, run_id, trace_id, span_id, parent_span_id, name, started_at,
            ended_at, status_code, status_description, attributes_json)
            VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                f"{span.trace_id}:{span.span_id}",
                span.trace_id,
                span.span_id,
                span.parent_span_id,
                span.name,
                span.started_at.isoformat(),
                span.ended_at.isoformat() if span.ended_at else None,
                span.status_code,
                span.status_description,
                json.dumps(span.attributes, sort_keys=True),
            ),
        )

    @staticmethod
    def _insert_billable_usage(
        connection: sqlite3.Connection, span: NormalizedSpan
    ) -> None:
        model = span.response_model or span.request_model or "unknown"
        connection.execute(
            """INSERT OR IGNORE INTO model_usage
            (id, run_id, trace_id, span_id, provider, model, request_model,
            response_model, operation_name, agent_id, agent_name, workflow_id,
            session_id, executor_id, message_source, message_target, error_type,
            input_tokens, output_tokens, recorded_at)
            VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                f"{span.trace_id}:{span.span_id}",
                span.trace_id,
                span.span_id,
                span.provider_name or "unknown",
                model,
                span.request_model,
                span.response_model,
                span.operation_name,
                span.agent_id,
                span.agent_name,
                span.workflow_id,
                span.session_id,
                span.executor_id,
                span.message_source,
                span.message_target,
                span.error_type,
                span.input_tokens,
                span.output_tokens,
                (span.ended_at or span.started_at).isoformat(),
            ),
        )