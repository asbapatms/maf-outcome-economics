---
title: OutcomeMeter — A Day in the Life (Story-Format Demo Script)
description: An alternate, narrative-driven recording plan for the Executive Challenge video, told as one executive's governance decision
ms.date: 2026-09-17
ms.topic: tutorial
---

## Why This Version Exists

[DEMO.md](../DEMO.md) is the rubric-aligned, feature-by-feature narration
script. This file is an **alternate storyboard** that shows the exact same
product, the exact same dashboard, and the exact same verified numbers, but
tells it as a short narrative: one executive's morning, spent deciding whether
to scale, adjust, or stop an AI support-triage pilot.

Use this file instead of [DEMO.md](../DEMO.md) if the story format lands
better with judges, or record both and pick the stronger cut. Nothing in
[DEMO.md](../DEMO.md), [POWERPOINT_VIDEO_GUIDE.md](../POWERPOINT_VIDEO_GUIDE.md),
or `artifacts/` is modified by this file — every visual referenced below
already exists.

If building an animated concept deck instead of (or alongside) a Clipchamp
recording, use [STORY_POWERPOINT_GUIDE.md](./STORY_POWERPOINT_GUIDE.md) — it
mirrors [POWERPOINT_VIDEO_GUIDE.md](../POWERPOINT_VIDEO_GUIDE.md) slide for
slide, framed through Priya's decision the same way this file reframes
[DEMO.md](../DEMO.md).

> [!IMPORTANT]
> This is a new, standalone recording plan. Setup commands, dashboard prep,
> and the underlying product are identical to [DEMO.md](../DEMO.md) Steps 1
> and 2 — re-use that setup rather than duplicating it. Only the narration
> voice, the framing, and the shot order change here.

## The Character

**Priya Nair, VP of Customer Support Operations.** Two weeks ago her team
turned on an AI agent to triage incoming support tickets — deciding category,
priority, and resolver group before a human ever sees them. This morning she
has one job: decide whether it is safe and valuable enough to scale to the
rest of the organization.

The viewer follows her through one governance decision, told in real time.

## Judging Strategy (Unchanged)

| Rubric | Where the story proves it |
|--------|----------------------------|
| Inspiration | Priya starts the day trusting activity metrics and ends it trusting verified outcomes |
| Business Value | Her decision is backed by cost-per-verified-outcome and net savings, not raw spend |
| Customer Focus | The entire video is framed from her point of view, as the accountable leader |
| Feasibility | She previews the same governance core running for claims, security, and code review |
| Make Something | The terminal run and the live dashboard she opens are the real, working product |

Target export duration: **1 minute 50 seconds** (same 2:00 ceiling as
[DEMO.md](../DEMO.md)).

## Story Storyboard

| Time | Moment in Priya's day | Visual |
|------|------------------------|--------|
| 0:00-0:08 | 8:58 AM — the question on her desk | Title card |
| 0:08-0:18 | 9:00 AM — what the pilot actually does | Scenario card |
| 0:18-0:26 | 9:01 AM — how she knows an answer is "right" | Golden-dataset card |
| 0:26-0:41 | 9:02 AM — she watches it run, live | Live terminal |
| 0:41-1:05 | 9:05 AM — she opens the dashboard: is it worth it? | Dashboard Section 1 |
| 1:05-1:25 | 9:07 AM — she checks what the reviewers actually caught | Dashboard Section 2 |
| 1:25-1:45 | 9:09 AM — the governance engine gives her a verdict | Governance flow + scenario matrix |
| 1:45-1:53 | 9:11 AM — she decides, and sees what's next | Architecture / scale card |
| 1:53-1:58 | Closing card | Title card |

## Recording the Clips

