---
title: OutcomeMeter PowerPoint Video Guide
description: Step-by-step guide for creating an animated concept introduction and combining it with OutcomeMeter demo recordings in PowerPoint
ms.date: 2026-09-16
ms.topic: tutorial
keywords:
  - OutcomeMeter
  - PowerPoint
  - demo video
  - animation
  - hackathon
estimated_reading_time: 12
---

## Objective

Use five animated PowerPoint slides to establish the OutcomeMeter concept
before showing the working product. Build every visual with standard PowerPoint
shapes, icons, and text. No generated artwork is required.

Slides 1 to 3 introduce the OutcomeMeter concept and must stay below 25 seconds
combined. Slide 4 introduces the specific scenario about to run, its pain
point, why it is a good testbed for token-and-outcome measurement, and how the
same pattern generalizes to other scenarios, adding 12 to 14 seconds. Slide 5
proves that both scenarios check the agent against a golden dataset it never
sees, adding 8 to 9 seconds immediately before the live demo starts. Their
purpose is to give the viewer a mental model; the demo recording remains the
primary visual proof.

> [!IMPORTANT]
> Always build and review Slides 4 and 5 (the scenario and golden-dataset
> explainers) before running any live demo command. Presenters and reviewers
> must know what fictional scenario is about to execute, and how its answer
> gets checked, before they see it execute.

## Presentation Setup

1. Open PowerPoint and select **Blank Presentation**.
2. Go to **Design > Slide Size > Widescreen (16:9)**.
3. Set the slide background to white.
4. Use one font throughout, such as Aptos, Segoe UI, or Arial.
5. Use these colors consistently:
   * Charcoal: `#263238`
   * Green: `#18864B`
   * Amber: `#D98200`
   * Red: `#C62828`
   * Light gray: `#ECEFF1`
6. Open **Animations > Animation Pane** and keep it open while building.
7. Open **Home > Arrange > Selection Pane** and rename objects as you create
   them.
8. Use only **Appear**, **Fade**, **Wipe**, and **Motion Paths**. Avoid bounce,
   spin, and heavy zoom effects.

> [!TIP]
> Keep important content out of the bottom 15 percent of each slide so captions
> do not cover it in the final video.

**Match animation cue count to target duration.** A slide under 10 seconds
has no room for one entrance per icon; group related objects with `Ctrl+G`
and use two to four grouped entrances total (title, then one entrance per
idea, then a footer if present). Reserve a longer, element-by-element build
for Slide 4, where the 12-to-14-second budget actually needs it. If
narration finishes before the last animation cue plays, the cue count is
still too high. Cut it further rather than slowing playback speed.

## Slide 1: The Measurement Gap

Target duration: 6 to 7 seconds.

### Build the Slide

1. Add this title at the top:

   ```text
   AI activity is visible. Business value is not.
   ```

2. Go to **Insert > Shapes > Rounded Rectangle**.
3. Draw a box on the left and type `AI Workflow`.
4. Set the fill to light gray and the outline to charcoal.
5. Go to **Insert > Icons**, search for `coin`, and add three coin icons to the
   left of the workflow box.
6. Insert a right-facing arrow between the coins and workflow by selecting
   **Insert > Shapes > Right Arrow**.
7. Add another right-facing arrow after the workflow box.
8. Insert a document icon on the right.
9. Add a large text box containing `?` above the document.
10. Add `Tokens and spend` below the coins.
11. Add `Trusted outcome?` below the document.
12. Select related objects and use **Shape Format > Align > Align Middle**.
13. Use **Shape Format > Align > Distribute Horizontally** to even the spacing.

The finished flow should resemble:

```text
Tokens and spend -> AI Workflow -> Trusted outcome?
```

### Name the Objects

Use the Selection Pane to assign these names:

* `S1_Title`
* `S1_Coins`
* `S1_Arrow_In`
* `S1_Workflow`
* `S1_Arrow_Out`
* `S1_Document`
* `S1_Question`

