# Roadmap

eskill-analyze is a harness-neutral analysis engine: triage a request, apply only the frameworks that fit,
stress-test at the rigor the stakes deserve, and emit a prioritized, buildable action plan. The roadmap keeps
the core *selective, not exhaustive* and the tiers strict supersets of the shared engine.

## Who it's for

- **Solo builder / staff engineer** deciding what to build to make something world-class, not just "good enough".
- **Tech lead** who wants a second (and third) frontier-model opinion on a high-stakes architecture or build-vs-buy call.
- **Anyone** who wants a repeatable analysis with an honest confidence rating, not a wall of generic advice.

## Now (v1.0)

- Four installable tiers (`/esa`, `/esat`, `/esat-fleet`, `/esat-frontier`) sharing one engine and output contract.
- Triage-driven framework selection (13-model toolkit), evidence Phase 0, comparison mode.
- **Two install paths**: Claude Code plugin (`/plugin install eskill-analyze@renn-labs`) and `install.sh`
  (symlink/copy, multi-harness). Cross-skill references are relocatable (`${CLAUDE_SKILL_DIR}/../<sibling>/`),
  so the tiers resolve under both layouts.
- Structural CI (frontmatter, no abs paths, cross-ref + manifest validation), security/governance docs.

## Next

- More worked **examples** under `examples/` (product, strategic, comparative — not just technical).
- A short **rubric** for the output's confidence column so ratings are consistent across runs.

## Later / ideas

- Optional machine-readable analysis output (JSON sidecar) for piping into a sprint planner.
- Harden the frontier roster contract with harness profiles for model labels such as Fable, Sonnet 5, Codex Medium, and Grok.
- Pluggable verifier panel — let every tier use a configured roster rather than fixed defaults.
- Harness profiles (à la sibling tools) so non-Claude harnesses get first-class sub-agent delegation.

Issues and discussions shape priority — see [SUPPORT.md](SUPPORT.md) and [CONTRIBUTING.md](CONTRIBUTING.md).
