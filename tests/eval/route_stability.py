#!/usr/bin/env python3
"""Route stability between two runs of the same engine: does the router decide, or roll dice?

    route_stability.py RUNS_DIR ARM_A ARM_B [--ids P001,P002]
"""
from __future__ import annotations

import argparse
import pathlib
import re

ROUTE = re.compile(r"^\*\*Route\*\*:(.*)$", re.M)
MODULES = {
    "evidence": r"evidence|phase 0",
    "premortem": r"premortem|phase p",
    "compare": r"compar",
    "borrow": r"borrow|range",
    "actions": r"action",
    "stress": r"stress|phase 9|critic",
    "security": r"security",
}


def parse(path: pathlib.Path) -> dict | None:
    m = ROUTE.search(path.read_text(encoding="utf-8"))
    if not m:
        return None
    line = m.group(1)
    kind = re.search(r"([a-z-]+)/(quick|standard|deep)", line, re.I)
    mods = re.search(r"modules?:\s*(.*?)(?:·|·|$)", line, re.I)
    body = mods.group(1) if mods else ""
    found = {k for k, pat in MODULES.items() if re.search(pat, body, re.I)}
    return {"scale": kind.group(2).lower() if kind else None,
            "inline": not found, "modules": found}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", type=pathlib.Path)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--ids")
    args = ap.parse_args()
    ids = args.ids.split(",") if args.ids else sorted(p.stem for p in (args.runs / args.a).glob("*.md"))
    rows = []
    for i in ids:
        pa, pb = args.runs / args.a / f"{i}.md", args.runs / args.b / f"{i}.md"
        if pa.exists() and pb.exists():
            ra, rb = parse(pa), parse(pb)
            if ra and rb:
                rows.append((i, ra, rb))
    n = len(rows) or 1
    inline = sum(ra["inline"] == rb["inline"] for _, ra, rb in rows)
    scale = sum(ra["scale"] == rb["scale"] for _, ra, rb in rows)
    exact = sum(ra["modules"] == rb["modules"] for _, ra, rb in rows)
    jacc = [len(ra["modules"] & rb["modules"]) / len(ra["modules"] | rb["modules"])
            for _, ra, rb in rows if ra["modules"] | rb["modules"]]
    print(f"{args.a} vs {args.b}: {len(rows)} prompts")
    print(f"inline-vs-modules agree {inline}/{len(rows)} · scale agree {scale}/{len(rows)} · "
          f"identical module set {exact}/{len(rows)} · mean module Jaccard {sum(jacc) / (len(jacc) or 1):.2f}")
    flips = {m: sum((m in ra["modules"]) != (m in rb["modules"]) for _, ra, rb in rows) for m in MODULES}
    print("per-module flips: " + " · ".join(f"{m} {k}/{len(rows)}" for m, k in flips.items()))
    for i, ra, rb in rows:
        if ra["inline"] != rb["inline"] or ra["scale"] != rb["scale"]:
            print(f"  flip {i}: {ra['scale']}/{'inline' if ra['inline'] else sorted(ra['modules'])}"
                  f" -> {rb['scale']}/{'inline' if rb['inline'] else sorted(rb['modules'])}")


if __name__ == "__main__":
    main()