### Animate the Slide

This slide's narration is short, so use two animation cues, not seven. A
staggered build for every icon only fits when several seconds of talking
cover the reveal; at 6 to 7 seconds the whole flow must already be readable
while the title is still fading in.

1. Select `S1_Title` and choose **Fade**. Set **Start** to **With Previous**
   and **Duration** to `0.4` seconds.
2. Select every remaining object (`S1_Coins`, `S1_Arrow_In`, `S1_Workflow`,
   `S1_Arrow_Out`, `S1_Document`, `S1_Question`), group them with `Ctrl+G`,
   and choose **Appear**.
3. Set **Start** to **After Previous**, with no added delay, so the whole
   flow reads as one beat right after the title settles.

### Narration

> Enterprises can measure AI tokens and spend. But those numbers do not prove
> that the AI produced a correct and trusted business outcome.

## Slide 2: The OutcomeMeter Measure

Target duration: 8 to 9 seconds.

### Build the Slide

1. Add this title:

   ```text
   Put the verified outcome in the denominator
   ```

2. Select **Insert > Shapes > Line** and draw a horizontal line in the center.
   Hold `Shift` while drawing to keep the line straight.
3. Add coin and receipt icons above the line.
4. Add `Total tokens and cost` above the icons.
5. Add a small caption below it in 10-11 pt: `human + platform + model spend`.
6. Add a document icon below the line.
7. Add a magnifying-glass icon over the document.
8. Add a green checkmark beside the document.
9. Add `Independently verified outcomes` below these icons.
10. Add a small caption below it in 10-11 pt:
    `category, priority, resolver group all match the golden record`.
11. Insert a large right arrow to the right of the fraction.
12. Add a rounded rectangle after the arrow and type:

    ```text
    Trusted unit economics
    ```

13. Add this footer near the bottom of the slide:

    ```text
    The AI does not grade its own work.
    ```

The visual equation should resemble:

```text
     Total tokens and cost
     (human + platform + model spend)
--------------------------------  ->  Trusted unit economics
Independently verified outcomes
(category, priority, resolver group match)
```

This is not illustrative shorthand: the numerator is the literal sum of
`CostEntry` amounts across `CostCategory.HUMAN_PROCESSING`,
`CostCategory.PLATFORM`, and `CostCategory.MODEL`, and the denominator only
counts outcomes where an independent `RoutingVerificationResult` agrees with
the gold fields. Both come from
`src/maf_outcome_economics/domain/models.py`.
The two captions are shown on the slide but never spoken; they exist so a
technical reviewer can trace the equation to code without lengthening the
narration.

### Name and Group the Objects

1. Select the numerator label, its caption, coins, and receipt, then press
   `Ctrl+G`.
2. Name the group `S2_Numerator`.
3. Select the denominator label, its caption, and document, then press
   `Ctrl+G`.
4. Name the group `S2_Denominator`.
5. Keep the magnifying glass and checkmark separate for animation.
6. Name the remaining objects:
   * `S2_Title`
   * `S2_Fraction_Line`
   * `S2_Magnifier`
   * `S2_Check`
   * `S2_Result_Arrow`
   * `S2_Result_Box`
   * `S2_Footer`

### Animate the Slide

This slide's narration is short, so favor one entrance per idea instead of
one entrance per icon. Skip the motion path; a plain **Appear** on the
magnifier reads just as clearly at this pace and keeps the beat inside 8 to
9 seconds.

1. Animate `S2_Title` with **Fade** and start **With Previous**.
2. Group `S2_Numerator`, `S2_Fraction_Line`, and `S2_Denominator`; animate the
   group with **Appear**, **Start: After Previous**, so the whole fraction
   lands as one idea.
3. Group `S2_Magnifier` and `S2_Check`; animate the group with **Appear**,
   **Start: After Previous**, to show the verification step.
