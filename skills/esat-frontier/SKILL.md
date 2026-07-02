---
name: esat-frontier
description: "Frontier-led world-class level-up analysis. Reuses eskill-analyze's engine, then runs a configurable model-fusion panel where a frontier lead such as Fable synthesizes independent reviewers such as Sonnet 5, Codex Medium, Grok, and optional fleet/OpenRouter voices. Use for /esat-frontier, frontier analysis, Fable-led analysis, model-fusion review, or highest-stakes analysis where one lead frontier model should judge, reconcile, and route a configurable council rather than relying on the fixed esat trio."
---

# eSkill: Analyze Frontier — Frontier-Led Fusion Analyzer

`esat-frontier` = `eskill-analyze` + a **frontier-led configurable fusion panel**. It keeps the original analysis engine intact, then replaces the fixed trio stress test with a lead frontier model and a configurable roster of independent reviewers.

Default posture:
- **Lead**: Fable if the harness exposes it; otherwise the strongest available frontier model.
- **Reviewers**: Sonnet 5, Codex Medium, Grok, plus optional fleet/OpenRouter voices when configured.
- **Synthesis**: the lead does not average votes. It verifies claims, reconciles disagreements, and emits one evidence-backed verdict.

## Engine — reuse eskill-analyze verbatim

Run the full `eskill-analyze` protocol for Input Parameters, Triage, Delegation, Framework Selection, Evidence Gathering, and Steps 1-8. Read and follow, in order:

1. `${CLAUDE_SKILL_DIR}/../eskill-analyze/SKILL.md`
2. `${CLAUDE_SKILL_DIR}/../eskill-analyze/references/triage-guide.md`
3. `${CLAUDE_SKILL_DIR}/../eskill-analyze/references/mental-models.md`
4. `${CLAUDE_SKILL_DIR}/../eskill-analyze/references/analysis-protocol.md` — run Phase 0 + Steps 1-8. **Skip that file's Phase 9.**
5. `${CLAUDE_SKILL_DIR}/../eskill-analyze/references/world-class-signals.md`

## Frontier overrides

- **Phase 9 is mandatory** for `standard` and `deep`; for `quick`, run a compact two-voice panel unless the user explicitly asks for no panel.
- **Phase 9 uses this skill's fusion panel**, not `eskill-analyze`'s single critic and not `esat`'s fixed trio.
- **The lead is responsible for judgment**, not just summarization. It must verify claims against the item/repo before adopting reviewer output.

## Phase 9 — Frontier Fusion Panel

After Steps 1-8 produce the draft analysis, read and execute `${CLAUDE_SKILL_DIR}/references/frontier-panel.md`.

## Configuration

Use environment variables when the harness or shell supports them:

| Variable | Default | Effect |
|-|-|-|
| `ESAT_FRONTIER_LEAD` | `fable` | Preferred lead model label. If unavailable, use the strongest available frontier model and state the fallback. |
| `ESAT_FRONTIER_ROSTER` | `sonnet-5,codex-medium,grok` | Comma-separated reviewer roster. Supported labels are harness-dependent; unknown labels are skipped with a panel note. |
| `ESAT_FRONTIER_FLEET` | `0` | `1` adds the `esat-fleet` OSS swarm leg through `fleet-fuse` when sensitivity allows. |
| `ESAT_FRONTIER_SENSITIVITY` | `medium` | `high` keeps review local/first-party only; `medium` allows redacted external reviewers; `low` allows broader low-tier pools. |
| `ESAT_FRONTIER_BUDGET_USD` | unset | Optional cap for external fleet calls. |

## Output

Use `${CLAUDE_SKILL_DIR}/../eskill-analyze/assets/output-template.md` plus the `### Frontier Fusion Panel` block defined in `references/frontier-panel.md`.

Set the triage header to `esat-frontier (frontier fusion)` and save output to `.omc/plans/esat-frontier-{date}-{focus}.md`.

## Post-Analysis Routing

Same as `eskill-analyze`: route confirmed action lists to sprint or overnight execution only after the user confirms the actions.
