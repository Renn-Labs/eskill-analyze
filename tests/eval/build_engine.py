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

# (file, pattern, replacement, is_regex)
DROPS: dict[str, list[tuple[str, str, str, bool]]] = {
    "deepen": [
        (TRIAGE, r"## Step 0: Deepen the Ask\n.*?(?=## Ambition Lenses)", "", True),
        (TRIAGE, "Tag lenses from the Step 0 answers;", "Tag lenses from the prompt;", False),
        (TRIAGE, "; Step 0 found reachable raw material", "", False),
        (TRIAGE, "State the Deepened Ask (Step 0), then your triage result, at the start",
         "State your triage result at the start", False),
        (SKILL, r"First run triage Step 0, \*\*Deepen the Ask\*\*.*?\n\n", "", True),
        (SKILL, "State the Deepened Ask and the triage result", "State the triage result", False),
        (SKILL, "- Deepened Ask and Triage header", "- Triage header", False),
        (SKILL, "the rawest material Step 0 named", "the rawest material available", False),
        (PROTOCOL, "the rawest material triage Step 0 named", "the rawest material available", False),
        (TEMPLATE, r"### Deepened Ask\n\*\*Expert move\*\*.*?\n\n", "", True),
        (TEMPLATE, r"### Deepened Ask\n_Same five lines.*?\n\n", "", True),
    ],
    "lenses": [
        (TRIAGE, r"## Ambition Lenses\n.*?(?=## Step 1: Classify Type)", "", True),
        (TRIAGE, "| Phase 0: Evidence Gathering | Skip*** |", "| Phase 0: Evidence Gathering | Skip |", False),
        (TRIAGE, "\n\\*** Under the Depth lens, make at least one raw read in-session even on `quick`.\n", "", False),
        (TRIAGE, "**Lenses**: {Depth, Range, Altitude — or Speed (default)}\n", "", False),
        (SKILL, ", plus one borrowed field technique when the Range lens is tagged", "", False),
        (SKILL, "3. **Lenses**: Depth / Range / Altitude, or none (Speed is the default)\n4. **Agents**",
         "3. **Agents**", False),
        (SKILL, "5. **Models**", "4. **Models**", False),
        (SKILL, "6. **Phases**", "5. **Phases**", False),
        (SKILL, " raw-first (start from the rawest material Step 0 named)", "", False),
        (SKILL, "Triage header (with Lenses)", "Triage header", False),
        (SKILL, "Find primary sources (filings, datasets, specs, source code, raw user evidence)\n"
                "     and the instruments practitioners use for: {domain}/{focus_area}. Tag each finding raw or digested.",
         "Research world-class benchmarks and best practices for: {domain}/{focus_area}.", False),
        (PROTOCOL, r"\*\*Raw first\.\*\*.*?\n\n", "", True),
        (PROTOCOL, "     Find primary sources first (filings, datasets, specs, source code, raw user evidence), then\n"
                   "     best-in-class examples and the instruments practitioners use. Tag each finding raw or digested.",
         "     Find: industry benchmarks, best-in-class examples, emerging patterns, common pitfalls.", False),
        (PROTOCOL, "     Start from raw records (logs, events, exports), not dashboards.\n", "", False),
        (PROTOCOL, "\nUnder the Depth or Range lens, apply that file's Instruments and Range rules.", "", False),
        (MODELS, r"## Depth: Instruments Over Vocabulary\n.*?(?=## Auto-Selection)", "", True),
        (TEMPLATE, "**Lenses**: {Depth, Range, Altitude — or Speed (default)}\n", "", False),
        (TEMPLATE, " Tag each item `raw` or `digested`.", "", False),
    ],
    "verifier": [
        (TEMPLATE, "| AAARRR | Verifier | Why |\n|-|-|-|-|-|-|-|-|-|-|\n"
                   "| 1 | | H/M/L | H/M/L | H/M/L | Y/N | Quick/Foundation/Long | | | |",
         "| AAARRR | Why |\n|-|-|-|-|-|-|-|-|-|\n"
         "| 1 | | H/M/L | H/M/L | H/M/L | Y/N | Quick/Foundation/Long | | |", False),
        (TEMPLATE, r"_Verifier: what, other than.*?\n", "", True),
        (TEMPLATE, "| Horizon | Verifier | Why |\n|-|-|-|-|-|-|-|-|-|\n"
                   "| 1 | | H/M/L | H/M/L | H/M/L | Y/N | Quick/Foundation/Long | | |",
         "| Horizon | Why |\n|-|-|-|-|-|-|-|-|\n"
         "| 1 | | H/M/L | H/M/L | H/M/L | Y/N | Quick/Foundation/Long | |", False),
        (SKILL, "- Verifier column in Prioritized Actions: always\n", "", False),
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
