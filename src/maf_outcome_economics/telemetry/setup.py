"""Agent Framework observability setup."""

from pathlib import Path

from agent_framework.observability import configure_otel_providers

from maf_outcome_economics.config import Settings
from maf_outcome_economics.telemetry.sqlite_exporter import SQLiteSpanExporter


def configure_telemetry(database_path: Path | None = None) -> SQLiteSpanExporter:
    """Configure MAF telemetry with secure SQLite and environment exporters."""
    path = database_path or Settings.from_env().database_path
    exporter = SQLiteSpanExporter(path)
    configure_otel_providers(enable_sensitive_data=False, exporters=[exporter])
    return exporter