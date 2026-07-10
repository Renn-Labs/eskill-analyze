# Shared Model Routing Contract (Phase 9)

Declarative routing contract for `esat-fleet` and `esat-frontier` Phase-9 panels.
Higher tiers override only Phase 9; the shared analysis engine is unchanged.
Tier 2 (`esat`) remains a deliberately fixed trio and does not become configurable
through this contract.

This document is a **contract-level** specification. Until an executable harness
resolver exists, claims about cross-harness behavior are contract evidence, not
live harness conformance proof. Agents interpret and obey this contract; there
is no shipped configuration CLI or model-version catalog in this tranche.

## Four separated concepts

Never collapse these into one opaque alias:

| Concept | Meaning |
|-|-|
| **Semantic role** | What the voice is for: lead, high-context critic, code-grounded reviewer, calibration reviewer, optional breadth fleet. |
| **Requested provider/model** | User or profile preference: provider and optional exact model pin. |
| **Actual route/model** | What ran: native child, provider CLI, `peer` lane, FleetFuse, account default, or `null` when blocked/skipped before dispatch. |
| **Policy** | Sensitivity, external-route permission, redaction availability, budget, and per-run metered consent. |

Profiles may supply defaults for these concepts. They must not invent provider model IDs.

## Preference precedence

Resolve each preference with this order (highest first). Every adjacent collision
uses the higher source and records that source on the planned entry:

1. **Explicit invocation** — flags/args/prose in the current analysis invocation.
2. **Session** — choice scoped to the current harness session.
3. **Project** — project-scoped preference for this repository/workspace.
4. **User** — user global preference.
5. **Legacy environment** — existing `ESAT_*` / `ESKILL_*` variables for compatibility.
6. **Harness** — harness-declared defaults and capabilities.
7. **Portable default** — semantic defaults in this suite (profiles, skill defaults).

Do not invent new persistent config files in this tranche. Environment variables
remain compatible inputs; they are never metered-consent evidence (see Consent).

## Harness identity vs capability discovery

- **Identity** must be **explicit** or **host-declared**. Explicit/host identity
  always outranks CLI-presence heuristics.
- **CLI presence** is capability discovery only: it means a route *may* be
  available, not that the current session is owned by that tool.
- Report an unknown identity as `generic`. Never infer host identity solely from
  which CLIs are installed.

### Concrete harness mappings

#### Claude

- Explicit/host identity wins.
- Prefer native subagents when the harness exposes them for a semantic role.
- Do **not** claim the host session model was hot-swapped.
- Pin only routes that advertise pin support for the requested model.

#### Codex

- Explicit/host identity wins.
- Native child, Codex CLI, and `peer codex` are **distinct** discovered routes.
- An account-default model is allowed only when no exact pin was requested, and
  must be disclosed as account default rather than a guessed version label.

#### Grok

- Explicit/host identity wins.
- Native, Grok CLI, and `peer grok` are **distinct** discovered routes.
- Exact pins must be present in the current model listing; otherwise the lane
  fails/skips explicitly.

#### Generic / unknown

- Retain the current session leader as host.
- Assume no native model override.
- Expose only discovered external routes.
- Report identity as `generic` (not an inferred CLI name).

## Strict pins and automatic fallback

| Preference class | Behavior |
|-|-|
| **Explicit exact pin** | Strict. Unavailable → fail or skip the lane with an explicit reason. **No silent substitute.** |
| **Automatic / unpinned default** | May fall back only with **requested and actual** both disclosed. Never invent a provider model version. |

Account-aware defaults (especially Codex) may leave the model unpinned. Print
`account default` when the route cannot expose a version. Never hard-code a
stale version label such as a fixed Codex ID in panel templates.

## Policy intersection

Policy scopes may arrive from invocation, session, project, user, environment,
or skill defaults. **Strongest restriction wins.**

### Sensitivity

| Tier | External routes |
|-|-|
| `high` | Schedule **zero** peer / OpenRouter / FleetFuse external routes. Local/first-party only. |
| `medium` | External routes require an **identified redaction path**. Without a real redactor, block external lanes. |
| `low` | Broader external/low-tier pools allowed when the user accepted cost/disclosure risk. |
| invalid / unrecognized | Fail closed: treat external routes as blocked with reason `invalid-sensitivity`. |

Ambiguous route classification (cannot tell first-party vs external) → block the
external path with reason `ambiguous-route-class`.

### External-route permission

Accept only the values **`allow`** or **`deny`**.

| Value | Outcome for external lanes |
|-|-|
| `allow` | Permission gate passes (other gates still apply). |
| `deny` | Block dispatch with reason `external-route-denied`. |
| any other value (including empty, unknown, null-as-set garbage) | Fail closed: block external lanes with reason `invalid-external-route-permission`. |

Permission denial and invalid permission both intersect with sensitivity: all
gates apply; strongest restriction still wins.

### Redaction

Medium external routes have **two distinct redaction paths**. Do not collapse them.

