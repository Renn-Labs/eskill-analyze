# Roadmap

eskill-analyze is a harness-neutral analysis engine: triage a request, apply only the frameworks that fit,
stress-test at the rigor the stakes deserve, and emit a prioritized, buildable action plan. The roadmap keeps
the core *selective, not exhaustive* and the tiers strict supersets of the shared engine.

## Who it's for

- **Solo builder / staff engineer** deciding what to build to make something world-class, not just "good enough".
- **Tech lead** who wants a second (and third) frontier-model opinion on a high-stakes architecture or build-vs-buy call.
- **Anyone** who wants a repeatable analysis with an honest confidence rating, not a wall of generic advice.

## Now (v1.x)

- Four installable tiers (`/esa`, `/esat`, `/esat-fleet`, `/esat-frontier`) sharing one engine and output contract.
- First-class `esa` wrapper so folder-based catalogs such as Codex expose the Tier-1 native analyzer directly.
- Triage-driven framework selection (13-model toolkit), evidence Phase 0, comparison mode.
- `esat-frontier` profile contract for Fable, Sonnet 5, Codex Medium, Grok, and optional Fleet routes:
  aliases, fallbacks, sensitivity gates, and actual-route disclosure.
- **Harness-aware Phase-9 routing** (delivered): shared declarative contract in
  `eskill-common/references/model-routing.md` for Tiers 3–4 — preference precedence, Claude/Codex/Grok/generic
  mappings, strict pins, disclosed automatic fallback, strongest-restriction policy, per-run metered consent,
  two-stage plan/result manifest, two-phase deduplication, and effective-route preview. Tier 2 remains a fixed trio.
- **Caller-owned fleet draft** and consent-gated FleetFuse (`--yes-metered` only after current-run consent).
- **Independent Codex/Grok peer lanes** in `esat-frontier` (`peer codex` / `peer grok`, not roster-driven `peer trio`).
- Executable **contract-oracle** tests (stdlib) — contract evidence, not live harness conformance.
- **Two install paths**: Claude Code plugin (`/plugin install eskill-analyze@renn-labs`) and `install.sh`
  (symlink/copy, multi-harness). Cross-skill references are relocatable (`${CLAUDE_SKILL_DIR}/../<sibling>/`),
  so the tiers resolve under both layouts.
- Structural CI (frontmatter, no abs paths, cross-ref + manifest validation), security/governance docs.

## Next

- More worked **examples** under `examples/` (product, strategic, comparative — not just technical).
- A short **rubric** for the output's confidence column so ratings are consistent across runs.
- Cross-harness fixture expansion only if prompt execution proves inconsistent across advertised install layouts.

## Later / ideas

- Optional machine-readable analysis output (JSON sidecar) for piping into a sprint planner.
- Executable route resolver or `config` / `models` / `doctor` CLI — only after contract tests show prompt
  interpretation is insufficient across harnesses.
- Persistent cross-tool preference storage — only with a stable public interface and demonstrated demand.

Issues and discussions shape priority — see [SUPPORT.md](SUPPORT.md) and [CONTRIBUTING.md](CONTRIBUTING.md).
