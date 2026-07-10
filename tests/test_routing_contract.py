#!/usr/bin/env python3
"""Phase-9 harness-aware routing contract tests.

These tests are **executable contract/oracle evidence** for the documented
routing algebra in ``skills/eskill-common/references/model-routing.md``.
They do **not** prove that every external harness obeys the prompt at runtime.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "routing"
ORACLE_DIR = pathlib.Path(__file__).resolve().parent

sys.path.insert(0, str(ORACLE_DIR))
from oracle.routing_oracle import (  # noqa: E402
    evaluate,
    assert_matches_expected,
    resolve_preference,
    planned_route_fingerprint,
    independent_voices_summary,
    PRECEDENCE,
)

CONTRACT_LABEL = (
    "CONTRACT EVIDENCE ONLY — not live harness conformance proof"
)


def _read(rel: str) -> str:
    return (SKILLS / rel).read_text(encoding="utf-8")


def _all_skill_md() -> list[pathlib.Path]:
    return sorted(SKILLS.rglob("SKILL.md"))


# ---------------------------------------------------------------------------
# Shared contract presence
# ---------------------------------------------------------------------------


def test_shared_contract_file_exists():
    path = SKILLS / "eskill-common" / "references" / "model-routing.md"
    assert path.is_file(), "model-routing.md missing"
    text = path.read_text(encoding="utf-8")
    for token in (
        "semantic role",
        "Preference precedence",
        "explicit invocation",
        "legacy environment",
        "portable default",
        "Strongest restriction",
        "Metered consent",
        "current-invocation",
        "Two-stage panel manifest",
        "observed_route",
        "Two-phase deduplication",
        "peer codex",
        "peer grok",
        "invalid-external-route-permission",
        "math.isfinite",
    ):
        assert token.lower() in text.lower(), f"contract missing concept: {token}"


def test_fleet_and_frontier_load_shared_contract():
    fleet = _read("esat-fleet/SKILL.md")
    frontier = _read("esat-frontier/SKILL.md")
    marker = "eskill-common/references/model-routing.md"
    assert marker in fleet or "../eskill-common/references/model-routing.md" in fleet
    assert "${CLAUDE_SKILL_DIR}/../eskill-common/references/model-routing.md" in fleet
    assert "${CLAUDE_SKILL_DIR}/../eskill-common/references/model-routing.md" in frontier
    assert "model-routing.md" in _read("esat-fleet/references/fleet-leg.md")
    assert "model-routing.md" in _read("esat-frontier/references/frontier-panel.md")


def test_precedence_order_documented_unambiguously():
    text = _read("eskill-common/references/model-routing.md")
    # Parse only the authoritative "## Preference precedence" section so
    # introductory mentions of "project"/"user"/etc. cannot scramble order.
    m = re.search(
        r"## Preference precedence\n(.*?)(?=\n## |\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    assert m, "Preference precedence section missing"
    section = m.group(1)
    labels = (
        "Explicit invocation",
        "Session",
        "Project",
        "User",
        "Legacy environment",
        "Harness",
        "Portable default",
    )
    positions = []
    for label in labels:
        # Numbered list item: "N. **Label**" or "N. Label"
        pat = re.compile(
            rf"^\s*\d+\.\s+\*{{0,2}}{re.escape(label)}\*{{0,2}}\b",
            re.MULTILINE | re.IGNORECASE,
        )
        mm = pat.search(section)
        assert mm, f"precedence tier missing from ordered list: {label}"
        positions.append(mm.start())
    assert positions == sorted(positions), "precedence tiers are out of order"
    # Exact 1..7 numbering for the seven tiers in that section
    nums = [
        int(n)
        for n in re.findall(
            r"^\s*(\d+)\.\s+\*{0,2}(?:"
            + "|".join(re.escape(lbl) for lbl in labels)
            + r")\*{0,2}\b",
            section,
            re.MULTILINE | re.IGNORECASE,
        )
    ]
    assert nums[:7] == list(range(1, 8)), f"expected tiers numbered 1..7, got {nums[:7]}"


# ---------------------------------------------------------------------------
# Frontmatter validity
# ---------------------------------------------------------------------------


def test_frontmatter_only_name_and_description():
    unsupported = re.compile(
        r"^(aliases|user-invocable|allowed-tools|argument-hint)\s*:",
        re.MULTILINE,
    )
    for skill in _all_skill_md():
        text = skill.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        assert m, f"{skill}: missing frontmatter"
        fm = m.group(1)
        assert re.search(r"^name:\s*\S", fm, re.MULTILINE), f"{skill}: no name"
        assert re.search(r"^description:\s*\S", fm, re.MULTILINE), f"{skill}: no description"
        bad = unsupported.findall(fm)
        assert not bad, f"{skill}: unsupported frontmatter keys: {bad}"


# ---------------------------------------------------------------------------
# Draft ownership contracts
# ---------------------------------------------------------------------------


def test_standalone_tier2_draft_owns_cleanup():
    trio = _read("esat/references/trio-panel.md")
    assert "Standalone Tier 2" in trio or "standalone" in trio.lower()
    assert "rm -f \"$DRAFT\"" in trio
    # Standalone section creates draft
    assert "Standalone draft lifecycle" in trio
    assert "Caller-owned draft lifecycle" in trio
    # Caller-owned must not delete
    assert "Do NOT" in trio and "delete" in trio.lower()
    # Timeout-safe EXIT trap for standalone owner
    assert "trap" in trio and "EXIT" in trio


def test_tier3_caller_owned_draft_single_cleanup():
    fleet_skill = _read("esat-fleet/SKILL.md")
    fleet_leg = _read("esat-fleet/references/fleet-leg.md")
    for text in (fleet_skill, fleet_leg):
        assert "caller-owned" in text.lower() or "Caller-owned" in text
        assert "exactly once" in text.lower() or "Clean exactly once" in text
    assert "Do NOT rm \"$DRAFT\" here" in fleet_leg or "Do NOT rm" in fleet_leg
    assert "success" in fleet_leg.lower() and "timeout" in fleet_leg.lower()
    # trio must not delete when caller-owned
    trio = _read("esat/references/trio-panel.md")
    assert "must not" in trio.lower() and "delete" in trio.lower()
    # Owner EXIT trap covers DRAFT, peer-redacted, REVIEW
    assert "trap" in fleet_leg and "EXIT" in fleet_leg
    assert "PEER_REDACTED" in fleet_leg
    assert "REVIEW" in fleet_leg


def test_timeout_safe_temp_cleanup_trap_probe():
    """Deterministic TemporaryDirectory probe: EXIT trap cleans after timeout.

    Creates three mktemp files inside an isolated directory, arms EXIT cleanup,
    lets timeout(1) kill the shell, asserts returncode is exactly 124 and the
    directory is empty. No global /tmp globbing, no soft returncode match.
    """
    with tempfile.TemporaryDirectory(prefix="esat-probe-") as tmp:
        tmp_path = pathlib.Path(tmp)
        script = f"""
