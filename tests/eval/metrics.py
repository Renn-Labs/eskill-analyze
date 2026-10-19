#!/usr/bin/env python3
"""Deterministic depth metrics per eval arm (no model calls).

    metrics.py RUNS_DIR ARM [ARM ...]
"""
from __future__ import annotations

import pathlib
import re
import statistics
import sys

SELF_VERIFIER = re.compile(r"^\s*(the model|the user|user|model|me|you|claude|critic|tbd|-|)\s*$", re.I)


def verifier_cells(text: str) -> list[str]:
    """Return Verifier-column cells from any markdown table whose header names a Verifier column."""
    cells: list[str] = []
    col = None
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            col = None
            continue
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if col is None:
            col = next((i for i, p in enumerate(parts) if p.lower() == "verifier"), None)
            continue
        if set("".join(parts)) <= set("-: "):
            continue
        if col < len(parts):
            cells.append(parts[col])
    return cells


def arm_metrics(arm_dir: pathlib.Path) -> dict:
    files = sorted(arm_dir.glob("*.md"))
    words, deepened, lenses, ver_rows, ver_self, raw_tags = [], 0, 0, 0, 0, 0
    for f in files:
        t = f.read_text(encoding="utf-8")
        words.append(len(t.split()))
        deepened += "Ask, deepened" in t or "Deepened Ask" in t  # current label, then the round-1 one
        lenses += "**Lenses**" in t
        cells = verifier_cells(t)
        ver_rows += len(cells)
        ver_self += sum(1 for c in cells if SELF_VERIFIER.match(c))
        raw_tags += len(re.findall(r"`?\b(raw|digested)\b`?", t, re.I))
    n = len(files) or 1
    return {
        "n": len(files),
        "median_words": int(statistics.median(words)) if words else 0,
        "deepened_ask": f"{deepened}/{len(files)}",
        "lenses_line": f"{lenses}/{len(files)}",
        "verifier_cells": ver_rows,
        "verifier_self_or_blank": ver_self,
        "raw_digested_mentions_per_run": round(raw_tags / n, 1),
    }


def main() -> None:
    runs = pathlib.Path(sys.argv[1])
    arms = sys.argv[2:]
    rows = {a: arm_metrics(runs / a) for a in arms}
    keys = list(next(iter(rows.values())).keys())
    print("| Metric | " + " | ".join(arms) + " |")
    print("|-|" + "-|" * len(arms))
    for k in keys:
        print(f"| {k} | " + " | ".join(str(rows[a][k]) for a in arms) + " |")


if __name__ == "__main__":
    main()
