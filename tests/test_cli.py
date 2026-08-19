"""Tests for the Typer CLI."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from typer.testing import CliRunner

from maf_outcome_economics.agents import create_rehearsal_agent_suite
from maf_outcome_economics.cli import AgentSmokeResult, app
from maf_outcome_economics.config import Settings
from maf_outcome_economics.console_service import (
    ConsoleProvider,
    ConsoleService,
    ConsoleSetupError,
)
from maf_outcome_economics.domain import TriageResult, WorkflowVariant
from maf_outcome_economics.persistence import OutcomeRepository, seed_fictional_tickets


def test_given_local_environment_when_health_runs_then_dependencies_are_reported() -> None:
    # Arrange
    runner = CliRunner()

    # Act
    result = runner.invoke(app, ["health"])

    # Assert
    assert result.exit_code == 0
    assert "Agent Framework" in result.stdout
    assert "SQLite" in result.stdout


def test_init_db_creates_schema(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    database_path = tmp_path / "cli.db"
    monkeypatch.setenv("MAF_DATABASE_PATH", str(database_path))

    result = CliRunner().invoke(app, ["init-db"])

    assert result.exit_code == 0
    assert database_path.exists()
    assert "outcome_contracts" in OutcomeRepository(database_path).table_names()


def test_seed_inserts_fictional_tickets_and_configurable_estimated_pricing(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "cli.db"
    monkeypatch.setenv("MAF_DATABASE_PATH", str(database_path))

    result = CliRunner().invoke(
        app,
        [
            "seed",
            "--provider",
            "demo-provider",
            "--model",
            "demo-model",
            "--input-cost-per-million",
            "1.25",
            "--output-cost-per-million",
            "5.00",
        ],
    )

    repository = OutcomeRepository(database_path)
    pricing = repository.list_pricing()
    assert result.exit_code == 0
    assert "estimated" in result.stdout
    assert len(repository.list_tickets()) == 20
    assert pricing[0].input_cost_per_million_tokens == Decimal("1.25")
    assert pricing[0].output_cost_per_million_tokens == Decimal("5.0")
    assert pricing[0].illustrative is True


def test_telemetry_smoke_test_proves_span_was_persisted(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "telemetry.db"
    monkeypatch.setenv("MAF_DATABASE_PATH", str(database_path))
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", raising=False)

    result = CliRunner().invoke(app, ["telemetry-smoke-test"])

    spans = OutcomeRepository(database_path).list_telemetry_spans()
    assert result.exit_code == 0
    assert "Telemetry smoke test passed" in result.stdout
    assert len(spans) == 1
    assert spans[0]["name"] == "telemetry.smoke_test"
    assert spans[0]["attributes"]["smoke_test.id"]


def test_agent_smoke_test_prints_response_trace_and_captured_tokens(
    monkeypatch: pytest.MonkeyPatch,
    mocker,
) -> None:
    # Arrange
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_CHAT_MODEL", "test-deployment")
    smoke_result = AgentSmokeResult(
        response=TriageResult(
            run_id="smoke-test",
            ticket_id="TKT-001",
            category="Identity and access",
            priority="P2",
            resolver_group="Identity Operations",
            confidence=0.95,
            rationale="The fictional user cannot sign in.",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        trace_id="0123456789abcdef0123456789abcdef",
        input_tokens=120,
        output_tokens=30,
    )
    run_smoke = mocker.patch(
        "maf_outcome_economics.cli._run_agent_smoke_test",
        new=mocker.AsyncMock(return_value=smoke_result),
    )

    # Act
    result = CliRunner().invoke(app, ["agent-smoke-test"])

    # Assert
    assert result.exit_code == 0
    assert 'response={"run_id":"smoke-test"' in result.stdout
    assert "trace_id=0123456789abcdef0123456789abcdef" in result.stdout
    assert "captured_tokens input=120 output=30" in result.stdout
    run_smoke.assert_awaited_once()


def test_run_defaults_to_live_and_requires_azure_configuration(
    tmp_path, mocker
) -> None:
    settings = Settings(database_path=tmp_path / "cli.db")
    mocker.patch("maf_outcome_economics.cli.Settings.from_env", return_value=settings)

    result = CliRunner().invoke(app, ["run", "--variant", "baseline", "--limit", "1"])

    assert result.exit_code == 2
    assert "LIVE MODE" in result.stdout
    assert "AZURE_OPENAI_ENDPOINT" in result.stdout
    assert "AZURE_OPENAI_CHAT_MODEL" in result.stdout


async def test_live_run_rejects_missing_chat_usage_without_substitution(
    tmp_path, mocker
) -> None:
    settings = Settings(
        azure_openai_endpoint="https://example.openai.azure.com",
        azure_openai_chat_model="test-deployment",
        database_path=tmp_path / "cli.db",
    )
    repository = OutcomeRepository(settings.database_path)
    seed_fictional_tickets(repository)
    mocker.patch(
        "maf_outcome_economics.console_service.create_support_agent_suite",
        return_value=create_rehearsal_agent_suite(),
    )

    with pytest.raises(RuntimeError, match="no billable chat telemetry"):
        await ConsoleService(settings).run_variant(
            WorkflowVariant.BASELINE, 1, ConsoleProvider.LIVE
        )

    assert repository.list_billable_model_usage() == []


def test_explicit_fake_run_persists_illustrative_usage(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "cli.db"
    monkeypatch.setenv("MAF_DATABASE_PATH", str(database_path))
    runner = CliRunner()
    assert runner.invoke(app, ["seed"]).exit_code == 0

    result = runner.invoke(
        app,
        ["run", "--variant", "baseline", "--limit", "1", "--provider", "fake"],
    )

    usage = OutcomeRepository(database_path).list_billable_model_usage()
    assert result.exit_code == 0
    assert "REHEARSAL MODE" in result.stdout
    assert "baseline 1/1: Starting TKT-001" in result.stdout
    assert "baseline 1/1: Completed TKT-001" in result.stdout
    assert "tokens=200" in result.stdout
    assert "in/50 out" in result.stdout
    assert "trace=" in result.stdout
    assert "illustrative" in result.stdout
    assert {row["provider"] for row in usage} == {"illustrative-provider"}
    assert sum(int(row["input_tokens"]) for row in usage) == 200
    assert sum(int(row["output_tokens"]) for row in usage) == 50


def test_compare_trace_and_decide_render_persisted_rehearsal_results(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "cli.db"
    monkeypatch.setenv("MAF_DATABASE_PATH", str(database_path))
    runner = CliRunner()
    assert runner.invoke(app, ["seed"]).exit_code == 0
    for variant in ("baseline", "optimized"):
        assert runner.invoke(
            app,
            ["run", "--variant", variant, "--limit", "1", "--provider", "fake"],
        ).exit_code == 0

    comparison = runner.invoke(app, ["compare"])
    trace_result = runner.invoke(app, ["trace", "--ticket", "TKT-001"])
    decision = runner.invoke(app, ["decide", "--variant", "optimized"])

    assert comparison.exit_code == 0
    assert "Input tokens" in comparison.stdout
    assert "Baseline" in comparison.stdout
    assert "Optimized" in comparison.stdout
    assert trace_result.exit_code == 0
    assert "Safe telemetry metadata" in trace_result.stdout
    assert "VPN drops every few minutes" not in trace_result.stdout
    assert decision.exit_code == 0
    assert "Governance: scale" in decision.stdout


def test_report_explains_how_to_seed_captured_live_model_pricing(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "cli.db"
    monkeypatch.setenv("MAF_DATABASE_PATH", str(database_path))
    runner = CliRunner()
    assert runner.invoke(app, ["seed"]).exit_code == 0
    assert runner.invoke(
        app,
        ["run", "--variant", "baseline", "--limit", "1", "--provider", "fake"],
    ).exit_code == 0
    repository = OutcomeRepository(database_path)
    run_id = str(repository.list_runs(WorkflowVariant.BASELINE)[0]["id"])
    repository.save_rehearsal_model_call(
        usage_id="captured-live-call",
        run_id=run_id,
        provider="azure.ai.openai",
        model="gpt-5.4-mini-2026-03-17",
        agent_id="triage",
        agent_name="TriageAgent",
        input_tokens=100,
        output_tokens=20,
    )

    with pytest.raises(ConsoleSetupError) as error:
        ConsoleService(Settings(database_path=database_path)).report(
            WorkflowVariant.BASELINE
        )

    message = str(error.value)
    assert "azure.ai.openai" in message
    assert "gpt-5.4-mini-2026-03-17" in message
    assert "--input-cost-per-million <INPUT_PRICE>" in message
    assert "--output-cost-per-million <OUTPUT_PRICE>" in message


def test_demo_runs_both_variants_with_trace_tokens_and_governance(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAF_DATABASE_PATH", str(tmp_path / "demo.db"))

    result = CliRunner().invoke(
        app, ["demo", "--limit", "1", "--provider", "fake"]
    )

    assert result.exit_code == 0
    assert "REHEARSAL MODE" in result.stdout
    assert "Starting baseline variant" in result.stdout
    assert "baseline 1/1: Starting TKT-001" in result.stdout
    assert "baseline 1/1: Completed TKT-001" in result.stdout
    assert "Starting optimized variant" in result.stdout
    assert "optimized 1/1: Completed TKT-001" in result.stdout
    assert "Calculating quality and outcome economics" in result.stdout
    assert "Evaluating optimized governance decision" in result.stdout
    assert "Baseline workflow results" in result.stdout
    assert "Optimized workflow results" in result.stdout
    assert "Trace ID" in result.stdout
    assert "Input tokens" in result.stdout
    assert "Governance: scale" in result.stdout