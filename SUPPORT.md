# Support

Use **GitHub Issues** for reproducible bugs, documentation gaps, and install problems. Use **GitHub Discussions**
(if enabled) for open-ended usage questions — triage strategy, framework selection, comparing the three tiers.

## Before opening an issue

- Re-run with the triage line visible — the skill states `**Triage**: {type} / {scale}` and which agents/models
  it activated. Paste that; it's the fastest way to see why the output looked the way it did.
- For the trio/fleet tiers, note whether `peer` / `fleet-fuse` were available, and which `ESKILL_PEER` /
  `ESAT_FLEET` / `ESAT_FLEET_SENSITIVITY` values you ran with.
- Confirm the skills are installed where your harness looks (`~/.claude/skills/` by default — see `install.sh`).

## What to include

- Harness (Claude Code / Codex / Grok / other) and OS.
- The analysis request you gave and the four inputs (Project / Focus Area / Current State / World-Class Definition).
- Expected vs. actual output. Redact anything proprietary — never paste secrets or private code into an issue.

## Boundaries

Maintainers can help with the skills and the installer. Problems with the companion CLIs (`peer`, `fleet-fuse`)
or with a model provider's account/billing belong to those projects' or providers' channels.