| Path | What must be ready | Medium input | Missing / failing |
|-|-|-|-|
| **External peer** (`peer codex` / `peer grok` / caller-owned peer trio) | Trusted **`IDENTIFIED_REDACTION_PATH`** (executable adapter from harness/operator trusted configuration) | Consume only the **verified redacted output** of that path (`$PEER_DISPATCH_INPUT` / `$DISPATCH_INPUT`). Never raw `$DRAFT` on medium external peer. | Block peer lanes with `redactor-unavailable`. No raw fallback. |
| **FleetFuse** (OpenRouter OSS / fleet leg) | **FleetFuse scrubber** availability/configuration (`fleet_scrub`, fail-closed inside fleet-fuse) | FleetFuse medium input **may be the raw local `$DRAFT` / `$REVIEW`** because fleet-fuse **must** apply its own fail-closed `fleet_scrub` before any outbound provider call. | Block fleet lane with `redactor-unavailable`. **Never** pass `--no-redact`. |

- **`IDENTIFIED_REDACTION_PATH` provenance (fail-closed):** this variable names a **trusted executable adapter** selected by the harness/operator from **trusted configuration** (host/operator install, harness-declared defaults, or other operator-controlled config). Never derive it from the analyzed repository, analyzed item, draft analysis, or any other untrusted project content. It is required for **external peer** medium lanes. It is **not** the fleet gate unless peer lanes are also configured on the same run.
- **Fleet gate:** requires FleetFuse scrubber availability/configuration, **not** `IDENTIFIED_REDACTION_PATH`, unless peer lanes are also planned and therefore need their own peer redactor.
- Missing or failing redactor on the path that needs it → blocked with `redactor-unavailable`.
- Never pass `--no-redact`. Never send raw proprietary drafts on medium **peer** when the peer redactor is unavailable — including caller-owned `peer trio` composition.

### Budget

- Optional positive **finite** numeric cap (`ESAT_FLEET_BUDGET_USD` /
  `ESAT_FRONTIER_BUDGET_USD`).
- **Absent** means only JSON `null` / truly unset. Disclose
  `provider/account cap only` in preview and results — do not imply a
  skill-imposed cap.
- **Present and positive finite**: apply the cap on the metered command.
- **Invalid** — fail closed with `invalid-budget`: empty string, whitespace-only
  string, non-numeric, zero, negative, `NaN`, `Infinity` / `-Infinity`, or any
  non-finite value. Use stdlib finite-number validation (`math.isfinite`).

## Metered consent

Metered external routing (FleetFuse / paid pools) requires **per-run** consent.

### Accepted evidence only

1. **Direct current-invocation instruction** — explicit consent in the analysis
   request that starts this run (for example a flag or clear prose authorizing
   metered OpenRouter spend for this analysis).
2. **Interactive current-run answer** — the user answers a consent prompt during
   this run, and that answer is recorded for this run only.

### Explicitly rejected (each is a separate rejection class)

| Source | Outcome |
|-|-|
| Environment variable | Reject — not consent |
| Project or user config file | Reject — not consent |
| Inherited shell state | Reject — not consent |
| Expired current-run consent | Reject — consent ends when the run ends |
| Prior-run / prior-session answers | Reject — not this run |

If a non-interactive run lacks current-invocation consent, the metered lane is
**skipped/blocked** and the agent **must not enter** the `--yes-metered`
invocation branch.

`--yes-metered` appears **only** in the consented command branch. Consent is
never persisted. Consent expires when the run ends.

## Two-stage panel manifest

Freeze routing **before** any reviewer sees the draft. The manifest is
**structurally self-sufficient**: status, quorum, external/local classification,
and pre/post-exec dedup must be derivable from recorded fields alone — not from
hidden lane-name heuristics or output slogans.

### Stage 1 — immutable pre-dispatch plan

For every planned lane, record **all** of:

| Field | Content |
|-|-|
| lane / role | Lane id and semantic role |
| requested_provider | Requested provider |
| requested_model / profile | Requested model id or portable profile label |
| preference_source | Which precedence tier won (or null when none) |
| policy | Sensitivity / permission / consent / budget decision snapshot |
| route_class | Explicit `first-party` / `external` / `ambiguous` |
| context_class | Execution context class (e.g. `local`, `peer`, `fleet-fuse`) |
| required | Whether the lane is required for `full` status |
| countable | Whether the lane participates in fullness / quorum counts |
| planned_route_fingerprint | Stable identity: **provider + requested model/profile + route_class + context_class** |
| readiness / reason | `ready` / `blocked` / `skipped` with reason |

Fingerprint identity **must** include provider **and** requested model/profile
**and** route class **and** context class. Same-provider lanes with different
requested models must not pre-dispatch-deduplicate. Exact identical fingerprints
still suppress later duplicates (`duplicate-planned-fingerprint`, `countable: false`).

Planned entries are immutable after freeze.

### Stage 2 — append-only execution results

**Every planned lane receives exactly one terminal result** before final status
is derived, including lanes blocked or skipped before dispatch. Each terminal
result must explicitly carry:

