<!-- Thanks for contributing to eskill-analyze! See CONTRIBUTING.md. -->

## What & why
<!-- One or two lines: the change and the problem it solves. -->

## Checklist
- [ ] `python3 tests/test_structure.py` passes
- [ ] `shellcheck install.sh` is clean (CI runs it)
- [ ] `install.sh` still installs + uninstalls into a temp `HOME` (CI runs the smoke)
- [ ] Docs updated (README / the relevant `SKILL.md` / `references/`) if behavior changed

## Invariants (eskill-analyze keeps these — confirm none are broken)
- [ ] **Selective, not exhaustive** — no forced/empty sections; a change must be able to alter a recommendation
- [ ] Tier supersets intact — `esat` reuses `eskill-analyze` verbatim; `esat-fleet` reuses `esat` verbatim; only Phase 9 is overridden
- [ ] No absolute, user-specific paths (`~/.claude/skills/...` or env vars only)
- [ ] No new hard dependency; graceful degradation when `peer` / `fleet-fuse` / sub-agents are absent
- [ ] External model output stays untrusted advisory — maker ≠ checker