4. Group `S2_Result_Arrow`, `S2_Result_Box`, and `S2_Footer`; animate the
   group with **Appear**, **Start: After Previous**, to close the slide.

### Narration

> OutcomeMeter connects telemetry to independent business evidence. It measures
> tokens and cost per verified outcome, rather than merely per model call.

## Slide 3: Assurance Before Economics

Target duration: 8 to 9 seconds.

### Build the Gates

1. Add this title:

   ```text
   Assurance comes before economics
   ```

2. Insert one rounded rectangle across the middle of the slide.
3. Duplicate it twice with `Ctrl+D` so all three gates have identical sizes.
4. Label the gates `QUALITY`, `SAFETY`, and `ECONOMICS`.
5. Add a small caption in 10-11 pt under each gate label:
   `quality score >= minimum` under Quality, `critical recall >= minimum`
   under Safety, `cost per outcome <= budget` under Economics.
6. Add a checklist icon to the Quality gate.
7. Add a shield icon to the Safety gate.
8. Add a coin or receipt icon to the Economics gate.
9. Insert right arrows between the gates.
10. Set all three gate fills to light gray and their outlines to charcoal.
11. Add this footer:

    ```text
    Savings never override failed assurance.
    ```

These captions are not paraphrased for effect: each one is a real threshold
field on `OutcomeContract` (`minimum_quality_score`,
`minimum_critical_priority_recall`, `maximum_cost_per_accepted_outcome`),
checked in that exact order by `GovernanceEngine.evaluate` in
`src/maf_outcome_economics/governance/engine.py`. The captions are shown but
never spoken, so the narration stays inside its time budget.

### Build the Decisions

1. Add three smaller rounded rectangles on the right side of the slide.
2. Stack them vertically and label them `SCALE`, `OPTIMIZE`, and `STOP`.
3. Set the `SCALE` box fill to green with white text.
4. Set the `OPTIMIZE` box fill to amber with white text.
5. Set the `STOP` box fill to red with white text.
6. Select **Insert > Shapes > Lines > Elbow Arrow Connector**.
7. Connect the Economics gate to `SCALE`.
8. Duplicate the connector and connect it to `OPTIMIZE` and `STOP`.
9. Add a green checkmark over the Quality gate.
10. Duplicate the checkmark and place it over the Safety gate.

The finished layout should resemble:

```text
QUALITY -> SAFETY -> ECONOMICS --+-> SCALE
                                 +-> OPTIMIZE
                                 +-> STOP
```

### Name the Objects

Name the elements in the Selection Pane:

* `S3_Title`
* `S3_Quality`
* `S3_Quality_Caption`
* `S3_Quality_Check`
* `S3_Arrow_Quality_Safety`
* `S3_Safety`
* `S3_Safety_Caption`
* `S3_Safety_Check`
* `S3_Arrow_Safety_Economics`
* `S3_Economics`
* `S3_Economics_Caption`
* `S3_Branches`
* `S3_Scale`
* `S3_Optimize`
* `S3_Stop`
* `S3_Footer`

### Animate the Gates and Decisions

This slide's narration is short, so build the gate row and the decision row
as two grouped entrances instead of ten individual clicks.

1. Animate `S3_Title` with **Fade** and start **With Previous**.
2. Group `S3_Quality`, `S3_Quality_Caption`, `S3_Quality_Check`,
   `S3_Arrow_Quality_Safety`, `S3_Safety`, `S3_Safety_Caption`,
   `S3_Safety_Check`, `S3_Arrow_Safety_Economics`, `S3_Economics`, and
   `S3_Economics_Caption`; animate the group with **Appear**, **Start: After
   Previous**, so the whole gate row lands together.
3. Group `S3_Branches`, `S3_Scale`, `S3_Optimize`, and `S3_Stop`; animate the
   group with **Appear**, **Start: After Previous**, so the decision row
   lands as one beat.
4. Animate `S3_Footer` last with **Fade**, **Start: After Previous**.

### Narration

