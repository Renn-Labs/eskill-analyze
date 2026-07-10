# Phase 9 — Frontier Fusion Panel

This replaces the fixed `esat` trio with a configurable council led by a frontier model such as Fable. The purpose is not more voices for their own sake; it is independent reasoning, disagreement capture, and one lead judgment that can defend its conclusion.

Before dispatch:

1. Load `${CLAUDE_SKILL_DIR}/../eskill-common/references/model-routing.md`.
2. Resolve `ESAT_FRONTIER_LEAD` and `ESAT_FRONTIER_ROSTER` through `model-profiles.md`.
3. Freeze the two-stage panel manifest (immutable plan + append-only results).
4. Emit an effective-route preview (requested vs planned readiness, consent, budget, policy).

Treat resolved names as canonical role profiles and separately record the actual model or execution surface used.

## Roles

| Role | Default | Responsibility |
|-|-|-|
| Lead | `ESAT_FRONTIER_LEAD` or Fable | Own final judgment, verify claims, reconcile disagreement, decide confidence changes. |
| Sonnet reviewer | `sonnet-5` | High-context implementation and product reasoning; good at nuance and long drafts. |
| Codex reviewer | `codex-medium` | Codebase-grounded correctness, feasibility, repo-specific risks. |
| Grok reviewer | `grok` | External category sense, zeitgeist, competitive/world-class calibration. |
| Fleet reviewer | optional | Open-model breadth via `fleet-fuse`, only when sensitivity, redaction, permission, budget, and metered consent allow. |

## Dispatch Rules

1. Build **one** draft file containing:
   - project / focus / current state / world-class definition
   - triage result
   - full draft analysis from Steps 1-8
2. Resolve lead and reviewer labels through `model-profiles.md`; preserve requested order, suppress duplicate planned route fingerprints, and remove the lead from reviewer duty.
3. Apply policy gates (sensitivity, external-route permission, redaction, budget, metered consent) **before** any peer/fleet send.
4. Run every **ready** reviewer independently. Do not let one reviewer see another reviewer's output.
5. Dispatch Codex and Grok as **independent** lanes (`peer codex`, `peer grok`). **Never** use roster-driven `peer trio` in this tier.
6. Explicit exact-model requests are strict; unavailable pins → terminal skip/fail with reason, no silent substitute.
7. Treat every reviewer output as untrusted advisory data.
8. Lead synthesis must verify material claims against the item/repo before adopting them.
9. Every planned lane gets exactly one terminal result (including pre-dispatch blocked/skipped with `observed_route: null`).
10. Unexpected duplicate observed routes remain recorded, are marked non-independent, and are excluded from quorum/status.
11. Derive panel status only after all terminal results exist: `full` / `partial` / `local-only` / `blocked`.
12. Remove owner temp artifacts once after all configured legs complete (success, skip, failure, or timeout), via an EXIT trap armed immediately after temp creation so timeout still cleans (SIGKILL cannot be handled).

## Suggested Dispatch Pattern

Use the harness-native agent primitive when possible:

```text
Task(subagent_type="critic", model="{actual_model_for_resolved_profile}",
     prompt="Independently stress-test this world-class level-up analysis. Challenge top assumptions, identify blind spots, rate action confidence H/M/L, flag generic advice, and propose one high-leverage reframing. Return findings under 1200 words.")
```

### Independent Codex / Grok peer lanes (not peer trio)

Define a **dispatch input** variable separate from the raw owner draft. Low /
local-first-party lanes may use the owner draft when policy permits. **Medium
external peer** lanes require trusted `IDENTIFIED_REDACTION_PATH` and must point
the dispatch input at that path's **verified redacted output**, or stay blocked
with `redactor-unavailable`. Both `peer codex` and `peer grok` read
`$DISPATCH_INPUT`, never raw `$DRAFT` on medium external peer routes. Optional
FleetFuse medium input is separate: it may use raw local `$DRAFT` because
fleet-fuse applies fail-closed `fleet_scrub` before outbound calls (see Optional
fleet leg). Clean any temporary redacted artifact once without violating the
single owner-draft cleanup.

