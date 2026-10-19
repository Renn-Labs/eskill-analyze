#!/usr/bin/env python3
"""Run eval prompts through one engine arm with `claude -p`, no tools, isolated from local config.

    run_eval.py --engine ENGINE.txt --arm NAME --prompts P.json [--prompts P2.json] --out DIR
                [--model sonnet] [--jobs 4] [--ids A01,R3]

Writes DIR/NAME/<id>.md. Existing outputs are kept, so a rerun resumes; an arm is pinned to the hash of
its engine file, so a changed engine needs a new arm name. Exits 1 if any requested run failed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

ISOLATED_ENV = {
    "DISABLE_OMC": "1",
    "OMC_SKIP_HOOKS": "all",
    "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1",
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
    "CLAUDE_CODE_DISABLE_ADVISOR_TOOL": "1",
}
# Hooks can inject context into a run; the env vars above only quiet OMC's own.
NO_HOOKS = json.dumps({"disableAllHooks": True})
SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")


def load_prompts(paths: list[str], ids: set[str] | None) -> list[dict]:
    items = [p for path in paths for p in json.loads(pathlib.Path(path).read_text(encoding="utf-8"))]
    bad = [p["id"] for p in items if not SAFE_ID.match(p["id"])]
    if bad:
        raise SystemExit(f"unsafe prompt ids (used as file names): {bad}")
    return [p for p in items if not ids or p["id"] in ids]


def run_one(item: dict, engine: pathlib.Path, out_dir: pathlib.Path, model: str, timeout: int) -> str:
    out = out_dir / f"{item['id']}.md"
    if out.exists() and out.stat().st_size > 0:
        return f"{item['id']}: cached"
    # A leading "/esa" would make claude load the installed skill on top of the arm's engine.
    prompt = re.sub(r"^/\S+\s+", "", item["prompt"])
    start = time.time()
    # The prompt goes on stdin so prompt text can never be parsed as a CLI option.
    try:
        proc = subprocess.run(
            ["claude", "-p", "--model", model, "--tools", "", "--no-session-persistence",
             "--strict-mcp-config", "--settings", NO_HOOKS, "--system-prompt-file", str(engine)],
            input=prompt, capture_output=True, text=True, timeout=timeout, cwd=out_dir,
            env={**os.environ, **ISOLATED_ENV},
        )
    except subprocess.TimeoutExpired:
        return f"{item['id']}: FAILED timeout after {timeout}s"
    secs = round(time.time() - start)
    if proc.returncode != 0 or not proc.stdout.strip():
        return f"{item['id']}: FAILED rc={proc.returncode} {proc.stderr.strip()[:200]}"
    out.write_text(proc.stdout, encoding="utf-8")
    return f"{item['id']}: {len(proc.stdout.split())} words, {secs}s"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", type=pathlib.Path, required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--prompts", action="append", required=True)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--ids")
    args = ap.parse_args()

    out_dir = (args.out / args.arm).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    engine = args.engine.resolve()
    pin = out_dir / ".engine.sha256"
    digest = hashlib.sha256(engine.read_bytes()).hexdigest()
    if pin.exists() and pin.read_text().strip() != digest:
        raise SystemExit(f"arm {args.arm} was generated with a different engine; use a new --arm name")
    pin.write_text(digest + "\n")
    items = load_prompts(args.prompts, set(args.ids.split(",")) if args.ids else None)
    failed = 0
    with ThreadPoolExecutor(args.jobs) as pool:
        for line in pool.map(lambda it: run_one(it, engine, out_dir, args.model, args.timeout), items):
            failed += ": FAILED" in line
            print(f"[{args.arm}] {line}", flush=True)
    if failed:
        raise SystemExit(f"[{args.arm}] {failed} of {len(items)} runs failed")


if __name__ == "__main__":
    main()