set -u
TMPDIR={tmp!r}
DRAFT="$(mktemp "$TMPDIR/draft.XXXXXX.md")"
REVIEW="$(mktemp "$TMPDIR/review.XXXXXX.md")"
REDACTED="$(mktemp "$TMPDIR/redacted.XXXXXX.md")"
printf 'secret-draft\\n' > "$DRAFT"
printf 'secret-review\\n' > "$REVIEW"
printf 'secret-redacted\\n' > "$REDACTED"
_owner_cleanup() {{
  rm -f "$DRAFT"
  rm -f "$REVIEW"
  rm -f "$REDACTED"
}}
trap '_owner_cleanup' EXIT
# Work terminated by timeout(1); EXIT trap must still clean.
sleep 30
_owner_cleanup
trap - EXIT
"""
        r = subprocess.run(
            ["timeout", "0.4", "bash", "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )
        # GNU coreutils timeout exits 124 when it kills the child.
        assert r.returncode == 124, (
            f"expected timeout returncode 124, got {r.returncode}; "
            f"stderr={r.stderr!r} stdout={r.stdout!r}"
        )
        remaining = sorted(p.name for p in tmp_path.iterdir())
        assert remaining == [], f"timeout left sensitive temps: {remaining}"


def test_final_cleanup_after_last_draft_consumer():
    """Final normal cleanup must occur after the last peer/fleet DRAFT consumer."""
    fleet = _read("esat-fleet/references/fleet-leg.md")
    frontier = _read("esat-frontier/references/frontier-panel.md")

    # --- esat-fleet ---
    last_fleet_consumer = max(
        fleet.rfind('cat "$DRAFT"'),
        fleet.rfind('cat "$REVIEW"'),
        fleet.rfind("fleet-fuse.py"),
        fleet.rfind('python3 "${FLEET_FUSE_PY:-fleet-fuse.py}"'),
    )
    assert last_fleet_consumer >= 0, "fleet-leg.md missing DRAFT/REVIEW consumer"
    fleet_normal = [
        m.start()
        for m in re.finditer(r"(?m)^_esat_fleet_owner_cleanup\s*$", fleet)
    ]
    assert len(fleet_normal) == 1, (
        f"fleet-leg.md expected exactly one normal-path cleanup, found {len(fleet_normal)}"
    )
    fleet_cleanup = fleet_normal[0]
    assert fleet.find("trap - EXIT", fleet_cleanup) > fleet_cleanup
    assert fleet_cleanup > last_fleet_consumer, (
        "fleet-leg.md final cleanup must be after last peer/fleet DRAFT consumer"
    )
    # Setup/draft block must not normal-cleanup before fleet consumers.
    setup_end = fleet.find("## When it runs")
    assert setup_end > 0
    setup = fleet[:setup_end]
    assert not re.search(r"(?m)^_esat_fleet_owner_cleanup\s*$", setup), (
        "fleet-leg.md must not normal-cleanup in the initial draft/setup block"
    )
    assert not re.search(r"(?m)^trap - EXIT\s*$", setup), (
        "fleet-leg.md must not trap-disarm in the initial draft/setup block"
    )
    # Coverage: DRAFT, PEER_REDACTED, REVIEW all owned by the cleanup function.
    fn_m = re.search(
        r"_esat_fleet_owner_cleanup\(\)\s*\{(.*?)\n\}",
        fleet,
        re.DOTALL,
    )
    assert fn_m, "_esat_fleet_owner_cleanup function body missing"
    body = fn_m.group(1)
    for var in ("$DRAFT", "$PEER_REDACTED", "$REVIEW"):
        assert var in body, f"owner cleanup must remove {var}"

    # --- esat-frontier ---
    last_frontier_consumer = max(
        frontier.rfind('peer codex "$PEER_PROMPT" < "$DISPATCH_INPUT"'),
        frontier.rfind('peer grok "$PEER_PROMPT" < "$DISPATCH_INPUT"'),
        frontier.rfind('cat "$DRAFT"'),
        frontier.rfind("fleet-fuse.py"),
        frontier.rfind('python3 "${FLEET_FUSE_PY:-fleet-fuse.py}"'),
    )
    assert last_frontier_consumer >= 0, "frontier-panel.md missing DRAFT consumer"
    frontier_normal = [
        m.start()
        for m in re.finditer(r"(?m)^_esat_frontier_owner_cleanup\s*$", frontier)
    ]
    assert len(frontier_normal) == 1, (
        f"frontier-panel.md expected exactly one normal-path cleanup, "
        f"found {len(frontier_normal)}"
    )
    frontier_cleanup = frontier_normal[0]
    assert frontier.find("trap - EXIT", frontier_cleanup) > frontier_cleanup
    assert frontier_cleanup > last_frontier_consumer, (
        "frontier-panel.md final cleanup must be after last peer/fleet DRAFT consumer"
    )
    # Peer block must not normal-cleanup before optional fleet.
    peer_block = re.search(
        r"### Independent Codex / Grok peer lanes.*?(?=### Optional fleet)",
        frontier,
        re.DOTALL,
    )
    assert peer_block, "frontier peer section missing"
    assert not re.search(
        r"(?m)^_esat_frontier_owner_cleanup\s*$",
        peer_block.group(0),
    ), "frontier-panel.md must not cleanup immediately after peer commands"
    assert not re.search(r"(?m)^trap - EXIT\s*$", peer_block.group(0)), (
        "frontier-panel.md must not trap-disarm immediately after peer commands"
    )


def test_owner_exit_traps_documented_for_all_tiers():
    """Standalone esat, esat-fleet, esat-frontier document EXIT cleanup traps."""
    trio = _read("esat/references/trio-panel.md")
    fleet = _read("esat-fleet/references/fleet-leg.md")
    frontier = _read("esat-frontier/references/frontier-panel.md")
    for text, name in ((trio, "esat"), (fleet, "esat-fleet"), (frontier, "esat-frontier")):
        assert "trap" in text and "EXIT" in text, f"{name} missing EXIT trap"
        assert "SIGKILL" in text, f"{name} must not claim SIGKILL is handled (mention limit)"
        # Mention of SIGKILL must be a non-claim (cannot / does not / not handle).
        assert re.search(
            r"SIGKILL.*(cannot|does not|not claim|can't)",
            text,
            re.IGNORECASE | re.DOTALL,
        ) or re.search(
            r"(cannot|does not|not claim|Do not claim).*SIGKILL",
            text,
            re.IGNORECASE | re.DOTALL,
        ), f"{name} must not claim SIGKILL handling"
        assert "trap - EXIT" in text, f"{name} must disarm EXIT after normal cleanup"
    assert "_esat_cleanup_temps" in trio
    assert "_esat_fleet_owner_cleanup" in fleet
    assert "_esat_frontier_owner_cleanup" in frontier


# ---------------------------------------------------------------------------
# Metered consent command branches
# ---------------------------------------------------------------------------


def test_fleet_yes_metered_only_in_consented_branch():
    fleet_leg = _read("esat-fleet/references/fleet-leg.md")
    assert "--yes-metered" in fleet_leg
    assert "CONSENTED BRANCH ONLY" in fleet_leg
    assert "do **not** enter" in fleet_leg.lower() or "do not enter" in fleet_leg.lower()
    # Rejected sources
    for token in (
        "Environment",
        "project/user config",
        "Inherited shell",
        "prior-run",
        "expired",
    ):
        assert token.lower() in fleet_leg.lower(), f"consent rejection missing: {token}"


def test_frontier_yes_metered_only_in_consented_branch():
    panel = _read("esat-frontier/references/frontier-panel.md")
    assert "--yes-metered" in panel
    assert "CONSENTED BRANCH ONLY" in panel
    # Must not document unconsented --yes-metered outside the consented block
    # Count: yes-metered should appear only in consented guidance
    assert panel.count("--yes-metered") == 1


def test_budget_provider_account_cap_disclosure():
    for rel in (
        "eskill-common/references/model-routing.md",
        "esat-fleet/references/fleet-leg.md",
        "esat-frontier/references/frontier-panel.md",
    ):
        text = _read(rel)
        assert "provider/account cap only" in text


# ---------------------------------------------------------------------------
# Sensitivity
# ---------------------------------------------------------------------------


def test_high_sensitivity_blocks_external_routes():
    for rel in (
        "eskill-common/references/model-routing.md",
        "esat-fleet/SKILL.md",
        "esat-frontier/references/model-profiles.md",
        "esat-frontier/references/frontier-panel.md",
    ):
        text = _read(rel).lower()
        assert "high" in text
        assert "zero" in text or "skipped" in text or "local" in text


def test_tier3_high_sensitivity_blocks_all_external_not_full_trio():
    """High must not claim degrade-to-full esat frontier trio (external peer)."""
    fleet_skill = _read("esat-fleet/SKILL.md")
    fleet_leg = _read("esat-fleet/references/fleet-leg.md")
    contract = _read("eskill-common/references/model-routing.md")

    # Contradictory wording must not reappear
    forbidden = (
        "degrades to esat (frontier trio only)",
        "degrade to esat (frontier trio only)",
        "degrades to the full esat",
        "degrade to the full esat",
    )
    for phrase in forbidden:
        assert phrase not in fleet_skill.lower() and phrase not in fleet_skill, (
            f"esat-fleet still claims high degrades to full trio: {phrase!r}"
        )
        assert phrase not in fleet_leg.lower() and phrase not in fleet_leg

    # Positive contract: zero external + local/first-party only
    for text in (fleet_skill, fleet_leg, contract):
        low = text.lower()
        assert "zero" in low
        assert "local" in low or "first-party" in low
    assert "high-sensitivity" in fleet_skill or "high-sensitivity" in fleet_leg
    # Peer external routes explicitly gated on high (not only fleet)
    assert "peer" in fleet_skill.lower()
    assert (
        "do **not** claim" in fleet_skill.lower()
        or "do not claim" in fleet_skill.lower()
        or "do **not** degrade" in fleet_skill.lower()
        or "do not degrade" in fleet_skill.lower()
    )


def test_medium_requires_redaction_path():
    for rel in (
        "eskill-common/references/model-routing.md",
        "esat-fleet/references/fleet-leg.md",
        "esat-frontier/references/frontier-panel.md",
    ):
        text = _read(rel).lower()
        assert "redact" in text
        assert "redactor-unavailable" in text or "redaction path" in text or "identified redaction" in text


def test_identified_redaction_path_provenance_boundary_documented():
    """IDENTIFIED_REDACTION_PATH must be trusted harness/operator config only.

    Shared contract + Tier-3 surfaces must document the provenance boundary:
    trusted executable adapter selected by harness/operator from trusted
    configuration; never derived from analyzed repo/item/draft or untrusted
    project content. Fail-closed redactor-unavailable is preserved.
    """
    surfaces = (
        "eskill-common/references/model-routing.md",
        "esat-fleet/references/fleet-leg.md",
        "esat-frontier/references/frontier-panel.md",
    )
    required_concepts = (
        "IDENTIFIED_REDACTION_PATH",
        "trusted executable adapter",
        "harness/operator",
        "trusted configuration",
        "redactor-unavailable",
    )
    # Provenance must forbid derivation from untrusted analysis content.
    forbidden_source_markers = (
        "never derive",
        "must never be derived",
        "never from the analyzed",
    )
    untrusted_content_markers = (
        "analyzed repository",
        "analyzed item",
        "draft",
        "untrusted project content",
    )
    for rel in surfaces:
        text = _read(rel)
        low = text.lower()
        for token in required_concepts:
            assert token.lower() in low, f"{rel} missing provenance concept: {token}"
        assert any(m in low for m in forbidden_source_markers), (
            f"{rel} must forbid deriving IDENTIFIED_REDACTION_PATH from untrusted content"
        )
        for marker in untrusted_content_markers:
            assert marker in low, (
                f"{rel} must name untrusted source boundary: {marker}"
            )
        # Fail-closed preserved: missing/empty path or failing adapter blocks.
        assert "redactor-unavailable" in low
        assert (
            '[ -z "${IDENTIFIED_REDACTION_PATH:-}" ]' in text
            or "missing" in low
        ), f"{rel} must document missing-path fail-closed"


def test_frontier_medium_peer_uses_dispatch_input_not_raw_draft():
    """Medium external peer lanes consume verified redacted DISPATCH_INPUT."""
    panel = _read("esat-frontier/references/frontier-panel.md")
    assert "DISPATCH_INPUT" in panel
    assert "REDACTED" in panel
    # Peer commands must read DISPATCH_INPUT, not raw $DRAFT
    assert 'peer codex "$PEER_PROMPT" < "$DISPATCH_INPUT"' in panel
    assert 'peer grok "$PEER_PROMPT" < "$DISPATCH_INPUT"' in panel
    assert not re.search(
        r'peer codex "\$PEER_PROMPT" < "\$DRAFT"', panel
    ), "peer codex must not read raw $DRAFT"
    assert not re.search(
        r'peer grok "\$PEER_PROMPT" < "\$DRAFT"', panel
    ), "peer grok must not read raw $DRAFT"
    assert "redactor-unavailable" in panel
    assert "identified redaction" in panel.lower() or "IDENTIFIED_REDACTION_PATH" in panel
    # Separate redacted cleanup must not replace owner draft cleanup
    assert 'rm -f "$REDACTED"' in panel
    assert 'rm -f "$DRAFT"' in panel
    # medium external must use redacted artifact
    assert "verified redacted" in panel.lower() or "verified output" in panel.lower()


def _caller_owned_trio_section() -> str:
    """Extract the caller-owned Tier 3 lifecycle section from trio-panel.md."""
    trio = _read("esat/references/trio-panel.md")
    m = re.search(
        r"### Caller-owned draft lifecycle \(Tier 3\+\)\n(.*?)(?=\n## |\Z)",
        trio,
        re.DOTALL,
    )
    assert m, "caller-owned draft lifecycle section missing from trio-panel.md"
    return m.group(1)


def _bash_code_lines(section: str) -> str:
    """Return non-comment lines from fenced bash blocks in a markdown section."""
    blocks = re.findall(r"```(?:bash)?\n(.*?)```", section, re.DOTALL)
    lines: list[str] = []
    for block in blocks:
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            lines.append(line)
    return "\n".join(lines)


def test_tier3_medium_peer_uses_dispatch_input_not_raw_draft():
    """Caller-owned medium peer has no raw $DRAFT sink; trio reads PEER_DISPATCH_INPUT."""
    fleet_skill = _read("esat-fleet/SKILL.md")
    fleet_leg = _read("esat-fleet/references/fleet-leg.md")
    trio = _read("esat/references/trio-panel.md")
    caller_owned = _caller_owned_trio_section()
    caller_code = _bash_code_lines(caller_owned)
    fleet_code = _bash_code_lines(fleet_leg)

    # PEER_DISPATCH_INPUT defined separately from raw DRAFT across Tier-3 surfaces
    for text, label in (
        (fleet_skill, "esat-fleet/SKILL.md"),
        (fleet_leg, "fleet-leg.md"),
        (trio, "trio-panel.md"),
    ):
        assert "PEER_DISPATCH_INPUT" in text, f"{label} missing PEER_DISPATCH_INPUT"

    # Caller-owned peer trio command reads PEER_DISPATCH_INPUT, never DRAFT
    assert "peer trio" in caller_code
    assert '< "$PEER_DISPATCH_INPUT"' in caller_code, (
        "caller-owned peer trio must read $PEER_DISPATCH_INPUT"
    )
    assert '< "$DRAFT"' not in caller_code, (
        "caller-owned medium path must not have raw $DRAFT peer sink"
    )
    # Executable peer-redirect targets (end-of-line stdin sinks only)
    peer_sinks = re.findall(
        r'^\s*peer trio\b.*<\s*"(\$[^"]+)"\s*$',
        caller_code,
        re.MULTILINE,
    )
    assert peer_sinks == ["$PEER_DISPATCH_INPUT"], (
        f"caller-owned peer sinks must be only PEER_DISPATCH_INPUT, got {peer_sinks}"
    )
    # Fleet medium path assigns redacted artifact
    assert 'PEER_DISPATCH_INPUT="$PEER_REDACTED"' in fleet_code

    # Medium: PEER_REDACTED via trusted IDENTIFIED_REDACTION_PATH
    assert "PEER_REDACTED" in fleet_leg
    assert "IDENTIFIED_REDACTION_PATH" in fleet_leg
    assert (
        '"$IDENTIFIED_REDACTION_PATH" < "$DRAFT" > "$PEER_REDACTED"' in fleet_leg
    ), "medium must create PEER_REDACTED via IDENTIFIED_REDACTION_PATH"
    assert 'PEER_DISPATCH_INPUT="$PEER_REDACTED"' in fleet_leg

    # High forces external peer readiness 0; low allows raw DRAFT only when
    # already-resolved EXTERNAL_PEER_READY is 1.
    assert "EXTERNAL_PEER_READY=0" in fleet_leg
    assert re.search(
        r'if \[ "\$TIER" = "high" \]; then',
        fleet_leg,
    ), "high tier branch required"
    high_section = re.search(
        r'if \[ "\$TIER" = "high" \]; then(.*?)(?:elif|else)',
        fleet_leg,
        re.DOTALL,
    )
    assert high_section, "high tier branch body missing"
    assert "EXTERNAL_PEER_READY=0" in high_section.group(1)
    assert 'PEER_DISPATCH_INPUT="$DRAFT"' in fleet_leg
    assert '[ "$TIER" = "low" ]' in fleet_leg
    assert '[ "${EXTERNAL_PEER_READY:-0}" = "1" ]' in fleet_leg

    # Standalone Tier 2 preserved: still may pipe $DRAFT
    assert "### Standalone draft lifecycle" in trio
    assert re.search(
        r'peer trio\s+"[^"]*"\s*<\s*"\$DRAFT"',
        trio,
    ), "standalone Tier 2 must still allow peer trio < $DRAFT"


def test_tier3_medium_missing_or_failing_redactor_blocks_peer():
    """Missing/failing redactor sets redactor-unavailable and must not call peer."""
    fleet_leg = _read("esat-fleet/references/fleet-leg.md")
    fleet_skill = _read("esat-fleet/SKILL.md")
    trio = _read("esat/references/trio-panel.md")
    caller_owned = _caller_owned_trio_section()

    for text in (fleet_leg, fleet_skill, trio):
        assert "redactor-unavailable" in text

    # Missing IDENTIFIED_REDACTION_PATH blocks
    assert '[ -z "${IDENTIFIED_REDACTION_PATH:-}" ]' in fleet_leg
    # Failing redactor path present
    assert (
        'if ! "$IDENTIFIED_REDACTION_PATH" < "$DRAFT" > "$PEER_REDACTED"' in fleet_leg
    )
    # Failure paths force readiness 0 and clear dispatch input (do not call peer)
    assert fleet_leg.count("EXTERNAL_PEER_READY=0") >= 2
    assert fleet_leg.count("PEER_DISPATCH_READY=0") >= 2
    # Medium success assigns PEER_REDACTED; low may assign $DRAFT under ready=1
    assigns = re.findall(r'PEER_DISPATCH_INPUT="([^"]*)"', fleet_leg)
    assert "$PEER_REDACTED" in assigns
    assert "$DRAFT" in assigns
    # Empty clear on failure also present
    assert 'PEER_DISPATCH_INPUT=""' in fleet_leg

    # Caller-owned peer call is gated: PEER_DISPATCH_READY=1 AND non-empty input
    assert '[ "${PEER_DISPATCH_READY:-0}" = "1" ]' in caller_owned
    assert '[ -n "${PEER_DISPATCH_INPUT:-}" ]' in caller_owned
    # Explicit: do not call peer / never fall back to raw on redactor failure
    assert (
        "do not call peer" in caller_owned.lower()
        or "never fall back" in caller_owned.lower()
        or "no raw draft sink" in caller_owned.lower()
    )
    assert "redactor-unavailable" in caller_owned or "redactor-unavailable" in trio
    assert "never" in fleet_leg.lower() and "raw" in fleet_leg.lower()


def _frontier_shell_external_peer_would_dispatch(
    *, tier: str, external_peer_ready: str
) -> bool:
    """Mirror the published frontier-panel.md external peer dispatch gate.

    Fail-closed positive gate: EXTERNAL_PEER_READY equals 1 AND TIER is not high.
    High also forces ready=0 before the gate (defense in depth). Low must never
    act as an alternate positive gate via ``|| [ "$TIER" = "low" ]``.
    """
    ready = external_peer_ready
    if tier == "high":
        ready = "0"
    return ready == "1" and tier != "high"


def test_frontier_external_peer_dispatch_uses_readiness_not_low_bypass():
    """Public shell: no low-tier OR bypass; high never dispatches even if ready=1."""
    panel = _read("esat-frontier/references/frontier-panel.md")

    # Exact unsafe expression must not appear in the public shell example.
    unsafe = 'if [ "${EXTERNAL_PEER_READY:-0}" = "1" ] || [ "$TIER" = "low" ]; then'
    assert unsafe not in panel, "unsafe low-tier OR bypass still present in shell"

    # Published shell must not contain any low-tier OR bypass expression.
    bypass_patterns = (
        r'\$\{EXTERNAL_PEER_READY:-0\}\"\s*=\s*"1"\s*\]\s*\|\|\s*\[\s*"\$TIER"\s*=\s*"low"',
        r'EXTERNAL_PEER_READY:-0\}\"\s*=\s*"1"\s*\]\s*\|\|\s*\[\s*"\$TIER"\s*=\s*"low"',
        r'\]\s*\|\|\s*\[\s*"\$TIER"\s*=\s*"low"\s*\]',
        r'EXTERNAL_PEER_READY.*\|\|.*"\$TIER".*low',
        r'\[\s*"\$TIER"\s*=\s*"low"\s*\]\s*\|\|',
    )
    for pat in bypass_patterns:
        assert not re.search(pat, panel), f"low-tier bypass still present: {pat}"
    assert '|| [ "$TIER" = "low" ]' not in panel
    assert '|| [ "$TIER" = "low"]' not in panel

    # Fail-closed positive gate: ready=1 AND TIER is not high.
    fail_closed = (
        'if [ "${EXTERNAL_PEER_READY:-0}" = "1" ] && [ "$TIER" != "high" ]; then'
    )
    assert fail_closed in panel, (
        "public shell must dispatch only when EXTERNAL_PEER_READY=1 and TIER != high"
    )
    assert "no-external-send" in panel.lower() or (
        "high" in panel.lower() and "never external" in panel.lower()
    )
    assert "fail-closed" in panel.lower()

    # low + permission denied readiness (ready=0) → no dispatch
    assert (
        _frontier_shell_external_peer_would_dispatch(
            tier="low", external_peer_ready="0"
        )
        is False
    )
    # low + ready=1 → dispatch allowed by shell gate (other gates already resolved)
    assert (
        _frontier_shell_external_peer_would_dispatch(
            tier="low", external_peer_ready="1"
        )
        is True
    )
    # high + inconsistent truthy readiness → still no dispatch (even if ready=1)
    assert (
        _frontier_shell_external_peer_would_dispatch(
            tier="high", external_peer_ready="1"
        )
        is False
    )
    # medium + ready=1 → dispatch allowed
    assert (
        _frontier_shell_external_peer_would_dispatch(
            tier="medium", external_peer_ready="1"
        )
        is True
    )
    # medium + ready=0 → no dispatch
    assert (
        _frontier_shell_external_peer_would_dispatch(
            tier="medium", external_peer_ready="0"
        )
        is False
    )


def test_oracle_low_external_permission_denied_blocks_peer():
    """Low sensitivity + external-route deny must not ready external peer lanes."""
    fixture_path = FIXTURES / "T19-low-external-permission-denied-peer.json"
    assert fixture_path.is_file(), (
        "missing low-sensitivity external permission denied fixture: "
        f"{fixture_path.name}"
    )
    fixtures = _load_fixtures()
    by_id = {f["id"]: f for f in fixtures}
    key = "T19-low-external-permission-denied-peer"
    assert key in by_id, f"missing fixture {key}"
    actual = evaluate(by_id[key])
    for lane in ("peer-codex", "peer-grok"):
        assert actual["plan"][lane]["readiness"] == "blocked"
        assert actual["plan"][lane]["reason"] == "external-route-denied"
        result = next(r for r in actual["results"] if r["lane"] == lane)
        assert result["observed_route"] is None
        assert result["outcome"] == "blocked"
    assert actual["panel_status"] == "local-only"


def test_oracle_high_local_critic_blocked_external_is_local_only():
    """High with local critic + blocked external lanes derives local-only, not partial."""
    fixtures = _load_fixtures()
    by_id = {f["id"]: f for f in fixtures}
    # T20 is the high + critic ran + external blocked fixture
    actual = evaluate(by_id["T20-all-planned-have-terminal"])
    assert actual["plan"]["fleet"]["reason"] == "high-sensitivity"
    assert actual["plan"]["peer-codex"]["reason"] == "high-sensitivity"
    critic = next(r for r in actual["results"] if r["lane"] == "critic")
    assert critic["outcome"] == "ran" and critic["independent"] is True
    assert actual["panel_status"] == "local-only"

    # Inline scenario mirrors the documented high local-only case
    scenario = {
        "input": {
            "harness": {"explicit": "claude"},
            "requested_routes": ["critic", "peer-codex", "peer-grok", "fleet"],
            "sensitivity_scopes": ["high"],
            "external_route_permission": "allow",
            "redactor_available": True,
            "metered_consent": {"source": "current-invocation", "status": "valid"},
            "budget_usd": 1.0,
            "route_outcomes": {
                "critic": {"outcome": "ran", "observed_route": "native-critic"}
            },
        }
    }
    got = evaluate(scenario)
    assert got["panel_status"] == "local-only"
    assert all(
        got["plan"][lane]["reason"] == "high-sensitivity"
        for lane in ("peer-codex", "peer-grok", "fleet")
    )


def test_oracle_high_not_masked_by_fleet_availability():
    """High sensitivity reason must outrank fleet-disabled / fuse-unavailable."""
    from oracle.routing_oracle import plan_lane, evaluate_consent, evaluate_budget

    consent = evaluate_consent({"source": "current-invocation", "status": "valid"})
    budget = evaluate_budget(1.0)
    for fleet_enabled, fuse_ok in ((False, True), (True, False), (False, False)):
        p = plan_lane(
            "fleet",
            sensitivity="high",
            sensitivity_error=None,
            external_route_permission="allow",
            redactor_available=True,
            consent=consent,
            budget=budget,
            fleet_enabled=fleet_enabled,
            fleet_fuse_available=fuse_ok,
            peer_available=False,
        )
        assert p["readiness"] == "blocked", p
        assert p["reason"] == "high-sensitivity", p

    # Peer: high also outranks peer-unavailable
    for lane in ("peer-codex", "peer-grok"):
        p = plan_lane(
            lane,
            sensitivity="high",
            sensitivity_error=None,
            external_route_permission="allow",
            redactor_available=True,
            consent=consent,
            budget=budget,
            peer_available=False,
        )
        assert p["reason"] == "high-sensitivity", p


def test_oracle_medium_missing_redactor_blocks_peer():
    """Missing medium redactor blocks peer dispatch with redactor-unavailable."""
    fixtures = _load_fixtures()
    by_id = {f["id"]: f for f in fixtures}
    actual = evaluate(by_id["T5-medium-no-redactor"])
    assert actual["plan"]["fleet"]["readiness"] == "blocked"
    assert actual["plan"]["fleet"]["reason"] == "redactor-unavailable"

    scenario = {
        "input": {
            "harness": {"explicit": "claude"},
            "requested_routes": ["peer-codex", "peer-grok"],
            "sensitivity_scopes": ["medium"],
            "external_route_permission": "allow",
            "redactor_available": False,
            "metered_consent": {"source": "current-invocation", "status": "valid"},
            "budget_usd": 1.0,
        }
    }
    got = evaluate(scenario)
    for lane in ("peer-codex", "peer-grok"):
        assert got["plan"][lane]["readiness"] == "blocked"
        assert got["plan"][lane]["reason"] == "redactor-unavailable"


# ---------------------------------------------------------------------------
# Frontier peer dispatch exactness
# ---------------------------------------------------------------------------


def test_frontier_uses_independent_peer_lanes_not_trio():
    panel = _read("esat-frontier/references/frontier-panel.md")
    profiles = _read("esat-frontier/references/model-profiles.md")
    skill = _read("esat-frontier/SKILL.md")
    for text in (panel, profiles, skill):
        assert "peer codex" in text
        assert "peer grok" in text
    # Negative: no roster-driven peer trio
    assert "peer trio" not in panel or "NEVER" in panel and "peer trio" in panel
    assert "Never" in panel or "NEVER" in panel
    assert "roster-driven `peer trio`" in skill or "peer trio" in skill
    # Command forms present
    assert "peer codex" in panel
    assert "peer grok" in panel
    # Must not have a case that calls peer trio for roster
    assert not re.search(r"^\s*peer trio\b", panel, re.MULTILINE)
    # Codex-only / Grok-only exclusivity stated
    assert "Codex-only" in panel or "codex-only" in panel.lower()
    assert "Grok-only" in panel or "grok-only" in panel.lower()


def test_no_stale_gpt55_in_active_panel_templates():
    """Active panel output templates must not claim gpt-5.5."""
    panel_files = [
        "esat/references/trio-panel.md",
        "esat-fleet/references/fleet-leg.md",
        "esat-frontier/references/frontier-panel.md",
        "esat-frontier/references/model-profiles.md",
    ]
    bad = []
    for rel in panel_files:
        text = _read(rel)
        if "gpt-5.5" in text:
            bad.append(rel)
    assert not bad, f"stale gpt-5.5 claims remain in: {bad}"
    # Prefer actual/account default language
    trio = _read("esat/references/trio-panel.md")
    assert "account default" in trio.lower()


def test_requested_vs_actual_and_panel_status_required():
    for rel in (
        "eskill-common/references/model-routing.md",
        "esat-frontier/references/frontier-panel.md",
        "esat-fleet/references/fleet-leg.md",
    ):
        text = _read(rel)
        assert "Panel status" in text or "panel status" in text.lower()
        assert "actual" in text.lower()
        assert "full" in text and "partial" in text and "local-only" in text


# ---------------------------------------------------------------------------
# Deduplication documented
# ---------------------------------------------------------------------------


def test_two_phase_dedup_documented():
    text = _read("eskill-common/references/model-routing.md")
    assert "pre-dispatch" in text.lower() or "Before dispatch" in text
    assert "non-independent" in text.lower() or "independent: false" in text
    assert "quorum" in text.lower()


# ---------------------------------------------------------------------------
# Fixture / oracle matrix
# ---------------------------------------------------------------------------


def _load_fixtures() -> list[dict]:
    assert FIXTURES.is_dir(), f"missing fixtures dir {FIXTURES}"
    out = []
    for p in sorted(FIXTURES.glob("*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    assert out, "no routing fixtures found"
    return out


def test_oracle_matrix_all_fixtures():
    """Run the full JSON matrix through the stdlib oracle."""
    print(f"\n[{CONTRACT_LABEL}]")
    fixtures = _load_fixtures()
    ids = {f["id"] for f in fixtures}
    # Required scenario families
    required_prefixes = (
        "T2-",
        "T3-",
        "T3b-",
        "T3c-",
        "T4-",
        "T5-",
        "T5b-",
        "T6-",
        "T7-",
        "T8-",
        "T9-",
        "T10-",
        "T11-",
        "T16-",
        "T18-",
        "T19-",
        "T20-",
    )
    for prefix in required_prefixes:
        assert any(i.startswith(prefix) for i in ids), f"missing fixture family {prefix}"

    for fx in fixtures:
        actual = evaluate(fx)
        assert actual.get("contract_evidence_only") is True
        if fx.get("expected_budget_disclosure"):
            assert actual["budget"]["disclosure"] == fx["expected_budget_disclosure"]
        assert_matches_expected(actual, fx)
        # T20: every planned lane has exactly one terminal result
        assert len(actual["results"]) == len(actual["plans"])
        for r in actual["results"]:
            assert "outcome" in r
            assert "observed_route" in r
            if r["outcome"] in ("blocked", "skipped"):
                assert r["observed_route"] is None


def test_oracle_precedence_covers_all_adjacent_collisions():
    fixtures = _load_fixtures()
    needed = {
        f"T18-precedence-{PRECEDENCE[i]}-over-{PRECEDENCE[i+1]}"
        for i in range(len(PRECEDENCE) - 1)
    }
    have = {f["id"] for f in fixtures}
    missing = needed - have
    assert not missing, f"missing precedence collision fixtures: {missing}"


def test_oracle_t18_preference_drives_planned_model_and_fingerprint():
    """Every T18 fixture: plans use expected preference value/source and fingerprint."""
    fixtures = _load_fixtures()
    t18 = [f for f in fixtures if f["id"].startswith("T18-")]
    assert t18, "expected T18 precedence fixtures"
    for fx in t18:
        assert "expected_preference_source" in fx, fx["id"]
        assert "expected_preference_value" in fx, fx["id"]
        actual = evaluate(fx)
        assert_matches_expected(actual, fx)
        exp_val = fx["expected_preference_value"]
        exp_src = fx["expected_preference_source"]
        assert actual["model_preference"]["value"] == exp_val
        assert actual["model_preference"]["source"] == exp_src
        for p in actual["plans"]:
            assert p["requested_model"] == exp_val, (
                f"{fx['id']} plan[{p['lane']}].requested_model"
            )
            assert p["preference_source"] == exp_src, (
                f"{fx['id']} plan[{p['lane']}].preference_source"
            )
            assert exp_val in p["planned_route_fingerprint"], (
                f"{fx['id']} fingerprint missing model: {p['planned_route_fingerprint']}"
            )
            assert p["planned_route_fingerprint"] == planned_route_fingerprint(
                provider=p["requested_provider"],
                requested_model=exp_val,
                route_class=p["route_class"],
                context_class=p["context_class"],
            )


def test_oracle_consent_rejection_classes_separate():
    fixtures = _load_fixtures()
    by_id = {f["id"]: f for f in fixtures}
    for src in ("environment", "config", "inherited-shell", "expired", "prior-run"):
        key = f"T3b-consent-{src}"
        assert key in by_id, f"missing consent rejection fixture {key}"
        actual = evaluate(by_id[key])
        assert actual["yes_metered_allowed"] is False
        assert actual["plan"]["fleet"]["readiness"] == "blocked"


def test_oracle_budget_absent_vs_empty_and_nonfinite():
    """Null/unset → provider/account cap only; empty string and non-finite invalid."""
    from oracle.routing_oracle import evaluate_budget

    absent = evaluate_budget(None)
    assert absent["ok"] is True
    assert absent["disclosure"] == "provider/account cap only"
    assert absent["cap"] is None

    for bad in ("", "   ", "NaN", "nan", "Infinity", "-Infinity", "inf", 0, -1, "abc"):
        got = evaluate_budget(bad)
        assert got["ok"] is False, f"expected invalid for {bad!r}"
        assert got["reason"] == "invalid-budget"

    # Finite positive still accepted
    ok = evaluate_budget(2.5)
    assert ok["ok"] is True
    assert ok["cap"] == 2.5

    fixtures = _load_fixtures()
    by_id = {f["id"]: f for f in fixtures}
    for fid in (
        "T3c-budget-empty-string",
        "T3c-budget-nonfinite",
        "T3c-budget-infinity",
    ):
        assert fid in by_id, f"missing fixture {fid}"
        actual = evaluate(by_id[fid])
        assert actual["plan"]["fleet"]["readiness"] == "blocked"
        assert actual["plan"]["fleet"]["reason"] == "invalid-budget"
        assert actual["yes_metered_allowed"] is False

    # Null fixture still provider/account-cap-only
    absent_fx = evaluate(by_id["T3c-budget-absent"])
    assert absent_fx["budget"]["disclosure"] == "provider/account cap only"
    assert absent_fx["plan"]["fleet"]["readiness"] == "ready"


def test_oracle_invalid_external_route_permission_fail_closed():
    fixtures = _load_fixtures()
    by_id = {f["id"]: f for f in fixtures}
    assert "T19-external-permission-invalid" in by_id
    actual = evaluate(by_id["T19-external-permission-invalid"])
    for lane in ("fleet", "peer-codex", "peer-grok"):
        assert actual["plan"][lane]["readiness"] == "blocked"
        assert actual["plan"][lane]["reason"] == "invalid-external-route-permission"
    assert actual["yes_metered_allowed"] is False

    contract = _read("eskill-common/references/model-routing.md")
    assert "invalid-external-route-permission" in contract
    assert "`allow`" in contract and "`deny`" in contract


def test_oracle_harness_mappings_claude_codex_grok_generic():
    fixtures = _load_fixtures()
    by_id = {f["id"]: f for f in fixtures}
    for hid, fid in (
        ("claude", "T11-claude-explicit-over-clis"),
        ("codex", "T11-codex-host"),
        ("grok", "T11-grok-explicit"),
        ("generic", "T11-generic-unknown"),
    ):
        actual = evaluate(by_id[fid])
        assert actual["harness"]["identity"] == hid


# ---------------------------------------------------------------------------
# Preference: structured multi-key exact match
# ---------------------------------------------------------------------------


def test_resolve_preference_structured_form_requires_exact_key():
    """{source,key,value} is accepted only when item.key equals the requested key.

    Higher-precedence entries for a *different* key must not steal resolution
    for the requested key (competing multi-key precedence regression).
    """
    # Higher-precedence structured entry for a different key must not win.
    sources = [
        {
            "source": "explicit-invocation",
            "key": "temperature",
            "value": "should-not-win",
        },
        {
            "source": "session",
            "key": "model",
            "value": "from-session-structured",
        },
        {
            "source": "project",
            "model": "from-project-direct",
        },
    ]
    got = resolve_preference(sources, "model")
    assert got is not None
    assert got["source"] == "session"
    assert got["value"] == "from-session-structured"
    assert got["key"] == "model"

    # Direct key on higher source still wins over structured lower source.
    sources2 = [
        {"source": "explicit-invocation", "model": "from-explicit-direct"},
        {
            "source": "session",
            "key": "model",
            "value": "from-session-structured",
        },
    ]
    got2 = resolve_preference(sources2, "model")
    assert got2 is not None
    assert got2["source"] == "explicit-invocation"
    assert got2["value"] == "from-explicit-direct"

    # Structured entry with wrong key is ignored even when it is the only high source.
    sources3 = [
        {"source": "explicit-invocation", "key": "lead", "value": "fable"},
        {"source": "user", "key": "model", "value": "user-model"},
    ]
    got3 = resolve_preference(sources3, "model")
    assert got3 is not None
    assert got3["source"] == "user"
    assert got3["value"] == "user-model"

    # Fixture family also covers the multi-key collision — preference drives plan.
    fixtures = _load_fixtures()
    by_id = {f["id"]: f for f in fixtures}
    key = "T18-precedence-multi-key-exact-match"
    assert key in by_id, f"missing multi-key preference fixture {key}"
    actual = evaluate(by_id[key])
    assert actual["model_preference"]["source"] == "session"
    assert actual["model_preference"]["value"] == "from-session-model-key"
    for p in actual["plans"]:
        assert p["requested_model"] == "from-session-model-key"
        assert p["preference_source"] == "session"
        assert p["planned_route_fingerprint"] == planned_route_fingerprint(
            provider=p["requested_provider"],
            requested_model="from-session-model-key",
            route_class=p["route_class"],
            context_class=p["context_class"],
        )


def test_oracle_lane_specific_requested_model_outranks_global_preference():
    """Explicit per-lane requested_model stays lane-specific when a global pref exists."""
    scenario = {
        "input": {
            "harness": {"explicit": "claude"},
            "preference_sources": [
                {"source": "session", "model": "global-session-model"},
            ],
            "requested_routes": ["critic", "peer-codex"],
            "sensitivity_scopes": ["low"],
            "external_route_permission": "allow",
            "redactor_available": True,
            "lane_specs": {
                "peer-codex": {
                    "requested_model": "lane-specific-codex",
                    "route_class": "external",
                    "context_class": "peer",
                },
            },
            "route_outcomes": {
                "critic": {
                    "outcome": "ran",
                    "observed_route": "native",
                    "observed_provider": "native",
                    "observed_model": "global-session-model",
                },
                "peer-codex": {
                    "outcome": "ran",
                    "observed_route": "peer-codex",
                    "observed_provider": "codex",
                    "observed_model": "lane-specific-codex",
                },
            },
        }
    }
    actual = evaluate(scenario)
    critic = next(p for p in actual["plans"] if p["lane"] == "critic")
    peer = next(p for p in actual["plans"] if p["lane"] == "peer-codex")
    # Global preference applies only to lanes without an explicit model.
    assert critic["requested_model"] == "global-session-model"
    assert critic["preference_source"] == "session"
    assert critic["planned_route_fingerprint"] == planned_route_fingerprint(
        provider="native",
        requested_model="global-session-model",
        route_class="first-party",
        context_class="local",
    )
    # Lane-specific model is more specific and is not overwritten by preference.
    assert peer["requested_model"] == "lane-specific-codex"
    assert peer["preference_source"] is None
    assert peer["planned_route_fingerprint"] == planned_route_fingerprint(
        provider="codex",
        requested_model="lane-specific-codex",
        route_class="external",
        context_class="peer",
    )
    assert "global-session-model" not in peer["planned_route_fingerprint"]


# ---------------------------------------------------------------------------
# Two-stage manifest schema + fingerprint identity
# ---------------------------------------------------------------------------


_PLANNED_REQUIRED_FIELDS = (
    "lane",
    "role",
    "requested_provider",
    "requested_model",
    "preference_source",
    "policy",
    "route_class",
    "context_class",
    "required",
    "countable",
    "planned_route_fingerprint",
    "readiness",
    "reason",
)

_RESULT_REQUIRED_FIELDS = (
    "lane",
    "observed_provider",
    "observed_model",
    "route_class",
    "context_class",
    "required",
    "countable",
    "observed_route",
    "outcome",
    "reason",
    "independent",
)


def test_oracle_planned_and_result_records_are_structurally_self_sufficient():
    """Every plan/result carries the explicit schema (no hidden name heuristics)."""
    scenario = {
        "input": {
            "harness": {"explicit": "claude"},
            "preference_sources": [
                {"source": "session", "model": "session-model"},
            ],
            "requested_routes": ["critic", "peer-codex", "fleet"],
            "sensitivity_scopes": ["high"],
            "external_route_permission": "allow",
            "redactor_available": True,
            "metered_consent": {
                "source": "current-invocation",
                "status": "valid",
            },
            "budget_usd": 1.0,
            "route_outcomes": {
                "critic": {
                    "outcome": "ran",
                    "observed_route": "native-critic",
                    "observed_provider": "native",
                    "observed_model": "critic",
                }
            },
        }
    }
    actual = evaluate(scenario)
    assert len(actual["plans"]) == 3
    assert len(actual["results"]) == 3
    _POLICY_REQUIRED = (
        "sensitivity",
        "sensitivity_error",
        "external_route_permission",
        "consent_accepted",
        "consent_class",
        "budget_ok",
        "budget_disclosure",
        "peer_redactor_available",
        "fleet_scrubber_available",
        "effective_redaction_gate",
        "effective_redaction_available",
    )
    for p in actual["plans"]:
        for field in _PLANNED_REQUIRED_FIELDS:
            assert field in p, f"planned record missing {field}: {p}"
        assert p["route_class"] in ("first-party", "external", "ambiguous")
        assert isinstance(p["required"], bool)
        assert isinstance(p["countable"], bool)
        assert p["planned_route_fingerprint"]
        # Preference drives planned model + fingerprint (not metadata-only).
        assert p["requested_model"] == "session-model"
        assert p["preference_source"] == "session"
        assert "session-model" in p["planned_route_fingerprint"]
        # Each plan carries a self-sufficient per-lane policy snapshot.
        for pk in _POLICY_REQUIRED:
            assert pk in p["policy"], f"policy missing {pk}: {p['policy']}"
        assert p["policy"]["peer_redactor_available"] is True
        assert p["policy"]["fleet_scrubber_available"] is True
    # Lane-specific effective redaction gates (not one shared opaque object).
    critic_plan = next(p for p in actual["plans"] if p["lane"] == "critic")
    peer_plan = next(p for p in actual["plans"] if p["lane"] == "peer-codex")
    fleet_plan = next(p for p in actual["plans"] if p["lane"] == "fleet")
    assert critic_plan["policy"]["effective_redaction_gate"] == "n/a"
    assert critic_plan["policy"]["effective_redaction_available"] is True
    assert peer_plan["policy"]["effective_redaction_gate"] == "identified-redaction-path"
    assert peer_plan["policy"]["effective_redaction_available"] is True
    assert fleet_plan["policy"]["effective_redaction_gate"] == "fleet-scrub"
    assert fleet_plan["policy"]["effective_redaction_available"] is True
    # Policies are per-lane objects (not one reused identity).
    assert critic_plan["policy"] is not peer_plan["policy"]
    assert peer_plan["policy"] is not fleet_plan["policy"]
    for r in actual["results"]:
        for field in _RESULT_REQUIRED_FIELDS:
            assert field in r, f"result record missing {field}: {r}"
        assert r["route_class"] in ("first-party", "external", "ambiguous")
        if r["outcome"] in ("blocked", "skipped"):
            assert r["observed_route"] is None
            assert r["independent"] is False
    # High local critic + blocked external derives local-only from schema.
    assert actual["panel_status"] == "local-only"
    critic = next(r for r in actual["results"] if r["lane"] == "critic")
    assert critic["outcome"] == "ran" and critic["independent"] is True
    assert critic["route_class"] == "first-party"
    for lane in ("peer-codex", "fleet"):
        r = next(x for x in actual["results"] if x["lane"] == lane)
        assert r["route_class"] == "external"
        assert r["outcome"] == "blocked"
        assert r["reason"] == "high-sensitivity"


def test_oracle_same_provider_different_models_not_predispatch_duplicates():
    """Same provider/context with different requested models keep distinct fingerprints."""
    scenario = {
        "input": {
            "harness": {"explicit": "claude"},
            "requested_routes": ["peer-codex", "codex-medium"],
            "sensitivity_scopes": ["low"],
            "external_route_permission": "allow",
            "redactor_available": True,
            "lane_specs": {
                "peer-codex": {
                    "requested_provider": "codex",
                    "requested_model": "codex-a",
                    "route_class": "external",
                    "context_class": "peer",
                },
                "codex-medium": {
                    "requested_provider": "codex",
                    "requested_model": "codex-b",
                    "route_class": "external",
                    "context_class": "peer",
                },
            },
            "route_outcomes": {
                "peer-codex": {
                    "outcome": "ran",
                    "observed_route": "peer-codex",
                    "observed_provider": "codex",
                    "observed_model": "codex-a",
                },
                "codex-medium": {
                    "outcome": "ran",
                    "observed_route": "codex-medium",
                    "observed_provider": "codex",
                    "observed_model": "codex-b",
                },
            },
        }
    }
    actual = evaluate(scenario)
    fps = [p["planned_route_fingerprint"] for p in actual["plans"]]
    assert fps[0] != fps[1], f"different models must not share fingerprint: {fps}"
    assert fps[0] == planned_route_fingerprint(
        provider="codex",
        requested_model="codex-a",
        route_class="external",
        context_class="peer",
    )
    assert fps[1] == planned_route_fingerprint(
        provider="codex",
        requested_model="codex-b",
        route_class="external",
        context_class="peer",
    )
    assert all(p["readiness"] == "ready" for p in actual["plans"])
    assert all(
        r["outcome"] == "ran" and r["independent"] is True for r in actual["results"]
    )
    assert actual["panel_status"] == "full"


def test_oracle_exact_duplicate_fingerprints_are_predispatch_duplicates():
    """Identical planned fingerprints still skip later lanes."""
    fixtures = _load_fixtures()
    by_id = {f["id"]: f for f in fixtures}
    actual = evaluate(by_id["T10-predispatch-duplicate-fingerprint"])
    assert actual["plan"]["peer-codex"]["readiness"] == "ready"
    assert actual["plan"]["codex-medium"]["readiness"] == "skipped"
    assert actual["plan"]["codex-medium"]["reason"] == "duplicate-planned-fingerprint"
    dup = next(p for p in actual["plans"] if p["lane"] == "codex-medium")
    assert dup["countable"] is False
    res_dup = next(r for r in actual["results"] if r["lane"] == "codex-medium")
    assert res_dup["countable"] is False
    assert res_dup["outcome"] == "skipped"


def test_oracle_high_local_critic_blocked_external_local_only_schema():
    """High + local critic + blocked external is local-only from required/countable schema."""
    scenario = {
        "input": {
            "harness": {"explicit": "claude"},
            "requested_routes": ["critic", "peer-codex", "peer-grok", "fleet"],
            "sensitivity_scopes": ["high"],
            "external_route_permission": "allow",
            "redactor_available": True,
            "metered_consent": {
                "source": "current-invocation",
                "status": "valid",
            },
            "budget_usd": 1.0,
            "route_outcomes": {
                "critic": {
                    "outcome": "ran",
                    "observed_route": "native-critic",
                    "observed_provider": "native",
                    "observed_model": "critic",
                }
            },
        }
    }
    got = evaluate(scenario)
    assert got["panel_status"] == "local-only"
    voices = independent_voices_summary(got["results"])
    assert [v["lane"] for v in voices["independent_voices"]] == ["critic"]
    blocked_lanes = {b["lane"] for b in voices["blocked_or_skipped"]}
    assert blocked_lanes == {"peer-codex", "peer-grok", "fleet"}
    # Must not look like a partial external panel.
    assert got["panel_status"] != "partial"


# ---------------------------------------------------------------------------
# esat-fleet output: actual independent voices only (no fixed trio slogan)
# ---------------------------------------------------------------------------


def test_fleet_output_lists_only_actual_independent_voices():
    """Council header must not always claim Frontier trio / Codex / Grok ran."""
    fleet = _read("esat-fleet/references/fleet-leg.md")

    # Extract the Output block template; fixed trio slogan must not be the header.
    out_m = re.search(
        r"## Output block\n(.*?)(?=\n## |\Z)",
        fleet,
        re.DOTALL,
    )
    assert out_m, "fleet-leg.md Output block missing"
    output_block = out_m.group(1)
    # Exact fixed slogan forms that always claimed trio voices.
    forbidden_header = (
        "_Frontier trio — Claude (`critic`) + Codex",
        "_Frontier trio — Claude",
        "### Council Panel\n_Frontier trio",
    )
    for phrase in forbidden_header:
        assert phrase not in output_block, (
            f"stale fixed trio slogan still present in output template: {phrase!r}"
        )
    # Template must not present Codex/Grok as always-ran header placeholders.
    assert not re.search(
        r"^_Frontier trio",
        output_block,
        re.MULTILINE,
    ), "output template still opens with fixed Frontier trio slogan"

    # Positive contract: list independent voices from terminal results.
    assert "Independent voices (from terminal results)" in output_block
    assert "Requested lanes blocked/skipped" in output_block
    assert "independent=true" in output_block
    # High / local-only must not claim trio/frontier/Codex/Grok ran.
    assert "must **not** claim trio" in fleet or "must not claim trio" in fleet.lower()
    assert "high" in fleet.lower() and "local-only" in fleet.lower()

    # Oracle-backed exact contract: high local-only summary never lists peer voices.
    scenario = {
        "input": {
            "harness": {"explicit": "claude"},
            "requested_routes": ["critic", "peer-codex", "peer-grok", "fleet"],
            "sensitivity_scopes": ["high"],
            "external_route_permission": "allow",
            "route_outcomes": {
                "critic": {
                    "outcome": "ran",
                    "observed_route": "native-critic",
                    "observed_provider": "native",
                    "observed_model": "critic",
                }
            },
        }
    }
    actual = evaluate(scenario)
    summary = independent_voices_summary(actual["results"])
    voice_lanes = [v["lane"] for v in summary["independent_voices"]]
    assert voice_lanes == ["critic"]
    assert "peer-codex" not in voice_lanes
    assert "peer-grok" not in voice_lanes
    assert "fleet" not in voice_lanes
    assert actual["panel_status"] == "local-only"
    # Rendered independent-voice line would not contain Codex/Grok/fleet.
    rendered = ", ".join(voice_lanes) if voice_lanes else "none"
    assert rendered == "critic"
    assert "peer-codex" not in rendered
    assert "peer-grok" not in rendered
    assert "Codex" not in rendered
    assert "Grok" not in rendered

# ---------------------------------------------------------------------------
# Medium redaction: peer IDENTIFIED path vs FleetFuse scrubber
# ---------------------------------------------------------------------------


def test_frontier_medium_peer_vs_fleet_redaction_paths_documented():
    """Peer requires IDENTIFIED_REDACTION_PATH; fleet uses fleet_scrub on raw DRAFT."""
    panel = _read("esat-frontier/references/frontier-panel.md")
    contract = _read("eskill-common/references/model-routing.md")
    fleet = _read("esat-fleet/references/fleet-leg.md")

    for text in (panel, contract, fleet):
        low = text.lower()
        assert "fleet_scrub" in low or "fleetfuse scrubber" in low
        assert "identified_redaction_path" in low
        assert "redactor-unavailable" in low
        assert "--no-redact" in text or "no-redact" in low

    # Peer medium: verified redacted dispatch input
    assert "IDENTIFIED_REDACTION_PATH" in panel
    assert 'peer codex "$PEER_PROMPT" < "$DISPATCH_INPUT"' in panel
    assert "verified redacted" in panel.lower() or "verified output" in panel.lower()

    # Fleet medium: may use raw DRAFT; scrubber is the gate (not IDENTIFIED path alone)
    assert "raw local" in panel.lower() or "raw local `$draft`" in panel.lower()
    assert "fleet_scrub" in panel
    assert (
        "Do **not** require `IDENTIFIED_REDACTION_PATH` for the fleet gate alone."
        in panel
    )
    # Explicit: fleet gate is scrubber availability
    assert "FleetFuse scrubber" in panel or "fleet scrubber" in panel.lower()
    assert "Never pass `--no-redact`" in panel or "never `--no-redact`" in panel.lower() or "Never** pass `--no-redact`" in panel or "never pass `--no-redact`" in panel.lower()

    # Shared contract table distinguishes the two paths
    assert "External peer" in contract or "external peer" in contract.lower()
    assert "FleetFuse" in contract
    assert "IDENTIFIED_REDACTION_PATH" in contract
    assert "fleet_scrub" in contract


def test_oracle_peer_and_fleet_redactors_are_independent_gates():
    """Missing peer redactor blocks peers; missing fleet scrubber blocks fleet only."""
    # Peer redactor down, fleet scrubber up → peer blocked, fleet ready
    peer_only_fail = {
        "input": {
            "harness": {"explicit": "claude"},
            "requested_routes": ["peer-codex", "peer-grok", "fleet"],
            "sensitivity_scopes": ["medium"],
            "external_route_permission": "allow",
            "redactor_available": False,
            "fleet_scrubber_available": True,
            "metered_consent": {
                "source": "current-invocation",
                "status": "valid",
            },
            "budget_usd": 1.0,
        }
    }
    got = evaluate(peer_only_fail)
    for lane in ("peer-codex", "peer-grok"):
        assert got["plan"][lane]["readiness"] == "blocked"
        assert got["plan"][lane]["reason"] == "redactor-unavailable"
        plan = next(p for p in got["plans"] if p["lane"] == lane)
        assert plan["policy"]["peer_redactor_available"] is False
        assert plan["policy"]["fleet_scrubber_available"] is True
        assert plan["policy"]["effective_redaction_gate"] == "identified-redaction-path"
        assert plan["policy"]["effective_redaction_available"] is False
    fleet_plan = next(p for p in got["plans"] if p["lane"] == "fleet")
    assert got["plan"]["fleet"]["readiness"] == "ready"
    assert fleet_plan["policy"]["peer_redactor_available"] is False
    assert fleet_plan["policy"]["fleet_scrubber_available"] is True
    assert fleet_plan["policy"]["effective_redaction_gate"] == "fleet-scrub"
    assert fleet_plan["policy"]["effective_redaction_available"] is True
    assert got["yes_metered_allowed"] is True

    # Peer redactor up, fleet scrubber down → fleet blocked, peers ready
    fleet_only_fail = {
        "input": {
            "harness": {"explicit": "claude"},
            "requested_routes": ["peer-codex", "peer-grok", "fleet"],
            "sensitivity_scopes": ["medium"],
            "external_route_permission": "allow",
            "redactor_available": True,
            "fleet_scrubber_available": False,
            "metered_consent": {
                "source": "current-invocation",
                "status": "valid",
            },
            "budget_usd": 1.0,
        }
    }
    got2 = evaluate(fleet_only_fail)
    assert got2["plan"]["fleet"]["readiness"] == "blocked"
    assert got2["plan"]["fleet"]["reason"] == "redactor-unavailable"
    fleet_plan2 = next(p for p in got2["plans"] if p["lane"] == "fleet")
    assert fleet_plan2["policy"]["peer_redactor_available"] is True
    assert fleet_plan2["policy"]["fleet_scrubber_available"] is False
    assert fleet_plan2["policy"]["effective_redaction_gate"] == "fleet-scrub"
    assert fleet_plan2["policy"]["effective_redaction_available"] is False
    for lane in ("peer-codex", "peer-grok"):
        assert got2["plan"][lane]["readiness"] == "ready"
        plan = next(p for p in got2["plans"] if p["lane"] == lane)
        assert plan["policy"]["peer_redactor_available"] is True
        assert plan["policy"]["fleet_scrubber_available"] is False
        assert plan["policy"]["effective_redaction_gate"] == "identified-redaction-path"
        assert plan["policy"]["effective_redaction_available"] is True
    assert got2["yes_metered_allowed"] is False

    # Compat: redactor_available=false without fleet_scrubber key still blocks fleet
    # (single-flag fixtures such as T5-medium-no-redactor).
    fixtures = _load_fixtures()
    by_id = {f["id"]: f for f in fixtures}
    t5 = evaluate(by_id["T5-medium-no-redactor"])
    assert t5["plan"]["fleet"]["readiness"] == "blocked"
    assert t5["plan"]["fleet"]["reason"] == "redactor-unavailable"
    t5_fleet = next(p for p in t5["plans"] if p["lane"] == "fleet")
    assert t5_fleet["policy"]["peer_redactor_available"] is False
    assert t5_fleet["policy"]["fleet_scrubber_available"] is False
    assert t5_fleet["policy"]["effective_redaction_gate"] == "fleet-scrub"
    assert t5_fleet["policy"]["effective_redaction_available"] is False


# ---------------------------------------------------------------------------
# Install copy layout (temporary HOME)
# ---------------------------------------------------------------------------


def test_copy_install_uninstall_codex_grok_temp_home():
    install = ROOT / "install.sh"
    assert install.is_file()
    with tempfile.TemporaryDirectory(prefix="eskill-install-") as tmp:
        env = {**dict(**{k: v for k, v in __import__("os").environ.items()}), "HOME": tmp}
        # Install copy into claude (canonical) + codex + grok
        r = subprocess.run(
            ["bash", str(install), "--copy", "--harness", "codex", "grok"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert r.returncode == 0, r.stderr + r.stdout
        for harness in ("claude", "codex", "grok"):
            base = pathlib.Path(tmp) / f".{harness}" / "skills"
            for skill in (
                "eskill-common",
                "eskill-analyze",
                "esa",
                "esat",
                "esat-fleet",
                "esat-frontier",
            ):
                skill_dir = base / skill
                assert skill_dir.is_dir(), f"missing install {skill_dir}"
                assert (skill_dir / "SKILL.md").is_file()
            # Sibling routing contract present
            assert (
                base / "eskill-common" / "references" / "model-routing.md"
            ).is_file()
            # Relocatable sibling path target exists from esat-fleet view
            assert (
                base / "esat" / "references" / "trio-panel.md"
            ).is_file()

        r2 = subprocess.run(
            ["bash", str(install), "--uninstall", "--harness", "codex", "grok"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert r2.returncode == 0, r2.stderr + r2.stdout
        for harness in ("claude", "codex", "grok"):
            base = pathlib.Path(tmp) / f".{harness}" / "skills"
            for skill in ("eskill-common", "esat-fleet", "esat-frontier"):
                assert not (base / skill).exists(), f"uninstall left {base / skill}"


# ---------------------------------------------------------------------------
# README public docs
# ---------------------------------------------------------------------------


def test_readme_documents_routing_semantics():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for token in (
        "model-routing.md",
        "Preference",
        "Metered consent",
        "provider/account cap only",
        "observed_route",
        "contract",
    ):
        assert token.lower() in readme.lower(), f"README missing: {token}"
    assert "gpt-5.5" not in readme


def test_roadmap_marks_phase9_routing_delivered():
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    assert "Harness-aware Phase-9 routing" in roadmap or "harness-aware" in roadmap.lower()
    assert "delivered" in roadmap.lower()


def test_changelog_unreleased_mentions_routing():
    cl = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "[Unreleased]" in cl
    assert "model-routing" in cl or "Harness-aware" in cl
    assert "--yes-metered" in cl or "metered consent" in cl.lower()


# ---------------------------------------------------------------------------
# Privacy: no absolute user paths in product files
# ---------------------------------------------------------------------------

# Local harness / agent telemetry — never treated as shipped product.
_NON_PRODUCT_TOP = {".git", ".omc", ".omx", ".grokprint", "tests", "__pycache__", ".pytest_cache"}
_PRIVACY_SUFFIXES = {".md", ".sh", ".json", ".yml", ".yaml", ".svg", ".txt"}
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


def _product_paths_for_privacy() -> list[pathlib.Path]:
    """Public/product surfaces: skills/, public root docs/scripts/config, tracked files.

    Untracked hidden Grok/agent telemetry (``.grokprint``) is not product.
    Tracked files outside non-product tops remain fully scanned.
    """
    found: set[pathlib.Path] = set()

    skills = ROOT / "skills"
    if skills.is_dir():
        for p in skills.rglob("*"):
            if p.is_file() and p.suffix in _PRIVACY_SUFFIXES:
                found.add(p)

    for name in _PUBLIC_ROOT_DOCS:
        p = ROOT / name
        if p.is_file():
            found.add(p)

    for rel in ("scripts", ".claude-plugin"):
        d = ROOT / rel
        if d.is_dir():
            for p in d.rglob("*"):
                if p.is_file() and (
                    p.suffix in _PRIVACY_SUFFIXES or p.name == "install.sh"
                ):
                    found.add(p)

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
                parts = pathlib.Path(rel).parts
                if not parts or parts[0] in _NON_PRODUCT_TOP:
                    continue
                p = ROOT / rel
                if p.is_file() and (
                    p.suffix in _PRIVACY_SUFFIXES or p.name in {"install.sh", "LICENSE"}
                ):
                    found.add(p)
    except OSError:
        pass

    return sorted(found)


def test_no_private_paths_in_product_docs():
    bad = []
    scanned = _product_paths_for_privacy()
    assert any(p.relative_to(ROOT).parts[0] == "skills" for p in scanned), (
        "privacy scan must cover skills/"
    )
    # Root public docs that exist must be in scope
    for name in ("README.md", "CHANGELOG.md", "ROADMAP.md"):
        p = ROOT / name
        if p.is_file():
            assert p in scanned, f"privacy scan must cover public root doc {name}"
    for p in scanned:
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "/home/" in text or "/Users/" in text:
            bad.append(str(p.relative_to(ROOT)))
    assert not bad, f"absolute user paths: {bad}"


if __name__ == "__main__":
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
    print(f"[{CONTRACT_LABEL}]")
    sys.exit(1 if failed else 0)
