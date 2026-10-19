#!/usr/bin/env python3
"""Assemble the eskill-analyze engine into one system prompt for no-tool eval runs.

    build_engine.py SKILLS_DIR [--drop deepen|lenses|verifier ...] [--live] > engine.txt

--drop removes one addition from the pre-elastic 1.2.0 engine (commit 437a9e8; round-1 ablation).
Each removal asserts its anchor text exists, so a drifted engine fails loudly.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

FILES = [
    "eskill-analyze/SKILL.md",
    "eskill-analyze/references/triage-guide.md",
    "eskill-analyze/references/mental-models.md",
    "eskill-analyze/references/analysis-protocol.md",
    "eskill-analyze/references/world-class-signals.md",
    "eskill-analyze/assets/output-template.md",
    "eskill-common/references/quality-principles.md",
    "eskill-common/references/anti-slop-rules.md",
    "eskill-common/references/project-impact-protocol.md",
]

HARNESS = """You are executing the eskill-analyze skill below in a non-interactive, no-tools evaluation.
You cannot read files, run commands, browse, or spawn subagents. Where the skill says to dispatch an
agent or read material, reason in-session instead; name a source you could not read only where the
answer depends on it. Do not stop to ask the user questions: where the skill says to ask, make the most
reasonable assumption, state it in one line, and continue. Output only the final analysis in the skill's
output format.
"""

LIVE_HARNESS = """You are executing the eskill-analyze skill below for a real user request. You have read-only
tools, and the working directory is the user's project. Spawn subagents only if an Agent tool is
available; otherwise do their work yourself. Output only the final analysis in the skill's output format.
"""

TRIAGE = "eskill-analyze/references/triage-guide.md"
SKILL = "eskill-analyze/SKILL.md"
PROTOCOL = "eskill-analyze/references/analysis-protocol.md"
MODELS = "eskill-analyze/references/mental-models.md"
TEMPLATE = "eskill-analyze/assets/output-template.md"
ANTI = "eskill-common/references/anti-slop-rules.md"

# (file, pattern, replacement, is_regex). Anchors track the shipped engine; test_structure builds every drop.
DROPS: dict[str, list[tuple[str, str, str, bool]]] = {
    "deepen": [
        (TRIAGE, r"Also answer the four deepening questions.*?\n\n", "", True),
        (TRIAGE, r"If the answers change the ask, restate it.*?\n\n", "", True),
        (TRIAGE, "**Ask, deepened**: {one line, only if Step 0 changed the ask}\n", "", False),
        (SKILL, "| `/esa deepen <ask>` | Router Step 0; prints the four answers and the deepened ask |\n", "", False),
        (SKILL, " The four deepening answers surface inside those sections, never as their own block.", "", False),
        (TEMPLATE, "**Ask, deepened**: {one line, only if router Step 0 changed the ask}\n", "", False),
    ],
    "lenses": [
        (TRIAGE, r"Lenses generate atoms; they are not labels\..*?\n\n", "", True),
        (SKILL, ", plus one borrowed field technique when the Range lens produces an atom", "", False),
        (PROTOCOL, "\nUnder the Depth or Range lens, apply that file's Instruments and Range rules.", "", False),
        (MODELS, r"\n## Depth: Instruments Over Vocabulary\n.*", "\n", True),
    ],
    "verifier": [
        (TEMPLATE, "| AAARRR | Verifier | Why |\n|-|-|-|-|-|-|-|-|-|-|\n"
                   "| 1 | | H/M/L | H/M/L | H/M/L | Y/N | Quick/Foundation/Long | | | |",
         "| AAARRR | Why |\n|-|-|-|-|-|-|-|-|-|\n"
         "| 1 | | H/M/L | H/M/L | H/M/L | Y/N | Quick/Foundation/Long | | |", False),
        (TEMPLATE, "| Horizon | Verifier | Why |\n|-|-|-|-|-|-|-|-|-|\n"
                   "| 1 | | H/M/L | H/M/L | H/M/L | Y/N | Quick/Foundation/Long | | |",
         "| Horizon | Why |\n|-|-|-|-|-|-|-|-|\n"
         "| 1 | | H/M/L | H/M/L | H/M/L | Y/N | Quick/Foundation/Long | |", False),
        (TEMPLATE, r"_Verifier: what, other than.*?\n", "", True),
        (TEMPLATE, r"\*\*Verifier\*\*: \[what, other than.*?\n", "", True),
        (TRIAGE, r"- Every action that exists has an outside Verifier.*?\n", "", True),
        (ANTI, r"\n12\. \*\*Vocabulary is not a method\.\*\*.*", "", True),
    ],
}


def build(skills_dir: pathlib.Path, drops: list[str], live: bool = False) -> str:
    texts = {rel: (skills_dir / rel).read_text(encoding="utf-8") for rel in FILES}
    for name in drops:
        for rel, pat, rep, is_regex in DROPS[name]:
            if is_regex:
                new, n = re.subn(pat, rep, texts[rel], count=1, flags=re.S)
            else:
                n = texts[rel].count(pat)
                new = texts[rel].replace(pat, rep)
            if n == 0:
                sys.exit(f"--drop {name}: anchor not found in {rel}: {pat[:60]!r}")
            texts[rel] = new
    parts = [LIVE_HARNESS if live else HARNESS]
    for rel in FILES:
        body = texts[rel].replace("${CLAUDE_SKILL_DIR}/..", "skills").replace("${CLAUDE_SKILL_DIR}", "skills/eskill-analyze")
        parts.append(f"\n===== FILE: skills/{rel} =====\n{body}")
    return "\n".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("skills_dir", type=pathlib.Path)
    ap.add_argument("--drop", action="append", default=[], choices=sorted(DROPS))
    ap.add_argument("--live", action="store_true", help="harness preamble for runs with read-only tools")
    args = ap.parse_args()
    sys.stdout.write(build(args.skills_dir, args.drop, args.live))


if __name__ == "__main__":
    main()
