# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Notes
- Prior post-1.0.0 tree changes that were still listed as unreleased before the Phase P
  ship are recorded under **[1.1.0]** only for Phase P; remaining historical unreleased
  notes:

### Added
- **`esa`** (`/esa`): a first-class short Tier-1 wrapper around the original
  `eskill-analyze` engine so Codex and other folder-based skill catalogs expose
  the native in-session analyzer directly instead of relying on alias metadata.
- **Tier 4 — `esat-frontier`** (`/esat-frontier`): a frontier-led configurable
  fusion panel. Reuses the `eskill-analyze` engine, then makes a frontier lead
  such as Fable synthesize independent reviewers such as Sonnet 5, Codex Medium,
  Grok, and optional fleet/OpenRouter voices.
- Frontier model profile contract for `esat-frontier`: portable aliases,
  fallback behavior, sensitivity gates, and requested-profile vs actual-route
  disclosure for Fable, Sonnet 5, Codex Medium, Grok, and Fleet.
- **Harness-aware Phase-9 routing contract** in
  `skills/eskill-common/references/model-routing.md`: semantic role vs
  requested vs actual route vs policy; preference precedence (invocation >
  session > project > user > legacy environment > harness > portable default);
  Claude/Codex/Grok/generic harness mappings; strict pins; disclosed automatic
  fallback; strongest-restriction policy; external-route permission; sensitivity
  and redaction gates; per-run metered consent; optional budget with
  provider/account-cap-only disclosure; two-phase deduplication; two-stage
  panel manifest (immutable plan + append-only terminal results).
- Stdlib **contract-oracle** tests and JSON fixture matrix under `tests/`
  (contract evidence; not live harness conformance).

### Changed
- **Installer safety**: installations now refuse unowned collisions by default,
  mark owned copies, serialize concurrent runs, stage replacements, and restore
  prior targets if a swap fails. `--force` remains the explicit destructive path.
- **`esat-fleet`**: caller-owned draft retained across trio and fleet consumers
  with single cleanup after success/skip/failure/timeout; FleetFuse uses
  `--yes-metered` only after accepted current-run consent; blocked/skipped lanes
  record terminal results with `observed_route: null`.
- **`esat-frontier`**: independent `peer codex` / `peer grok` dispatch (no
  roster-driven `peer trio`); exact pins fail closed; actual/account-default
  model disclosure; fleet consent and budget gates align with Tier 3.
- **`esat` trio panel**: explicit standalone vs caller-owned draft contract;
  panel templates disclose actual model or account default instead of a fixed
  Codex version label.
- Skill frontmatter limited to `name` + `description` (unsupported `aliases` /
  `user-invocable` keys removed; activation language preserved in descriptions).
- README/ROADMAP document routing inputs, precedence, preview/manifest, consent,
  degradation, and delivered harness-aware Phase-9 status.

### Fixed
- Fleet leg no longer depends on a draft deleted by the trio panel.
- Non-interactive metered FleetFuse path no longer omits required per-run consent.
- Frontier Codex-only / Grok-only rosters no longer over-dispatch via `peer trio`.
- **Medium Tier-3 peer egress**: caller-owned `peer trio` consumes
  `$PEER_DISPATCH_INPUT` (verified redacted artifact) rather than raw `$DRAFT`;
  missing/failing `IDENTIFIED_REDACTION_PATH` blocks peer dispatch.
- **Timeout-safe temp cleanup**: owner-scoped EXIT traps for DRAFT / REVIEW /
  REDACTED temps in standalone `esat`, `esat-fleet`, and `esat-frontier`
  (normal path cleans once then disarms; timeout still hits the trap).
- Routing oracle panel status: local independent voices with no external
  independent voice yield `local-only` (not `partial`); high-sensitivity reasons
  are not masked by fleet/peer availability ordering.

## [1.2.0] — 2026-10-18 (not tagged)