> Quality and safety are evaluated before economics. OutcomeMeter then produces
> a deterministic recommendation to scale, optimize, or stop.

## Slide 4: The Scenario You Are About to See

Target duration: 12 to 14 seconds. Build and show this slide before running
any live demo command, whether recording a video or presenting live.

This slide answers three questions for the audience: **what real-world
situation is this demo standing in for and why does it hurt, why does that
situation make a good testbed for measuring AI tokens against verified
outcomes, and why is this scenario just one example of a reusable pattern?**
Do not repeat the measurement gap, the verified-outcome equation, the
assurance gates, or any business-value, waste-reduction, governance, or
feasibility language. Those are covered by Slides 1 to 3 and by the demo
narration in [DEMO.md](./DEMO.md). The other-scenario examples are shown only
as short icon labels, never spoken; the narration stays about ticket triage
so it does not grow past its 12-to-14-second target. This slide must appear
immediately before the terminal is shown so no one has to guess what workflow
produced the numbers.

### Build the Slide

1. Add this title at the top:

   ```text
   The scenario: support-ticket triage
   ```

2. Insert a stack of three or four document or ticket icons on the left and
   label them `Incoming tickets`.
3. Add a question-mark icon to the right of the tickets and label it
   `Category? Priority? Resolver group?`.
4. Insert a right-facing arrow from the question mark to a small warning-sign
   icon on the right.
5. Label the warning icon `Wrong team, wrong priority, slower resolution`.
6. Add this caption beneath the ticket stack:

   ```text
   Every support organization triages tickets like this every day.
   ```

7. Below the pain-point row, add a robot or chat-bubble icon labeled
   `An AI agent decides the triage`.
8. Add a small coin-stack icon beside the robot labeled `Tokens spent per
   ticket`.
9. Add a checkmark-over-document icon beside the coins labeled `Checked
   against the known-correct answer`.
10. Add this caption beneath that row:

    ```text
    A short, well-defined decision with a right answer makes tokens and
    outcomes easy to compare, ticket by ticket.
    ```

11. Below that row, add three small icons in a horizontal row: a receipt, a
    shield, and a code bracket.
12. Add a small text label directly beneath each icon, one word or short
    phrase each, so the audience can read the other use cases without any
    narration:

    ```text
    Receipt icon -> Invoice coding
    Shield icon   -> Claims or security triage
    Code icon     -> Code review acceptance
    ```

13. Add this caption beneath the three labeled icons:

    ```text
    Any short AI decision with tokens in and a checkable outcome out fits the
    same pattern.
    ```

14. Add this footer near the bottom of the slide:

    ```text
    Swap the connector, keep the same measurement and governance core.
    ```

The finished layout should resemble:

```text
Incoming tickets -> Category? Priority? Resolver group? -> Wrong team,
                                                            wrong priority,
                                                            slower resolution

AI agent decides triage -> Tokens spent per ticket -> Checked against the
                                                       known-correct answer

Receipt icon      Shield icon           Code icon
Invoice coding    Claims or security    Code review
                   triage                acceptance
  Any short AI decision with tokens in and a checkable outcome out
```

### Name the Objects

Use the Selection Pane to assign these names:

* `S4_Title`
* `S4_Tickets`
* `S4_Question`
* `S4_Arrow_Warning`
* `S4_Warning`
* `S4_Caption`
* `S4_Agent`
* `S4_TokenCoins`
* `S4_GoldCheck`
* `S4_Relevance_Caption`
* `S4_GeneralIcons`
* `S4_GeneralIcons_Labels`
* `S4_General_Caption`
* `S4_Footer`

### Animate the Slide

