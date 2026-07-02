#!/usr/bin/env python3
"""Structural validator for the eskill-analyze skill bundle.

Stdlib only — no pytest, no PyYAML required. Run directly:

    python3 tests/test_structure.py

It also exposes test_* functions so `pytest -q` works if you have it.
Checks the invariants that keep the bundle installable and portable:
  1. Every skill dir has a SKILL.md with `name:` and `description:` frontmatter.
  2. No bundled file contains an absolute, user-specific path (`/home/`, `/Users/`).
  3. Every `~/.claude/skills/<x>/...` cross-reference points to a skill bundled here.
  4. The README documents all tiers.
  5. install.sh exists.
"""
from __future__ import annotations
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
SKILLS = ["eskill-common", "eskill-analyze", "esat", "esat-fleet", "esat-frontier"]


def _frontmatter(text: str) -> str:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    return m.group(1) if m else ""


def test_skill_frontmatter():
    for s in SKILLS:
        skill = SKILLS_DIR / s / "SKILL.md"
        assert skill.is_file(), f"missing {skill}"
        fm = _frontmatter(skill.read_text(encoding="utf-8"))
        assert re.search(r"^name:\s*\S", fm, re.MULTILINE), f"{s}: no name: in frontmatter"
        assert re.search(r"^description:\s*\S", fm, re.MULTILINE), f"{s}: no description: in frontmatter"


def test_no_absolute_user_paths():
    bad = []
    for p in ROOT.rglob("*"):
        rel_parts = p.relative_to(ROOT).parts
        if not p.is_file() or rel_parts[0] in {".git", ".omc", ".omx", "tests"}:
            continue
        if p.suffix not in (".md", ".sh", ".svg", ".txt", ".yml", ".yaml", ".json"):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for token in ("/home/", "/Users/"):
            if token in text:
                bad.append(f"{p.relative_to(ROOT)} contains '{token}'")
    assert not bad, "absolute user paths found:\n" + "\n".join(bad)


def test_no_legacy_absolute_cross_refs():
    # Cross-skill refs must be relocatable (${CLAUDE_SKILL_DIR}/../<sib>/...), not
    # ~/.claude/skills/<sib>/... — the absolute form breaks when installed as a plugin
    # (skills live in the plugin cache dir, not ~/.claude/skills).
    bad = []
    for p in SKILLS_DIR.rglob("*.md"):
        for ln, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if "~/.claude/skills/" in line:
                bad.append(f"{p.relative_to(ROOT)}:{ln}")
    assert not bad, "legacy ~/.claude/skills cross-refs (break plugin install):\n" + "\n".join(bad)


def test_relocatable_cross_refs_resolve():
    # Every ${CLAUDE_SKILL_DIR}/../<sib>/<path> must point at a real bundled file.
    # CLAUDE_SKILL_DIR == skills/<owner>, so ../<sib>/<path> == skills/<sib>/<path>.
    pat = re.compile(r"\$\{CLAUDE_SKILL_DIR\}/\.\./([a-z0-9-]+)/([^\s`)]+)")
    bad = []
    for p in SKILLS_DIR.rglob("*.md"):
        for sib, rel in pat.findall(p.read_text(encoding="utf-8")):
            if sib not in SKILLS:
                bad.append(f"{p.relative_to(ROOT)} -> unknown skill '{sib}'")
            elif not (SKILLS_DIR / sib / rel).is_file():
                bad.append(f"{p.relative_to(ROOT)} -> missing {sib}/{rel}")
    assert not bad, "unresolved relocatable cross-references:\n" + "\n".join(bad)


def test_plugin_manifests():
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert plugin.get("name") == "eskill-analyze", "plugin.json name must be eskill-analyze"
    mkt = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert mkt.get("name"), "marketplace.json needs a name"
    assert mkt.get("owner", {}).get("name"), "marketplace.json needs owner.name"
    plugins = mkt.get("plugins") or []
    assert any(pl.get("name") == "eskill-analyze" and pl.get("source") for pl in plugins), \
        "marketplace.json must list the eskill-analyze plugin with a source"


def test_readme_documents_tiers():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for tier in ("eskill-analyze", "esat", "esat-fleet", "esat-frontier"):
        assert tier in readme, f"README does not mention tier '{tier}'"


def test_esat_frontier_model_profiles_documented():
    skill = (SKILLS_DIR / "esat-frontier" / "SKILL.md").read_text(encoding="utf-8")
    panel = (SKILLS_DIR / "esat-frontier" / "references" / "frontier-panel.md").read_text(encoding="utf-8")
    profiles_path = SKILLS_DIR / "esat-frontier" / "references" / "model-profiles.md"
    profiles = profiles_path.read_text(encoding="utf-8")

    assert "references/model-profiles.md" in skill, "esat-frontier must load model profile mapping"
    assert "model-profiles.md" in panel, "frontier panel must resolve roster through model profiles"
    for label in ("fable", "sonnet-5", "codex-medium", "grok", "fleet"):
        assert label in profiles, f"model profile '{label}' is not documented"
    for rule in ("Drop duplicate profiles", "Keep the lead out of the reviewer roster", "Sensitivity"):
        assert rule in profiles, f"model profile rule missing: {rule}"


def test_installer_present():
    assert (ROOT / "install.sh").is_file(), "install.sh missing"


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
