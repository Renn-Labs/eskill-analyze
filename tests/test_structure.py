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
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
SKILLS = [
    "eskill-common",
    "eskill-analyze",
    "esa",
    "esat",
    "esat-fleet",
    "esat-frontier",
]
# Local harness / agent telemetry — never treated as shipped product surfaces.
_NON_PRODUCT_TOP = {".git", ".omc", ".omx", ".grokprint", "tests", "__pycache__", ".pytest_cache"}
_PRIVACY_SUFFIXES = {".md", ".sh", ".svg", ".txt", ".yml", ".yaml", ".json"}
_PUBLIC_ROOT_DOCS = (
    "README.md",
    "CHANGELOG.md",
    "ROADMAP.md",
    "LICENSE",
    "LICENSE.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "RELEASE.md",
    "install.sh",
)


def _frontmatter(text: str) -> str:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    return m.group(1) if m else ""


def _is_product_text(path: pathlib.Path) -> bool:
    return path.suffix in _PRIVACY_SUFFIXES or path.name in {"install.sh", "LICENSE"}


def _product_paths_for_privacy() -> list[pathlib.Path]:
    """Public/product surfaces only.

    Covers skills/, public root docs/scripts/config, and tracked public files.
    Does **not** treat untracked hidden Grok/agent telemetry (e.g. ``.grokprint``)
    as shipped product. Does **not** broadly hide tracked leaks: any tracked file
    outside non-product tops is still scanned.
    """
    found: set[pathlib.Path] = set()

    # skills/ always (primary product surface)
    if SKILLS_DIR.is_dir():
        for p in SKILLS_DIR.rglob("*"):
            if p.is_file() and _is_product_text(p):
                found.add(p)

    # Public root docs + installer
    for name in _PUBLIC_ROOT_DOCS:
        p = ROOT / name
        if p.is_file():
            found.add(p)

    # scripts/ and public config manifests
    for rel in ("scripts", ".claude-plugin"):
        d = ROOT / rel
        if d.is_dir():
            for p in d.rglob("*"):
                if p.is_file() and _is_product_text(p):
                    found.add(p)

    # Tracked public files (catches tracked leaks; skips non-product tops)
    try:
        r = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z"],
            capture_output=True,
            check=False,
        )
        if r.returncode == 0:
            for raw in r.stdout.split(b"\0"):
                if not raw:
                    continue
                rel = raw.decode("utf-8", errors="replace")
                p = ROOT / rel
                parts = pathlib.Path(rel).parts
                if not parts or parts[0] in _NON_PRODUCT_TOP:
                    continue
                if p.is_file() and _is_product_text(p):
                    found.add(p)
    except OSError:
        pass

    return sorted(found)


def test_skill_frontmatter():
    unsupported = re.compile(
        r"^(aliases|user-invocable|allowed-tools|argument-hint)\s*:",
        re.MULTILINE,
    )
    for s in SKILLS:
        skill = SKILLS_DIR / s / "SKILL.md"
        assert skill.is_file(), f"missing {skill}"
        fm = _frontmatter(skill.read_text(encoding="utf-8"))
        assert re.search(r"^name:\s*\S", fm, re.MULTILINE), f"{s}: no name: in frontmatter"
        assert re.search(r"^description:\s*\S", fm, re.MULTILINE), f"{s}: no description: in frontmatter"
        bad = unsupported.findall(fm)
        assert not bad, f"{s}: unsupported frontmatter keys: {bad}"


def test_shared_model_routing_contract_present():
    path = SKILLS_DIR / "eskill-common" / "references" / "model-routing.md"
    assert path.is_file(), "eskill-common must ship model-routing.md"
    text = path.read_text(encoding="utf-8")
    assert "Preference precedence" in text
    assert "Two-stage panel manifest" in text
    fleet = (SKILLS_DIR / "esat-fleet" / "SKILL.md").read_text(encoding="utf-8")
    frontier = (SKILLS_DIR / "esat-frontier" / "SKILL.md").read_text(encoding="utf-8")
    assert "model-routing.md" in fleet and "model-routing.md" in frontier


def test_no_absolute_user_paths():
    bad = []
    scanned = _product_paths_for_privacy()
    assert any(p.relative_to(ROOT).parts[0] == "skills" for p in scanned), (
        "privacy scan must cover skills/"
    )
    for p in scanned:
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
    for tier in ("eskill-analyze", "esa", "esat", "esat-fleet", "esat-frontier"):
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


def test_installer_lists_all_skills():
    text = (ROOT / "install.sh").read_text(encoding="utf-8")
    match = re.search(r"^SKILLS=\(([^)]*)\)", text, re.MULTILINE)
    assert match, "install.sh must declare SKILLS=(...)"
    installed = set(match.group(1).split())
    assert installed == set(SKILLS), (
        f"installer skill set differs: expected={sorted(SKILLS)} actual={sorted(installed)}"
    )


