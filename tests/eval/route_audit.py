#!/usr/bin/env python3
"""Deterministic route audit: does the router pick the expected shape? No model calls.

    route_audit.py RUNS_DIR ARM [--ids A01,A02] [--verbose]

Checks every output in RUNS_DIR/ARM for a Route line and no ceremony blocks, then checks each
prompt that has an entry in expected_routes.json against its expectations.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
ROUTE = re.compile(r"^\*\*Route\*\*:(.*)$", re.M)


def modules_in(route: str) -> int | None:
    m = re.search(r"modules?:\s*(.*?)(?:·|·|$)", route, re.I)
    if not m:
        return None
    body = m.group(1).strip().strip("{}")
    if not body or re.fullmatch(r"(none|inline|—|-)[^,]*", body, re.I):
        return 0
    return len([p for p in re.split(r",|\+| and ", body) if p.strip()])


def action_rows(text: str) -> int:
    m = re.search(r"### Prioritized Actions.*?\n((?:\|.*\n?)+)", text, re.S)
    if not m:
        return 0
    rows = [r for r in m.group(1).splitlines() if r.startswith("|") and not set(r) <= set("|-: ")]
    return max(0, len(rows) - 1)


def check(text: str, exp: dict) -> list[str]:
    fails = []
    route = ROUTE.search(text)
    n = modules_in(route.group(1)) if route else None
    if "max_modules" in exp and (n is None or n > exp["max_modules"]):
        fails.append(f"modules={n} > {exp['max_modules']}")
    words = len(text.split())
    if "max_words" in exp and words > exp["max_words"]:
        fails.append(f"words={words} > {exp['max_words']}")
    for pat in exp.get("require", []):
        if not re.search(pat, text, re.I):
            fails.append(f"missing /{pat}/")
    for pat in exp.get("forbid", []):
        if re.search(pat, text, re.I):
            fails.append(f"forbidden /{pat}/")
    if "max_actions" in exp and action_rows(text) > exp["max_actions"]:
        fails.append(f"actions={action_rows(text)} > {exp['max_actions']}")
    return fails


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", type=pathlib.Path)
    ap.add_argument("arm")
    ap.add_argument("--ids")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    expected = {k: v for k, v in json.loads((HERE / "expected_routes.json").read_text()).items() if not k.startswith("_")}
    files = sorted((args.runs / args.arm).glob("*.md"))
    if args.ids:
        keep = set(args.ids.split(","))
        files = [f for f in files if f.stem in keep]

    no_route = [f.stem for f in files if not ROUTE.search(f.read_text(encoding="utf-8"))]
    ceremony = [f.stem for f in files if re.search(r"### Deepened Ask|\*\*Lenses\*\*", f.read_text(encoding="utf-8"))]
    passed, audited = 0, 0
    for f in files:
        if f.stem not in expected:
            continue
        audited += 1
        fails = check(f.read_text(encoding="utf-8"), expected[f.stem])
        passed += not fails
        if fails or args.verbose:
            print(f"{'FAIL' if fails else 'ok  '} {f.stem} ({expected[f.stem]['why']}): {'; '.join(fails)}")
    print(f"\n{args.arm}: route audit {passed}/{audited} · Route line missing in {len(no_route)}/{len(files)}"
          f"{' ' + ','.join(no_route[:8]) if no_route else ''} · ceremony blocks in {len(ceremony)}")


if __name__ == "__main__":
    main()
