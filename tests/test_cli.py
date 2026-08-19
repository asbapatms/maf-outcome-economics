"""Tests for the Typer CLI."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from typer.testing import CliRunner

from maf_outcome_economics.cli import AgentSmokeResult, app
from maf_outcome_economics.domain import TriageResult
from maf_outcome_economics.persistence import OutcomeRepository


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