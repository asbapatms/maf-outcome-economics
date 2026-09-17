---
title: OutcomeMeter Two-Minute Clipchamp Demo
description: Rubric-aligned recording plan and narration for the Executive Challenge video
ms.date: 2026-09-16
ms.topic: tutorial
---

## Objective

Create a product-first video that is **no longer than 2 minutes** and shows why
OutcomeMeter matters to its primary customer:

> **Enterprise leaders, AI portfolio owners, and process owners deciding which
> AI workflows are safe and valuable enough to scale.**

Target an exported duration of **1 minute 50 seconds**. The ten-second buffer
protects eligibility if Clipchamp adds a transition or trailing frame.

## Judging Strategy

| Rubric | What the video must prove |
|--------|---------------------------|
| Inspiration | A fresh shift from measuring AI activity to measuring verified value |
| Business Value | Better investment decisions, lower token waste, and protected quality |
| Customer Focus | Clear value for leaders accountable for AI spend, risk, and scaling |
| Feasibility | A framework-neutral design with a practical enterprise adoption path |
| Make Something | A working product using Azure OpenAI, Microsoft Agent Framework, telemetry, verification, governance, and a live dashboard |

Do not spend time listing every feature. Show the product, the result, and the
decision it enables.

## Final Storyboard

| Time | Visual | Rubric emphasis |
|------|--------|-----------------|
| 0:00-0:08 | Title and executive problem | Inspiration, Customer Focus |
| 0:08-0:18 | Scenario you are about to see | Customer Focus |
| 0:18-0:26 | Proving the answer with a golden dataset | Feasibility, Customer Focus |
| 0:26-0:41 | Live terminal execution | Make Something |
| 0:41-1:05 | Live dashboard: outcome economics | Business Value |
| 1:05-1:25 | Live dashboard: tokenomics and review waste | Innovation, Business Value |
| 1:25-1:45 | Live dashboard: governance decision, then scenarios | Customer Focus, Make Something |
| 1:45-1:53 | Architecture and scale | Feasibility |
| 1:53-1:58 | Closing card | Inspiration |

Maximum planned duration: **1 minute 58 seconds**. Trim toward 1:50 during
editing. The scenario beat mirrors Slide 4 of
[POWERPOINT_VIDEO_GUIDE.md](./POWERPOINT_VIDEO_GUIDE.md), and the golden-dataset
beat mirrors Slide 5; if those PowerPoint slides already exist, export their
animations as clips and drop them in here instead of rebuilding them as
Clipchamp text cards.

## Step 1: Generate Fresh Evidence

Open PowerShell in the project directory and install the optional dashboard
dependency:

```powershell
Set-Location C:\Hackathon2026\Tokenomics\maf-outcome-economics
uv sync --extra dashboard
uv run maf-outcome-economics health
```

Generate the clean 32-ticket dashboard evidence used for Clips 5 through 7:

```powershell
Remove-Item data\dashboard-demo.db -ErrorAction SilentlyContinue
$env:MAF_DATABASE_PATH = "data\dashboard-demo.db"
uv run maf-outcome-economics demo --provider fake --limit 32 --html-output artifacts\dashboard-demo.html
uv run maf-outcome-economics dashboard --database data\dashboard-demo.db --port 8510
```

Leave this dashboard running in its own PowerShell window. It reads
`data\dashboard-demo.db`, not the accumulated live telemetry database, so
the visual story stays balanced and repeatable:

* `MONITOR` governance decision because all gates pass but costs are still
  estimated.
* `31` verified treatment outcomes.
* About `27.5%` token-efficiency improvement.
* About `27%` lower cost per verified outcome.
* `69%` fewer review calls.
* `100%` of useful corrections retained.
* `81%` of no-change review tokens removed.
* Review-token consumption reduced from `3,200` to `1,000` tokens.

In a second PowerShell window, run the live demo command for Clip 3. This
window can use the default `data\outcomes.db`; it does not affect the sample
dashboard because the dashboard command above was launched with an explicit
database path:

```powershell
uv run maf-outcome-economics demo --provider live --limit 3
uv run maf-outcome-economics demo-scenarios
```

The live command proves real Azure OpenAI execution, trace capture, and token
usage. `demo-scenarios` refreshes the scenario-comparison asset:

```text
artifacts/hackathon-live-demo.html
artifacts/demo-scenarios.html
```

Use the terminal output for the live-proof clip and the sample dashboard for
the readable executive metric clips. Do not mix the two in narration: say the
terminal proves execution, and the dashboard shows a curated representative
portfolio of the same measurement framework.

