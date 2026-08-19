"""Tests for Microsoft Agent Framework OpenTelemetry persistence."""

import pytest
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExportResult
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Status, StatusCode
from opentelemetry.util.types import AttributeValue

from maf_outcome_economics.config import Settings
from maf_outcome_economics.domain import Ticket, WorkflowVariant
from maf_outcome_economics.persistence import OutcomeRepository
from maf_outcome_economics.telemetry import MAFSpanNormalizer, SQLiteSpanExporter
from maf_outcome_economics.telemetry import setup as telemetry_setup


@pytest.fixture(autouse=True)
def reset_telemetry_setup():
    """Isolate process-global telemetry setup between tests."""
    telemetry_setup.reset_telemetry_configuration()
    yield
    telemetry_setup.reset_telemetry_configuration()


def _make_maf_chat_span(
    attribute_overrides: dict[str, AttributeValue] | None = None,
    omitted_attributes: set[str] | None = None,
) -> ReadableSpan:
    provider = TracerProvider()
    memory_exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(memory_exporter))
    tracer = provider.get_tracer("telemetry-tests")
    attributes: dict[str, AttributeValue] = {
        "gen_ai.operation.name": "chat",
        "gen_ai.provider.name": "illustrative-provider",
        "gen_ai.request.model": "requested-model",
        "gen_ai.response.model": "response-model",
        "gen_ai.usage.input_tokens": 120,
        "gen_ai.usage.output_tokens": 30,
        "gen_ai.agent.id": "agent-001",
        "gen_ai.agent.name": "Triage Agent",
        "workflow.id": "workflow-001",
        "session.id": "session-001",
        "executor.id": "executor-001",
        "message.source_id": "source-001",
        "message.target_id": "target-001",
        "error.type": "RateLimitError",
        "gen_ai.input.messages": "sensitive prompt content",
    }
    attributes.update(attribute_overrides or {})
    for key in omitted_attributes or set():
        attributes.pop(key, None)
    with tracer.start_as_current_span("workflow parent"), tracer.start_as_current_span(
        "chat model call",
        attributes=attributes,
    ) as child_span:
        child_span.set_status(Status(StatusCode.ERROR, "illustrative failure"))
    return next(
        span for span in memory_exporter.get_finished_spans() if span.name == "chat model call"
    )


def test_normalizer_extracts_maf_attributes_without_sensitive_content() -> None:
    normalized = MAFSpanNormalizer().normalize(_make_maf_chat_span())

    assert normalized.input_tokens == 120
    assert normalized.output_tokens == 30
    assert normalized.agent_id == "agent-001"
    assert normalized.agent_name == "Triage Agent"
    assert normalized.request_model == "requested-model"
    assert normalized.response_model == "response-model"
    assert normalized.operation_name == "chat"
    assert normalized.workflow_id == "workflow-001"
    assert normalized.session_id == "session-001"
    assert normalized.executor_id == "executor-001"
    assert normalized.message_source == "source-001"
    assert normalized.message_target == "target-001"
    assert normalized.error_type == "RateLimitError"
    assert normalized.parent_span_id is not None
    assert normalized.status_code == "ERROR"
    assert normalized.status_description == "illustrative failure"
    assert "gen_ai.input.messages" not in normalized.attributes


def test_exporter_persists_span_and_deduplicates_billable_chat_call(tmp_path) -> None:
    database_path = tmp_path / "telemetry.db"
    exporter = SQLiteSpanExporter(database_path)
    readable_span = _make_maf_chat_span()

    assert exporter.export([readable_span, readable_span]) is SpanExportResult.SUCCESS
    assert exporter.export([readable_span]) is SpanExportResult.SUCCESS

    repository = OutcomeRepository(database_path)
    spans = repository.list_telemetry_spans()
    billable_usage = repository.list_billable_model_usage()
    assert len(spans) == 1
    assert spans[0]["parent_span_id"] is not None
    assert spans[0]["status_code"] == "ERROR"
    assert spans[0]["started_at"]
    assert spans[0]["ended_at"]
    assert len(billable_usage) == 1
    assert billable_usage[0]["input_tokens"] == 120
    assert billable_usage[0]["output_tokens"] == 30
    assert billable_usage[0]["agent_id"] == "agent-001"
    assert billable_usage[0]["workflow_id"] == "workflow-001"


@pytest.mark.parametrize("output_tokens", [-1, float("nan"), "missing"])
def test_missing_or_malformed_tokens_persist_span_without_billable_usage(
    tmp_path,
    output_tokens: AttributeValue,
) -> None:
    # Arrange
    database_path = tmp_path / "telemetry.db"
    exporter = SQLiteSpanExporter(database_path)
    readable_span = _make_maf_chat_span(
        {"gen_ai.usage.output_tokens": output_tokens},
        omitted_attributes={"gen_ai.usage.input_tokens"},
    )

    # Act
    result = exporter.export([readable_span])

    # Assert
    repository = OutcomeRepository(database_path)
    assert result is SpanExportResult.SUCCESS
    assert len(repository.list_telemetry_spans()) == 1
    assert repository.list_billable_model_usage() == []


