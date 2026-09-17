"""Streamlit dashboard that renders live governance evidence from SQLite.

Run with:

    uv run streamlit run src/maf_outcome_economics/dashboard/app.py

or via the CLI wrapper:

    uv run maf-outcome-economics dashboard

The dashboard re-runs the same generic analysis pipeline used by the console
and HTML reports (`TicketEconomicsAnalyzer`) directly against the configured
SQLite database, so it always reflects the latest persisted evidence. It adds
no new decision logic; it only visualizes the existing `GenericGovernanceEngine`
decision, gate results, process comparison, and token efficiency evidence so a
reviewer can watch a demo run without waiting for a static HTML report.
"""

from __future__ import annotations

import asyncio
import time
from decimal import Decimal
from html import escape
from typing import Any

import streamlit as st

from maf_outcome_economics.config import Settings
from maf_outcome_economics.core import (
    GateStatus,
    GenericGovernanceAction,
    ReviewTokenAttribution,
)
from maf_outcome_economics.persistence import OutcomeRepository
from maf_outcome_economics.scenarios.ticket import (
    TicketEconomicsAnalyzer,
    TicketGenericAnalysis,
)

_ACTION_STYLE: dict[GenericGovernanceAction, tuple[str, str]] = {
    GenericGovernanceAction.SCALE: ("🟢", "SCALE"),
    GenericGovernanceAction.MONITOR: ("🔵", "MONITOR"),
    GenericGovernanceAction.OPTIMIZE: ("🟡", "OPTIMIZE"),
    GenericGovernanceAction.STOP: ("🔴", "STOP"),
    GenericGovernanceAction.INSUFFICIENT_EVIDENCE: ("⚪", "INSUFFICIENT EVIDENCE"),
}

_GATE_STYLE: dict[GateStatus, str] = {
    GateStatus.PASS: "✅ pass",
    GateStatus.FAIL: "❌ fail",
    GateStatus.UNKNOWN: "❔ unknown",
}

_GATE_CHIP_STYLE: dict[GateStatus, tuple[str, str, str]] = {
    GateStatus.PASS: ("✓", "#DCFCE7", "#166534"),
    GateStatus.FAIL: ("!", "#FEE2E2", "#991B1B"),
    GateStatus.UNKNOWN: ("?", "#F1F5F9", "#475569"),
}

_COLORS = {
    "navy": "#172554",
    "blue": "#2563EB",
    "cyan": "#0891B2",
    "green": "#16A34A",
    "amber": "#D97706",
    "red": "#DC2626",
    "purple": "#7C3AED",
    "slate": "#64748B",
}

_ACTION_COLORS: dict[GenericGovernanceAction, tuple[str, str]] = {
    GenericGovernanceAction.SCALE: ("#DCFCE7", "#166534"),
    GenericGovernanceAction.MONITOR: ("#DBEAFE", "#1E40AF"),
    GenericGovernanceAction.OPTIMIZE: ("#FEF3C7", "#92400E"),
    GenericGovernanceAction.STOP: ("#FEE2E2", "#991B1B"),
    GenericGovernanceAction.INSUFFICIENT_EVIDENCE: ("#F1F5F9", "#475569"),
}