Reuse the same eight-clip capture approach from
[DEMO.md](../DEMO.md#step-3-record-eight-short-visual-clips) — same dashboard,
same terminal command, same `artifacts/demo-scenarios.html` scenarios tab. Only
the text cards and the narration below change. Story-specific cutaway assets
fit naturally into this narration and are called out where they help:

* [`assets/priya-title-card.png`](./assets/priya-title-card.png) — use as
  Clip 1 in place of a plain text card, or hold it under the text card for the
  full 7-8 seconds. It already shows Priya's persona, the 9:00 AM timestamp,
  and the `MONITOR` verdict she is about to reason through.
* [`artifacts/old-way-vs-new-way.png`](../artifacts/old-way-vs-new-way.png) —
  works well as a 1-to-2 second cutaway right as Priya questions the activity
  metrics she used to rely on (around 0:41).
* [`artifacts/decision-matrix.png`](../artifacts/decision-matrix.png) — works
  well as a cutaway right after the `MONITOR` verdict, to show Priya (and the
  viewer) that the same engine would have said `STOP` or `SCALE` under
  different evidence (around 1:40).
* [`artifacts/architecture-diagram.png`](../artifacts/architecture-diagram.png)
  — works well under the closing line about extending to other teams (around
  1:47).
* [`assets/priya-decision-memo.png`](./assets/priya-decision-memo.png) — use
  as Clip 8's visual instead of, or alongside, the closing text card. It
  reads as the memo Priya sends her team right after deciding, with the same
  verified numbers and four concrete next steps.

None of these require new recordings; they are already-rendered PNGs that can
be dropped directly into the Clipchamp timeline as brief cutaway stills.

### Clip 1 — Title Card: The Question on Her Desk

Duration: 7-8 seconds

```text
9:00 AM. Priya's AI triage pilot has been live for two weeks.

Today she decides: scale it, fix it, or shut it down.
```

Use [`assets/priya-title-card.png`](./assets/priya-title-card.png) as the
full-frame visual for this clip instead of building a plain text card — it
already contains this beat's timestamp, persona, and verdict preview.

### Clip 2 — The Scenario Card: What the Pilot Actually Does

Duration: 9-10 seconds

```text
Every ticket needs a category, a priority, and a resolver group.

Get it wrong, and it lands with the wrong team — support waits longer.

An AI agent makes that call now. Priya needs to know: is it right,
and is it worth what it spends?
```

On-screen only, never narrated: `Invoice coding`, `Claims or security triage`,
`Code review acceptance` — small icon labels signaling this is one instance of
a reusable governance pattern.

### Clip 3 — The Golden-Dataset Card: How She Knows "Right"

Duration: 8-9 seconds

```text
Before she trusts any of it, Priya needs proof the agent isn't grading
its own homework.

Every ticket carries three hidden correct answers the agent never sees.
```

### Clip 4 — Live Terminal: She Watches It Run

Duration: 15-18 seconds (final edit)

Record the same command as [DEMO.md Clip 4](../DEMO.md):

```powershell
uv run maf-outcome-economics demo --provider live --limit 3
```

Keep the same footage priorities: `LIVE MODE`, baseline vs. optimized
execution, real trace IDs and token counts, review invoked or skipped,
deterministic acceptance. Trim wait time and repeated output.

### Clip 5 — Dashboard Section 1: Is It Worth It?

Duration: 22-24 seconds

Priya opens the dashboard she has open every Monday morning. Show the same
Executive overview from [DEMO.md Clip 5](../DEMO.md):

* `31` verified treatment outcomes
* `0.0007 USD` cost per verified outcome
* `0.0088 USD` estimated net savings versus control
* `27.5%` token-efficiency gain
* The three before-and-after charts (cost per outcome, human reviews, tokens
  per outcome)

Cutaway option here: 1-2 seconds on
[`artifacts/old-way-vs-new-way.png`](../artifacts/old-way-vs-new-way.png),
timed to the beat where Priya stops looking at raw activity and starts
looking at verified outcomes.

### Clip 6 — Dashboard Section 2: What Did the Reviewers Actually Catch?

Duration: 18-20 seconds

Same Section 2 recording as [DEMO.md Clip 6](../DEMO.md). Show:

* `100%` of useful corrections retained
* `81%` of no-change review tokens removed
* `69%` reduction in total review tokens, from `3,200` to `1,000`
* `4` useful corrections preserved while `22` no-change reviews were
  eliminated

### Clip 7 — The Verdict: Governance Flow + Scenario Matrix

Duration: 20 seconds

Same governance-flow crop as [DEMO.md Clip 7](../DEMO.md): `11/11 GATES
PASSED`, move through **Evidence → Trust → Value → Tokens → Waste**, land on
`MONITOR`. Hover **Trust**, then **Value**. Text overlay in editing (not
narrated): "Trust ✓ Value ✓ — savings proven, not assumed."

Then cut briefly to `artifacts/demo-scenarios.html` (or the static
[`artifacts/decision-matrix.png`](../artifacts/decision-matrix.png)) showing
`SCALE`, `OPTIMIZE`, and `STOP` — the same engine, three different verdicts,
proving Priya isn't the one deciding the threshold. The evidence is.

### Clip 8 — Her Decision, and What's Next

Duration: 14-15 seconds

```text
Priya's decision: keep monitoring, reconcile real billing next cycle,
then scale.

One governance core.
Support | Finance | Claims | Security | Software Delivery

Measure what AI spends. Verify what it achieves. Decide what to scale.
```

Cutaway option: [`artifacts/architecture-diagram.png`](../artifacts/architecture-diagram.png)
under the four-team list, reinforcing that the same core extends elsewhere.
Alternatively, hold on
[`assets/priya-decision-memo.png`](./assets/priya-decision-memo.png) for the
first half of this clip (the memo she sends her team) before cutting to the
architecture diagram for the four-team reuse point.

## Narration Script (Story Voice)

Same target pace as [DEMO.md](../DEMO.md): 130-140 words per minute, about
1:47-1:55 total. Record each paragraph as a separate voiceover clip so timing
stays adjustable.

### 0:00-0:08 — The Question

> Every Monday, Priya has to decide which AI workflows earned the right to
> keep running. Today it's support-ticket triage.

### 0:08-0:18 — The Scenario

> Her team's AI agent has been deciding ticket category, priority, and
> resolver group for two weeks. Wrong routing means slower resolution, so
> before Priya trusts a token of it, she needs proof it's actually right —
> not just fast.

### 0:18-0:26 — Proving the Answer

> Every one of those tickets carries a hidden, known-correct answer the agent
> never sees. It doesn't get to grade its own work — and neither does Priya,
> on instinct alone.

### 0:26-0:41 — Watching It Run

> This is the real thing running: Microsoft Agent Framework and Azure OpenAI,
> executing baseline and optimized versions of the same workflow, while
> OpenTelemetry captures every trace and every token.

### 0:41-1:05 — Opening the Dashboard

> Priya used to track spend and call volume. Now she opens a dashboard that
> shows cost and tokens per **verified** outcome — not per model call. Thirty
> one outcomes verified, a fraction of a cent each, and real net savings
> against the old process.

### 1:05-1:25 — What the Reviewers Caught

> Before she scales anything, Priya wants to know what her human reviewers
> were actually catching. The answer: every useful correction was kept, while
> eighty-one percent of reviews that changed nothing were removed — cutting
> review token spend by sixty-nine percent without losing a single real catch.

### 1:25-1:45 — The Verdict

> Then the governance engine gives its recommendation: monitor. Quality,
> safety, and compliance clear first — savings never override a failed
> safeguard. The same engine, on different evidence, would say scale it, fix
> it, or stop it entirely. Priya isn't guessing. The evidence decided.

### 1:45-1:58 — Her Decision and the Close

> Priya's call: keep monitoring, reconcile real billing next cycle, then
> scale. The same governance core extends from support to finance, claims,
> security, and software delivery. Measure what AI spends. Verify what it
> achieves. Decide what to scale.

## Assembly, Captions, and Export

Follow [DEMO.md Steps 5 through 9](../DEMO.md#step-5-assemble-in-clipchamp)
unchanged — same Clipchamp assembly process, same caption corrections
(`OutcomeMeter`, `Microsoft Agent Framework`, `Azure OpenAI`, `OpenTelemetry`,
`Tokenomics`, `Dashboard`), same eligibility and privacy checklist, same
export target (`1080p`, under 2:00). Only suggested output file name differs
so both cuts can be compared side by side before submission:

```text
OutcomeMeter-Executive-Challenge-Story.mp4
```

## Rubric Self-Check for the Story Cut

* Does the opening make Priya's accountability, not the product's feature
  list, the first thing the viewer understands?
* Does the dashboard section clearly show *her* reasoning changing from
  activity to verified outcomes?
* Is the governance verdict shown as evidence-driven rather than as Priya's
  personal judgment call?
* Does the closing line make the four-domain reuse feel like a natural next
  step in her story, not a bolted-on feature list?

If the story framing ever forces a metric to be dropped, restated
imprecisely, or contradicts a stated dashboard value, revert that beat to the
matching clip's wording in [DEMO.md](../DEMO.md) — narrative flow never
overrides evidence accuracy.
