---
title: OutcomeMeter Story-Format PowerPoint Guide
description: Step-by-step guide for building the Priya Nair narrative slides that pair with STORY_DEMO.md, combined with the same OutcomeMeter demo recordings
ms.date: 2026-09-17
ms.topic: tutorial
keywords:
  - OutcomeMeter
  - PowerPoint
  - demo video
  - animation
  - hackathon
  - story
estimated_reading_time: 12
---

## Why This Version Exists

[POWERPOINT_VIDEO_GUIDE.md](../POWERPOINT_VIDEO_GUIDE.md) builds five
concept-first slides (measurement gap, verified-outcome equation, governance
gates, scenario, golden dataset). This file is an **alternate slide deck** that
teaches the exact same five ideas, in the exact same order, using the exact
same colors, fonts, captions, and source-code references — but every slide
opens through **Priya Nair, VP of Customer Support Operations**, deciding
whether to scale her team's AI ticket-triage pilot. It pairs with
[STORY_DEMO.md](./STORY_DEMO.md) the same way
[POWERPOINT_VIDEO_GUIDE.md](../POWERPOINT_VIDEO_GUIDE.md) pairs with
[DEMO.md](../DEMO.md).

Use this guide instead of [POWERPOINT_VIDEO_GUIDE.md](../POWERPOINT_VIDEO_GUIDE.md)
if the narrative framing lands better with judges, or build both decks and
compare. Nothing in [POWERPOINT_VIDEO_GUIDE.md](../POWERPOINT_VIDEO_GUIDE.md),
[DEMO.md](../DEMO.md), or `artifacts/` is modified by this file.

> [!IMPORTANT]
> Slides 4 and 5 still must be built and shown before any live demo command
> runs, exactly as in [POWERPOINT_VIDEO_GUIDE.md](../POWERPOINT_VIDEO_GUIDE.md).
> The audience must know what fictional scenario Priya is looking at, and how
> her dashboard's "known-correct answer" gets checked, before the terminal
> appears.

## The Character

**Priya Nair, VP of Customer Support Operations.** Two weeks ago her team
turned on an AI agent to triage incoming support tickets. This deck follows
one Monday morning where she has to decide whether it is safe and valuable
enough to scale. Every slide is a beat in that same 10-minute decision — the
underlying product concepts are unchanged from
[POWERPOINT_VIDEO_GUIDE.md](../POWERPOINT_VIDEO_GUIDE.md).

Two ready-made stills are already rendered in
[story-demo/assets/](./assets) and can be inserted directly, with no drawing
required:

* [`assets/priya-title-card.png`](./assets/priya-title-card.png) — a cold-open
  hero image for Slide 1 or the opening title slide: Priya's persona card next
  to her dashboard, showing the `MONITOR` verdict she is about to reason
  through.
* [`assets/priya-decision-memo.png`](./assets/priya-decision-memo.png) — a
  decision-memo mockup for the closing slide: the message Priya would send
  her team after deciding, with the same verified numbers and four concrete
  next steps.

## Building Priya as a Human Figure in PowerPoint

Judges respond to a face, but this project avoids photorealistic AI-generated
people (inconsistent likeness across slides, and it distracts from the
product). Use one of these four approaches instead, in order of recommended
effort-to-payoff:

### Option A — Fluent/People Icons (fastest, recommended default)

1. Go to **Insert > Icons** and search `person` or `business person`.
2. PowerPoint's built-in icon set includes several flat, single-color human
   silhouettes (standing figure, person-at-desk, person-with-speech-bubble).
   These are vector, recolor cleanly to the deck's palette, and never look
   like a specific real person.
3. Recolor to `#44d7cf` (cyan) or `#263238` (charcoal) via
   **Graphics Format > Graphics Fill** to match the deck.
4. Use the same icon for Priya throughout the deck for visual consistency —
   do not swap styles between slides.
5. This is exactly the technique used to build
   [`assets/priya-title-card.png`](./assets/priya-title-card.png) and
   [`assets/priya-decision-memo.png`](./assets/priya-decision-memo.png): both
   use a simple two-shape SVG silhouette (a circle for the head, a rounded
   arc for the shoulders), not a photo or generated portrait.

