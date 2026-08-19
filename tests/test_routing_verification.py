"""Tests for deterministic final routing verification."""

from decimal import Decimal

from maf_outcome_economics.domain import Ticket
from maf_outcome_economics.verification import verify_routing_outcome


def _ticket(*, gold_priority: str = "P3") -> Ticket:
    return Ticket(
        id="TKT-VERIFY",
        subject="Fictional verification ticket",
        description="A fictional ticket used only for deterministic tests.",
        gold_category="Application",
        gold_priority=gold_priority,
        gold_resolver_group="Business Applications",
    )


def _verify(
    ticket: Ticket,
    *,
    category: str = "Application",
    priority: str = "P3",
    resolver_group: str = "Business Applications",
):
    return verify_routing_outcome(
        verification_id="verification-test",
        contract_id="contract-test",
        run_id="run-test",
        ticket=ticket,
        final_category=category,
        final_priority=priority,
        final_resolver_group=resolver_group,
    )


def test_given_all_final_labels_match_when_verified_then_result_is_accepted() -> None:
    # Arrange
    ticket = _ticket()

    # Act
    result = _verify(ticket)

    # Assert
    assert result.category_correct is True
    assert result.priority_correct is True
    assert result.resolver_group_correct is True
    assert result.accepted is True
    assert result.correction_required is False
    assert result.quality_score == Decimal("1")
    assert result.critical_priority_recalled is None


def test_given_one_final_label_mismatches_when_verified_then_result_is_rejected() -> None:
    # Arrange
    ticket = _ticket()

    # Act
    result = _verify(ticket, category="Network")

    # Assert
    assert result.category_correct is False
    assert result.priority_correct is True
    assert result.resolver_group_correct is True
    assert result.accepted is False
    assert result.correction_required is True
    assert result.quality_score == Decimal(2) / Decimal(3)


def test_given_critical_gold_priority_is_under_prioritized_when_verified_then_recall_is_false(
) -> None:
    # Arrange
    ticket = _ticket(gold_priority="P1")

    # Act
    result = _verify(ticket, priority="P2")

    # Assert
    assert result.critical_priority_expected is True
    assert result.critical_priority_recalled is False
    assert result.priority_correct is False
    assert result.accepted is False
    assert result.correction_required is True