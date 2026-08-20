"""Self-contained HTML reporting for the baseline versus optimized demo."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from html import escape
from pathlib import Path
from typing import TYPE_CHECKING

from maf_outcome_economics.console_service import (
    ConsoleProvider,
    TicketProgress,
    VariantReport,
)
from maf_outcome_economics.core import (
    GenericGovernanceAction,
    GenericGovernanceDecision,
)
from maf_outcome_economics.domain import (
    GovernanceAction,
    GovernanceDecision,
    GovernanceReasonCode,
    WorkflowVariant,
)

if TYPE_CHECKING:
    from maf_outcome_economics.scenarios.ticket import TicketGenericAnalysis

_REASON_EXPLANATIONS = {
    GovernanceReasonCode.THRESHOLDS_MET: (
        "Quality, safety, and unit-cost gates passed."
    ),
    GovernanceReasonCode.COST_EXCEEDS_BUDGET: (
        "Quality passed, but cost per accepted outcome exceeds budget."
    ),
    GovernanceReasonCode.NO_ACCEPTED_OUTCOMES: (
        "No outcomes passed deterministic verification."
    ),
    GovernanceReasonCode.ACCEPTANCE_BELOW_MINIMUM: (
        "The verified acceptance rate is below the contract minimum."
    ),
    GovernanceReasonCode.QUALITY_BELOW_MINIMUM: (
        "Average deterministic quality is below the contract minimum."
    ),
    GovernanceReasonCode.CRITICAL_RECALL_BELOW_MINIMUM: (
        "Critical-priority recall is below the safety threshold."
    ),
}

GovernanceDisplayDecision = GovernanceDecision | GenericGovernanceDecision


def write_demo_report(
    output_path: Path,
    reports: list[VariantReport],
    decision: GovernanceDisplayDecision,
    provider: ConsoleProvider,
    progress_events: list[TicketProgress],
    ticket_limit: int,
    generic_analysis: TicketGenericAnalysis | None = None,
) -> Path:
    """Write a self-contained HTML report from typed demo results."""
    reports_by_variant = {report.variant: report for report in reports}
    try:
        baseline = reports_by_variant[WorkflowVariant.BASELINE]
        optimized = reports_by_variant[WorkflowVariant.OPTIMIZED]
    except KeyError as error:
        raise ValueError("Demo report requires baseline and optimized reports") from error

    completed = [event for event in progress_events if event.stage == "completed"]
    html = _render_page(
        baseline,
        optimized,
        decision,
        provider,
        completed,
        ticket_limit,
        datetime.now(UTC),
        generic_analysis,
    )
    resolved_path = output_path.resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path.write_text(html, encoding="utf-8")
    return resolved_path


def write_scenario_index(
    output_path: Path,
    results: list[tuple[str, VariantReport, GovernanceDecision, Path]],
) -> Path:
    """Write a combined HTML index for all governance scenario outcomes."""
    cards = []
    for scenario, report, decision, detail_path in results:
        cost = report.economics.cost_per_accepted_outcome
        evidence = decision.evidence_metrics
        budget = (
            evidence.maximum_cost_per_accepted_outcome
            if evidence is not None
            else None
        )
        color = {
            GovernanceAction.SCALE: "green",
            GovernanceAction.OPTIMIZE: "amber",
            GovernanceAction.STOP: "red",
        }.get(decision.action, "amber")
        reasons = " ".join(
            _REASON_EXPLANATIONS[code] for code in decision.reason_codes
        )
        cards.append(
            f"""<article class="scenario-card {color}">
    <div class="scenario-name">{escape(scenario.upper())} DATASET</div>
    <div class="scenario-decision">{decision.action.value.upper()}</div>
    <dl>
        <div><dt>Quality</dt><dd>{_percent(report.average_quality)}</dd></div>
        <div><dt>Critical recall</dt><dd>{_percent(report.critical_priority_recall)}</dd></div>
        <div><dt>Cost / accepted</dt><dd>{_money(cost)}</dd></div>
        <div><dt>Approved budget</dt><dd>{_money(budget)}</dd></div>
    </dl>
    <p>{escape(reasons)}</p>
    <a href="{escape(detail_path.name)}">Open detailed evidence</a>
