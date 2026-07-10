---
name: esat-fleet
description: "esat + a fleet council. Runs the full esat tri-model panel (Claude critic + Codex + Grok), then ALSO fans the same review across the OpenRouter OSS swarm via fleet-fuse (sensitivity-tiered, redacted, off the first-party trio). Claude remains the sole chairman — it reconciles every voice into consensus / divergence / unique-catch. Use for the highest-stakes analysis where you want frontier + open-model breadth. Triggers: /esat-fleet, esatf, eskill-analyze-fleet, eskill analyze fleet, fleet council review."
---

# eSkill: Analyze Fleet (esat-fleet) — Frontier + OSS-Swarm Council

`esat-fleet` = **`esat` + a fleet council leg**. It runs everything esat does (full world-class analysis engine + the 3-frontier-model panel), then broadens the council with the **OpenRouter OSS swarm** dispatched through `fleet-fuse` — tier-gated, redacted, and off the first-party trio so it adds breadth rather than duplicating it. You (Claude) stay the sole chairman: you reconcile frontier + OSS voices into one verdict and decide.

Use `esat-fleet` when you want both **frontier depth** (critic + Codex + Grok with actual/account-default disclosure) **and open-model breadth** (DeepSeek / Qwen / Kimi / GLM via OpenRouter) cross-checking the same item — the widest fixed-council in the stack below the configurable frontier tier. For frontier-only, use `/esat`; for a single-model pass, `/esa`.

## Shared routing contract (load first)

Before Phase 9 dispatch, read and obey:

`${CLAUDE_SKILL_DIR}/../eskill-common/references/model-routing.md`

That contract defines semantic role vs requested vs actual route, preference precedence, harness identity, strict pins, disclosed automatic fallback, strongest-restriction policy, metered consent, two-stage manifest, two-phase deduplication, and draft ownership. This skill owns Phase-9 composition only.

## Engine + trio — reuse esat with caller-owned draft

Run `esat` for the engine and trio reviewers, with **one ownership change**:

1. `${CLAUDE_SKILL_DIR}/../esat/SKILL.md` — which reuses the eskill-analyze engine (Input Params, Triage, Delegation, mental models, Phase 0 + Steps 1–8, output template) and defines the fixed trio panel.
2. `${CLAUDE_SKILL_DIR}/../esat/references/trio-panel.md` — Phase 9 reviewers 1–3. **Use the caller-owned draft lifecycle**: Tier 3 supplies `$DRAFT`, defines `$PEER_DISPATCH_INPUT` separately from raw `$DRAFT`, the trio must not delete the draft, and Tier 3 cleans once after all consumers finish.

`esat-fleet` changes Phase 9 as follows:

1. Create and retain **one caller-owned draft** for trio **and** fleet; arm an owner EXIT trap immediately after temp creation (also covers `$PEER_REDACTED` and fleet `$REVIEW`).
2. Define **`PEER_DISPATCH_INPUT` separately from raw `$DRAFT`** for external peer egress (see sensitivity rules below and `fleet-leg.md`).
3. Freeze the **two-stage route manifest** (immutable plan + append-only results) before dispatch.
4. Emit an effective-route preview (consent, budget, sensitivity, readiness).
5. Run the trio with caller-owned lifecycle: `peer trio` reads `$PEER_DISPATCH_INPUT` only — **never** raw `$DRAFT` (no trio-side cleanup of `$DRAFT`).
6. Run the fleet leg per `${CLAUDE_SKILL_DIR}/references/fleet-leg.md` when policy allows.
7. Append exactly one terminal result per planned lane (including blocked/skipped with `observed_route: null`).
8. Derive panel status only after all terminal results exist.
9. Clean owner temps (**exactly once**) after trio and fleet success, skip, failure, or timeout — normal path invokes cleanup and disarms EXIT; timeout still hits the trap. SIGKILL cannot be handled.

## Phase 9 — add the fleet leg

