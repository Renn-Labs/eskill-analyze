# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
