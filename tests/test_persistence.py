"""Tests for SQLite persistence."""

import sqlite3
from datetime import UTC, datetime
from decimal import Decimal

from maf_outcome_economics.domain import (
    EconomicAssessment,
    GovernanceAction,
    GovernanceDecision,
    OutcomeContract,
    OutcomeStatus,
    PricingRecord,
    ReviewResult,
    Ticket,
    TriageResult,
    Variant,
    VerificationResult,
)
from maf_outcome_economics.persistence import OutcomeRepository, seed_fictional_tickets


def test_given_assessment_when_saved_then_it_can_be_loaded(tmp_path) -> None:
    # Arrange
    repository = OutcomeRepository(tmp_path / "outcomes.db")
    assessment = EconomicAssessment(
        outcome_name="Retention",
        incremental_units=Decimal("2"),
        gross_value=Decimal("20"),
        net_value=Decimal("15"),
        return_on_investment=Decimal("3"),
        verified=True,
    )

    # Act
    repository.save(assessment)

    # Assert
    assert repository.get("Retention") == assessment


def test_initialize_creates_requested_tables(tmp_path) -> None:
    repository = OutcomeRepository(tmp_path / "outcomes.db")

    assert {
        "outcome_contracts",
        "tickets",
        "runs",
        "telemetry_spans",
        "model_usage",
        "pricing",
        "verifications",
        "governance_decisions",
    } <= repository.table_names()


def test_given_legacy_runs_table_when_initialized_then_business_task_column_is_added(
    tmp_path,
) -> None:
    # Arrange
    database_path = tmp_path / "legacy.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """CREATE TABLE runs (
            id TEXT PRIMARY KEY, ticket_id TEXT NOT NULL, variant TEXT NOT NULL,
            trace_id TEXT, status TEXT NOT NULL, started_at TEXT NOT NULL,
            completed_at TEXT, triage_payload TEXT, review_payload TEXT)"""
        )

    # Act
    OutcomeRepository(database_path).initialize()

    # Assert
    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(runs)").fetchall()
        }
        indexes = {
            row[1] for row in connection.execute("PRAGMA index_list(runs)").fetchall()
        }
    assert "business_task_id" in columns
    assert "idx_runs_business_task_id" in indexes


def test_seed_inserts_twenty_fictional_labeled_tickets_idempotently(tmp_path) -> None:
    repository = OutcomeRepository(tmp_path / "outcomes.db")

    assert seed_fictional_tickets(repository) == 20
    assert seed_fictional_tickets(repository) == 20

    tickets = repository.list_tickets()
    assert len(tickets) == 20
    assert all(ticket.gold_category for ticket in tickets)
    assert all(ticket.gold_priority.startswith("P") for ticket in tickets)
    assert all(ticket.gold_resolver_group for ticket in tickets)


def test_contract_pricing_verification_and_governance_round_trip(tmp_path) -> None:
    repository = OutcomeRepository(tmp_path / "outcomes.db")
    contract = OutcomeContract(
        id="CONTRACT-001",
        name="Routing accuracy",
        description="Measure routing accuracy for fictional tickets.",
        variant=Variant.TREATMENT,
        status=OutcomeStatus.ACTIVE,
        metric_name="accuracy",
        target_value=Decimal("0.90"),
        unit="ratio",
        measurement_window_days=30,
        minimum_acceptance_rate=Decimal("0.90"),
        minimum_quality_score=Decimal("0.90"),
        minimum_critical_priority_recall=Decimal("1"),
        maximum_cost_per_accepted_outcome=Decimal("1"),
    )
    pricing = PricingRecord(
        id="PRICE-001",
        provider="illustrative-provider",
        model="illustrative-model",
        input_cost_per_million_tokens=Decimal("2.50"),
        output_cost_per_million_tokens=Decimal("10.00"),
    )
    verification = VerificationResult(
        id="VERIFY-001",
        contract_id=contract.id,
        passed=True,
        observed_value=Decimal("0.95"),
        evidence_count=20,
        reason="The illustrative target was met.",
    )
    decision = GovernanceDecision(
        id="DECISION-001",
        contract_id=contract.id,
        action=GovernanceAction.APPROVE,
        reason="Verification passed.",
        decided_by="governance-test",
    )

    repository.save_outcome_contract(contract)
    repository.save_pricing(pricing)
    repository.save_verification(verification)
    repository.save_governance_decision(decision)

    assert repository.get_outcome_contract(contract.id) == contract
    assert repository.get_pricing(pricing.id) == pricing
    assert repository.list_verifications(contract.id) == [verification]
    assert repository.list_governance_decisions(contract.id) == [decision]


def test_run_telemetry_and_usage_round_trip(tmp_path) -> None:
    repository = OutcomeRepository(tmp_path / "outcomes.db")
    timestamp = datetime(2026, 8, 19, tzinfo=UTC)
    ticket = Ticket(
        id="TKT-RUN",
        subject="Fictional run ticket",
        description="A ticket used to test run persistence.",
        gold_category="Application",
        gold_priority="P2",
        gold_resolver_group="Application Support",
        created_at=timestamp,
    )
    triage = TriageResult(
        run_id="RUN-001",
        ticket_id=ticket.id,
        category="Application",
        priority="P2",
        resolver_group="Application Support",
        confidence=0.98,
        rationale="The labels match the fictional application issue.",
        created_at=timestamp,
    )
    review = ReviewResult(
        run_id="RUN-001",
        ticket_id=ticket.id,
        approved=True,
        created_at=timestamp,
    )

    repository.save_ticket(ticket)
    repository.create_run("RUN-001", ticket.id, Variant.TREATMENT, timestamp)
    repository.complete_run("RUN-001", triage, review, timestamp)
    repository.save_telemetry_span(
        "SPAN-001",
        "RUN-001",
        "triage",
        "TRACE-001",
        timestamp,
        timestamp,
        {"agent": "triage"},
    )
    repository.save_model_usage(
        "USAGE-001",
        "RUN-001",
        "illustrative-provider",
        "illustrative-model",
        100,
        25,
        timestamp,
    )

    run = repository.get_run("RUN-001")
    assert run is not None
    assert run["triage"] == triage
    assert run["review"] == review
    assert repository.list_telemetry_spans("RUN-001")[0]["attributes"] == {
        "agent": "triage"
    }
    assert repository.list_model_usage("RUN-001")[0]["input_tokens"] == 100