1. Animate `S4_Title` with **Fade** and start **With Previous**.
2. Animate `S4_Tickets` with **Appear**.
3. Animate `S4_Question` with **Fade**.
4. Animate `S4_Arrow_Warning` with **Wipe > From Left**.
5. Animate `S4_Warning` with **Fade**.
6. Animate `S4_Caption` with **Fade**.
7. Animate `S4_Agent` with **Appear**.
8. Animate `S4_TokenCoins` with **Fade** immediately afterward.
9. Animate `S4_GoldCheck` with **Appear** immediately afterward.
10. Animate `S4_Relevance_Caption` with **Fade**.
11. Group the receipt, shield, and code icons, name the group
    `S4_GeneralIcons`, and animate it with **Appear**.
12. Group the three labels beneath those icons, name the group
    `S4_GeneralIcons_Labels`, and animate it with **Fade** immediately after
    `S4_GeneralIcons` so the icons and their labels read together.
13. Animate `S4_General_Caption` with **Fade**.
14. Animate `S4_Footer` last with **Fade**.

### Narration

> Ticket triage happens in every support org, and wrong routing wastes time.
> An AI decides it against a known-correct answer, so tokens and outcomes
> compare cleanly. The same pattern fits any short, checkable decision.

This narration is 35 words. At the same pace used for Slides 1 to 3, that
speaks in roughly 12 to 14 seconds. Do not lengthen it. The on-slide
captions carry the supporting detail visually, so the spoken line only needs
to hit the three points once.

### How This Generalizes

Ticket triage is a stand-in for a broader class of AI decisions, not the only
scenario OutcomeMeter measures. Use this framing when explaining the pattern,
whether in the slide narration above or in follow-up questions:

* The pattern that matters is **tokens in, a checkable outcome out**, not the
  specific ticket fields. Any workflow where an AI agent makes a short,
  bounded decision against a known-correct or independently verifiable answer
  fits the same shape.
* OutcomeMeter's contracts (`Ticket`, `OutcomeContract`, `WorkflowVariant`) and
  governance engine are scenario-agnostic. A new scenario adapter supplies its
  own domain objects and gold answers; the token capture, verification
  scoring, and `SCALE` / `OPTIMIZE` / `STOP` governance logic do not change.
* Only the connector layer changes between scenarios. Swapping ticket triage
  for invoice coding, insurance claims triage, security-alert classification,
  or code-review acceptance means writing a new adapter, not a new
  measurement framework.
* Slide 4 shows these other use cases as short icon labels
  (`S4_GeneralIcons_Labels`) so the audience sees the pattern generalize
  without adding a spoken line. The closing slide repeats a similar list in
  its own words. That repetition is fine because only one of the two is
  spoken aloud; never add a matching narration sentence here.

### When to Use This Slide

* **Recorded video**: place it as its own beat immediately after Slide 3 and
  before the demo-transition card in [DEMO.md](./DEMO.md).
* **Live presentation without a recorded video**: display this slide alone,
  right before running `uv run maf-outcome-economics demo --provider live` or
  `demo-scenarios`, so the audience understands the pain point before the
  terminal appears.
* Update the ticket labels and pain-point wording if a future scenario adapter
  (finance, claims, security, or software delivery) replaces ticket triage,
  so the slide always matches the scenario that actually runs.

## Slide 5: Proving the Answer With a Golden Dataset

Target duration: 8 to 9 seconds. Build and show this slide immediately after
Slide 4 and before the live demo starts, whether recording a video or
presenting live.

This slide answers one question only: **how does OutcomeMeter know the
agent's answer was actually right?** Do not repeat the scenario pain point,
the measurement gap, or the governance gates. Those are covered by Slides 1
to 4. Keep the two-column layout simple; the on-slide labels carry the field
names and process detail so the spoken line stays short.

### Build the Slide

1. Add this title at the top:

   ```text
   Checked against ground truth the agent never sees
   ```

2. Split the slide into two labeled columns: `Ticket triage` on the left,
   `Invoice processing` on the right.
3. Left column: add a ticket icon, then a right-facing arrow to a tag icon,
   then another arrow to a locked-padlock icon. Label the row:

   ```text
   Ticket -> gold_category, gold_priority, gold_resolver_group -> hidden
   from the agent
   ```