Depth without bulk: the engine asks for a deeper version of each task, not a bigger one, and runs only
the modules a question needs. Deepening questions follow Felix Rieseberg, "How to be more ambitious: A
tutorial for humans with models" (2026-10-13).

### Added
- **Elastic router** (`references/triage-guide.md`): Atom-of-Thoughts waves. Wave 1 answers outcome,
  sufficiency, premise and options in-session; wave 2 selects modules (evidence, premortem, borrow,
  actions); wave 3 sizes the independent check. Invariants: an outside verifier per action, raw/digested
  tags on cited evidence, Phase P on irreversible decisions at any scale, security-reviewer on security
  signals, checker ≠ maker at `deep`. Escalate-up and contradiction rules.
- **Module entry points**: `/esa deepen`, `/esa evidence`, `/esa premortem`, `/esa verify`, each with an
  output contract, so a harness or another skill can call one module.
- **Deepening questions**, answered internally: the expert move, the rawest material, the field's
  instruments, and what other than the model or user shows the result is right. Each surfaces where it
  belongs (Evidence, the analysis, the Verifier column, an action or reframe), never as its own block.
- **Lenses as atom generators**: Depth (instruments over vocabulary), Range (borrow one field's
  technique), Altitude (outcome reframe).
- **Verifier column** in both action tables, with `none — unverifiable` forcing Confidence L.
- **Depth check** in every Phase 9 reviewer prompt (critic, `esat` trio, `esat-fleet` fleet leg,
  `esat-frontier` critic and peers). Anti-slop rule 12: vocabulary is not a method.
- **Depth eval harness** (`tests/eval/`): engine builder with leave-one-out ablation, isolated no-tool
  runner, blind order-swapped pairwise judge on another model family, deterministic metrics, route audit,
  route stability, 20 adversarial prompts and 4 entry-point prompts.
- `test_depth_contract`; `test_engine_word_budget` holds the engine at or below the 1.1.0 size (4969 words).

### Changed
- One terse Route line replaces the Triage header; sections appear only when their module ran; body
  headings follow the question, not the framework; Evidence lists only what was read.
- Phase 0 reads raw sources first; the document-specialist looks for primary sources, not benchmarks.
- Mandatory checks (premortem keywords, invariants, stakes) run before the inline exit, and stakes override
  scale. A missing input triggers a question when it would change the answer, not only the route. World-
  Class Criteria run with Actions or world-class language. Execution principles trimmed to two.
- `esa`, `esat`, `esat-fleet`, `esat-frontier` wording aligned to the router. README engine steps updated.

### Evaluation (Claude Sonnet generator in a no-tool harness unless stated; blind pairwise judges)
- What the scores measure: which analysis proposes rawer sources, runnable methods and outside checks —
  not retrieval or checks actually carried out. Each prompt is judged in both orders and pooled; a prompt
  whose winner flips with the order counts as a tie.
- Round 1, 25 prompts: a pre-elastic draft beat 1.1.0 on content (23 of 25) but lost on leanness (3 vs 14)
  and in maintainer blind ratings, so its display blocks were removed. Leave-one-out ablation, n=5 each,
  indicative only: without the deepening step the draft lost 4 of 5; without the Verifier column, 3 of 5
  (2 ties); without the lenses, 2 of 5 (2 ties).
- Held-out, 27 real prompts never used for tuning, shipped engine vs 1.1.0, Codex judge: 22 wins, 4 ties,
  1 loss (89%); shape 91%, lean 80%, proposed outside verifier 83%, raw material 93%; median 1457 vs 1624
  words. Two of 27 prompts changed winner when the order was swapped.
- Second judge family, GLM-5.2, on the 20 synthetic prompts: 18 wins, 1 tie, 1 loss (Codex: 20 of 20).
  On an earlier build the two judges picked the same winner on 18 of 20 pairs.
- Judge behavior, from 552 verdicts: the second slot wins 59%, which is why orders are swapped. Depth
  criteria favor longer answers and lean/shape favor shorter ones; overall they roughly cancel.
  Comparisons between close engine versions flipped on 7–11 of 24 prompts, and the same engine judged
  against itself scored 9 wins, 10 ties, 5 losses on 24, so loop-to-loop differences were not resolvable.
