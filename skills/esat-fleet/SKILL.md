---
name: esat-fleet
aliases: [eskill-analyze-fleet, esatf]
description: "esat + a fleet council. Runs the full esat tri-model panel (Claude critic + Codex + Grok), then ALSO fans the same review across the OpenRouter OSS swarm via fleet-fuse (sensitivity-tiered, redacted, off the first-party trio). Claude remains the sole chairman — it reconciles every voice into consensus / divergence / unique-catch. Use for the highest-stakes analysis where you want frontier + open-model breadth. Triggers: /esat-fleet, esatf, eskill analyze fleet, fleet council review."
---

# eSkill: Analyze Fleet (esat-fleet) — Frontier + OSS-Swarm Council

`esat-fleet` = **`esat` + a fleet council leg**. It runs everything esat does (full world-class analysis engine + the 3-frontier-model panel), then broadens the council with the **OpenRouter OSS swarm** dispatched through `fleet-fuse` — tier-gated, redacted, and off the first-party trio so it adds breadth rather than duplicating it. You (Claude) stay the sole chairman: you reconcile frontier + OSS voices into one verdict and decide.

Use `esat-fleet` when you want both **frontier depth** (Opus + gpt-5.5 + grok) **and open-model breadth** (DeepSeek / Qwen / Kimi / GLM via OpenRouter) cross-checking the same item — the widest council in the stack. For frontier-only, use `/esat`; for a single-model pass, `/esa`.

## Engine + trio — reuse esat verbatim

Run `esat` exactly as written — do not re-derive it. Read and follow:

1. `~/.claude/skills/esat/SKILL.md` — which itself reuses the eskill-analyze engine (Input Params, Triage, Delegation, mental models, Phase 0 + Steps 1–8, output template) and defines the trio panel.
2. `~/.claude/skills/esat/references/trio-panel.md` — Phase 9 reviewers 1–3 (Claude `critic` + Codex + Grok via `peer trio`) and the untrusted-input synthesis rules.

`esat-fleet` changes **one thing**: Phase 9 gains a fourth leg — the fleet OSS swarm — folded into the **same** consensus / divergence / unique-catch synthesis.

## Phase 9 — add the fleet leg

After dispatching esat's trio (critic + `peer trio`) in the usual turn, **also** run the fleet leg per `${CLAUDE_SKILL_DIR}/references/fleet-leg.md`, then synthesize all voices together. The fleet leg reuses the same draft file the trio leg already wrote.

## Sensitivity gate (read before running)

The fleet leg reaches **external open-source models** (OpenRouter), so it is sensitivity-tiered — this is the core governance difference from esat:

| `ESAT_FLEET_SENSITIVITY` | Fleet leg behavior |
|-|-|
| `high` (sensitive/proprietary) | **Fleet leg SKIPPED** — OpenRouter is blocked at high tier, so there is no OSS to add. esat-fleet degrades to esat (frontier trio only). |
| `medium` (default) | OpenRouter OSS swarm (ZDR), redacted fail-closed by `fleet_scrub`. |
| `low` (clearly non-sensitive) | + jimmy / low-tier pools. |

Default is `medium`. Outbound redaction is automatic and fail-closed; never pass `--no-redact`. State the tier you ran in the panel.

## Output

Use esat's output (eskill-analyze template + the `### Tri-Model Panel` block), **extended to a council** per `references/fleet-leg.md` — the panel lists the frontier trio plus the OSS-swarm verdict, and records the sensitivity tier and whether the fleet leg ran. Save to `.omc/plans/esat-fleet-{date}-{focus}.md`.

## Switches

- `ESAT_FLEET=0` → skip the fleet leg (degrade to esat).
- `ESKILL_PEER=0` → skip the Codex+Grok trio leg (inherited from esat). Both off → Claude-only.
- `ESAT_FLEET_SENSITIVITY` → `high|medium|low` (default `medium`).
- Cost: the fleet leg adds metered OpenRouter spend (OSS is cheap; cap with `--budget-usd`). Codex+Grok remain off the Claude reserve; only the Claude critic + orchestration are on-reserve.