After the policy-gated reviewer legs against the **caller-owned** draft, **also** run the fleet leg per `${CLAUDE_SKILL_DIR}/references/fleet-leg.md` when readiness is `ready`, then synthesize all voices together.

On **high** sensitivity, schedule **zero external Phase-9 routes** (not only FleetFuse): run only local/first-party reviewers (normally the in-harness critic). Skip/block `peer trio` Codex/Grok unless the harness explicitly classifies those routes as first-party. Append terminal results with `observed_route: null` for every blocked external lane. **Do not** claim the external frontier trio ran. On medium/low (when policy allows), the critic + `peer trio` (or first-party equivalents) may run, then the fleet leg when ready.

## Sensitivity gate (read before running)

Phase 9 is sensitivity-tiered for **every external route** — FleetFuse OSS **and** external `peer` Codex/Grok — not only the fleet leg:

| `ESAT_FLEET_SENSITIVITY` | Phase-9 external-route behavior |
|-|-|
| `high` (sensitive/proprietary) | **Zero external routes.** Local/first-party reviewers only (normally the in-harness critic). Fleet leg blocked. External peer readiness forced `0`. External `peer trio` / `peer codex` / `peer grok` skipped/blocked unless the harness explicitly classifies them first-party. Terminal results: `observed_route: null`, reason `high-sensitivity`. Do **not** degrade to a full external esat frontier trio and do **not** claim that trio ran. |
| `medium` (default) | External peer + OpenRouter OSS only with an identified redaction path. Peer: create `$PEER_REDACTED` via trusted `$IDENTIFIED_REDACTION_PATH` and set `$PEER_DISPATCH_INPUT` to that file; `peer trio` reads `$PEER_DISPATCH_INPUT` only — never raw `$DRAFT`. Fleet: `fleet_scrub` fail-closed. Missing/failing redactor → readiness blocked `redactor-unavailable`, **do not call peer** / do not raw-send. |
| `low` (clearly non-sensitive) | + jimmy / low-tier pools when permitted. Raw `$DRAFT` as `$PEER_DISPATCH_INPUT` only if the **already-resolved** external peer readiness flag is `1`. Low never bypasses readiness. |
| invalid | Fail closed — block external routes with `invalid-sensitivity`. |

Default is `medium`. Outbound redaction is automatic and fail-closed; never pass `--no-redact`. State the tier you ran in the panel. Multiple policy scopes intersect with **strongest restriction wins**.

## Metered consent and budget

- Metered FleetFuse requires **per-run** consent: direct current-invocation instruction **or** interactive current-run answer only.
- Environment variables, project/user config, inherited shell state, expired consent, and prior-run answers are **rejected** as consent.
- Without accepted consent, skip/block the fleet lane and **do not enter** the `--yes-metered` branch.
- `--yes-metered` appears **only** in the consented command branch.
- `ESAT_FLEET_BUDGET_USD`: optional positive numeric cap. Absent → disclose `provider/account cap only`. Invalid → fail closed (`invalid-budget`).

## Output

Use esat's output (eskill-analyze template + the `### Tri-Model Panel` block), **extended to a council** per `references/fleet-leg.md` — the panel lists the frontier trio plus the OSS-swarm verdict, records the sensitivity tier, consent/budget disclosure, actual routes, and whether the fleet leg ran. Save to `.omc/plans/esat-fleet-{date}-{focus}.md`.

## Switches

- `ESAT_FLEET=0` → skip the fleet leg (degrade to esat); still emit a terminal skip result and clean the draft once.
- `ESKILL_PEER=0` → skip the Codex+Grok trio leg (inherited from esat). Both off → Claude-only + optional fleet if policy allows.
- `ESAT_FLEET_SENSITIVITY` → `high|medium|low` (default `medium`).
- Cost: the fleet leg may add metered OpenRouter spend only after consent; Codex+Grok remain off the Claude reserve when using `peer`.