def _apply_dashboard_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at 85% 5%, rgba(37, 99, 235, 0.10), transparent 24rem),
                linear-gradient(180deg, #f8fafc 0%, #ffffff 28rem);
        }
        .block-container {
            max-width: 1500px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        div[data-testid="stVerticalBlock"] {
            gap: 0.7rem;
        }
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid #e2e8f0;
            border-top: 4px solid #2563eb;
            border-radius: 10px;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
            min-height: 104px;
            padding: 0.7rem 0.85rem;
        }
        [data-testid="stMetricLabel"] {
            color: #475569;
            font-size: 0.95rem;
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            color: #172554;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
        }
        [data-testid="stVegaLiteChart"] {
            margin-top: 0.375rem;
        }
        h1, h2, h3 {
            color: #172554;
            letter-spacing: -0.02em;
        }
        .executive-kicker {
            color: #2563eb;
            font-size: 0.6rem;
            font-weight: 800;
            letter-spacing: 0.13em;
            margin-bottom: 0.05rem;
            text-transform: uppercase;
        }
        .executive-title {
            color: #172554;
            font-size: clamp(1.55rem, 2.4vw, 2rem);
            font-weight: 800;
            letter-spacing: -0.045em;
            line-height: 1.1;
            margin-bottom: 0.2rem;
        }
        .screen-section-heading {
            align-items: center;
            display: flex;
            gap: 0.7rem;
            margin: 0.2rem 0 0.45rem;
        }
        .screen-section-heading.second {
            border-top: 2px solid #cbd5e1;
            margin-top: 9rem;
            padding-top: 2rem;
            scroll-margin-top: 1rem;
        }
        .section-end-spacer {
            height: 10rem;
        }
        .screen-section-number {
            background: #2563eb;
            border-radius: 999px;
            color: white;
            flex: 0 0 auto;
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            padding: 0.32rem 0.6rem;
            text-transform: uppercase;
        }
        .screen-section-copy {
            min-width: 0;
        }
        .screen-section-title {
            color: #172554;
            font-size: 1.25rem;
            font-weight: 800;
            line-height: 1.2;
        }
        .screen-section-subtitle {
            color: #475569;
            font-size: 0.9rem;
            line-height: 1.35;
            margin-top: 0.1rem;
        }
        .decision-banner {
            border-radius: 10px;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
            margin: 0.2rem 0 0.35rem;
            padding: 0.7rem 0.9rem;
        }
        .decision-label {
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            opacity: 0.8;
            text-transform: uppercase;
        }
        .decision-value {
            font-size: 1.55rem;
            font-weight: 800;
            margin-top: 0.05rem;
        }
        .chart-title {
            color: #172554;
            font-size: 1.05rem;
            font-weight: 750;
            line-height: 1.1;
            margin-bottom: 0.15rem;
        }
        .chart-caption {
            background: #f8fafc;
            border-left: 3px solid #2563eb;
            border-radius: 5px;
            color: #475569;
            font-size: 0.88rem;
            line-height: 1.35;
            margin-top: 0.15rem;
            min-height: 58px;
            padding: 0.55rem 0.65rem;
        }
        .chart-caption b {
            color: #172554;
        }
        .gate-heading {
            color: #475569;
            font-size: 0.85rem;
            font-weight: 750;
            margin: 0.8rem 0 0.35rem;
            text-transform: uppercase;
        }
        .governance-flow {
            display: block;
            height: auto;
            margin-bottom: 0;
            max-height: 168px;
            width: 100%;
        }
        .waste-card {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid #cbd5e1;
            border-left: 4px solid #7c3aed;
            border-radius: 12px;
            box-shadow: 0 12px 30px rgba(76, 29, 149, 0.08);
            margin: 0.35rem 0 0.3rem;
            padding: 1rem 1.1rem;
        }
        .waste-card-title {
            color: #172554;
            font-size: 1.3rem;
            font-weight: 800;
            margin-bottom: 0.65rem;
        }
        .waste-insights {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-bottom: 0.8rem;
        }
        .waste-insight {
            background: #f1f5f9;
            border-radius: 999px;
            color: #475569;
            font-size: 0.9rem;
            padding: 0.35rem 0.65rem;
        }
        .waste-insight strong {
            color: #4c1d95;
        }
        .waste-story-grid {
            display: grid;
            gap: 0.75rem;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            margin-bottom: 0.9rem;
        }
        .waste-story {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 9px;
            padding: 0.7rem 0.8rem;
        }
        .waste-story-value {
            color: #4c1d95;
            font-size: 1.65rem;
            font-weight: 850;
            line-height: 1;
        }
        .waste-story-label {
            color: #172554;
            font-size: 0.95rem;
            font-weight: 750;
            margin-left: 0.35rem;
        }
        .waste-story-detail {
            color: #475569;
            font-size: 0.82rem;
            line-height: 1.35;
            margin-top: 0.35rem;
        }
        .waste-row {
            align-items: center;
            display: grid;
            gap: 0.75rem;
            grid-template-columns: 6.5rem minmax(10rem, 1fr) 7rem;
            margin: 0.55rem 0;
        }
        .waste-row-label {
            color: #334155;
            font-size: 0.95rem;
            font-weight: 700;
        }
        .waste-track {
            background: #e2e8f0;
            border-radius: 999px;
            display: flex;
            height: 28px;
            overflow: hidden;
        }
        .waste-segment {
            height: 100%;
        }
        .waste-total {
            color: #475569;
            font-size: 0.9rem;
            text-align: right;
        }
        .waste-legend {
            color: #64748b;
            display: flex;
            flex-wrap: wrap;
            font-size: 0.82rem;
            gap: 1rem;
            margin-top: 0.65rem;
        }
        .waste-swatch {
            border-radius: 2px;
            display: inline-block;
            height: 11px;
            margin-right: 0.3rem;
            width: 11px;
        }
        .waste-caption {
            color: #475569;
            font-size: 0.88rem;
            line-height: 1.45;
            margin-top: 0.7rem;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            font-size: 1.8rem;
        }
        @media (max-width: 900px) {
            .screen-section-heading {
                align-items: flex-start;
            }
            .waste-story-grid {
                grid-template-columns: 1fr;
            }
            .waste-row {
                grid-template-columns: 5.5rem minmax(7rem, 1fr) 5.8rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _decimal_text(value: Decimal | None, *, suffix: str = "") -> str:
    """Render an optional `Decimal` for display, matching the console CLI style.

    Values derived from division (e.g. tokens avoided, review ratios) can carry
    dozens of repeating decimal digits; quantize to 4 decimal places before
    trimming trailing zeros so the dashboard stays readable.
    """
    if value is None:
        return "—"
    exponent = value.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -4:
        value = value.quantize(Decimal("0.0001"))
    return f"{value.normalize():f}{suffix}"


def _currency_text(value: Decimal | None, currency: str | None) -> str:
    if value is None:
        return "—"
    return f"{value.quantize(Decimal('0.0001'))} {currency or ''}".strip()


def _percent_text(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return f"{value:.1%}"


def _reduction_text(control: Decimal | int | None, treatment: Decimal | int | None) -> str:
    if control is None or treatment is None or control == 0:
        return "comparison unavailable"
    reduction = (Decimal(control) - Decimal(treatment)) / Decimal(control)
    return f"{reduction:.0%} lower" if reduction >= 0 else f"{abs(reduction):.0%} higher"


def _load_settings() -> Settings:
    return Settings.from_env()


def _run_analysis(settings: Settings) -> TicketGenericAnalysis:
    """Load the configured SQLite database and evaluate the ticket scenario."""
    repository = OutcomeRepository(settings.database_path)
    repository.initialize()
    return asyncio.run(TicketEconomicsAnalyzer(repository).analyze())


def _recent_runs(settings: Settings, limit: int = 15) -> list[dict[str, Any]]:
    repository = OutcomeRepository(settings.database_path)
    repository.initialize()
    runs = repository.list_runs()
    return sorted(runs, key=lambda row: str(row.get("started_at") or ""), reverse=True)[
        :limit
    ]


def _render_header() -> None:
    st.markdown(
        """
        <div class="executive-kicker">AI governance · outcome economics</div>
        <div class="executive-title">Executive Decision Dashboard</div>
        """,
        unsafe_allow_html=True,
    )


def _render_action_banner(analysis: TicketGenericAnalysis) -> None:
    emoji, label = _ACTION_STYLE[analysis.decision.action]
    background, foreground = _ACTION_COLORS[analysis.decision.action]
    st.markdown(
        (
            f'<div class="decision-banner" style="background:{background};'
            f'color:{foreground}; border-left:6px solid {foreground}">'
            '<div class="decision-label">Governance recommendation</div>'
            f'<div class="decision-value">{emoji} {escape(label)}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def _render_screen_section(
    number: int,
    title: str,
    subtitle: str,
    *,
    second: bool = False,
) -> None:
    modifier = " second" if second else ""
    st.markdown(
        (
            f'<div class="screen-section-heading{modifier}">'
            f'<span class="screen-section-number">Section {number}</span>'
            '<div class="screen-section-copy">'
            f'<div class="screen-section-title">{escape(title)}</div>'
            f'<div class="screen-section-subtitle">{escape(subtitle)}</div>'
            "</div></div>"
        ),
        unsafe_allow_html=True,
    )


def _render_kpis(analysis: TicketGenericAnalysis) -> None:
    comparison = analysis.comparison
    token_comparison = analysis.token_comparison
    columns = st.columns(4)
    columns[0].metric(
        "Verified outcomes",
        comparison.treatment.verified_outcomes,
        help=(
            "Treatment runs that passed independent outcome verification. "
            "This is the delivered-value denominator for cost and token efficiency."
        ),
    )
    columns[1].metric(
        "Cost / verified outcome",
        _currency_text(
            comparison.treatment.cost_per_verified_outcome, comparison.currency
        ),
        help=(
            "Treatment model cost divided by independently verified outcomes. "
            "Lower values indicate better unit economics."
        ),
    )
    columns[2].metric(
        "Net savings vs. control",
        _currency_text(comparison.net_savings, comparison.currency),
        help=(
            "Estimated cost avoided by treatment compared with equivalent control "
            "work. Positive values support the economic case for optimization."
        ),
    )
    columns[3].metric(
        "Token efficiency gain",
        (
            "—"
            if token_comparison.efficiency_improvement is None
            else f"{token_comparison.efficiency_improvement:.1%}"
        ),
        help=(
            "Reduction in tokens required per verified outcome versus control. "
            "Higher positive percentages mean more productive AI execution."
        ),
    )


def _render_compact_bar_chart(
    values: list[dict[str, str | float | int]],
    *,
    value_field: str,
    axis_title: str,
    colors: tuple[str, str],
    value_format: str,
) -> None:
    if not values:
        st.info("Evidence is not available yet.")
        return
    st.vega_lite_chart(
        {
            "data": {"values": values},
            "layer": [
                {
                    "mark": {
                        "type": "bar",
                        "cornerRadiusTopLeft": 5,
                        "cornerRadiusTopRight": 5,
                    }
                },
                {
                    "mark": {
                        "type": "text",
                        "dy": -7,
                        "fontSize": 12,
                        "fontWeight": "bold",
                        "color": _COLORS["navy"],
                    },
                    "encoding": {
                        "text": {
                            "field": value_field,
                            "type": "quantitative",
                            "format": value_format,
                        }
                    },
                },
            ],
            "encoding": {
                "x": {
                    "field": "Variant",
                    "type": "nominal",
                    "axis": {"labelAngle": 0, "title": None},
                },
                "y": {
                    "field": value_field,
                    "type": "quantitative",
                    "title": axis_title,
                    "axis": {"tickCount": 4},
                },
                "color": {
                    "field": "Variant",
                    "type": "nominal",
                    "scale": {"range": list(colors)},
                    "legend": None,
                },
                "tooltip": [
                    {"field": "Variant", "type": "nominal"},
                    {
                        "field": value_field,
                        "type": "quantitative",
                        "format": value_format,
                    },
                ],
            },
            "height": 190,
            "config": {
                "axis": {
                    "labelFontSize": 14,
                    "titleFontSize": 14,
                    "titleFontWeight": 600,
                },
                "view": {"stroke": None},
            },
        },
        width="stretch",
    )


def _render_governance_flow(analysis: TicketGenericAnalysis) -> None:
    results = {result.gate.value: result for result in analysis.decision.gate_results}
    passed = sum(result.status is GateStatus.PASS for result in results.values())
    groups = [
        ("Evidence", ("evidence",), ("Evidence",)),
        ("Trust", ("quality", "safety", "compliance"), ("Quality · Safety", "Compliance")),
        (
            "Value",
            ("business_outcome", "unit_cost", "net_value"),
            ("Business outcome", "Unit cost · Net value"),
        ),
        (
            "Tokens",
            ("token_budget", "token_efficiency"),
            ("Budget · Efficiency",),
        ),
        (
            "Waste",
            ("review_waste", "retry_waste"),
            ("Review · Retry",),
        ),
    ]

    treatment_summary = analysis.comparison.treatment
    unit_cost = treatment_summary.cost_per_verified_outcome
    net_value = analysis.comparison.net_savings
    efficiency = analysis.token_comparison.efficiency_improvement
    tokens_per_outcome = analysis.token_comparison.treatment.tokens_per_verified_outcome
    no_change_ratio = analysis.treatment_review_attribution.non_contributing_review_ratio
    total_review_tokens = analysis.treatment_review_attribution.total_review_tokens
    metric_captions: dict[str, str | None] = {
        "Evidence": (
            f"{treatment_summary.total_work_units} evaluated · "
            f"{treatment_summary.verified_outcomes} passed"
        ),
        "Value": (
            f"${unit_cost:.4f}/out · +${net_value:.4f} net"
            if unit_cost is not None and net_value is not None
            else None
        ),
        "Tokens": (
            f"{efficiency:.0%} eff · {tokens_per_outcome:.0f} tok/out"
            if efficiency is not None and tokens_per_outcome is not None
            else None
        ),
        "Waste": (
            f"{no_change_ratio:.0%} no-change · {total_review_tokens:,} tok"
            if no_change_ratio is not None
            else None
        ),
    }

    cards = []
    for index, (title, gate_names, lines) in enumerate(groups):
        group_results = [results[name] for name in gate_names if name in results]
        statuses = {result.status for result in group_results}
        status = (
            GateStatus.FAIL
            if GateStatus.FAIL in statuses
            else GateStatus.UNKNOWN
            if GateStatus.UNKNOWN in statuses
            else GateStatus.PASS
        )
        icon, background, foreground = _GATE_CHIP_STYLE[status]
        tooltip = escape(
            " | ".join(
                f"{result.gate.value.replace('_', ' ').title()}: "
                f"{result.status.value.upper()} — {result.reason}"
                for result in group_results
            ),
            quote=True,
        )
        pass_count = sum(1 for r in group_results if r.status is GateStatus.PASS)
        fail_count = sum(1 for r in group_results if r.status is GateStatus.FAIL)
        total = len(group_results)
        metric_caption = metric_captions.get(title)
        if fail_count:
            caption = f"{fail_count} check{'s' if fail_count != 1 else ''} failed"
        elif pass_count < total:
            caption = f"{pass_count}/{total} passed · pending"
        elif metric_caption:
            caption = metric_caption
        elif total > 1:
            caption = f"All {total} checks passed"
        else:
            caption = "Verified"
        x = index * 180
        subtitles = "".join(
            f'<text x="{x + 14}" y="{57 + line_index * 17}" '
            'font-size="12" fill="#475569">'
            f"{escape(line)}</text>"
            for line_index, line in enumerate(lines)
        )
        cards.append(
            f'<g class="governance-stage"><title>{tooltip}</title>'
            f'<rect x="{x}" y="5" width="160" height="88" rx="10" '
            f'fill="{background}" stroke="{foreground}" stroke-width="1.5"/>'
            f'<circle cx="{x + 17}" cy="25" r="7" fill="{foreground}"/>'
            f'<text x="{x + 17}" y="29" text-anchor="middle" font-size="12" '
            f'font-weight="bold" fill="white">{icon}</text>'
            f'<text x="{x + 30}" y="30" font-size="15" font-weight="bold" '
            f'fill="{foreground}">{escape(title)}</text>{subtitles}'
            f'<text x="{x + 80}" y="107" text-anchor="middle" font-size="11" '
            f'font-weight="600" fill="{foreground}">{escape(caption)}</text></g>'
        )
        if index < len(groups) - 1:
            cards.append(
                f'<path d="M {x + 163} 49 L {x + 176} 49" stroke="#94a3b8" '
                'stroke-width="2"/><path d="M '
                f'{x + 172} 45 L {x + 176} 49 L {x + 172} 53" '
                'fill="none" stroke="#94a3b8" stroke-width="2"/>'
            )

    emoji, decision_label = _ACTION_STYLE[analysis.decision.action]
    decision_background, decision_foreground = _ACTION_COLORS[analysis.decision.action]
    cards.append(
        f'<path d="M 883 49 L 896 49" stroke="#94a3b8" stroke-width="2"/>'
        f'<path d="M 892 45 L 896 49 L 892 53" fill="none" stroke="#94a3b8" '
        f'stroke-width="2"/><g><title>Final governance recommendation</title>'
        f'<rect x="900" y="5" width="160" height="88" rx="10" '
        f'fill="{decision_background}" stroke="{decision_foreground}" stroke-width="2"/>'
        f'<text x="980" y="38" text-anchor="middle" font-size="14" font-weight="bold" '
        f'fill="{decision_foreground}">{emoji} DECISION</text>'
        f'<text x="980" y="66" text-anchor="middle" font-size="16" font-weight="bold" '
        f'fill="{decision_foreground}">{escape(decision_label)}</text>'
        f'<text x="980" y="107" text-anchor="middle" font-size="11" font-weight="600" '
        f'fill="{decision_foreground}">{passed}/{len(results)} gates passed</text></g>'
    )
    st.markdown(
        '<div class="gate-heading">Sample governance flow · '
        f"{passed}/{len(results)} gates passed · hover each stage for full detail</div>"
        '<svg class="governance-flow" viewBox="0 0 1065 122" '
        'role="img" aria-label="Governance gates leading to the final recommendation">'
        f'{"".join(cards)}</svg>',
        unsafe_allow_html=True,
    )


def _render_compact_review_attribution(analysis: TicketGenericAnalysis) -> None:
    control = analysis.control_review_attribution
    treatment = analysis.treatment_review_attribution
    maximum_tokens = max(control.total_review_tokens, treatment.total_review_tokens, 1)

    def segments(attribution: ReviewTokenAttribution) -> str:
        values = [
            (
                "Useful",
                attribution.useful_review_tokens,
                attribution.useful_corrections,
                _COLORS["green"],
            ),
            (
                "Harmful",
                attribution.harmful_review_tokens,
                attribution.harmful_corrections,
                _COLORS["red"],
            ),
            (
                "No measured change",
                attribution.non_contributing_review_tokens,
                attribution.non_contributing_reviews,
                _COLORS["amber"],
            ),
            (
                "Inconclusive",
                attribution.inconclusive_review_tokens,
                attribution.inconclusive_reviews,
                _COLORS["slate"],
            ),
        ]
        return "".join(
            f'<span class="waste-segment" style="width:{tokens / maximum_tokens:.2%};'
            f'background:{color}" title="{label}: {reviews} review(s), {tokens:,} tokens">'
            "</span>"
            for label, tokens, reviews, color in values
            if tokens
        )

    total_reduction = (
        Decimal(1)
        - Decimal(treatment.total_review_tokens) / Decimal(control.total_review_tokens)
        if control.total_review_tokens
        else Decimal(0)
    )
    no_change_reduction = (
        Decimal(1)
        - Decimal(treatment.non_contributing_review_tokens)
        / Decimal(control.non_contributing_review_tokens)
        if control.non_contributing_review_tokens
        else Decimal(0)
    )
    useful_retention = (
        Decimal(treatment.useful_corrections) / Decimal(control.useful_corrections)
        if control.useful_corrections
        else Decimal(1)
    )
    removed_no_change_reviews = (
        control.non_contributing_reviews - treatment.non_contributing_reviews
    )
    st.markdown(
        (
            '<div class="waste-card">'
            '<div class="waste-card-title">Novelty and waste reduction · '
            "assurance retained, unnecessary review removed</div>"
            '<div class="waste-insights">'
            f'<span class="waste-insight"><strong>{useful_retention:.0%}</strong> '
            "useful corrections retained</span>"
            f'<span class="waste-insight"><strong>{no_change_reduction:.0%}</strong> '
            "no-change review tokens removed</span>"
            f'<span class="waste-insight"><strong>{total_reduction:.0%}</strong> '
            "total review tokens reduced</span></div>"
            '<div class="waste-story-grid">'
            '<div class="waste-story">'
            f'<span class="waste-story-value">{treatment.useful_corrections}</span>'
            '<span class="waste-story-label">useful corrections preserved</span>'
            '<div class="waste-story-detail">Treatment kept review where it changed '
            "the measured outcome, preserving assurance for work that needed it.</div>"
            "</div>"
            '<div class="waste-story">'
            f'<span class="waste-story-value">{removed_no_change_reviews}</span>'
            '<span class="waste-story-label">no-change reviews eliminated</span>'
            '<div class="waste-story-detail">Review calls that added consumption '
            "without changing the verified result were removed.</div>"
            "</div></div>"
            '<div class="waste-row"><span class="waste-row-label">Control</span>'
            f'<div class="waste-track">{segments(control)}</div>'
            f'<span class="waste-total">{control.total_review_tokens:,} tokens</span></div>'
            '<div class="waste-row"><span class="waste-row-label">Treatment</span>'
            f'<div class="waste-track">{segments(treatment)}</div>'
            f'<span class="waste-total">{treatment.total_review_tokens:,} tokens</span></div>'
            '<div class="waste-legend">'
            f'<span><i class="waste-swatch" style="background:{_COLORS["green"]}"></i>'
            "Useful correction</span>"
            f'<span><i class="waste-swatch" style="background:{_COLORS["red"]}"></i>'
            "Harmful correction</span>"
            f'<span><i class="waste-swatch" style="background:{_COLORS["amber"]}"></i>'
            "No measured change</span>"
            f'<span><i class="waste-swatch" style="background:{_COLORS["slate"]}"></i>'
            "Inconclusive</span></div>"
            '<div class="waste-caption">'
            f"Treatment preserved {treatment.useful_corrections} useful corrections while "
            f"eliminating {removed_no_change_reviews} reviews that produced no measurable "
            "outcome change. Bar length shows absolute review-token consumption; hover "
            "segments for counts.</div></div>"
        ),
        unsafe_allow_html=True,
    )


def _render_executive_overview(analysis: TicketGenericAnalysis) -> None:
    _render_screen_section(
        1,
        "Executive value and efficiency",
        "Decision, unit economics, review workload, and token productivity.",
    )
    _render_action_banner(analysis)
    _render_kpis(analysis)

    comparison = analysis.comparison
    token_comparison = analysis.token_comparison
    summaries = (
        ("Control", comparison.control),
        ("Treatment", comparison.treatment),
    )
    token_summaries = (
        ("Control", token_comparison.control),
        ("Treatment", token_comparison.treatment),
    )
    cost_reduction = _reduction_text(
        comparison.control.cost_per_verified_outcome,
        comparison.treatment.cost_per_verified_outcome,
    )
    token_reduction = _reduction_text(
        token_comparison.control.tokens_per_verified_outcome,
        token_comparison.treatment.tokens_per_verified_outcome,
    )
    attribution = analysis.treatment_review_attribution
    treatment_reviews = sum(
        (
            attribution.useful_corrections,
            attribution.harmful_corrections,
            attribution.non_contributing_reviews,
            attribution.inconclusive_reviews,
        )
    )
    review_reduction = _reduction_text(
        comparison.control.total_work_units,
        treatment_reviews,
    )
    chart_columns = st.columns(3)
    with chart_columns[0]:
        st.markdown(
            f'<div class="chart-title">Cost per outcome · {cost_reduction}</div>',
            unsafe_allow_html=True,
        )
        _render_compact_bar_chart(
            [
                {"Variant": label, "Cost": float(summary.cost_per_verified_outcome)}
                for label, summary in summaries
                if summary.cost_per_verified_outcome is not None
            ],
            value_field="Cost",
            axis_title=f"Cost ({comparison.currency})",
            colors=(_COLORS["slate"], _COLORS["blue"]),
            value_format=",.4f",
        )
        st.markdown(
            '<div class="chart-caption"><b>Why it matters:</b> Lower cost delivers '
            "more verified outcomes from the same budget.</div>",
            unsafe_allow_html=True,
        )
    with chart_columns[1]:
        st.markdown(
            f'<div class="chart-title">Human reviews · {review_reduction}</div>',
            unsafe_allow_html=True,
        )
        _render_compact_bar_chart(
            [
                {
                    "Variant": "Control",
                    "Reviews": comparison.control.total_work_units,
                },
                {"Variant": "Treatment", "Reviews": treatment_reviews},
            ],
            value_field="Reviews",
            axis_title="Review calls",
            colors=(_COLORS["slate"], _COLORS["cyan"]),
            value_format=",",
        )
        st.markdown(
            '<div class="chart-caption"><b>Why it matters:</b> Selective review '
            "preserves assurance while removing avoidable effort.</div>",
            unsafe_allow_html=True,
        )
    with chart_columns[2]:
        st.markdown(
            f'<div class="chart-title">Tokens per outcome · {token_reduction}</div>',
            unsafe_allow_html=True,
        )
        _render_compact_bar_chart(
            [
                {
                    "Variant": label,
                    "Tokens per outcome": float(summary.tokens_per_verified_outcome),
                }
                for label, summary in token_summaries
                if summary.tokens_per_verified_outcome is not None
            ],
            value_field="Tokens per outcome",
            axis_title="Tokens / outcome",
            colors=(_COLORS["slate"], _COLORS["purple"]),
            value_format=",.1f",
        )
        st.markdown(
            '<div class="chart-caption"><b>Why it matters:</b> Fewer tokens per '
            "outcome means more efficient AI execution.</div>",
            unsafe_allow_html=True,
        )

    _render_screen_section(
        2,
        "Novelty and waste reduction",
        "One scroll reveals which assurance was valuable and which consumption "
        "produced no measurable outcome change.",
        second=True,
    )
    _render_compact_review_attribution(analysis)

    if analysis.decision.gate_results:
        _render_governance_flow(analysis)
    st.markdown(
        '<div class="section-end-spacer" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )


def _render_gate_table(analysis: TicketGenericAnalysis) -> None:
    st.markdown("### Governance assurance")
    gate_results = analysis.decision.gate_results
    passed = sum(result.status is GateStatus.PASS for result in gate_results)
    failed = sum(result.status is GateStatus.FAIL for result in gate_results)
    unknown = sum(result.status is GateStatus.UNKNOWN for result in gate_results)
    columns = st.columns(3)
    columns[0].metric("Gates passed", passed)
    columns[1].metric("Gates requiring action", failed)
    columns[2].metric("Gates awaiting evidence", unknown)
    if gate_results:
        st.progress(
            passed / len(gate_results),
            text=f"{passed} of {len(gate_results)} governance gates passed",
        )
    rows = [
        {
            "Gate": result.gate.value.replace("_", " ").title(),
            "Status": _GATE_STYLE[result.status],
            "Reason": result.reason,
        }
        for result in analysis.decision.gate_results
    ]
    with st.expander("Gate evidence and rationale"):
        st.dataframe(rows, hide_index=True, width="stretch")
    if analysis.decision.optimization_recommendations:
        st.markdown("#### Priority optimization opportunities")
        recommendation_rows = [
            {
                "Lever": recommendation.lever.value.replace("_", " ").title(),
                "Evidence metric": recommendation.evidence_metric,
                "Observed": _decimal_text(recommendation.observed_value),
                "Target": _decimal_text(recommendation.target_value),
                "Suggested action": recommendation.suggested_action,
            }
            for recommendation in analysis.decision.optimization_recommendations
        ]
        st.dataframe(recommendation_rows, hide_index=True, width="stretch")


def _render_process_comparison(analysis: TicketGenericAnalysis) -> None:
    comparison = analysis.comparison
    st.markdown("### Business impact")
    summaries = (comparison.control, comparison.treatment)
    chart_columns = st.columns(2)
    cost_data = [
        {
            "Variant": summary.variant_id,
            "Cost": float(summary.cost_per_verified_outcome),
        }
        for summary in summaries
        if summary.cost_per_verified_outcome is not None
    ]
    with chart_columns[0]:
        st.markdown("#### Cost per verified outcome")
        if cost_data:
            st.vega_lite_chart(
                {
                    "data": {"values": cost_data},
                    "mark": {"type": "bar", "cornerRadiusTopLeft": 6, "cornerRadiusTopRight": 6},
                    "encoding": {
                        "x": {"field": "Variant", "type": "nominal", "axis": {"labelAngle": 0}},
                        "y": {
                            "field": "Cost",
                            "type": "quantitative",
                            "title": comparison.currency,
                        },
                        "color": {
                            "field": "Variant",
                            "type": "nominal",
                            "scale": {"range": [_COLORS["slate"], _COLORS["blue"]]},
                            "legend": None,
                        },
                        "tooltip": [
                            {"field": "Variant", "type": "nominal"},
                            {"field": "Cost", "type": "quantitative", "format": ",.4f"},
                        ],
                    },
                    "height": 210,
                },
                width="stretch",
            )
        else:
            st.info("Cost evidence is not available yet.")
    with chart_columns[1]:
        st.markdown("#### Verified outcomes delivered")
        st.vega_lite_chart(
            {
                "data": {
                    "values": [
                        {
                            "Variant": summary.variant_id,
                            "Outcomes": summary.verified_outcomes,
                        }
                        for summary in summaries
                    ]
                },
                "mark": {"type": "bar", "cornerRadiusTopLeft": 6, "cornerRadiusTopRight": 6},
                "encoding": {
                    "x": {"field": "Variant", "type": "nominal", "axis": {"labelAngle": 0}},
                    "y": {
                        "field": "Outcomes",
                        "type": "quantitative",
                        "title": "Verified outcomes",
                    },
                    "color": {
                        "field": "Variant",
                        "type": "nominal",
                        "scale": {"range": [_COLORS["slate"], _COLORS["green"]]},
                        "legend": None,
                    },
                    "tooltip": [
                        {"field": "Variant", "type": "nominal"},
                        {"field": "Outcomes", "type": "quantitative", "format": ","},
                    ],
                },
                "height": 210,
            },
            width="stretch",
        )
    rows = [
        {
            "Variant": summary.variant_id,
            "Work units": summary.total_work_units,
            "Verified outcomes": summary.verified_outcomes,
            "Total cost": _currency_text(summary.total_cost, summary.currency),
            "Cost / verified outcome": _currency_text(
                summary.cost_per_verified_outcome, summary.currency
            ),
            "Evidence": summary.evidence_status.value,
        }
        for summary in (comparison.control, comparison.treatment)
    ]
    with st.expander("Process economics detail"):
        st.dataframe(rows, hide_index=True, width="stretch")


def _render_token_comparison(analysis: TicketGenericAnalysis) -> None:
    token_comparison = analysis.token_comparison
    st.markdown("### Token efficiency")
    summaries = (token_comparison.control, token_comparison.treatment)
    chart_data = [
        {
            "Variant": summary.variant_id,
            "Tokens per outcome": float(summary.tokens_per_verified_outcome),
        }
        for summary in summaries
        if summary.tokens_per_verified_outcome is not None
    ]
    if chart_data:
        st.vega_lite_chart(
            {
                "data": {"values": chart_data},
                "mark": {
                    "type": "bar",
                    "cornerRadiusTopLeft": 6,
                    "cornerRadiusTopRight": 6,
                },
                "encoding": {
                    "x": {"field": "Variant", "type": "nominal", "axis": {"labelAngle": 0}},
                    "y": {
                        "field": "Tokens per outcome",
                        "type": "quantitative",
                        "title": "Tokens / verified outcome",
                    },
                    "color": {
                        "field": "Variant",
                        "type": "nominal",
                        "scale": {"range": [_COLORS["slate"], _COLORS["purple"]]},
                        "legend": None,
                    },
                    "tooltip": [
                        {"field": "Variant", "type": "nominal"},
                        {
                            "field": "Tokens per outcome",
                            "type": "quantitative",
                            "format": ",.1f",
                        },
                    ],
                },
                "height": 210,
            },
            width="stretch",
        )
    rows = [
        {
            "Variant": summary.variant_id,
            "Total tokens": summary.total_tokens,
            "Verified outcomes": summary.verified_outcomes,
            "Tokens / verified outcome": _decimal_text(
                summary.tokens_per_verified_outcome
            ),
        }
        for summary in (token_comparison.control, token_comparison.treatment)
    ]
    with st.expander("Token utilization detail"):
        st.dataframe(rows, hide_index=True, width="stretch")
    st.caption(
        f"Tokens avoided vs. a comparable control run: "
        f"{_decimal_text(token_comparison.tokens_avoided)}"
    )


def _render_review_attribution(analysis: TicketGenericAnalysis) -> None:
    st.markdown("### Review value attribution")
    attribution = analysis.treatment_review_attribution
    rows = [
        {
            "Outcome": "Useful correction",
            "Reviews": attribution.useful_corrections,
            "Tokens": attribution.useful_review_tokens,
        },
        {
            "Outcome": "Harmful correction",
            "Reviews": attribution.harmful_corrections,
            "Tokens": attribution.harmful_review_tokens,
        },
        {
            "Outcome": "Non-contributing",
            "Reviews": attribution.non_contributing_reviews,
            "Tokens": attribution.non_contributing_review_tokens,
        },
        {
            "Outcome": "Inconclusive",
            "Reviews": attribution.inconclusive_reviews,
            "Tokens": attribution.inconclusive_review_tokens,
        },
    ]
    chart_rows = [row for row in rows if row["Tokens"] > 0]
    if chart_rows:
        columns = st.columns([1.15, 1])
        with columns[0]:
            st.vega_lite_chart(
                {
                    "data": {"values": chart_rows},
                    "mark": {"type": "arc", "innerRadius": 70, "outerRadius": 120},
                    "encoding": {
                        "theta": {"field": "Tokens", "type": "quantitative"},
                        "color": {
                            "field": "Outcome",
                            "type": "nominal",
                            "scale": {
                                "domain": [
                                    "Useful correction",
                                    "Harmful correction",
                                    "Non-contributing",
                                    "Inconclusive",
                                ],
                                "range": [
                                    _COLORS["green"],
                                    _COLORS["red"],
                                    _COLORS["amber"],
                                    _COLORS["slate"],
                                ],
                            },
                            "legend": {"orient": "bottom", "columns": 2},
                        },
                        "tooltip": [
                            {"field": "Outcome", "type": "nominal"},
                            {"field": "Tokens", "type": "quantitative", "format": ","},
                            {"field": "Reviews", "type": "quantitative", "format": ","},
                        ],
                    },
                    "height": 220,
                },
                width="stretch",
            )
        with columns[1]:
            st.metric(
                "Productive review tokens",
                attribution.useful_review_tokens,
                help="Review tokens attributed to useful corrections.",
            )
            st.metric(
                "Non-contributing review ratio",
                _percent_text(attribution.non_contributing_review_ratio),
            )
            st.metric("Total review tokens", attribution.total_review_tokens)
    with st.expander("Review attribution detail"):
        st.dataframe(rows, hide_index=True, width="stretch")
    st.caption(
        "Non-contributing review tokens: "
        f"{_percent_text(attribution.non_contributing_review_ratio)} "
        f"({attribution.non_contributing_review_tokens} of "
        f"{attribution.total_review_tokens} review tokens)."
    )
    treatment_tokens = analysis.token_comparison.treatment.total_tokens
    gate_ratio = (
        Decimal(attribution.non_contributing_review_tokens)
        / Decimal(treatment_tokens)
        if treatment_tokens
        else None
    )
    st.caption(
        "Review-waste gate input: "
        f"{_percent_text(gate_ratio)} of total treatment tokens "
        f"({attribution.non_contributing_review_tokens} of {treatment_tokens})."
    )


def _render_recent_runs(settings: Settings) -> None:
    st.markdown("### Operational evidence")
    runs = _recent_runs(settings)
    if not runs:
        st.info("No runs persisted yet.")
        return
    rows = [
        {
            "Run": run.get("id"),
            "Ticket": run.get("ticket_id"),
            "Variant": run.get("variant"),
            "Status": run.get("status"),
            "Started": run.get("started_at"),
            "Completed": run.get("completed_at"),
        }
        for run in runs
    ]
    st.dataframe(rows, hide_index=True, width="stretch")


def main() -> None:
    """Render the dashboard. Entry point for `streamlit run`."""
    st.set_page_config(
        page_title="MAF Outcome Economics",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _apply_dashboard_theme()
    settings = _load_settings()
    _render_header()

    with st.sidebar:
        st.header("Controls")
        st.write(f"Database: `{settings.database_path}`")
        refresh_clicked = st.button("Refresh now", width="stretch")
        auto_refresh = st.checkbox("Auto-refresh", value=False)
        interval_seconds = st.slider(
            "Refresh interval (seconds)", min_value=3, max_value=60, value=10
        )
        st.caption(
            "Run `uv run maf-outcome-economics demo` in another terminal to "
            "generate evidence while this dashboard is open."
        )

    if refresh_clicked:
        st.cache_data.clear()

    try:
        analysis = _run_analysis(settings)
    except ValueError:
        st.warning(
            "No completed runs are persisted yet. Run "
            "`uv run maf-outcome-economics demo` (or `run-scenario`) first, "
            "then refresh this page."
        )
        _render_recent_runs(settings)
        return

    overview_tab, governance_tab, evidence_tab = st.tabs(
        ["Executive overview", "Governance & reviews", "Evidence detail"]
    )
    with overview_tab:
        _render_executive_overview(analysis)
    with governance_tab:
        if analysis.decision.recommended_actions:
            st.markdown("### Recommended management actions")
            for action in analysis.decision.recommended_actions:
                st.markdown(f"- {action}")
        _render_gate_table(analysis)
        _render_review_attribution(analysis)
    with evidence_tab:
        _render_process_comparison(analysis)
        _render_token_comparison(analysis)
        _render_recent_runs(settings)

    if auto_refresh:
        time.sleep(interval_seconds)
        st.rerun()


if __name__ == "__main__":
    main()