4. Right column: add a receipt icon, then an arrow to a ledger-book icon,
   then an arrow to the same locked-padlock icon. Label the row:

   ```text
   Invoice -> AP ledger, three-way match, duplicate check -> hidden from
   the agent
   ```

5. Add this shared footer beneath both columns:

   ```text
   32 fictional tickets, three gold labels each. The agent never grades its
   own work.
   ```

6. Add one small monospace text box beneath the footer showing the golden
   record schema, followed by a single example, so the slide reads as "real
   data," not a mockup. Use a code-block style fill (dark background, light
   monospace font, 12-14 pt so it stays readable at 8-9 seconds).

   Schema shared by both domains (the fields the agent is graded against
   but never sees; only `prompt_fields` is interpolated into its prompt
   template in `src/maf_outcome_economics/agents/prompts.py`):

   ```json
   {
     "work_unit_id": "string",
     "domain": "ticket | invoice",
     "hidden_gold_fields": "object, domain-specific",
     "prompt_fields": ["subject", "description"]
   }
   ```

   One example, from `src/maf_outcome_economics/scenarios/ticket/seed.py`:

   ```json
   {
     "work_unit_id": "TKT-002",
     "domain": "ticket",
     "hidden_gold_fields": {
       "gold_category": "Billing",
       "gold_priority": "P3",
       "gold_resolver_group": "Billing Support"
     },
     "prompt_fields": ["subject", "description"]
   }
   ```

   In plain words: a human support lead already decided this ticket's real
   category, how urgent it is, and which team should own it before the
   agent ever saw it. The agent only reads the subject and description text
   and has to land on the same three answers.

   Invoice records follow the same shape, using three plain checks instead
   of ticket labels: was the bill actually recorded (`posted`), does it match
   what was ordered and received (`amount_matched`), and is it a repeat
   charge (`duplicate_detected`)? Same idea as a bank reconciling a
   statement. None of these checks come from the agent. Source:
   `src/maf_outcome_economics/scenarios/invoice/connector.py`.

### Name the Objects

* `S5_Title`
* `S5_Ticket_Icon`, `S5_Ticket_Tag`, `S5_Ticket_Lock`
* `S5_Invoice_Icon`, `S5_Invoice_Ledger`, `S5_Invoice_Lock`
* `S5_Footer`
* `S5_Schema_Example`

### Animate the Slide

1. Animate `S5_Title` with **Fade** and start **With Previous**.
2. Group the ticket, tag, and padlock icons; animate the group with
   **Appear**.
3. Group the invoice, ledger, and padlock icons; animate the group with
   **Appear** immediately after the ticket group.
4. Group `S5_Footer` and `S5_Schema_Example`; animate the group last with
   **Fade** so the schema and example appear together with the summary
   line.

### Narration

> Tickets carry three hidden gold labels the agent never sees; invoices are
> checked against the ledger. Either way, the agent never grades its own
> work.

This narration is about 25 words, roughly 8 to 9 seconds at the same pace
used for Slide 4. Update the ticket count and field names here if the seed
data in `src/maf_outcome_economics/scenarios/ticket/seed.py` changes.

## Transition Into the Demo

Create a demo-transition slide after Slide 5 and keep it visible for
approximately two seconds.

1. Set the slide background to charcoal.
2. Add this large white text:

   ```text
   Let's test it on the same work.
   ```

3. Add this smaller white text:

   ```text
   Baseline versus optimized
   ```

4. Apply **Fade** to both text boxes.
5. Set **Transitions > Fade > Duration** to `0.4` seconds.
6. Cut directly from this slide to the live terminal recording.

## Add Demo Clips in PowerPoint

Create one blank slide for each demo section:

* Live terminal execution
* Live dashboard: verified outcome comparison
* Live dashboard: review-token waste
* Live dashboard: governance decision
* `SCALE`, `OPTIMIZE`, and `STOP` scenarios

For each clip:

