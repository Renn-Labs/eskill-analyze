# Roadmap

eskill-analyze is a harness-neutral analysis engine: triage a request, apply only the frameworks that fit,
stress-test at the rigor the stakes deserve, and emit a prioritized, buildable action plan. The roadmap keeps
the core *selective, not exhaustive* and the three tiers strict supersets of each other.

## Who it's for

- **Solo builder / staff engineer** deciding what to build to make something world-class, not just "good enough".
- **Tech lead** who wants a second (and third) frontier-model opinion on a high-stakes architecture or build-vs-buy call.
- **Anyone** who wants a repeatable analysis with an honest confidence rating, not a wall of generic advice.

## Now (v1.0)

- Three installable tiers (`/esa`, `/esat`, `/esat-fleet`) sharing one engine and output contract.
- Triage-driven framework selection (13-model toolkit), evidence Phase 0, comparison mode.
- `install.sh` (symlink/copy, multi-harness), structural CI, security/governance docs.

## Next

- **Plugin packaging** (`/plugin install eskill-analyze@renn-labs`). *Blocked on portability:* the tiers
  cross-reference each other via `~/.claude/skills/...` absolute paths, which don't resolve from a plugin cache
  dir. Requires converting cross-skill references to a relocatable form first, without breaking the verified
  skill bodies. Tracked as the top pre-plugin task.
- More worked **examples** under `examples/` (product, strategic, comparative — not just technical).
- A short **rubric** for the output's confidence column so ratings are consistent across runs.

## Later / ideas

- Optional machine-readable analysis output (JSON sidecar) for piping into a sprint planner.
- Pluggable verifier panel — let the trio/fleet roster be configured rather than fixed.
- Harness profiles (à la sibling tools) so non-Claude harnesses get first-class sub-agent delegation.

Issues and discussions shape priority — see [SUPPORT.md](SUPPORT.md) and [CONTRIBUTING.md](CONTRIBUTING.md).