</article>"""
        )
    captured_at = datetime.now(UTC)
    html = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>OutcomeMeter Governance Scenarios</title>
    <style>{_STYLES}{_SCENARIO_INDEX_STYLES}</style>
</head>
<body>
    <main class="scenario-index">
        <header>
            <div>
                <div class="eyebrow">Microsoft Agent Framework · Outcome Economics</div>
                <h1>Three Outcomes. One Governance Engine.</h1>
                <p class="subtitle">Isolated fictional datasets exercise every
                    deterministic action.</p>
            </div>
            <div class="mode fake">● Rehearsal mode</div>
        </header>
        <section class="scenario-intro">Each result is calculated from verified
            quality, critical recall, and cost per accepted outcome. The action is
            never hard-coded.</section>
        <section class="scenario-grid">{"".join(cards)}</section>
        <footer><span>Fictional tickets · deterministic hidden-label verification</span>
            <span>Captured {captured_at:%Y-%m-%d %H:%M UTC}</span></footer>
    </main>
</body>
</html>
"""
    resolved_path = output_path.resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path.write_text(html, encoding="utf-8")
    return resolved_path


def _render_page(
    baseline: VariantReport,
    optimized: VariantReport,
    decision: GovernanceDisplayDecision,
    provider: ConsoleProvider,
    completed: list[TicketProgress],
    ticket_limit: int,
    captured_at: datetime,
    generic_analysis: TicketGenericAnalysis | None,
) -> str:
    baseline_tokens = _total_tokens(baseline)
    optimized_tokens = _total_tokens(optimized)
    token_change = _relative_change(optimized_tokens, baseline_tokens)
    cost_change = _relative_change(
        optimized.economics.cost_per_accepted_outcome,
        baseline.economics.cost_per_accepted_outcome,
    )
    quality_change = optimized.average_quality - baseline.average_quality
    mode = provider.value.upper()
    evidence = (
        "Actual MAF OpenTelemetry spans"
        if provider is ConsoleProvider.LIVE
        else "Illustrative rehearsal telemetry"
    )
    if isinstance(decision, GenericGovernanceDecision):
        governance_color = {
            GenericGovernanceAction.SCALE: "green",
            GenericGovernanceAction.MONITOR: "blue",
            GenericGovernanceAction.OPTIMIZE: "amber",
            GenericGovernanceAction.STOP: "red",
            GenericGovernanceAction.INSUFFICIENT_EVIDENCE: "amber",
        }[decision.action]
        reasons = " ".join(result.reason for result in decision.gate_results)
        audit_codes = ", ".join(
            f"{result.gate.value}:{result.status.value}"
            for result in decision.gate_results
        )
        optimization = " ".join(
            recommendation.suggested_action
            for recommendation in decision.optimization_recommendations
        )
    else:
        governance_color = {
            GovernanceAction.SCALE: "green",
            GovernanceAction.OPTIMIZE: "amber",
            GovernanceAction.STOP: "red",
        }.get(decision.action, "amber")
        reasons = " ".join(
            _REASON_EXPLANATIONS[code] for code in decision.reason_codes
        )
        audit_codes = ", ".join(code.value for code in decision.reason_codes)
        optimization = ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OutcomeMeter Demo Report</title>
  <style>{_STYLES}</style>