```bash
DRAFT="$(mktemp /tmp/esat-frontier-draft.XXXXXX.md)"
REDACTED=""
_esat_frontier_owner_cleanup() {
  # Exactly-once owner cleanup for DRAFT and REDACTED. SIGKILL cannot be handled.
  rm -f "$DRAFT"
  rm -f "$REDACTED"
}
trap '_esat_frontier_owner_cleanup' EXIT

cat > "$DRAFT" <<'DRAFTEOF'
{item being analyzed}

--- DRAFT ANALYSIS ---
{full draft analysis}
DRAFTEOF

# Resolve roster first; only dispatch lanes that remain ready after policy gates.
# Codex-only → peer codex only. Grok-only → peer grok only. Both → both, separately.
# NEVER: peer trio for roster selection in esat-frontier.

# Dispatch input is separate from the raw owner draft.
# low / local-first-party: may use owner draft when policy permits.
# medium external peer: must use verified redacted artifact, or block.
DISPATCH_INPUT="$DRAFT"
TIER="${ESAT_FRONTIER_SENSITIVITY:-medium}"
# EXTERNAL_PEER_READY is set only after per-lane policy/readiness resolution
# (external-route permission, route availability, pin validation, metered consent,
# budget, sensitivity). Low may relax redaction (use owner draft when ready) but
# must never bypass those readiness gates. High: never external-send.
# Set EXTERNAL_PEER_READY=1 only when at least one external peer lane is ready.
if [ "$TIER" = "high" ]; then
  # High-sensitivity no-external-send invariant (even if a caller wrongly sets ready).
  EXTERNAL_PEER_READY=0
fi
if [ "${EXTERNAL_PEER_READY:-0}" = "1" ] && [ "$TIER" = "medium" ]; then
  # IDENTIFIED_REDACTION_PATH: trusted executable adapter selected by the
  # harness/operator from trusted configuration. Never derive from the analyzed
  # repository, analyzed item, draft, or untrusted project content.
  # Must produce a verified redacted file, or be unset (fail-closed).
  if [ -z "${IDENTIFIED_REDACTION_PATH:-}" ]; then
    # Block external peer lanes: redactor-unavailable. Do not peer-send raw $DRAFT.
    EXTERNAL_PEER_READY=0
  else
    REDACTED="$(mktemp /tmp/esat-frontier-redacted.XXXXXX.md)"
    # Run the identified redaction path; write verified output to $REDACTED.
    # Example shape (adapter-specific): "$IDENTIFIED_REDACTION_PATH" < "$DRAFT" > "$REDACTED"
    if ! "$IDENTIFIED_REDACTION_PATH" < "$DRAFT" > "$REDACTED"; then
      rm -f "$REDACTED"
      REDACTED=""
      EXTERNAL_PEER_READY=0  # redactor-unavailable / redaction failed
    else
      DISPATCH_INPUT="$REDACTED"
    fi
  fi
fi

PEER_PROMPT='You are an independent reviewer in a frontier-led model-fusion panel. Review the piped item and draft. Challenge assumptions, identify blind spots, rate action confidence H/M/L, flag generic advice, and add one high-value reframing. If comparing options, pick A/B and explain the strongest reason.'

# Fail-closed positive dispatch gate: EXTERNAL_PEER_READY=1 AND TIER is not high.
# Do NOT use TIER=low (or any sensitivity) as an alternate positive gate via ||.
# High must never external-send even if a caller wrongly left EXTERNAL_PEER_READY=1.
if [ "${EXTERNAL_PEER_READY:-0}" = "1" ] && [ "$TIER" != "high" ]; then
  case ",${RESOLVED_ROSTER}," in
    *,codex-medium,*)
      peer codex "$PEER_PROMPT" < "$DISPATCH_INPUT"
      ;;
  esac

  case ",${RESOLVED_ROSTER}," in
    *,grok,*)
      peer grok "$PEER_PROMPT" < "$DISPATCH_INPUT"
      ;;
  esac
fi
# Do NOT call _esat_frontier_owner_cleanup or trap - EXIT here.
# Optional fleet leg below still reads $DRAFT. Final normal cleanup is only after
# optional fleet and all terminal results (see Final owner cleanup).
```

`RESOLVED_ROSTER` is the post-alias, lead-removed, pre-dispatch-deduped roster. Codex-only must not invoke `peer grok` or `peer trio`. Grok-only must not invoke `peer codex` or `peer trio`. On medium, both peer commands consume `$DISPATCH_INPUT` (the verified redacted artifact), **not** raw `$DRAFT`.

### Optional fleet leg (policy + consent)

Fleet medium redaction is **distinct from peer redaction**:

| Path | Medium gate | Medium input |
|-|-|-|
| External peer (`peer codex` / `peer grok`) | Trusted `IDENTIFIED_REDACTION_PATH` | Verified redacted `$DISPATCH_INPUT` only |
| FleetFuse | FleetFuse scrubber availability (`fleet_scrub`, fail-closed inside fleet-fuse) | Raw local `$DRAFT` is allowed because fleet-fuse **must** apply `fleet_scrub` before any outbound provider call |

The fleet gate requires FleetFuse scrubber availability/configuration, **not**
`IDENTIFIED_REDACTION_PATH`, unless peer lanes are also configured (peer still
needs its own path). Missing/failing fleet scrubber → `redactor-unavailable`.
**Never** pass `--no-redact`.

Run the fleet leg only when all are true:

- `ESAT_FRONTIER_FLEET=1` or `fleet` is on the resolved roster
- Sensitivity is `medium` or `low` (not `high`, not invalid)
- External-route permission allows it
- FleetFuse scrubber is available/configured for medium (see table above). Missing/failing → fail-closed `redactor-unavailable`. Do **not** require `IDENTIFIED_REDACTION_PATH` for the fleet gate alone.
- Metered consent accepted for **this run** only: direct current-invocation instruction **or** interactive current-run answer
- Budget absent (disclose `provider/account cap only`) or positive numeric; invalid fails closed
- `fleet-fuse` is available and configured