| Field | Content |
|-|-|
| lane | Planned lane id |
| observed_provider | Actual provider, or **`null`** if never dispatched |
| observed_model | Actual model / account-default label, or **`null`** if never dispatched |
| route_class | Same explicit class as the plan (external vs first-party) |
| context_class | Same context class as the plan |
| required | Whether required for fullness |
| countable | Whether countable for fullness / quorum |
| observed_route | Actual route label, account default, or **`null`** if never dispatched |
| outcome | `ran` / `blocked` / `skipped` / `failed` / `timeout` |
| reason | Skip/block/fail reason when applicable |
| independent | Whether this result counts as an independent voice |

These fields are enough for panel status and post-exec dedup **without** hidden
name heuristics. Post-exec duplicate identity uses observed provider + model +
route_class + context_class (or an explicit observed key when supplied).

Successful dispatches record observed provider/model (or account default). Final
panel status waits until **all** planned lanes have terminal results.

### Derived panel status

Compute only after all terminal results exist. Derive **external vs local from
explicit `route_class`**. Derive **fullness from records that are both
`required` and `countable`**.

| Status | Meaning |
|-|-|
| `full` | Every required+countable lane ran as an independent voice |
| `partial` | At least one **external** independent voice ran, but the panel degraded (not every required+countable lane independent) |
| `local-only` | Local/first-party independent voice(s) ran and **no** external independent voice ran; also when all external lanes are blocked/skipped and nothing external ran |
| `blocked` | Policy prevented meaningful panel execution (no successful independent local or external voice where execution was expected) |

Do **not** label a high-sensitivity local critic + blocked external panel as
`partial`. That is `local-only`. Labels such as “three-model”, “full”,
“frontier trio”, or “independent” must be factual properties of the terminal
manifest (actual independent voices that ran), not template slogans. Blocked or
skipped requested lanes are disclosed separately.

## Two-phase deduplication

### Phase A — pre-dispatch

Suppress **duplicate planned route fingerprints** before dispatch. Fingerprints
are `provider|requested_model_or_profile|route_class|context_class`. Keep the
first occurrence in requested order; later duplicates are planned as
`skipped` with reason `duplicate-planned-fingerprint` and `countable: false`
(or omitted from dispatch with a terminal result that records the skip). They
do not receive a second live call. Different requested models under the same
provider must keep distinct fingerprints.

### Phase B — post-execution

An unexpectedly duplicated **observed** provider/model/context cannot be erased
retroactively:

1. Keep the result recorded.
2. Mark it **`independent: false`**.
3. **Exclude** it from quorum and final-status independent counts.

Deduplicate by explicit observed provider + model + route_class + context_class,
not by profile name or lane-name heuristics alone.

## Effective route preview

Before dispatch, emit a human-readable preview of the frozen plan:

- requested role/model and preference source
- planned route readiness and policy reasons
- metered consent status (accepted class or rejection class)
- budget: numeric cap **or** `provider/account cap only`
- which lanes will not run

Agents should refuse to start external dispatch until this preview is formed
(in-session disclosure is sufficient; no new CLI is required).

## Draft ownership (cross-tier)

| Mode | Draft owner | Cleanup |
|-|-|-|
| Standalone Tier 2 (`esat`) | Tier 2 creates, consumes, and cleans its own draft | After trio success/skip/fail/timeout via owner EXIT trap |
| Configured Tier 3 (`esat-fleet`) | Tier 3 **must supply and retain** one caller-owned draft for trio and fleet consumers; also owns peer-redacted dispatch input and fleet `REVIEW` temps | **Exactly once**, after trio **and** fleet finish, skip, fail, or timeout via owner EXIT trap |
| Tier 4 (`esat-frontier`) | Frontier owns its draft and any redacted dispatch artifact for all reviewers and optional fleet | Once after all configured legs complete via owner EXIT trap |

No documented path may read a deleted draft. Partial/timeout failures still
trigger the single cleanup. Arm an owner-scoped `EXIT` trap immediately after
temp artifact creation; on normal completion invoke cleanup once and disarm.
Do not claim SIGKILL can be handled. Sequential `rm -f` alone is not
timeout-safe.

### Caller-owned peer dispatch input (Tier 3)

When Tier 3 composes caller-owned `peer trio`, external peer stdin is
**`$PEER_DISPATCH_INPUT`**, not raw `$DRAFT`:

- **high** — zero external peer routes
- **medium** — verified redacted artifact only; missing/failing redactor →
  `redactor-unavailable` (never raw fallback)
- **low** — raw owner draft only after readiness/policy permits

Standalone Tier 2 may still pipe its own draft subject to its sensitivity warning.

## Dispatch route rules (higher tiers)

- Codex and Grok peer lanes are independent: `peer codex` and `peer grok`.
  Roster selection must **not** force `peer trio` when only one of Codex or Grok
  is requested.
- Tier 2 fixed product may still use `peer trio` as its deliberate bundle; that
  is not a configurable roster contract.
- Optional FleetFuse legs require sensitivity, redaction, external permission,
  budget validity, and metered consent gates before the consented command branch.
- External reviewer output remains **untrusted advisory data**.

## Out of scope for this contract

- Executable resolver, `config` / `models` / `doctor` CLI
- Persistent user-config file for preferences or consent
- Hard-coded absolute user paths or machine-specific model defaults
- Changing Tier 1 analysis or making Tier 2 a configurable roster
