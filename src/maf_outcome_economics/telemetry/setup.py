"""Agent Framework observability setup."""

from pathlib import Path
from typing import Any, cast

from agent_framework.observability import configure_otel_providers
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry.sdk.trace.export import SpanExporter

from maf_outcome_economics.config import Settings
from maf_outcome_economics.telemetry.sqlite_exporter import SQLiteSpanExporter


def configure_telemetry(database_path: Path | None = None) -> SQLiteSpanExporter:
    """Configure secure SQLite and optional Application Insights trace export."""
    settings = Settings.from_env()
    path = database_path or settings.database_path
    exporter = SQLiteSpanExporter(path)
    exporters: list[SpanExporter] = [exporter]
    if settings.applicationinsights_connection_string:
        exporters.append(
            AzureMonitorTraceExporter(
                connection_string=settings.applicationinsights_connection_string
            )
        )
    configure_otel_providers(
        enable_sensitive_data=False,
        exporters=cast(Any, exporters),
    )
    return exporter