> [!NOTE]
> `uv run maf-outcome-economics demo --provider live --limit 3` still uses the
> active live telemetry database and may return `STOP`, `OPTIMIZE`, or
> `MONITOR` depending on the real measured output from that run. That is fine.
> Clip 3 uses the terminal only to prove that real Azure OpenAI execution,
> traces, and tokens exist. Clips 5 through 7 use the separate sample dashboard
> database so the executive metric story is stable, credible, and readable.

> [!IMPORTANT]
> Use fictional data only. Hide notifications, account details, endpoints,
> secrets, and unrelated browser tabs before recording.

## Step 2: Prepare the Screen

1. Open `http://localhost:8510` (the sample dashboard) in one browser tab.
2. Open `artifacts/demo-scenarios.html` in another tab, used only for the
   `SCALE` / `OPTIMIZE` / `STOP` scenario comparison in Clip 7.
3. Keep the live-demo PowerShell window available for Clip 3.
4. Set browser zoom to `100%` at 1920 x 1080. Confirm
   **Executive Decision Dashboard** is visible and **Executive overview** is
   selected. Leave **Governance & reviews** and **Evidence detail** closed.
   Confirm Section 1 fills the opening frame and one scroll reveals the full
   Section 2 waste-reduction and governance view.
5. Increase the PowerShell font size.
6. Enable Windows Do Not Disturb.
7. Record at 1920 x 1080 with a 16:9 aspect ratio.
8. Keep personal bookmarks and desktop icons out of view.

### Capture Supporting Screenshots

Screenshots strengthen the submission when they prove the product is working
rather than decorate the idea. Capture a fresh live dashboard screenshot
before recording the video clips, while the dashboard is already staged. The
other supporting images are pre-built and ready to attach to the submission:

* A live dashboard screenshot showing the `MONITOR` decision, verified
  outcomes, cost per verified outcome, token-efficiency improvement,
  novelty-and-waste comparison, and governance flow
* [`artifacts/old-way-vs-new-way.png`](artifacts/old-way-vs-new-way.png) — the
  best single thumbnail/inspiration image: AI activity metrics side by side
  with verified outcome economics from the same run
* [`artifacts/architecture-diagram.png`](artifacts/architecture-diagram.png) —
  Azure OpenAI, Microsoft Agent Framework, OpenTelemetry, SQLite evidence
  storage, generic connectors, and the deterministic governance engine
* [`artifacts/scenario-flow.png`](artifacts/scenario-flow.png) — support-ticket
  triage moving from AI execution to independent route verification and
  outcome-adjusted token accounting
* [`artifacts/token-waste-funnel.png`](artifacts/token-waste-funnel.png) — a
  token track showing primary work, useful review, harmful review,
  non-contributing review, and the tokens avoided by confidence-gating
* [`artifacts/governance-flow-static.png`](artifacts/governance-flow-static.png)
  — a static, captioned export of the live governance cascade for embedding
  in the README or slides
* [`artifacts/decision-matrix.png`](artifacts/decision-matrix.png) — the
  SCALE / OPTIMIZE / STOP comparison table proving one engine reaches three
  different verdicts from three different evidence sets

Avoid generic AI artwork. The best images are product screenshots, metric
callouts, and simple diagrams that prove OutcomeMeter measures trusted
business value instead of raw model activity.

### Dashboard Recording Focus Path

Keep the **Executive overview** tab selected for every dashboard clip. Use one
deliberate scroll between the two screen-share sections. Do not make small
incremental scroll movements.

1. Before recording, expand the sidebar, confirm
   `data\dashboard-demo.db`, click **Refresh now**, and collapse the sidebar.
   Start recording only after the sidebar closes so the captured frame matches
   the clean Section 1 opening view.
2. Hold on the governance recommendation and four KPI cards for 3 seconds.
   Point once to `31` **Verified outcomes**, `0.0007 USD`
   **Cost / verified outcome**, `0.0088 USD` **Net savings vs. control**, and
   `27.5%` **Token efficiency gain**.
3. Move left to right across the three charts for 7 seconds. Pause on the
   exact chart headlines: `Cost per outcome · 27% lower`,
   `Human reviews · 69% lower`, and `Tokens per outcome · 28% lower`.
4. Hold on the three **Why it matters** cards for 3 seconds. Keep the pointer
   below the text so it remains readable.
5. Scroll once until **Section 2: Novelty and waste reduction** is at the top
   of the frame. Stop scrolling before moving the pointer.
