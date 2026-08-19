"""Agent Framework observability setup."""

from pathlib import Path
from typing import Any, cast

from agent_framework.observability import configure_otel_providers
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry import trace
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter

from maf_outcome_economics.config import Settings
from maf_outcome_economics.telemetry.sqlite_exporter import SQLiteSpanExporter

_configured_exporter: SQLiteSpanExporter | None = None
_configured_application_insights = False


def configure_telemetry(
    database_path: Path | None = None,
    *,
    enable_application_insights: bool = True,
) -> SQLiteSpanExporter:
    """Configure secure SQLite and optional Application Insights trace export."""
    global _configured_application_insights, _configured_exporter
    settings = Settings.from_env()
    path = (database_path or settings.database_path).resolve()
    if (
        _configured_exporter is not None
        and _configured_exporter.database_path.resolve() == path
        and _configured_application_insights == enable_application_insights
    ):
        return _configured_exporter

    exporter = SQLiteSpanExporter(path)
    exporters: list[SpanExporter] = [exporter]
    if (
        enable_application_insights
        and settings.applicationinsights_connection_string
    ):
        exporters.append(
            AzureMonitorTraceExporter(
                connection_string=settings.applicationinsights_connection_string
            )
        )
    if _configured_exporter is not None:
        provider = trace.get_tracer_provider()
        add_span_processor = getattr(provider, "add_span_processor", None)
        if callable(add_span_processor):
            for trace_exporter in exporters:
                add_span_processor(BatchSpanProcessor(trace_exporter))
            _configured_exporter = exporter
            _configured_application_insights = enable_application_insights
            return exporter
    configure_otel_providers(
        enable_sensitive_data=False,
        exporters=cast(Any, exporters),
    )
    _configured_exporter = exporter
    _configured_application_insights = enable_application_insights
    return exporter


def reset_telemetry_configuration() -> None:
    """Reset application setup state for isolated tests."""
    global _configured_application_insights, _configured_exporter
    _configured_exporter = None
    _configured_application_insights = False