- Router, same engine twice on 20 prompts: inline-vs-analyze agreed on 19 of 20, scale on 19,
  the exact module set 8. Flips concentrate in the stress test (7) and borrowed techniques (5); premortem
  flipped once, security twice. Across 40 audited runs one required module was dropped: an evidence probe
  a no-tool run cannot satisfy. Route audit: 18 and 19 of 19 probes.
- Live, Claude Opus with read-only tools, 4 asks: every run read real material and tagged it raw (up to 36
  distinct file references); one tested the installer twice in a throwaway home directory; one fit a
  statistical model to 552 raw judge verdicts and proposed a padding experiment as its check.
- Gains belong to the bundle: routing, wording, format and checks changed together. Adversarial reviews
  by gpt-6-astra and GLM-5.2 found the inline exit could skip mandatory checks; fixed before the held-out
  re-measurement above. Maintainer ratings on held-out pairs are pending.

## [1.1.0] — 2026-08-08

### Added
- **Phase P — Premortem Cycle** in the shared analysis engine (`eskill-analyze` /
  `/esa`): after provisional prioritized actions and **before** Phase 9, scale-gated
  failure modes, kill criteria, and action deltas (standard compact / deep full;
  quick only with premortem keywords).
- Output template `### Premortem Cycle` (and shared comparison variant).
- Phase P anti-slop rule (no boilerplate risks; falsifiable kill criteria).
- Higher-tier Phase 9 prompts (`esat` trio, `esat-fleet` fleet leg, `esat-frontier`
  fusion) attack premortem kill criteria when Phase P ran.

### Changed
- Step 6 retitled to **Inversion Seed** (feeds Phase P; not a full risk matrix).
- Triage phase table includes Phase P activation by scale.
- Example `examples/technical-rate-limiter.md` shows a full Premortem Cycle block.

## [1.0.0] — 2026-06-28

First open-source release. Bundles the full three-tier analysis suite plus the
shared engine.

### Added
- **Tier 1 — `eskill-analyze`** (`/esa`, `/eo`): triage-driven world-class
  level-up analysis engine — evidence gathering (Phase 0), 13-model mental-model
  toolkit, 8 analysis steps, discretionary single-critic stress test (Phase 9),
  comparison mode, and standard + comparison output templates.
- **Tier 2 — `esat`** (`/esat`): reuses the engine verbatim and replaces Phase 9
  with a mandatory three-frontier-model panel (harness critic + Codex + Grok via
  `peer trio`), with untrusted-input synthesis rules and `ESKILL_PEER` kill-switch.
- **Tier 3 — `esat-fleet`** (`/esat-fleet`, `esatf`): reuses `esat` verbatim and
  adds a fourth review leg — an OpenRouter open-model swarm via `fleet-fuse` —
  sensitivity-tiered (`high`/`medium`/`low`), redacted fail-closed, folded into
  one consensus / divergence / unique-catch synthesis.
- **`eskill-common`**: shared, non-invocable engine references (quality
  principles, anti-slop rules, project-impact protocol).
- `install.sh` (symlink/copy, multi-harness), README, MIT license, DCO
  contributing guide, and Contributor Covenant code of conduct.

### Packaging
- Claude Code **plugin** support: `.claude-plugin/{plugin.json,marketplace.json}` so the
  suite installs via `/plugin install eskill-analyze@renn-labs`. Verified end to end with a
  real isolated `claude plugin install` — all cross-tier references resolve from the plugin cache.

### Portability
- Removed the one hardcoded developer path; the fleet leg resolves `fleet-fuse` via
  `FLEET_FUSE_PY` (with `PATH` fallback).
- Cross-skill references are relocatable (`${CLAUDE_SKILL_DIR}/../<sibling>/`), so the tiers
  resolve under both the plugin cache layout and an `install.sh` (`~/.claude/skills/`) layout.
