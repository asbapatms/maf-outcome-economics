"""Deterministic verification for final support-ticket routing labels."""

from decimal import Decimal

from maf_outcome_economics.domain import RoutingVerificationResult, Ticket


def verify_routing_outcome(
    *,
    verification_id: str,
    contract_id: str,
    run_id: str,
    ticket: Ticket,
    final_category: str,
    final_priority: str,
    final_resolver_group: str,
) -> RoutingVerificationResult:
    """Compare final predictions with ticket-owned gold labels.

    The caller may derive final predictions from triage and review, but only the
    ticket's gold labels determine correctness and acceptance.
    """
    category_correct = final_category == ticket.gold_category
    priority_correct = final_priority == ticket.gold_priority
    resolver_group_correct = final_resolver_group == ticket.gold_resolver_group
    correct_count = sum(
        (category_correct, priority_correct, resolver_group_correct)
    )
    quality_score = Decimal(correct_count) / Decimal(3)
    accepted = correct_count == 3
    critical_priority_expected = ticket.gold_priority == "P1"
    critical_priority_recalled = (
        priority_correct if critical_priority_expected else None
    )
    return RoutingVerificationResult(
        id=verification_id,
        contract_id=contract_id,
        run_id=run_id,
        passed=accepted,
        observed_value=quality_score,
        evidence_count=3,
        reason=f"{correct_count} of 3 final routing labels matched gold labels.",
        category_correct=category_correct,
        priority_correct=priority_correct,
        resolver_group_correct=resolver_group_correct,
        accepted=accepted,
        correction_required=not accepted,
        quality_score=quality_score,
        critical_priority_expected=critical_priority_expected,
        critical_priority_recalled=critical_priority_recalled,
    )