</head>
<body>
  <main>
    <header>
      <div>
        <div class="eyebrow">Microsoft Agent Framework · Outcome Economics</div>
        <h1>OutcomeMeter</h1>
        <p class="subtitle">{escape(evidence)}, measured per verified outcome</p>
      </div>
      <div class="mode {provider.value}">● {mode} mode</div>
    </header>
    <section class="question"><strong>Experiment:</strong> Can risk-based review
      preserve routing quality while reducing token cost?</section>
    <section class="experiment">
      <article><h2>Baseline</h2><p>Triage and review every ticket. Maximum
        oversight, with coordination tokens on every run.</p></article>
      <article class="optimized"><h2>Optimized</h2><p>Triage every ticket.
        Review only low-confidence, sensitive, P1, or critical results.</p></article>
    </section>
    <section class="terminal">
      <div class="terminal-head"><span>RUN EVIDENCE · {ticket_limit} TICKETS PER VARIANT</span>
        <span>SQLite + OpenTelemetry</span></div>
      {_progress_rows(completed)}
    </section>
    <section class="results">
      <table>
        <caption>Quality and Outcome Economics</caption>
        <thead><tr><th>Persisted metric</th><th>Baseline</th><th>Optimized</th></tr></thead>
        <tbody>
                    {_report_rows(baseline, optimized, baseline_tokens, optimized_tokens)}
        </tbody>
      </table>
      <div>
        <h2 class="section-title">Measured Impact</h2>
        <div class="impact">
          {_impact_card(_change(token_change), "token usage")}
          {_impact_card(_change(cost_change), "cost per accepted outcome")}
          {_impact_card(f"{quality_change:+.1%}", "average quality")}
          {_impact_card(_percent(optimized.critical_priority_recall), "critical recall")}
        </div>
      </div>
    </section>
    {_tokenomics_section(generic_analysis)}
    <section class="governance {governance_color}">
      <div class="decision">{decision.action.value.upper()}</div>
      <div>
        <h2>Governance decision</h2>
        <p>{escape(reasons)}</p>
        <p class="recommendation">{escape(" ".join(decision.recommended_actions))}</p>
        {f'<p class="recommendation">{escape(optimization)}</p>' if optimization else ''}
        <div class="audit">audit codes: {escape(audit_codes)}</div>
      </div>
    </section>
    <footer><span>{escape(evidence)} · deterministic hidden-label verification</span>
      <span>Captured {captured_at:%Y-%m-%d %H:%M UTC}</span></footer>
  </main>