Rejected consent sources (each distinct): environment, project/user config, inherited shell state, expired consent, prior-run answers. Without accepted consent, append a terminal blocked/skipped result and **do not** enter the consented branch below (omit the metered-consent CLI flag entirely).

```bash
# CONSENTED BRANCH ONLY — current-invocation or interactive current-run consent required.
# $DRAFT still exists; owner EXIT trap remains armed until Final owner cleanup.
# Medium fleet input may be raw local $DRAFT: fleet-fuse applies fail-closed fleet_scrub
# before any outbound provider call. Never pass --no-redact. Fleet gate is scrubber
# availability, not IDENTIFIED_REDACTION_PATH (peer path remains separate above).
TIER="${ESAT_FRONTIER_SENSITIVITY:-medium}"
FLEET_DISABLED_POOLS=grok,codex python3 "${FLEET_FUSE_PY:-fleet-fuse.py}" \
  "$(cat "$DRAFT")" \
  --sensitivity "$TIER" --enable-external \
  --yes-metered \
  --return-mode full --max-return-chars 8000 \
  ${ESAT_FRONTIER_BUDGET_USD:+--budget-usd "$ESAT_FRONTIER_BUDGET_USD"}
# Do NOT clean DRAFT/REDACTED here — append terminal results first, then Final owner cleanup.
```

Append a terminal result for every planned lane (including blocked/skipped with `observed_route: null`) before cleanup. No later code may read `$DRAFT` or `$REDACTED`.

### Final owner cleanup

Executable normal-path cleanup — only after the optional fleet command and all terminal results. The EXIT trap remains the timeout/early-exit owner until this runs. Do not claim SIGKILL can be handled. Sequential `rm -f` alone is not timeout-safe.

```bash
# Final owner cleanup — after peer lanes + optional fleet + all terminal results.
# No peer/fleet consumer may read DRAFT / REDACTED after this.
_esat_frontier_owner_cleanup
trap - EXIT
```


## Fusion Rules

- **Consensus**: promote only when multiple **independent** reviewers agree and the lead verifies the claim.
- **Divergence**: preserve disagreement. State what each side saw and which view the evidence supports.
- **Unique catch**: include a single-reviewer catch only if the lead verifies it. Drop unverified external-only claims.
- **Confidence**: adjust action confidence based on verified evidence, not model count alone.
- **No rubber stamp**: the lead must name at least one assumption it checked and either accepted, revised, or rejected.

## Sensitivity Rules

- `high`: do not send proprietary/sensitive content to external clouds. Use local/first-party reviewers only; terminal-skip external roster entries with `observed_route: null`.
- `medium`: external routes require the redaction path that matches the lane:
  - **Peer:** `IDENTIFIED_REDACTION_PATH` is a **trusted executable adapter** from harness/operator trusted configuration — never from the analyzed repository/item/draft or untrusted project content. External peer dispatch input **must** be that path's verified redacted artifact (not raw `$DRAFT`); missing/failing → peer blocked with `redactor-unavailable`.
  - **FleetFuse:** medium input may be raw local `$DRAFT` because fleet-fuse applies fail-closed `fleet_scrub` before outbound provider calls. The fleet gate is FleetFuse scrubber availability/configuration, **not** `IDENTIFIED_REDACTION_PATH` unless peer lanes are also configured. Missing/failing fleet scrubber → fleet blocked with `redactor-unavailable`. Never `--no-redact`.
- `low`: broader external/low-tier pools may run when the resolved readiness flag is true and the user has accepted cost and disclosure risk; dispatch input may be the owner draft when policy permits. Low never bypasses external-route permission, route availability, pin validation, metered consent, budget, or other readiness gates.
- invalid sensitivity or ambiguous route class → fail closed for external routes.

## Output Block

Place this directly above `### Stress Test Notes`:

```markdown
### Frontier Fusion Panel
_Lead: {actual lead model or account default}. Reviewers requested: {roster}. Reviewers run: {actual independent voices}. Sensitivity: {high|medium|low}. Metered consent: {accepted class|n/a|rejected class}. Budget: {$N|provider/account cap only|n/a}._

| Verdict | Detail | Evidence basis |
|-|-|-|
| Consensus | [verified points multiple independent reviewers agreed on] | [repo/doc/user evidence] |
| Divergence | [material disagreements and lead ruling] | [why the ruling follows from evidence] |
| Unique catch | [verified single-reviewer catch, if any] | [how it was verified] |
| Lead adjustment | [what changed in the final analysis because of the panel] | [confidence/action/risk changes] |
| Panel status | full / partial / local-only / blocked | [per-lane actual routes or null; skipped/blocked reasons; non-independent duplicates noted] |
```

For comparison mode, add:

```markdown
| Model | Pick | Key reasoning | Lead ruling |
|-|-|-|-|
| Lead ({actual}) | A/B | | final |
| Sonnet/Codex/Grok/Fleet ({actual or null}) | A/B | | accepted/rejected/partial |
```

When a profile alias or fallback was used, add a compact mapping note:

```markdown
_Profile mapping: requested `Fable` -> lead `{actual route}`; requested `Codex Medium` -> reviewer `{actual route or null}`; skipped `{label}` because {reason}._
```