def test_non_chat_span_is_not_billable(tmp_path) -> None:
    provider = TracerProvider()
    memory_exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(memory_exporter))
    tracer = provider.get_tracer("telemetry-tests")
    with tracer.start_as_current_span(
        "workflow run",
        attributes={"gen_ai.operation.name": "invoke_agent", "gen_ai.request.model": "model"},
    ):
        pass
    exporter = SQLiteSpanExporter(tmp_path / "telemetry.db")
    assert exporter.export(memory_exporter.get_finished_spans()) is SpanExportResult.SUCCESS
    assert OutcomeRepository(tmp_path / "telemetry.db").list_billable_model_usage() == []


def test_exporter_associates_ticket_trace_spans_and_usage_with_persisted_run(
    tmp_path,
) -> None:
    database_path = tmp_path / "telemetry.db"
    repository = OutcomeRepository(database_path)
    repository.save_ticket(
        Ticket(
            id="TKT-TRACE",
            subject="Fictional trace correlation",
            description="Verify model spans are associated with their run.",
            gold_category="Application",
            gold_priority="P3",
            gold_resolver_group="Business Applications",
        )
    )
    provider = TracerProvider()
    memory_exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(memory_exporter))
    tracer = provider.get_tracer("telemetry-tests")
    with tracer.start_as_current_span("tokenomics.ticket") as parent:
        trace_id = format(parent.get_span_context().trace_id, "032x")
        repository.create_run(
            "run-trace",
            "TKT-TRACE",
            WorkflowVariant.BASELINE,
            trace_id=trace_id,
            business_task_id="task-trace",
        )
        with tracer.start_as_current_span(
            "chat model call",
            attributes={
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "requested-model",
                "gen_ai.usage.input_tokens": 10,
                "gen_ai.usage.output_tokens": 5,
            },
        ):
            pass
    exporter = SQLiteSpanExporter(database_path)
    assert exporter.export(memory_exporter.get_finished_spans()) is SpanExportResult.SUCCESS

    spans = repository.list_telemetry_spans("run-trace")
    usage = repository.list_model_usage("run-trace")
    billable_usage = repository.list_billable_model_usage()
    assert {span["name"] for span in spans} == {"tokenomics.ticket", "chat model call"}
    assert len(usage) == 1
    assert usage[0]["trace_id"] == trace_id
    assert billable_usage[0]["business_task_id"] == "task-trace"


def test_configure_telemetry_disables_sensitive_capture(
    tmp_path, mocker
) -> None:
    configure = mocker.patch.object(telemetry_setup, "configure_otel_providers")
    mocker.patch.object(
        telemetry_setup.Settings,
        "from_env",
        return_value=Settings(database_path=tmp_path / "telemetry.db"),
    )

    exporter = telemetry_setup.configure_telemetry(tmp_path / "telemetry.db")

    assert isinstance(exporter, SQLiteSpanExporter)
    configure.assert_called_once_with(enable_sensitive_data=False, exporters=[exporter])


def test_configure_telemetry_adds_application_insights_exporter_when_configured(
    tmp_path, mocker
) -> None:
    configure = mocker.patch.object(telemetry_setup, "configure_otel_providers")
    azure_exporter = mocker.patch.object(telemetry_setup, "AzureMonitorTraceExporter")
    azure_exporter.return_value = mocker.Mock()
    connection_string = "InstrumentationKey=00000000-0000-0000-0000-000000000000"
    mocker.patch.object(
        telemetry_setup.Settings,
        "from_env",
        return_value=Settings(
            applicationinsights_connection_string=connection_string,
            database_path=tmp_path / "telemetry.db",
        ),
    )

    sqlite_exporter = telemetry_setup.configure_telemetry(tmp_path / "telemetry.db")

    azure_exporter.assert_called_once_with(connection_string=connection_string)
    configure.assert_called_once_with(
        enable_sensitive_data=False,
        exporters=[sqlite_exporter, azure_exporter.return_value],
    )


def test_configure_telemetry_is_idempotent(tmp_path, mocker) -> None:
    # Arrange
    configure = mocker.patch.object(telemetry_setup, "configure_otel_providers")
    mocker.patch.object(
        telemetry_setup.Settings,
        "from_env",
        return_value=Settings(database_path=tmp_path / "telemetry.db"),
    )

    # Act
    first = telemetry_setup.configure_telemetry(tmp_path / "telemetry.db")
    second = telemetry_setup.configure_telemetry(tmp_path / "telemetry.db")

    # Assert
    assert second is first
    configure.assert_called_once()