</body>
</html>
"""


def _tokenomics_section(analysis: TicketGenericAnalysis | None) -> str:
    if analysis is None:
        return ""
    comparison = analysis.token_comparison
    improvement = (
        f"{comparison.efficiency_improvement:.1%}"
        if comparison.efficiency_improvement is not None
        else "n/a"
    )
    rows = (
        (
            "Verified outcomes",
            str(comparison.control.verified_outcomes),
            str(comparison.treatment.verified_outcomes),
        ),
        (
            "Tokens / verified outcome",
            _decimal(comparison.control.tokens_per_verified_outcome),
            _decimal(comparison.treatment.tokens_per_verified_outcome),
        ),
        (
            "Review tokens",
            f"{analysis.control_review_attribution.total_review_tokens:,}",
            f"{analysis.treatment_review_attribution.total_review_tokens:,}",
        ),
        (
            "Non-contributing review tokens",
            f"{analysis.control_review_attribution.non_contributing_review_tokens:,}",
            f"{analysis.treatment_review_attribution.non_contributing_review_tokens:,}",
        ),
        ("Token efficiency improvement", "-", improvement),
    )
    return f"""<section class="results tokenomics">
      <table>
        <caption>Verified Outcome Tokenomics</caption>
        <thead><tr><th>Persisted metric</th><th>Baseline</th><th>Optimized</th></tr></thead>
        <tbody>{''.join(_metric_row(*row) for row in rows)}</tbody>
      </table>
    </section>"""


def _decimal(value: Decimal | None) -> str:
    return f"{value:,.2f}" if value is not None else "n/a"


def _progress_rows(events: list[TicketProgress]) -> str:
    if not events:
        return '<div class="terminal-line muted">No completed ticket events captured.</div>'
    rows = []
    for event in events:
        accepted = "yes" if event.accepted else "no"
        review = "invoked" if event.review_invoked else "skipped"
        trace_id = event.trace_id or "unavailable"
        rows.append(
            '<div class="terminal-line">'
            f'<span class="prompt">{escape(event.variant.value)} '
            f'{event.current}/{event.total}</span> · {escape(event.ticket_id)} · '
            f'<span class="accepted-{accepted}">accepted={accepted}</span> · '
            f'<span class="review-{review}">review={review}</span> · '
            f'tokens={event.input_tokens or 0} in/{event.output_tokens or 0} out · '
            f'<span class="trace">trace={escape(_short_trace(trace_id))}</span></div>'
        )
    return "\n".join(rows)


def _metric_row(label: str, baseline: str, optimized: str) -> str:
    return (
        f"<tr><td>{escape(label)}</td><td>{escape(baseline)}</td>"
        f'<td class="optimized-value">{escape(optimized)}</td></tr>'
    )


def _report_rows(
    baseline: VariantReport,
    optimized: VariantReport,
    baseline_tokens: int,
    optimized_tokens: int,
) -> str:
    rows = (
        ("Runs", str(baseline.runs), str(optimized.runs)),
        (
            "Acceptance rate",
            _percent(baseline.acceptance_rate),
            _percent(optimized.acceptance_rate),
        ),
        (
            "Average quality",
            _percent(baseline.average_quality),
            _percent(optimized.average_quality),
        ),
        (
            "Critical recall",
            _percent(baseline.critical_priority_recall),
            _percent(optimized.critical_priority_recall),
        ),
        ("Total tokens", f"{baseline_tokens:,}", f"{optimized_tokens:,}"),
        (
            "Estimated model cost",
            _money(baseline.economics.estimated_model_cost),
            _money(optimized.economics.estimated_model_cost),
        ),
        (
            "Cost / accepted",
            _money(baseline.economics.cost_per_accepted_outcome),
            _money(optimized.economics.cost_per_accepted_outcome),
        ),
    )
    return "\n".join(_metric_row(*row) for row in rows)


def _impact_card(value: str, label: str) -> str:
    return (
        f'<div class="metric"><span class="value">{escape(value)}</span>'
        f'<span class="label">{escape(label)}</span></div>'
    )


def _total_tokens(report: VariantReport) -> int:
    return (
        report.economics.total_input_tokens + report.economics.total_output_tokens
    )


def _relative_change(
    current: int | Decimal | None,
    previous: int | Decimal | None,
) -> Decimal | None:
    if current is None or previous in (None, 0):
        return None
    return (Decimal(current) - Decimal(previous)) / Decimal(previous)


def _change(value: Decimal | None) -> str:
    return f"{value:+.1%}" if value is not None else "n/a"


def _percent(value: float) -> str:
    return f"{value:.1%}"


def _money(value: Decimal | None) -> str:
    return f"${value:.6f}" if value is not None else "n/a"


def _short_trace(trace_id: str) -> str:
    return trace_id if len(trace_id) <= 12 else f"{trace_id[:4]}…{trace_id[-4:]}"


_STYLES = """
:root{color-scheme:dark;--canvas:#101516;--panel:#182022;--alt:#1d282a;
--line:#385055;--ink:#f2f6f4;--muted:#9eb0ae;--cyan:#44d7cf;
--green:#7ae582;--amber:#ffca5c;--red:#ff6b6b}*{box-sizing:border-box}
body{margin:0;background-color:var(--canvas);background-image:
linear-gradient(rgba(68,215,207,.045) 1px,transparent 1px),
linear-gradient(90deg,rgba(68,215,207,.045) 1px,transparent 1px);
background-size:32px 32px;color:var(--ink);font-family:Bahnschrift,"Arial Narrow",sans-serif}
main{width:1600px;min-height:1200px;padding:72px 82px 64px}header{display:grid;
grid-template-columns:1fr auto;align-items:end;gap:40px;border-bottom:2px solid var(--cyan);
padding-bottom:28px;margin-bottom:34px}.eyebrow{color:var(--cyan);font:700 20px/1.2
"Cascadia Mono",Consolas,monospace;text-transform:uppercase}h1{margin:8px 0 10px;
font-size:62px;line-height:1}.subtitle{margin:0;color:var(--muted);font-size:25px}
.mode{border:1px solid;padding:13px 18px;font:700 20px/1 "Cascadia Mono",Consolas,monospace;
text-transform:uppercase}.mode.live{color:var(--green)}.mode.fake{color:var(--amber)}
.question{background:var(--alt);border-left:7px solid var(--cyan);padding:24px 28px;
margin-bottom:28px;font-size:29px}.question strong{color:var(--cyan)}
.experiment{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-bottom:28px}
.experiment article{background:var(--panel);border:1px solid var(--line);padding:24px 26px}
.experiment article.optimized{border-color:var(--green)}
h2,.section-title{margin:0 0 10px;font-size:26px;color:var(--cyan)}.optimized h2{color:var(--green)}
.experiment p{margin:0;color:var(--muted);font-size:21px;line-height:1.45}
.terminal{background:#0b0f10;
border:1px solid var(--line);padding:24px 26px;margin-bottom:28px;font:19px/1.55
"Cascadia Mono",Consolas,monospace}.terminal-head{display:flex;justify-content:space-between;
color:var(--muted);border-bottom:1px solid #293538;padding-bottom:13px;margin-bottom:14px}
.terminal-line{white-space:nowrap}.prompt{color:var(--cyan)}.accepted-yes{color:var(--green)}
.accepted-no{color:var(--red)}.review-skipped{color:var(--amber)}.trace{color:#7fb8ff}
.muted{color:var(--muted)}
.results{display:grid;grid-template-columns:1.18fr .82fr;gap:24px;margin-bottom:28px}
table{width:100%;
border-collapse:collapse;background:var(--panel);font:20px/1.3 "Cascadia Mono",Consolas,monospace}
caption{text-align:left;color:var(--cyan);font:700 26px/1.2 Bahnschrift,sans-serif;
padding-bottom:12px}
th,td{padding:13px 16px;border-bottom:1px solid var(--line);text-align:right}th:first-child,
td:first-child{text-align:left}th{color:var(--muted);font-weight:400}
.optimized-value{color:var(--green)}
.impact{display:grid;grid-template-columns:1fr 1fr;gap:14px}.metric{background:var(--alt);
border-top:4px solid var(--green);padding:18px;min-height:118px}.metric .value{color:var(--green);
font:700 38px/1 "Cascadia Mono",Consolas,monospace}.metric .label{display:block;margin-top:10px;
color:var(--muted);font-size:18px}.governance{display:grid;grid-template-columns:240px 1fr;
gap:28px;align-items:center;border:2px solid;padding:26px 30px}
.governance.green{background:#142219;border-color:var(--green)}
.governance.amber{background:#282216;border-color:var(--amber)}
.governance.red{background:#28191a;border-color:var(--red)}
.decision{font:700 54px/1 "Cascadia Mono",Consolas,monospace;text-align:center}
.green .decision,.green h2{color:var(--green)}.amber .decision,.amber h2{color:var(--amber)}
.red .decision,.red h2{color:var(--red)}.governance p{margin:0;font-size:22px;line-height:1.4}
.recommendation{margin-top:8px!important;color:var(--muted)}.audit{margin-top:8px;color:var(--muted);
font:17px/1.3 "Cascadia Mono",Consolas,monospace}footer{display:flex;justify-content:space-between;
margin-top:24px;color:var(--muted);font:17px/1.3 "Cascadia Mono",Consolas,monospace}
"""

_SCENARIO_INDEX_STYLES = """
.scenario-index{min-height:980px}.scenario-index h1{font-size:52px}
.scenario-intro{font-size:25px;line-height:1.4;color:var(--muted);margin-bottom:32px;
max-width:1180px}.scenario-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.scenario-card{background:var(--panel);border:2px solid;padding:28px;min-height:570px;
display:flex;flex-direction:column}.scenario-card.green{border-color:var(--green)}
.scenario-card.amber{border-color:var(--amber)}.scenario-card.red{border-color:var(--red)}
.scenario-name{color:var(--muted);font:700 18px/1.2 "Cascadia Mono",Consolas,monospace}
.scenario-decision{font:700 52px/1 "Cascadia Mono",Consolas,monospace;margin:24px 0 30px}
.scenario-card.green .scenario-decision{color:var(--green)}
.scenario-card.amber .scenario-decision{color:var(--amber)}
.scenario-card.red .scenario-decision{color:var(--red)}dl{margin:0}dl div{display:flex;
justify-content:space-between;border-bottom:1px solid var(--line);padding:15px 0;font-size:20px}
dt{color:var(--muted)}dd{margin:0;font-family:"Cascadia Mono",Consolas,monospace}
.scenario-card p{font-size:20px;line-height:1.45;color:var(--muted);flex:1;margin:26px 0}
.scenario-card a{color:var(--cyan);font:700 18px/1.2 "Cascadia Mono",Consolas,monospace}
"""