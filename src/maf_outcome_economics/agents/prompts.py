"""Prompt templates for support-ticket triage and review agents."""

from enum import StrEnum

from maf_outcome_economics.domain import ReviewResult, Ticket, TriageResult


class PromptProfile(StrEnum):
    """Instruction profile used for an agent invocation."""

    BASELINE = "baseline"
    OPTIMIZED = "optimized"


BASELINE_TRIAGE_TEMPLATE = """You are triaging a fictional enterprise support ticket.

Analyze the subject and description. Select a concise category, a priority from P1 through P4,
and the resolver group best equipped to own the issue. P1 means critical service or data impact;
P2 means major impact; P3 means limited impact; P4 means a routine request. Assign confidence from
0 to 1 and give a short rationale grounded only in the supplied ticket.

Return one JSON object matching the requested schema. Use run_id={run_id!r} and
ticket_id={ticket_id!r}. Do not include Markdown or commentary outside the JSON object.

Subject: {subject}
Description: {description}
"""

OPTIMIZED_TRIAGE_TEMPLATE = """Classify this fictional support ticket. Return concise JSON only,
matching the requested schema with run_id={run_id!r}, ticket_id={ticket_id!r}, priority P1-P4,
confidence 0-1, and no Markdown.
Subject: {subject}
Description: {description}
"""

BASELINE_REVIEW_TEMPLATE = """You are reviewing a fictional support-ticket triage decision.

Check whether the proposed category, priority, resolver group, confidence, and rationale are
consistent with the supplied ticket. Approve a sound decision. When it is not sound, set approved
to false and provide corrected fields and concise notes. Do not infer or expose any gold labels.

Return one JSON object matching the requested schema. Use run_id={run_id!r} and
ticket_id={ticket_id!r}. Do not include Markdown or commentary outside the JSON object.

Subject: {subject}
Description: {description}
Proposed triage JSON: {triage_json}
"""

OPTIMIZED_REVIEW_TEMPLATE = """Review this fictional ticket triage. Return concise JSON only,
matching the requested schema with run_id={run_id!r}, ticket_id={ticket_id!r}, and no Markdown.
Ticket subject: {subject}
Ticket description: {description}
Triage: {triage_json}
"""


def render_triage_prompt(
    ticket: Ticket,
    run_id: str,
    profile: PromptProfile,
) -> str:
    """Render a triage prompt without exposing evaluation labels."""
    template = (
        BASELINE_TRIAGE_TEMPLATE
        if profile is PromptProfile.BASELINE
        else OPTIMIZED_TRIAGE_TEMPLATE
    )
    return template.format(
        run_id=run_id,
        ticket_id=ticket.id,
        subject=ticket.subject,
        description=ticket.description,
    )


def render_review_prompt(
    ticket: Ticket,
    triage: TriageResult,
    profile: PromptProfile,
) -> str:
    """Render a review prompt without exposing evaluation labels."""
    template = (
        BASELINE_REVIEW_TEMPLATE
        if profile is PromptProfile.BASELINE
        else OPTIMIZED_REVIEW_TEMPLATE
    )
    return template.format(
        run_id=triage.run_id,
        ticket_id=ticket.id,
        subject=ticket.subject,
        description=ticket.description,
        triage_json=triage.model_dump_json(exclude={"created_at"}),
    )


def retry_prompt(prompt: str, response_type: type[TriageResult] | type[ReviewResult]) -> str:
    """Append one corrective instruction after malformed model output."""
    return (
        f"{prompt}\nYour previous response was malformed. Return exactly one valid JSON object "
        f"matching {response_type.__name__}; include no fences or explanatory text."
    )