### Option B — PowerPoint Designer Personas (fast, more polish)

1. Type Priya's name, role, and a short quote into a text placeholder.
2. Open **Design > Design Ideas**. PowerPoint frequently suggests a
   people-and-quote layout using its own built-in silhouette or initials-badge
   art.
3. Accept a suggestion that uses a flat icon or initials badge, not a stock
   photo, to stay consistent with the deck's illustrated style.
4. Recolor the accepted layout's accent color to match the deck palette if
   Designer does not do so automatically.

### Option C — Simple Hand-Drawn Shapes (no add-ins, full control)

Recommended when Options A/B are unavailable or a custom pose is needed (for
example, Priya pointing at a chart):

1. Draw a circle (**Insert > Shapes > Oval**) for the head.
2. Draw a rounded rectangle or a freeform arc beneath it for the
   shoulders/body — **Insert > Shapes > Freeform** lets you trace a simple
   silhouette in a few clicks.
3. Group the shapes (`Ctrl+G`) and name the group `Persona_Priya`.
4. Recolor both shapes to the same accent color (cyan or charcoal) so the
   figure reads as an icon, not an attempted likeness.
5. Reuse the exact same grouped shape across every slide where Priya appears,
   only changing its position or adding a small prop (a coffee cup icon, a
   laptop icon) if a slide needs a different pose.

### Option D — Stock Icon Libraries (if organizational licensing allows)

1. If your organization has a licensed stock-icon or illustration library
   (e.g., a Microsoft 365 content pack, an internal brand kit, or a
   licensed flat-illustration set), search for `business person`,
   `executive`, or `dashboard review` and insert a flat/illustrated
   (not photorealistic) figure.
2. Recolor to the deck palette if the library supports it.
3. Confirm the license permits use in a hackathon submission video before
   using it — when in doubt, use Option A or C instead.

> [!TIP]
> Whichever option is used, keep Priya visually identical across every slide
> and both story files (`STORY_DEMO.md` narration and this deck). A
> consistent, simple icon reads as intentional design; a different face or
> style per slide reads as inconsistent production value.

> [!IMPORTANT]
> Do not use a real photo of a real person, a photorealistic AI-generated
> face, or any image that could be mistaken for an actual employee. Priya
> Nair is an explicitly fictional persona used only to frame the narration —
> keep her visual representation abstract (icon, silhouette, or initials
> badge) to reinforce that.

## Presentation Setup

