# Contributing to eskill-analyze

Thanks for your interest in improving eskill-analyze.

## Developer Certificate of Origin (DCO)

All contributions are accepted under the [Developer Certificate of Origin](https://developercertificate.org/). Sign off every commit:

```bash
git commit -s -m "your message"
```

The `-s` adds a `Signed-off-by: Your Name <you@example.com>` trailer, certifying you wrote the change (or have the right to submit it) under the project's MIT license.

## Ground rules

- **Keep the engine selective.** This project's whole thesis is *fewer, better, actionable*. New mental models, steps, or sections must earn their place — if it can't change a recommendation, it doesn't ship.
- **Preserve the tier relationship.** `esat`, `esat-fleet`, and `esat-frontier` must reuse the `eskill-analyze` engine rather than fork it. Higher tiers override the single documented seam: Phase 9.
- **No new hard dependencies.** Tiers must degrade gracefully when `peer` / `fleet-fuse` / sub-agents are absent. External model output is always treated as untrusted advisory.
- **Portability.** No absolute, user-specific paths. Use `~/.claude/skills/...` (install convention) or env vars (`FLEET_FUSE_PY`).

## Proposing changes

1. Open an issue describing the problem before large changes.
2. Keep PRs focused; one concern per PR.
3. Update the relevant `references/` file and the README table if behavior changes.

## Reporting issues

Include: which tier, the triage the skill chose, the input you gave, and what you expected vs. got. For external-review tiers, note whether `peer` / `fleet-fuse` were available.