6. Hold the complete Section 2 view for 10 seconds. Focus on the three pills
   (`100%`, `81%`, and `69%`), the large `4` useful-corrections card, and the
   large `22` no-change-reviews card. Trace the control bar (`3,200` tokens)
   to the shorter treatment bar (`1,000` tokens).
7. Finish on the governance flow for 8 seconds. Move from **Evidence** through
   **Trust**, **Value**, **Tokens**, and **Waste** to `MONITOR`. Hover over
   **Trust**, then **Value**, long enough for each gate rationale to appear.
   **Text overlay (added in editing, not narrated):** "Trust ✓ Value ✓ —
   savings proven, not assumed." Place it near the Trust/Value boxes and fade
   it out before the pointer moves to `MONITOR`.
8. Keep pointer movement direct. Do not circle values, open a secondary tab,
   add another scroll, or leave a tooltip covering the next metric.

> [!TIP]
> Record one clean 45-to-50-second two-section dashboard take, then reuse crops
> for Clips 5 through 7. This preserves visual continuity and avoids repeating
> the refresh or scroll transition.

## Step 3: Record Eight Short Visual Clips

In Clipchamp, select **Create a new video**, choose 16:9, then use
**Record & create > Screen**. Record each clip separately without narration.

### Clip 1: Title and Problem

Duration: 7 to 8 seconds

Create a title card:

```text
OutcomeMeter
From AI Activity to Verified Business Value

For leaders deciding which AI workflows to scale
```

This immediately establishes the customer and the decision OutcomeMeter enables.

### Clip 2: The Scenario You Are About to See

Duration: 9 to 10 seconds

If Slide 4 from [POWERPOINT_VIDEO_GUIDE.md](./POWERPOINT_VIDEO_GUIDE.md) is
already built, export that slide's animation as a clip and use it here.
Otherwise, create a simple text card in Clipchamp:

```text
The scenario: support-ticket triage

Incoming tickets -> category, priority, resolver group?
Wrong answer = wrong team, wrong priority, slower resolution

An AI agent decides the triage.
Tokens spent per ticket, checked against the known-correct answer.
```

Add three small icon labels near the bottom of the card, shown on screen only
and never spoken: `Invoice coding`, `Claims or security triage`, and
`Code review acceptance`. They tell the viewer this is one example of a
reusable pattern without adding a second spoken sentence.

This clip answers, before any command runs, what fictional workflow is about
to execute and why it is a fair test of tokens against a checkable outcome.

### Clip 3: Proving the Answer With a Golden Dataset

Duration: 8 to 9 seconds

If Slide 5 from [POWERPOINT_VIDEO_GUIDE.md](./POWERPOINT_VIDEO_GUIDE.md) is
already built, export that slide's animation as a clip and use it here.
Otherwise, create a simple two-column text card in Clipchamp:

```text
Ticket -> category, priority, resolver group, three-way match -> hidden
from the agent

Invoice -> AP ledger, three-way match, duplicate check -> hidden from
the agent

32 fictional tickets, three gold labels each. The agent never grades its
own work.
```

This clip answers, before the live command runs, how the "known-correct
answer" from Clip 2 is actually built and checked: a golden dataset the
agent never sees, not the agent's own self-assessment.

### Clip 4: Working Product

Duration in final edit: 15 to 18 seconds

Record part of this live command:

```powershell
uv run maf-outcome-economics demo --provider live --limit 3
```

Keep footage showing:

* `LIVE MODE`
* Baseline and optimized workflow execution
* Real trace identities and token counts
* Review invoked or skipped
* Deterministic acceptance

Trim model wait time and repeated output. This scene proves that the team made a
working product rather than only proposing an idea. Do **not** keep the final
governance decision from this live terminal clip if it conflicts with the
sample dashboard story; trim the clip after trace IDs, token counts, review
activity, and deterministic acceptance are visible. The dashboard clip is where
the executive decision is explained.

### Clip 5: Business Outcome Comparison

Duration: 22 to 24 seconds

Switch to the sample dashboard tab (`http://localhost:8510`). Use the opening
portion of the recording from the focus path above. Keep the full Executive
overview visible and focus on:

* `31` verified treatment outcomes
* `0.0007 USD` cost per verified outcome
* `0.0088 USD` estimated net savings versus control
* `27.5%` token-efficiency gain
* The three before-and-after charts showing lower cost per outcome, fewer
  human reviews, and fewer tokens per outcome

Move across the charts from left to right. Pause on each headline percentage,
then on its **Why it matters** card. Use only the Section 1 portion of the
recording for this clip.

