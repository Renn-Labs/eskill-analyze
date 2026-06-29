# Release Checklist

Run before tagging a version or changing repository visibility. Targets a standalone public Renn Labs repo.

## Non-negotiable boundaries

- Do not make the repository public without explicit maintainer approval.
- Do not tag a version without explicit maintainer approval.
- Do not commit real config, private analysis outputs, or any secret.

## Offline gates (clean working tree)

```bash
python3 tests/test_structure.py                 # frontmatter, no abs paths, cross-refs resolve, README tiers
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

- README first screen shows the three tiers and the zero-dependency install path before external tiers.
- External tiers (`esat`, `esat-fleet`) are documented as sending the draft to third-party models, with the
  `ESKILL_PEER` / `ESAT_FLEET_SENSITIVITY` controls and graceful degradation.
- No claim that plugin install works until the cross-reference portability task lands (see ROADMAP).
- `CHANGELOG.md` updated for the tag.

## Review gate

- Independent review of any change to the skill bodies, the installer, or the security/data-handling docs.
- Any blocker in the data-handling wording or install correctness prevents tagging.