Identical to
[POWERPOINT_VIDEO_GUIDE.md > Presentation Setup](../POWERPOINT_VIDEO_GUIDE.md#presentation-setup).
Reuse the same widescreen 16:9 canvas, white background, single font, color
palette, and animation discipline:

* Charcoal: `#263238`
* Green: `#18864B`
* Amber: `#D98200`
* Red: `#C62828`
* Light gray: `#ECEFF1`

Use only **Appear**, **Fade**, **Wipe**, and **Motion Paths**. Keep the
Animation Pane and Selection Pane open while building, and match animation cue
count to target duration exactly as described in the base guide — group
related objects with `Ctrl+G` rather than animating every icon individually on
short slides.

Slides 1-3 introduce Priya's situation and must stay below 25 seconds
combined, matching the base guide's budget. Slide 4 stays at 12-14 seconds and
Slide 5 stays at 8-9 seconds, immediately before the live demo starts.

## Slide 1: Priya's Monday Morning Problem

Target duration: 6 to 7 seconds.

### Build the Slide

1. Add this title at the top:

   ```text
   Priya can see what the AI spends. Not what it's worth.
   ```

2. Go to **Insert > Shapes > Rounded Rectangle**.
3. Draw a box on the left and type `AI Triage Workflow`.
4. Set the fill to light gray and the outline to charcoal.
5. Go to **Insert > Icons**, search for `coin`, and add three coin icons to
   the left of the workflow box.
6. Insert a right-facing arrow between the coins and workflow.
7. Add another right-facing arrow after the workflow box.
8. Insert a document icon on the right.
9. Add a large text box containing `?` above the document.
10. Add `Tokens and spend` below the coins.
11. Add `Trusted routing decision?` below the document.
12. Add a small silhouette icon in the top-right corner labeled `Priya, VP
    Customer Support Ops` to establish whose desk this is. Build the
    silhouette using
    [Option A or C](#building-priya-as-a-human-figure-in-powerpoint) above —
    a simple recolored person icon or two-shape circle-plus-arc, matching the
    persona card already rendered in
    [`assets/priya-title-card.png`](./assets/priya-title-card.png).
13. Align and distribute the flow objects exactly as in
    [POWERPOINT_VIDEO_GUIDE.md Slide 1](../POWERPOINT_VIDEO_GUIDE.md#slide-1-the-measurement-gap).

> [!TIP]
> As a full-slide alternative to building Slide 1 from individual shapes,
> insert [`assets/priya-title-card.png`](./assets/priya-title-card.png)
> directly as the slide background or a large centered image, then animate
> only the title text box on top of it with **Fade**. This reaches the same
> 6-to-7-second target with fewer objects to animate.

The finished flow should resemble:

```text
Tokens and spend -> AI Triage Workflow -> Trusted routing decision?
```

### Name the Objects

* `PS1_Title`
* `PS1_Persona`
* `PS1_Coins`
* `PS1_Arrow_In`
* `PS1_Workflow`
* `PS1_Arrow_Out`
* `PS1_Document`
* `PS1_Question`

### Animate the Slide

1. Animate `PS1_Title` with **Fade**, **Start: With Previous**, `0.4` seconds.
2. Animate `PS1_Persona` with **Fade**, **Start: With Previous**, immediately
   after the title so the viewer knows whose morning this is right away.
3. Group every remaining object (`PS1_Coins`, `PS1_Arrow_In`, `PS1_Workflow`,
   `PS1_Arrow_Out`, `PS1_Document`, `PS1_Question`) and animate the group with
   **Appear**, **Start: After Previous**.

### Narration

> Every Monday, Priya has to decide which AI workflows earned the right to
> keep running. She can see tokens and spend. She can't yet see whether the
> AI actually got it right.

## Slide 2: The Question She Actually Needs Answered

Target duration: 8 to 9 seconds.

### Build the Slide

Reuse the same fraction layout as
[POWERPOINT_VIDEO_GUIDE.md Slide 2](../POWERPOINT_VIDEO_GUIDE.md#slide-2-the-outcomemeter-measure)
exactly — same icons, same captions, same source-code grounding — with one
title change and one closing line change:

1. Title:

   ```text
   Priya needs the verified outcome in the denominator
   ```

2. Build the numerator (`Total tokens and cost`, caption `human + platform +
   model spend`), the fraction line, and the denominator
   (`Independently verified outcomes`, caption `category, priority, resolver
   group all match the golden record`) identically to the base guide.
3. Add the result arrow and box: `Trusted unit economics`.
4. Footer:

   ```text
   The AI does not grade its own work — and neither does Priya, on
   instinct alone.
   ```

The numerator and denominator are the same literal `CostEntry` sums and
`RoutingVerificationResult` matches described in
[POWERPOINT_VIDEO_GUIDE.md Slide 2](../POWERPOINT_VIDEO_GUIDE.md#slide-2-the-outcomemeter-measure);
only the framing sentence around them changes here.

### Name and Group the Objects

Same grouping and naming pattern as the base guide, with a `PS2_` prefix:
`PS2_Title`, `PS2_Numerator`, `PS2_Fraction_Line`, `PS2_Denominator`,
`PS2_Magnifier`, `PS2_Check`, `PS2_Result_Arrow`, `PS2_Result_Box`,
`PS2_Footer`.

### Animate the Slide

Identical sequence to
[POWERPOINT_VIDEO_GUIDE.md Slide 2](../POWERPOINT_VIDEO_GUIDE.md#slide-2-the-outcomemeter-measure):
title fades with previous, the fraction group appears, the magnifier-and-check
group appears, then the result group appears last.

### Narration

> OutcomeMeter gives Priya tokens and cost per verified outcome, not per model
> call — so a cheaper but wrong answer can't quietly look like a win.

## Slide 3: Her Non-Negotiables, in Order

Target duration: 8 to 9 seconds.

### Build the Gates and Decisions

Reuse the exact gate row and decision row from
[POWERPOINT_VIDEO_GUIDE.md Slide 3](../POWERPOINT_VIDEO_GUIDE.md#slide-3-assurance-before-economics) —
`QUALITY`, `SAFETY`, `ECONOMICS` gates with the same threshold captions
(`quality score >= minimum`, `critical recall >= minimum`, `cost per outcome
<= budget`), the same `SCALE` / `OPTIMIZE` / `STOP` color-coded decision boxes,
and the same `GovernanceEngine.evaluate` grounding. Change only the title and
footer:

1. Title:

   ```text
   Priya doesn't set the threshold. The evidence does.
   ```

2. Footer:

   ```text
   Savings never override failed assurance — even when it's her budget.
   ```

### Name the Objects

Same naming pattern as the base guide, with a `PS3_` prefix:
`PS3_Title`, `PS3_Quality`, `PS3_Quality_Caption`, `PS3_Quality_Check`,
`PS3_Arrow_Quality_Safety`, `PS3_Safety`, `PS3_Safety_Caption`,
`PS3_Safety_Check`, `PS3_Arrow_Safety_Economics`, `PS3_Economics`,
`PS3_Economics_Caption`, `PS3_Branches`, `PS3_Scale`, `PS3_Optimize`,
`PS3_Stop`, `PS3_Footer`.

### Animate the Gates and Decisions

Identical sequence to
[POWERPOINT_VIDEO_GUIDE.md Slide 3](../POWERPOINT_VIDEO_GUIDE.md#slide-3-assurance-before-economics):
title fades with previous, the full gate row appears as one group, the
decision row appears as one group, the footer fades in last.

### Narration

> Quality and safety clear first, before a single dollar of savings counts.
> Then the same engine reaches one of three verdicts: scale, optimize, or
> stop.

## Slide 4: The Pilot on Priya's Desk

Target duration: 12 to 14 seconds. Build and show this slide before running
any live demo command.

This slide still answers the same three questions as
[POWERPOINT_VIDEO_GUIDE.md Slide 4](../POWERPOINT_VIDEO_GUIDE.md#slide-4-the-scenario-you-are-about-to-see):
what real-world situation is being measured and why does it hurt, why is it a
good testbed for tokens-versus-verified-outcomes, and why is it one instance
of a reusable pattern. Only the framing sentence and one added persona label
change.

### Build the Slide

1. Title:

   ```text
   What Priya's pilot actually does
   ```

2. Build the identical ticket-flow row, pain-point row, agent-and-tokens row,
   and reusable-pattern icon row described in
   [POWERPOINT_VIDEO_GUIDE.md Slide 4](../POWERPOINT_VIDEO_GUIDE.md#slide-4-the-scenario-you-are-about-to-see) —
   `Incoming tickets`, `Category? Priority? Resolver group?`,
   `Wrong team, wrong priority, slower resolution`, `An AI agent decides the
   triage`, `Tokens spent per ticket`, `Checked against the known-correct
   answer`, and the receipt/shield/code icon row labeled `Invoice coding`,
   `Claims or security triage`, `Code review acceptance`.
3. Add a small caption under the ticket-flow row:

   ```text
   This is the pilot Priya's team turned on two weeks ago.
   ```

4. Keep the same reusable-pattern footer:

   ```text
   Swap the connector, keep the same measurement and governance core.
   ```

### Name the Objects

Same naming pattern as the base guide, with a `PS4_` prefix (`PS4_Title`,
`PS4_Tickets`, `PS4_Question`, `PS4_Arrow_Warning`, `PS4_Warning`,
`PS4_Caption`, `PS4_Agent`, `PS4_TokenCoins`, `PS4_GoldCheck`,
`PS4_Relevance_Caption`, `PS4_GeneralIcons`, `PS4_GeneralIcons_Labels`,
`PS4_General_Caption`, `PS4_Footer`).

### Animate the Slide

Identical cue-by-cue sequence to
[POWERPOINT_VIDEO_GUIDE.md Slide 4](../POWERPOINT_VIDEO_GUIDE.md#slide-4-the-scenario-you-are-about-to-see).

### Narration

> Priya's team's AI agent has been deciding ticket category, priority, and
> resolver group for two weeks. Wrong routing means slower resolution, so
> before she trusts it, tokens and outcomes need to compare cleanly.

This is 34 words, matching the base guide's 12-to-14-second budget. Do not
lengthen it — the on-slide captions and icon labels carry the rest.

### How This Generalizes

Identical to
[POWERPOINT_VIDEO_GUIDE.md > How This Generalizes](../POWERPOINT_VIDEO_GUIDE.md#how-this-generalizes):
ticket triage is a stand-in for any short, checkable AI decision; only the
connector layer changes between scenarios; the governance core and contracts
stay scenario-agnostic. Frame follow-up questions the same way — Priya's
pilot is one instance, not the whole product.

### When to Use This Slide

Same guidance as
[POWERPOINT_VIDEO_GUIDE.md > When to Use This Slide](../POWERPOINT_VIDEO_GUIDE.md#when-to-use-this-slide):
place it immediately after Slide 3 and before the demo-transition card in
[STORY_DEMO.md](./STORY_DEMO.md), or show it alone right before running a live
demo command in a live presentation.

## Slide 5: How Priya Knows the Answer Is Actually Right

Target duration: 8 to 9 seconds. Build and show this slide immediately after
Slide 4 and before the live demo starts.

Reuse the identical two-column golden-dataset layout, schema example, and
`src/maf_outcome_economics/scenarios/ticket/seed.py` /
`src/maf_outcome_economics/scenarios/invoice/connector.py` grounding from
[POWERPOINT_VIDEO_GUIDE.md Slide 5](../POWERPOINT_VIDEO_GUIDE.md#slide-5-proving-the-answer-with-a-golden-dataset).
Change only the title and footer framing.

### Build the Slide

1. Title:

   ```text
   Before Priya trusts any of it
   ```

2. Build the ticket column (icon, tag, padlock) and invoice column (icon,
   ledger, padlock) exactly as in the base guide, including the same JSON
   schema example and plain-language explanation.
3. Footer:

   ```text
   Neither the agent, nor Priya, grades the agent's own work.
   ```

### Name the Objects

Same naming pattern as the base guide, with a `PS5_` prefix (`PS5_Title`,
`PS5_Ticket_Icon`, `PS5_Ticket_Tag`, `PS5_Ticket_Lock`, `PS5_Invoice_Icon`,
`PS5_Invoice_Ledger`, `PS5_Invoice_Lock`, `PS5_Footer`, `PS5_Schema_Example`).

### Animate the Slide

Identical sequence to
[POWERPOINT_VIDEO_GUIDE.md Slide 5](../POWERPOINT_VIDEO_GUIDE.md#slide-5-proving-the-answer-with-a-golden-dataset).

### Narration

> Every ticket carries a hidden, known-correct answer the agent never sees.
> It doesn't get to grade its own work — and neither does Priya, on instinct
> alone.

Roughly 25 words, matching the base guide's 8-to-9-second budget.

## Transition Into the Demo

Same transition card as
[POWERPOINT_VIDEO_GUIDE.md > Transition Into the Demo](../POWERPOINT_VIDEO_GUIDE.md#transition-into-the-demo),
with story-specific wording:

1. Set the slide background to charcoal.
2. Add this large white text:

   ```text
   Priya watches it run, live.
   ```

3. Add this smaller white text:

   ```text
   Baseline versus optimized
   ```

4. Apply **Fade** to both text boxes, `0.4`-second transition, then cut
   directly to the live terminal recording.

## Add Demo Clips in PowerPoint

Create one blank slide for each of these sections, following the exact
insert/trim workflow in
[POWERPOINT_VIDEO_GUIDE.md > Add Demo Clips in PowerPoint](../POWERPOINT_VIDEO_GUIDE.md#add-demo-clips-in-powerpoint):

* Live terminal execution (Priya watching it run)
* Live dashboard: is it worth it? (verified outcome comparison)
* Live dashboard: what did the reviewers catch? (review-token waste)
* Live dashboard: her verdict (governance decision)
* `SCALE`, `OPTIMIZE`, and `STOP` scenarios (what the engine would say
  otherwise)

Use the identical capture, trim, and dashboard focus-path steps as
[POWERPOINT_VIDEO_GUIDE.md > Record the Current Dashboard](../POWERPOINT_VIDEO_GUIDE.md#record-the-current-dashboard),
sourced from the same
`uv run maf-outcome-economics dashboard --database data\dashboard-demo.db --port 8510`
session and the same 45-to-50-second two-section take. No new recordings are
required — this deck reuses the same footage as the base guide.

Two optional story-specific cutaway stills, already rendered and requiring no
new recording, drop cleanly into these slides:

* [`artifacts/old-way-vs-new-way.png`](../artifacts/old-way-vs-new-way.png) —
  insert as a 1-to-2 second still on the "is it worth it?" slide, at the beat
  where Priya stops looking at raw activity metrics.
* [`artifacts/decision-matrix.png`](../artifacts/decision-matrix.png) — insert
  as a still immediately after the `MONITOR` verdict slide, showing the same
  engine reaching `SCALE` or `STOP` under different evidence.

### Add Metric Callouts

Identical technique and identical metric list to
[POWERPOINT_VIDEO_GUIDE.md > Add Metric Callouts](../POWERPOINT_VIDEO_GUIDE.md#add-metric-callouts):
green, `3 pt`, no-fill rectangles around `31` verified outcomes, `27%` lower
cost per outcome, `69%` fewer human reviews, `28%` lower tokens per outcome,
`81%` of no-change review tokens removed, `11/11` governance gates passed, and
`MONITOR`.

## Record Narration and Timings

Identical process to
[POWERPOINT_VIDEO_GUIDE.md > Record Narration and Timings](../POWERPOINT_VIDEO_GUIDE.md#record-narration-and-timings):
record from beginning with microphone only, pause before the demo transition,
review with **Slide Show > From Beginning**, and re-record individual slides
with **Record > From Current Slide** as needed.

## Closing Slide

1. Create a slide with a charcoal background.
2. Add `OutcomeMeter` in large white text.
3. Add this line above the standard three closing lines:

   ```text
   Priya's call: keep monitoring, reconcile real billing next cycle,
   then scale.
   ```

4. Add the same three closing lines as the base guide beneath it:

   ```text
   Measure what AI spends.
   Verify what it achieves.
   Decide what to scale.
   ```

5. Animate `OutcomeMeter` with **Fade**, then Priya's decision line with
   **Appear**, then each supporting line with **Appear** at `0.4`-second
   intervals.
6. Keep the completed closing slide visible for 3 seconds.

Optional cutaway: place
[`artifacts/architecture-diagram.png`](../artifacts/architecture-diagram.png)
behind or beside the closing text to reinforce that the same governance core
extends to other teams.

Alternatively, insert
[`assets/priya-decision-memo.png`](./assets/priya-decision-memo.png) as its
own slide immediately before this closing slide — it reads as the memo Priya
sends her team right after making the call, and its four next-step lines
mirror the closing slide's "measure, verify, decide" cadence without
repeating it word for word.

## Export the Final Video

Identical export steps to
[POWERPOINT_VIDEO_GUIDE.md > Export the Final Video](../POWERPOINT_VIDEO_GUIDE.md#export-the-final-video):
**File > Export > Create a Video**, **Full HD 1080p**, **Use Recorded Timings
and Narrations**, then review the exported MP4 end to end for readability,
narration sync, and duration before upload.

Suggested output file name, so both decks can be compared before submission:

```text
OutcomeMeter-Executive-Challenge-Story.pptx
OutcomeMeter-Executive-Challenge-Story.mp4
```

## Rubric Self-Check for the Story Deck

* Does Slide 1 establish Priya's accountability before any product concept
  is introduced?
* Does every slide title read as a beat in her decision rather than a
  restated feature?
* Do Slides 2 and 3 still teach the exact verified-outcome equation and gate
  order a technical judge would expect from
  [POWERPOINT_VIDEO_GUIDE.md](../POWERPOINT_VIDEO_GUIDE.md)?
* Does the closing slide make her decision, not just the governance core,
  the last thing the viewer remembers?

If the story framing on any slide ever forces a captioned number, threshold
name, or code reference to be paraphrased away from
[POWERPOINT_VIDEO_GUIDE.md](../POWERPOINT_VIDEO_GUIDE.md), revert that slide's
caption to the base guide's exact wording — narrative flavor never overrides
technical accuracy.