### Clip 6: Review Waste and Token Efficiency

Duration: 18 to 20 seconds

Use the Section 2 portion of the same recording after the single scroll.
Keep the full **Novelty and waste reduction** panel legible and show these
measured results:

* `100%` of useful corrections retained
* `81%` of no-change review tokens removed
* `69%` reduction in total review tokens
* Control reduced from `3,200` review tokens to `1,000`
* `4` useful corrections preserved while `22` reviews with no measurable
  outcome change were eliminated

Trace the control and treatment bars once. The shorter treatment bar is the
visual proof: OutcomeMeter separates assurance that changes an outcome from
review consumption that adds no measured value.

### Clip 7: Executive Governance

Duration: 20 seconds

Use a crop of the same recording centered on the governance flow. Show
`11/11 GATES PASSED`, then move in order through **Evidence**, **Trust**,
**Value**, **Tokens**, and **Waste** before landing on `MONITOR`. Hover over
**Trust** to expose quality, safety, and compliance, then hover over **Value**
to expose business outcome, unit cost, and net value. Add a text overlay in
editing (not narrated): "Trust ✓ Value ✓ — savings proven, not assumed."
`MONITOR` means the evidence is positive but costs are still estimated rather
than billing-reconciled.

Then switch briefly to `artifacts/demo-scenarios.html` and show `SCALE`,
`OPTIMIZE`, and `STOP`.

Emphasize that quality and safety override savings. A cheaper but unsafe
workflow is stopped.

### Clip 8: Scale and Closing

Duration: 14 to 15 seconds

Create one text card:

```text
One governance core
Support | Finance | Claims | Security | Software Delivery

Measure what AI spends.
Verify what it achieves.
Decide what to scale.
```

## Step 4: Record This Narration

This script is approximately 250 words, including the 35-word scenario line
that matches Slide 4 and the 25-word golden-dataset line that matches Slide 5
of [POWERPOINT_VIDEO_GUIDE.md](./POWERPOINT_VIDEO_GUIDE.md). At a clear
executive pace of 130 to 140 words per minute, it runs about 1 minute 47
seconds to 1 minute 55 seconds. The remaining time supports readable pauses,
transitions, and the closing card.

Record each paragraph as a separate Clipchamp voiceover so it can be aligned and
trimmed independently.

### 0:00-0:08: Inspiration and Customer

> Enterprise leaders can see AI spend, but not whether it created trusted
> business value. OutcomeMeter decides what to scale, improve, or stop.

### 0:08-0:18: The Scenario

> Ticket triage happens in every support org, and wrong routing wastes time.
> An AI decides it against a known-correct answer, so tokens and outcomes
> compare cleanly. The same pattern fits any short, checkable decision.

This is the same 35-word line used for Slide 4's narration. Do not add the
on-screen domain labels (invoice coding, claims or security triage, code
review acceptance) to the voiceover; they stay visual-only so this beat does
not grow past its 9-to-10-second target.

### 0:18-0:26: Proving the Answer

> Tickets carry three hidden gold labels the agent never sees; invoices are
> checked against the ledger. Either way, the agent never grades its own
> work.

This is the same 25-word line used for Slide 5's narration. It answers, before
the live command runs, how the "known-correct answer" from the previous beat
is actually built and checked.

### 0:26-0:41: Make Something

> This is a working product built with Microsoft Agent Framework and Azure
> OpenAI. It runs baseline and optimized workflows while OpenTelemetry captures
> real traces; the dashboard shows the same measurement pattern on a clean
> representative portfolio.

### 0:41-1:05: Business Value

> OutcomeMeter connects that telemetry to independent business evidence:
> quality, cost, and tokens per verified outcome, not per model call. That
> stops a cheaper, lower-quality workflow from looking successful, and gives
> leaders credible unit economics.

### 1:05-1:25: Novelty and Waste Reduction

> OutcomeMeter preserves every useful correction while removing 81 percent of
> review tokens that produced no outcome change. The sample cuts total review
> consumption by 69 percent, from 3,200 to 1,000 tokens, without weakening
> assurance for critical work.

### 1:25-1:45: Executive Decision

> A deterministic governance engine recommends monitor here, scale, optimize,
> stop, or collect more evidence. Quality, safety, compliance, and business
> outcomes are evaluated before economics; savings never override failed
> assurance.

### 1:45-1:58: Feasibility and Close