1. Go to **Insert > Video > This Device**.
2. Select the recorded clip.
3. Resize the video to fill the slide.
4. Open the **Playback** tab.
5. Set **Start** to **Automatically**.
6. Enable **Play Full Screen**.
7. Enable **Hide While Not Playing**.
8. Select **Playback > Trim Video**.
9. Remove command wait time, repeated output, and unnecessary pointer movement.

> [!TIP]
> Record the dashboard clips from the live Streamlit dashboard
> (`uv run maf-outcome-economics dashboard --database data\dashboard-demo.db --port 8510`)
> rather than from a static HTML export. Before recording, use the sidebar to
> confirm `data\dashboard-demo.db` and click **Refresh now**. Collapse the
> sidebar before capture so the dashboard matches the clean two-section
> layout. The terminal clip separately proves Azure OpenAI execution and
> telemetry.

### Record the Current Dashboard

Record at 1920 x 1080 with browser zoom at `100%`. Keep the sidebar collapsed
and the **Executive overview** tab active under
**Executive Decision Dashboard**. Leave **Governance & reviews** and
**Evidence detail** closed. The dashboard is designed as two screen-share
sections connected by one deliberate scroll.

Use this focus sequence:

1. Hold on the `MONITOR` recommendation and KPI row for 3 seconds.
2. Point to `31` **Verified outcomes**, `0.0007 USD`
   **Cost / verified outcome**, `0.0088 USD` **Net savings vs. control**, and
   `27.5%` **Token efficiency gain**.
3. Move left to right across the exact chart headlines:
   `Cost per outcome · 27% lower`, `Human reviews · 69% lower`, and
   `Tokens per outcome · 28% lower`.
4. Pause on each **Why it matters** card. Keep the pointer outside the text.
5. Scroll once until **Section 2: Novelty and waste reduction** reaches the
   top of the frame.
6. Hold the full Section 2 view. Show `100%` useful corrections retained,
   `81%` of no-change review tokens removed, and `69%` fewer total review
   tokens. Pause on the large `4` useful-corrections and `22` eliminated-review
   evidence cards.
7. Trace the review-consumption bars from `3,200` control tokens to `1,000`
   treatment tokens.
8. Finish on `11/11 GATES PASSED`. Move through **Evidence**, **Trust**,
   **Value**, **Tokens**, and **Waste** to `MONITOR`.
9. Hover over **Trust**, then **Value**, for their gate rationale. Add a text
   overlay in editing (not narrated): "Trust ✓ Value ✓ — savings proven, not
   assumed." Fade it out and move the pointer away before the final hold on
   `MONITOR`.

Record one 45-to-50-second two-section take. Reuse crops from that take for the
outcome, waste-reduction, and governance PowerPoint slides. Keep
**Executive overview** selected and do not open a secondary tab during the
main story. Use only one clean scroll between sections.

### Add Metric Callouts

1. Select **Insert > Shapes > Rectangle**.
2. Draw a rectangle around the metric being discussed.
3. Set **Shape Fill** to **No Fill**.
4. Set **Shape Outline** to green and **Weight** to `3 pt`.
5. Apply **Appear** when the narration reaches that metric.
6. Apply **Disappear** before highlighting another part of the report when the
   first box would become distracting.

Use callouts only for these values:

* `31` verified outcomes
* `27%` lower cost per outcome
* `69%` fewer human reviews
* `28%` lower tokens per outcome
* `81%` of no-change review tokens removed
* `11/11` governance gates passed
* `MONITOR` governance decision

## Record Narration and Timings

1. Go to **Record > From Beginning**.
2. Enable the microphone and disable the camera.
3. Narrate while advancing each animation.
4. Pause briefly before changing to the demo.
5. Press `Esc` when finished.
6. Review the result with **Slide Show > From Beginning**.
7. Re-record an individual slide with **Record > From Current Slide** when
   necessary.

> [!IMPORTANT]
> Record one slide at a time if the timing feels rushed. PowerPoint preserves
> each slide's narration and animation timing independently.

