#!/usr/bin/env python3
"""Blind pairwise judge for two eval arms, via `peer codex` (another model family).

    judge.py --runs DIR --a base --b full --prompts P.json [--prompts P2.json] [--jobs 4] [--ids ...]
    judge.py --runs DIR --a base --b full --report

Each pair is judged twice with the order swapped. Analyses go on stdin, never argv.
Verdicts append to DIR/judge-A-vs-B.jsonl; a rerun skips pairs already judged.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

CRITERIA = ["D1", "D2", "D3", "D4", "R", "A", "lean", "shape", "overall"]

RUBRIC = """You are a blind judge comparing two analyses written in answer to the same request. You do not
know which system wrote which. Judge substance, not labels: a heading such as "Verifier" or "Rawest
material" earns nothing unless its content is concrete and correct for this request. Longer is not
better; padding and extra workstreams count against an analysis.

For each criterion answer "1", "2" or "tie":
- D1: does something a top practitioner in this field would do that the request did not ask for, and it matters.
- D2: starts from, or names precisely, the most primary material (data, logs, code, filings, measurements)
  rather than digested summaries or the request's own framing; tests a premise against that material.
- D3: uses or specifies field-specific methods and tools in enough detail to run, not generic framework names.
- D4: names what, other than the model or the user, would show its conclusions or actions are right,
  concretely enough to check.
- R: brings in a technique from another field that changes the answer.
- A: connects the task to the outcome behind it where that helps; "tie" if neither needed it.
- lean: delivers its substance without bloat (fewer, sharper points).
- shape: reaches the substance fast; no process narration (how it was produced, what it skipped, meta labels).
- overall: which would teach a field expert more and be more useful to act on. Deeper, not bigger.

Reply with one JSON object only:
{"D1":"1|2|tie","D2":"..","D3":"..","D4":"..","R":"..","A":"..","lean":"..","shape":"..","overall":"1|2|tie","why":"<=30 words"}
"""

INSTRUCTION = "Follow the judging instructions in the piped input exactly. Output only the JSON object."


def load_prompts(paths: list[str]) -> dict[str, str]:
    return {p["id"]: p["prompt"] for path in paths for p in json.loads(pathlib.Path(path).read_text(encoding="utf-8"))}


def parse_verdict(text: str) -> dict | None:
    for m in reversed(list(re.finditer(r"\{[^{}]*\"overall\"[^{}]*\}", text, re.S))):
        try:
            v = json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
        if all(str(v.get(c)) in ("1", "2", "tie") for c in CRITERIA):
            return v
    return None


def judge_one(job: tuple, runs: pathlib.Path, a: str, b: str, prompts: dict[str, str]) -> dict:
    pid, order = job
    first, second = (a, b) if order == "ab" else (b, a)
    body = (f"{RUBRIC}\n=== REQUEST ===\n{prompts[pid]}\n\n=== ANALYSIS 1 ===\n"
            f"{(runs / first / f'{pid}.md').read_text(encoding='utf-8')}\n\n=== ANALYSIS 2 ===\n"
            f"{(runs / second / f'{pid}.md').read_text(encoding='utf-8')}\n")
    with tempfile.TemporaryDirectory() as cwd:
        for _ in range(2):
            proc = subprocess.run(["peer", "codex", INSTRUCTION], input=body, capture_output=True,
                                  text=True, timeout=900, cwd=cwd)
            verdict = parse_verdict(proc.stdout)
            if verdict:
                break
    if not verdict:
        return {"id": pid, "order": order, "error": (proc.stdout + proc.stderr)[-300:]}
    # Map "1"/"2" back to arm names so orders can be pooled.
    named = {c: {"1": first, "2": second, "tie": "tie"}[str(verdict[c])] for c in CRITERIA}
    return {"id": pid, "order": order, **named, "why": verdict.get("why", "")}


def report(path: pathlib.Path, a: str, b: str) -> None:
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if "error" not in r]
    by_id: dict[str, list[dict]] = {}
    for r in rows:
        by_id.setdefault(r["id"], []).append(r)
    print(f"{b} vs {a}: {len(by_id)} prompts, {len(rows)} verdicts")
    print("| Criterion | b wins | ties | a wins | b share |\n|-|-|-|-|-|")
    for c in CRITERIA:
        tally = Counter()
        for verdicts in by_id.values():
            score = sum(1 if v[c] == b else -1 if v[c] == a else 0 for v in verdicts)
            tally["b" if score > 0 else "a" if score < 0 else "tie"] += 1
        n = sum(tally.values()) or 1
        share = (tally["b"] + 0.5 * tally["tie"]) / n
        print(f"| {c} | {tally['b']} | {tally['tie']} | {tally['a']} | {share:.0%} |")
    both = [v for v in by_id.values() if len(v) == 2]
    agree = sum(1 for v in both if v[0]["overall"] == v[1]["overall"])
    print(f"\nPosition consistency (overall, both orders agree): {agree}/{len(both)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=pathlib.Path, required=True)
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--prompts", action="append", default=[])
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--ids")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    out = args.runs / f"judge-{args.a}-vs-{args.b}.jsonl"
    if args.report:
        report(out, args.a, args.b)
        return
    prompts = load_prompts(args.prompts)
    ids = args.ids.split(",") if args.ids else sorted(prompts)
    ids = [i for i in ids if (args.runs / args.a / f"{i}.md").exists() and (args.runs / args.b / f"{i}.md").exists()]
    done = set()
    if out.exists():
        done = {(r["id"], r["order"]) for r in map(json.loads, out.read_text().splitlines()) if "error" not in r}
    jobs = [(i, o) for i in ids for o in ("ab", "ba") if (i, o) not in done]
    with ThreadPoolExecutor(args.jobs) as pool, out.open("a", encoding="utf-8") as fh:
        for row in pool.map(lambda j: judge_one(j, args.runs, args.a, args.b, prompts), jobs):
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            print(row["id"], row["order"], row.get("overall", "ERROR"), flush=True)


if __name__ == "__main__":
    main()
