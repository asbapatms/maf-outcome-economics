"""Fictional seed data for local development and demonstrations."""

from maf_outcome_economics.domain import Ticket

from .sqlite_repository import OutcomeRepository

FICTIONAL_TICKETS = [
    Ticket(
        id="TKT-001",
        subject="Account locked after password reset",
        description="A fictional user cannot sign in after completing a password reset.",
        gold_category="Identity and access",
        gold_priority="P2",
        gold_resolver_group="Identity Operations",
    ),
    Ticket(
        id="TKT-002",
        subject="Duplicate invoice for July",
        description="A fictional customer reports two invoices for the same subscription period.",
        gold_category="Billing",
        gold_priority="P3",
        gold_resolver_group="Billing Support",
    ),
    Ticket(
        id="TKT-003",
        subject="Regional API requests timing out",
        description="A fictional integration sees sustained timeouts in one service region.",
        gold_category="Service availability",
        gold_priority="P1",
        gold_resolver_group="Cloud Reliability",
    ),
    Ticket(
        id="TKT-004",
        subject="Laptop battery no longer charging",
        description="A fictional employee laptop remains at zero percent while connected to power.",
        gold_category="Hardware",
        gold_priority="P3",
        gold_resolver_group="Endpoint Support",
    ),
    Ticket(
        id="TKT-005",
        subject="Cannot export monthly analytics",
        description="A fictional analyst receives an error while exporting a monthly report.",
        gold_category="Application",
        gold_priority="P2",
        gold_resolver_group="Business Applications",
    ),
    Ticket(
        id="TKT-006",
        subject="VPN disconnects every ten minutes",
        description="A fictional remote worker experiences repeated VPN disconnections.",
        gold_category="Network",
        gold_priority="P2",
        gold_resolver_group="Network Operations",
    ),
    Ticket(
        id="TKT-007",
        subject="Refund status is not visible",
        description="A fictional customer cannot see the status of an approved refund.",
        gold_category="Billing",
        gold_priority="P4",
        gold_resolver_group="Billing Support",
    ),
    Ticket(
        id="TKT-008",
        subject="Shared mailbox permissions missing",
        description="A fictional team member cannot open a newly assigned shared mailbox.",
        gold_category="Identity and access",
        gold_priority="P3",
        gold_resolver_group="Messaging Support",
    ),
    Ticket(
        id="TKT-009",
        subject="Production database storage alert",
        description="A fictional production database has exceeded ninety-five percent capacity.",
        gold_category="Database",
        gold_priority="P1",
        gold_resolver_group="Database Reliability",
    ),
    Ticket(
        id="TKT-010",
        subject="Mobile app crashes during upload",
        description="A fictional mobile app closes when a user uploads a large attachment.",
        gold_category="Application",
        gold_priority="P2",
        gold_resolver_group="Mobile Engineering",
    ),
    Ticket(
        id="TKT-011",
        subject="Office printer produces blank pages",
        description="A fictional office printer accepts jobs but outputs blank sheets.",
        gold_category="Hardware",
        gold_priority="P4",
        gold_resolver_group="Workplace Technology",
    ),
    Ticket(
        id="TKT-012",
        subject="DNS lookup fails for internal site",
        description="A fictional internal hostname cannot be resolved from one office.",
        gold_category="Network",
        gold_priority="P2",
        gold_resolver_group="Network Operations",
    ),
    Ticket(
        id="TKT-013",
        subject="Audit logs delayed by six hours",
        description="A fictional compliance workspace receives audit records several hours late.",
        gold_category="Observability",
        gold_priority="P2",
        gold_resolver_group="Telemetry Platform",
    ),
    Ticket(
        id="TKT-014",
        subject="Subscription cancellation did not apply",
        description="A fictional cancelled subscription renewed unexpectedly.",
        gold_category="Billing",
        gold_priority="P2",
        gold_resolver_group="Billing Support",
    ),
    Ticket(
        id="TKT-015",
        subject="Security key enrollment rejected",
        description="A fictional user cannot enroll an approved hardware security key.",
        gold_category="Identity and access",
        gold_priority="P2",
        gold_resolver_group="Identity Operations",
    ),
    Ticket(
        id="TKT-016",
        subject="Search index stopped updating",
        description="A fictional product catalog search index contains only yesterday's records.",
        gold_category="Data pipeline",
        gold_priority="P1",
        gold_resolver_group="Data Platform",
    ),
    Ticket(
        id="TKT-017",
        subject="Video calls have distorted audio",
        description="A fictional branch office reports distorted audio in all video calls.",
        gold_category="Collaboration",
        gold_priority="P3",
        gold_resolver_group="Unified Communications",
    ),
    Ticket(
        id="TKT-018",
        subject="Backup job missed recovery objective",
        description="A fictional nightly backup completed outside its recovery-point objective.",
        gold_category="Data protection",
        gold_priority="P1",
        gold_resolver_group="Backup Operations",
    ),
    Ticket(
        id="TKT-019",
        subject="New employee software request pending",
        description="A fictional software request has remained pending since employee onboarding.",
        gold_category="Service request",
        gold_priority="P4",
        gold_resolver_group="Service Desk",
    ),
    Ticket(
        id="TKT-020",
        subject="Dashboard uses stale exchange rates",
        description="A fictional finance dashboard displays exchange rates from the prior week.",
        gold_category="Data quality",
        gold_priority="P3",
        gold_resolver_group="Analytics Engineering",
    ),
]


def seed_fictional_tickets(repository: OutcomeRepository) -> int:
    """Insert or replace the fictional support-ticket dataset."""
    for ticket in FICTIONAL_TICKETS:
        repository.save_ticket(ticket)
    return len(FICTIONAL_TICKETS)