## Closing Slide

1. Create a slide with a charcoal background.
2. Add `OutcomeMeter` in large white text.
3. Add these three lines beneath the title:

   ```text
   Measure what AI spends.
   Verify what it achieves.
   Decide what to scale.
   ```

4. Animate `OutcomeMeter` with **Fade**.
5. Animate each supporting line with **Appear** at `0.4`-second intervals.
6. Keep the completed closing slide visible for 3 seconds.

## Export the Final Video

1. Go to **File > Export > Create a Video**.
2. Select **Full HD 1080p**.
3. Select **Use Recorded Timings and Narrations**.
4. Choose **Create Video**.
5. Export the presentation as an MP4 file.
6. Watch the exported file from beginning to end.
7. Confirm that text remains readable, narration matches the animation, and no
   callout covers a report value.
8. Confirm that the final duration remains below the hackathon limit.

## Recommended Timing

| Section | Duration |
|---------|---------:|
| Measurement gap (Slide 1) | 6 to 7 seconds |
| OutcomeMeter measure (Slide 2) | 8 to 9 seconds |
| Assurance and decisions (Slide 3) | 8 to 9 seconds |
| Scenario you are about to see (Slide 4) | 12 to 14 seconds |
| Proving the answer (Slide 5) | 8 to 9 seconds |
| Demo transition | 2 seconds |
| Recorded demo | 65 to 75 seconds |
| Closing slide | 5 to 6 seconds |
| **Target total** (every row at its low end) | **Approximately 1:54** |
| **Do-not-exceed total** | **1:58**, the same maximum planned duration set in [DEMO.md](./DEMO.md) |

Do not add every row's upper bound together and assume it fits: that sum
reaches roughly 2:11, which is over the two-minute limit. Treat the low end
of each row as the working target, and reserve the rest of each range for the
recorded demo, since its length depends on the live terminal output. If the
demo needs its full 65-to-75-second range, claw the time back in this order:

1. Keep Slide 4 and Slide 5's narration at their floor durations (12 seconds
   and 8 seconds); the on-slide captions still carry the pain-point,
   relevance, generalization, and evidence ideas visually even if the spoken
   line stays short.
2. Trim the closing slide to 5 seconds.
3. Trim Slides 1 to 3 to their combined floor (about 22 seconds).
4. Only as a last resort, shorten the recorded demo toward its 65-second
   floor by cutting one dashboard callout. The recorded demo is the "product
   in action" proof judges remember most, so protect its length until every
   other option is used.

Following this order keeps the export at or below 1:58, leaving a two-second
buffer under the hackathon's two-minute limit.

## Final Review Checklist

* Keep the concept section (Slides 1 to 3) below 25 seconds
* Show the scenario slide (Slide 4) before any live command runs, in every
  recording and every live presentation
* Show the golden-dataset slide (Slide 5) right before the demo transition,
  so judges see how the agent's answer is graded before they watch it act
* Show one spoken claim with one visual proof
* Use consistent colors and object sizes
* Keep captions clear of metrics and slide labels
* Remove model wait time and repeated terminal output
* Use footage from the live dashboard and reports instead of recreating them
  in PowerPoint
* Confirm the dashboard was refreshed from `data\dashboard-demo.db` before
  recording and is shown with the sidebar collapsed
* Confirm Section 1 is legible before one clean scroll reveals the complete
  Section 2 waste and governance view
* Confirm the outcome, waste-reduction, and governance crops come from the
  same dashboard take
* Confirm the current values (`31`, `27%`, `69%`, `28%`, `81%`, and `11/11`)
  are readable
* Confirm that quality and safety appear before economics
* Confirm that `SCALE`, `OPTIMIZE`, and `STOP` are readable
* Export at 1080p with recorded timings and narration
* Confirm the exported duration lands at or under 1:58, the two-second
  buffer under the hackathon's two-minute limit
