# Release Checklist

Run before tagging a version or changing repository visibility. Targets a standalone public Renn Labs repo.

## Non-negotiable boundaries

- Do not make the repository public without explicit maintainer approval.
- Do not tag a version without explicit maintainer approval.
- Do not commit real config, private analysis outputs, or any secret.

## Offline gates (clean working tree)

```bash
python3 -m pytest -q
python3 tests/test_structure.py                 # frontmatter, no abs paths, cross-refs resolve, README tiers
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/esa
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/esat-frontier
shellcheck install.sh                            # installer is clean
# install/uninstall round-trip into a throwaway HOME:
H="$(mktemp -d)"; HOME="$H" bash install.sh && \
  HOME="$H" bash install.sh --uninstall && \
  [ -z "$(ls -A "$H/.claude/skills")" ] && echo "install smoke OK"; rm -rf "$H"
```

## Launch hazard scan

```bash
! git grep -nE '/(home|Users)/'                 # no absolute user paths
! git grep -nE 'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9_]{36}|-----BEGIN .*PRIVATE KEY-----'
```

## Documentation claims

- README first screen shows the tiers and the zero-dependency install path before external tiers.
- External tiers (`esat`, `esat-fleet`, `esat-frontier`) are documented as potentially sending the draft to
  third-party models, with `ESKILL_PEER`, `ESAT_FLEET_SENSITIVITY`, and `ESAT_FRONTIER_*` controls plus
  graceful degradation.
- Plugin install claims are backed by relocatable cross-skill references and structural tests.
- `CHANGELOG.md` updated for the tag.

## Review gate

- Independent review of any change to the skill bodies, the installer, or the security/data-handling docs.
- Any blocker in the data-handling wording or install correctness prevents tagging.
