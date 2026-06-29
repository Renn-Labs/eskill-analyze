---
name: esat
aliases: [eskill-analyze-trio, eskill-trio]
description: "Tri-model (Claude + Codex + Grok) world-class level-up analysis. Same engine as eskill-analyze, but the stress-test phase is a mandatory 3-SOTA-model panel — Claude critic + Codex (gpt-5.5) + Grok (grok-build) independently review the item, then Claude synthesizes consensus / divergence / unique catches. Use for high-stakes analysis you want triple-checked across frontier models. Triggers: /esat, eskill analyze trio, trio analysis, three-model review."
---

# eSkill: Analyze Trio (esat) — 3-SOTA-Model Level-Up Analyzer

`esat` = `eskill-analyze` **+ a mandatory tri-model review panel**. It runs the full world-class analysis engine, then has three frontier models — **Claude** (`critic`), **Codex** (gpt-5.5), **Grok** (grok-build) — independently stress-test the item and the draft in parallel. You (Claude) are the only trusted integrator: you synthesize their verdicts into one panel and adjust the analysis accordingly.

Use `esat` when the stakes justify a triple-model cross-check (architecture bets, strategy calls, build-vs-buy, anything you want frontier-model consensus on). For a lighter single-model pass, use `/esa` (eskill-analyze).

## Engine — reuse eskill-analyze verbatim

Run the entire eskill-analyze protocol for Input Parameters, Triage, Delegation, Framework Selection, and Steps 1–8. Read and follow, in order:

1. `${CLAUDE_SKILL_DIR}/../eskill-analyze/SKILL.md` — Input Parameters, Scope check, Triage gate, Delegation Strategy, Framework Selection, Comparison Mode, Project-Level Impact, Post-Analysis Routing. **Apply the two esat overrides below.**
2. `${CLAUDE_SKILL_DIR}/../eskill-analyze/references/triage-guide.md` — classification
3. `${CLAUDE_SKILL_DIR}/../eskill-analyze/references/mental-models.md` — model selection
4. `${CLAUDE_SKILL_DIR}/../eskill-analyze/references/analysis-protocol.md` — Phase 0 + Steps 1–8. **Skip that file's "Phase 9: Stress Test"** — esat replaces it with the trio panel.
5. `${CLAUDE_SKILL_DIR}/../eskill-analyze/references/world-class-signals.md`

### esat overrides (only two differences from eskill-analyze)
- **Phase 9 is the Tri-Model Panel** (this skill's `references/trio-panel.md`), not the single Claude critic.
- **Phase 9 is mandatory, not discretionary.** The trio panel is the entire point of esat — triage may not skip it. (Kill-switch `ESKILL_PEER=0` degrades it to Claude-only; see below.)

## Phase 9 — Tri-Model Panel

After completing Steps 1–8 and producing the draft analysis, read and execute `${CLAUDE_SKILL_DIR}/references/trio-panel.md`. That file specifies the three concurrent reviewers, the untrusted-input synthesis rules, the gates/kill-switches, and the output block.

## Output

Use the eskill-analyze output template (`${CLAUDE_SKILL_DIR}/../eskill-analyze/assets/output-template.md`) **plus** the `### Tri-Model Panel` block defined in `references/trio-panel.md`. Place the panel directly above `### Stress Test Notes`. The triage header should read `esat (trio)` so it's clear which skill produced the analysis.

Save the analysis output to `.omc/plans/esat-{date}-{focus}.md`.

## Post-Analysis Routing

Same as eskill-analyze (sprint/overnight routing on the confirmed action list). See its SKILL.md "Post-Analysis Routing" section.