def test_installer_rejects_harness_path_traversal():
    """--harness must allowlist-only; traversal values must not touch the filesystem."""
    if os.name == "nt":
        return  # Installer execution is covered by Bash-capable Linux/macOS jobs.
    install = ROOT / "install.sh"
    assert install.is_file()
    with tempfile.TemporaryDirectory(prefix="eskill-harness-sec-") as outer:
        outer_path = pathlib.Path(outer)
        home = outer_path / "home"
        home.mkdir()
        # Baseline: only the empty home dir under outer.
        before = {p.relative_to(outer_path) for p in outer_path.rglob("*")}
        env = {**os.environ, "HOME": str(home)}
        # Would resolve to $HOME/../escape/skills → outer/escape/skills if accepted.
        traversal = "../escape"
        r = subprocess.run(
            ["bash", str(install), "--harness", traversal],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert r.returncode == 2, f"expected exit 2, got {r.returncode}: {r.stdout!r} {r.stderr!r}"
        err = r.stderr.strip()
        assert err, "expected concise error on stderr"
        assert "invalid" in err.lower() or "harness" in err.lower(), err
        assert traversal in err or "allowed" in err.lower(), err
        after = {p.relative_to(outer_path) for p in outer_path.rglob("*")}
        assert after == before, (
            f"installer created paths under temp root: before={sorted(before)} after={sorted(after)}"
        )
        # Explicitly: no escape dir outside HOME, no skills dirs under HOME.
        assert not (outer_path / "escape").exists()
        assert not (home / ".claude").exists()
        assert not any(home.iterdir()), f"HOME not empty: {list(home.iterdir())}"


def test_installer_preserves_foreign_skill():
    """Install and uninstall must not destroy a same-named skill they do not own."""
    if os.name == "nt":
        return  # Installer execution is covered by Bash-capable Linux/macOS jobs.
    install = ROOT / "install.sh"
    with tempfile.TemporaryDirectory(prefix="eskill-collision-") as tmp:
        home = pathlib.Path(tmp)
        foreign = home / ".claude" / "skills" / "esa"
        foreign.mkdir(parents=True)
        sentinel = foreign / "USER_OWNED.txt"
        sentinel.write_text("preserve me\n", encoding="utf-8")
        env = {**os.environ, "HOME": str(home)}

        attempted = subprocess.run(
            ["bash", str(install), "--copy"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert attempted.returncode == 3, attempted.stderr + attempted.stdout
        assert sentinel.read_text(encoding="utf-8") == "preserve me\n"
        assert not (home / ".claude" / "skills" / "eskill-common").exists(), (
            "collision preflight must run before any skill target is mutated"
        )

        removed = subprocess.run(
            ["bash", str(install), "--uninstall"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert removed.returncode == 0, removed.stderr + removed.stdout
        assert sentinel.read_text(encoding="utf-8") == "preserve me\n"

        forced = subprocess.run(
            ["bash", str(install), "--copy", "--force"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert forced.returncode == 0, forced.stderr + forced.stdout
        assert not sentinel.exists()
        marker = foreign / ".eskill-analyze-installed"
        assert marker.read_text(encoding="utf-8") == "eskill-analyze:esa\n"

        owned_remove = subprocess.run(
            ["bash", str(install), "--uninstall"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert owned_remove.returncode == 0, owned_remove.stderr + owned_remove.stdout
        assert not foreign.exists()


def test_installer_lock_and_rollback():
    """Active locks must fail closed; a failed swap must restore prior targets."""
    if os.name == "nt":
        return  # Installer execution is covered by Bash-capable Linux/macOS jobs.
    install = ROOT / "install.sh"
    with tempfile.TemporaryDirectory(prefix="eskill-rollback-") as tmp:
        home = pathlib.Path(tmp) / "home"
        skills_root = home / ".claude" / "skills"
        skills_root.mkdir(parents=True)
        env = {**os.environ, "HOME": str(home)}

        lock = skills_root / ".eskill-analyze-install.lock"
        lock.mkdir()
        locked = subprocess.run(
            ["bash", str(install), "--copy"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert locked.returncode == 4, locked.stderr + locked.stdout
        assert not (skills_root / "esa").exists()
        lock.rmdir()

        initial = subprocess.run(
            ["bash", str(install), "--copy"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert initial.returncode == 0, initial.stderr + initial.stdout
        sentinel = skills_root / "esa" / "ROLLBACK_SENTINEL.txt"
        sentinel.write_text("original\n", encoding="utf-8")

        fake_bin = pathlib.Path(tmp) / "bin"
        fake_bin.mkdir()
        fake_mv = fake_bin / "mv"
        fake_mv.write_text(
            "#!/usr/bin/env bash\n"
            "n=0\n"
            "[ -f \"$MV_COUNTER\" ] && n=$(cat \"$MV_COUNTER\")\n"
            "n=$((n + 1))\n"
            "printf '%s\\n' \"$n\" > \"$MV_COUNTER\"\n"
            "if [ \"$n\" -eq \"$MV_FAIL_AT\" ]; then exit 77; fi\n"
            "exec \"$REAL_MV\" \"$@\"\n",
            encoding="utf-8",
        )
        fake_mv.chmod(0o755)
        counter = pathlib.Path(tmp) / "mv-counter"
        injected_env = {
            **env,
            "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
            "REAL_MV": shutil.which("mv") or "mv",
            "MV_COUNTER": str(counter),
            "MV_FAIL_AT": "6",
        }
        failed = subprocess.run(
            ["bash", str(install), "--copy"],
            cwd=str(ROOT),
            env=injected_env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert failed.returncode == 77, failed.stderr + failed.stdout
        assert sentinel.read_text(encoding="utf-8") == "original\n"
        for skill in SKILLS:
            assert (skills_root / skill / "SKILL.md").is_file(), (
                f"failed swap did not restore {skill}"
            )
        assert not list(skills_root.glob(".eskill-analyze-backup-*"))
        assert not list(skills_root.glob(".eskill-analyze-stage-*"))


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
