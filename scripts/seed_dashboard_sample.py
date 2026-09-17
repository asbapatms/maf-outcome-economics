"""Seed a clean SQLite database with credible dashboard demonstration data."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from maf_outcome_economics.domain import PricingRecord, ReviewResult, Ticket, TriageResult
from maf_outcome_economics.persistence import OutcomeRepository, seed_fictional_tickets
from maf_outcome_economics.scenarios.ticket import WorkflowVariant, contract_id_for_variant
from maf_outcome_economics.scenarios.ticket.verification import verify_routing_outcome

EXIT_SUCCESS = 0

PROVIDER = "illustrative-provider"
MODEL = "illustrative-model"
BASELINE_TRIAGE_TOKENS = (260, 90)
BASELINE_REVIEW_TOKENS = (190, 60)
OPTIMIZED_TRIAGE_TOKENS = (120, 45)
OPTIMIZED_REVIEW_TOKENS = (150, 50)
OPTIMIZED_RETRY_TOKENS = (75, 25)


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Create credible sample data for the live governance dashboard.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/dashboard-sample.db"),
        help="SQLite database to create. Existing file is replaced.",
    )
    return parser


def main() -> int:
    """Seed the requested database and print the dashboard command."""
    args = create_parser().parse_args()
    database_path: Path = args.database
    if database_path.exists():
        database_path.unlink()
    repository = OutcomeRepository(database_path)
    tickets = seed_fictional_tickets(repository)
    repository.save_pricing(
        PricingRecord(
            id=f"pricing:{PROVIDER}:{MODEL}",
            provider=PROVIDER,
            model=MODEL,
            input_cost_per_million_tokens=Decimal("2.50"),
            output_cost_per_million_tokens=Decimal("10.00"),
        )
    )
    _seed_runs(repository, tickets)
    print(f"Seeded credible dashboard sample data at {database_path}")
    print("Run the dashboard with:")
    print(f"$env:MAF_DATABASE_PATH = '{database_path}'")
    print("uv run maf-outcome-economics dashboard")
    return EXIT_SUCCESS


def _seed_runs(repository: OutcomeRepository, ticket_count: int) -> None:
    tickets = repository.list_tickets()[:ticket_count]
    start = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
    for index, ticket in enumerate(tickets, start=1):
        _seed_baseline_run(repository, ticket, index, start + timedelta(minutes=index))
        _seed_optimized_run(
            repository,
            ticket,
            index,
            start + timedelta(minutes=ticket_count + index),
        )


def _seed_baseline_run(
    repository: OutcomeRepository,
    ticket: Ticket,
    index: int,
    timestamp: datetime,
) -> None:
    run_id = f"sample-baseline-{index:03d}"
    triage_correct = index not in {5, 12}
    triage = _triage(
        run_id,
        ticket,
        correct=triage_correct,
        confidence=0.72 if not triage_correct else 0.84,
    )
    review = (
        _correcting_review(run_id, ticket)
        if not triage_correct
        else _approving_review(run_id, ticket)
    )
    _persist_run(
        repository,
        ticket,
        WorkflowVariant.BASELINE,
        run_id,
        timestamp,
        triage,
        review,
    )
    _save_usage(repository, run_id, "triage", "TriageAgent", *BASELINE_TRIAGE_TOKENS, timestamp)
    _save_usage(
        repository,
        run_id,
        "review",
        "ReviewAgent",
        *BASELINE_REVIEW_TOKENS,
        timestamp + timedelta(seconds=5),
    )


def _seed_optimized_run(
    repository: OutcomeRepository,
    ticket: Ticket,
    index: int,
    timestamp: datetime,
) -> None:
    run_id = f"sample-optimized-{index:03d}"
    review_kind = _optimized_review_kind(index)
    triage = _triage(
        run_id,
        ticket,
        correct=review_kind != "useful",
        confidence=0.91 if review_kind is None else 0.76,
    )
    review = None
    if review_kind == "useful":
        review = _correcting_review(run_id, ticket)
    elif review_kind == "non_contributing":
        review = _approving_review(run_id, ticket)
    _persist_run(
        repository,
        ticket,
        WorkflowVariant.OPTIMIZED,
        run_id,
        timestamp,
        triage,
        review,
    )
    _save_usage(repository, run_id, "triage", "TriageAgent", *OPTIMIZED_TRIAGE_TOKENS, timestamp)
    if review is not None:
        _save_usage(
            repository,
            run_id,
            "review",
            "ReviewAgent",
            *OPTIMIZED_REVIEW_TOKENS,
            timestamp + timedelta(seconds=5),
        )
    if index in {7, 16}:
        _save_usage(
            repository,
            run_id,
            "triage",
            "TriageAgent",
            *OPTIMIZED_RETRY_TOKENS,
            timestamp + timedelta(seconds=10),
            suffix="retry",
        )


def _optimized_review_kind(index: int) -> str | None:
    if index in {3, 9, 18}:
        return "useful"
    if index in {2, 13, 17}:
        return "non_contributing"
    return None


def _persist_run(
    repository: OutcomeRepository,
    ticket: Ticket,
    variant: WorkflowVariant,
    run_id: str,
    timestamp: datetime,
    triage: TriageResult,
    review: ReviewResult | None,
) -> None:
    final_category, final_priority, final_resolver_group = _effective_labels(triage, review)
    repository.create_run(
        run_id,
        ticket.id,
        variant,
        started_at=timestamp,
        trace_id=f"{variant.value[:4]}{run_id[-3:]}".ljust(32, "0"),
        business_task_id=f"{variant.value}:{ticket.id}",
    )
    verification = verify_routing_outcome(
        verification_id=f"verification-{run_id}",
        contract_id=contract_id_for_variant(variant),
        run_id=run_id,
        ticket=ticket,
        final_category=final_category,
        final_priority=final_priority,
        final_resolver_group=final_resolver_group,
    )
    repository.save_verification(verification)
    repository.complete_run(run_id, triage, review, completed_at=timestamp + timedelta(seconds=20))


def _triage(
    run_id: str,
    ticket: Ticket,
    *,
    correct: bool,
    confidence: float,
) -> TriageResult:
    return TriageResult(
        run_id=run_id,
        ticket_id=ticket.id,
        category=ticket.gold_category if correct else "Application",
        priority=ticket.gold_priority if correct else "P3",
        resolver_group=ticket.gold_resolver_group if correct else "Business Applications",
        confidence=confidence,
        rationale="Credible dashboard sample routing decision.",
    )


def _approving_review(run_id: str, ticket: Ticket) -> ReviewResult:
    return ReviewResult(
        run_id=run_id,
        ticket_id=ticket.id,
        approved=True,
        notes="Reviewer confirmed the routing decision.",
    )


def _correcting_review(run_id: str, ticket: Ticket) -> ReviewResult:
    return ReviewResult(
        run_id=run_id,
        ticket_id=ticket.id,
        approved=False,
        corrected_category=ticket.gold_category,
        corrected_priority=ticket.gold_priority,
        corrected_resolver_group=ticket.gold_resolver_group,
        notes="Reviewer corrected a low-confidence routing decision.",
    )


def _effective_labels(
    triage: TriageResult,
    review: ReviewResult | None,
) -> tuple[str, str, str]:
    if review is None or review.approved:
        return triage.category, triage.priority, triage.resolver_group
    return (
        review.corrected_category or triage.category,
        review.corrected_priority or triage.priority,
        review.corrected_resolver_group or triage.resolver_group,
    )


def _save_usage(
    repository: OutcomeRepository,
    run_id: str,
    agent_id: str,
    agent_name: str,
    input_tokens: int,
    output_tokens: int,
    timestamp: datetime,
    *,
    suffix: str = "main",
) -> None:
    repository.save_rehearsal_model_call(
        usage_id=f"usage-{run_id}-{agent_id}-{suffix}",
        run_id=run_id,
        provider=PROVIDER,
        model=MODEL,
        agent_id=agent_id,
        agent_name=agent_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        recorded_at=timestamp,
    )


if __name__ == "__main__":
    sys.exit(main())