> The framework-neutral core can extend from support and invoices to claims,
> security, and software delivery through new adapters. OutcomeMeter turns AI
> telemetry into accountable investment decisions. Measure what AI spends.
> Verify what it achieves. Decide what to scale.

## Step 5: Assemble in Clipchamp

1. Add the eight clips to the timeline in storyboard order.
2. Trim command wait time, repeated output, silence, and pointer movement.
3. Add each narration paragraph below its matching visual.
4. Adjust visual length to the narration. Do not speed up the voice.
5. Use direct cuts and short fades only for the opening and closing cards.
6. Add four short on-screen labels:
   * Verified outcome
   * Tokens per verified outcome
   * Non-contributing review
   * Assurance before economics
7. Keep labels clear of report values.
8. Use one typeface and one accent color throughout.
9. Do not add feature lists, architecture detail, or background music that
   competes with narration.

## Step 6: Add Captions

Use **Captions > Transcribe media** and review every line. Correct these terms:

* OutcomeMeter
* Microsoft Agent Framework
* Azure OpenAI
* OpenTelemetry
* Tokenomics
* Dashboard

Keep captions to one or two lines and ensure they do not cover product metrics.

## Step 7: Rubric Review

Watch the edited video and answer each question:

* Inspiration: Does the opening make verified value feel like a fresh way to
  govern AI?
* Business Value: Does the video connect waste reduction and unit economics to
  better investment decisions?
* Customer Focus: Are enterprise leaders and process owners clearly identified?
* Feasibility: Does the video show a reusable architecture and pathway to more
  business domains?
* Make Something: Is real execution visible in the terminal, and does the
  dashboard visibly render the refreshed SQLite evidence?

If a criterion is unclear, strengthen its existing scene rather than adding
another scene.

## Step 8: Eligibility and Privacy Check

Before exporting, confirm:

* Final timeline is under 2:00, preferably 1:50 to 1:55
* The primary customer is named in the first 8 seconds
* The scenario clip explains the fictional workflow before the working
  product clip begins
* The golden-dataset clip explains how the "known-correct answer" is built,
  right before the working product clip begins
* The working product appears by 0:26
* Business value is stated before technical architecture
* Fictional data is identified
* Dashboard tab is using `data\dashboard-demo.db`
* Dashboard shows `MONITOR`, `31` verified treatment outcomes, `0.0007 USD`
  cost per verified outcome, and `27.5%` token-efficiency gain
* Waste reduction shows `100%` useful corrections retained, `81%` of no-change
  review tokens removed, and review consumption reduced from `3,200` to
  `1,000` tokens
* One scroll reveals the full Section 2 waste and governance view
* Estimated costs are not described as reconciled savings
* Quality and safety visibly override favorable economics
* No secrets, endpoints, account identifiers, or notifications are visible
* Captions are correct and readable

## Step 9: Export and Submit

1. Select **Export > 1080p HD**.
2. Save the file as `OutcomeMeter-Executive-Challenge.mp4`.
3. Play the exported MP4 from beginning to end.
4. Confirm the actual file duration is less than 2 minutes.
5. Confirm audio synchronization and metric readability.
6. Upload the video to the Hackathon project page before
   **September 21 at 11:59 PM Pacific Time**.
7. Select the intended Executive Challenge. Projects submitted as `Other` are
   not eligible for Executive Challenge awards.

## Final Checklist

* [ ] Video duration is below 2 minutes
* [ ] Primary customer is explicit
* [ ] Scenario clip runs before the live terminal in every recording
* [ ] Golden-dataset clip runs after the scenario clip and before the live
      terminal, explaining how the answer is graded
* [ ] Business value is clear
* [ ] Live working product is visible
* [ ] Before recording, the sample dashboard is refreshed from
      `data\dashboard-demo.db`, then captured with the sidebar collapsed
* [ ] Dashboard values show `MONITOR`, `31` **Verified outcomes**,
      `0.0007 USD` **Cost / verified outcome**, `0.0088 USD`
      **Net savings vs. control**, and `27.5%` **Token efficiency gain**
* [ ] Waste reduction shows `100%` useful corrections retained, `81%` of
      no-change review tokens removed, and `69%` fewer review tokens
* [ ] One deliberate scroll moves cleanly from Section 1 to the complete
      Section 2 waste and governance view
* [ ] Novel review-waste insight is demonstrated
* [ ] Governance decision is readable
* [ ] Feasibility across domains is stated
* [ ] Fictional data and estimated costs are represented accurately
* [ ] Captions and privacy are checked
* [ ] 1080p MP4 is reviewed before upload
