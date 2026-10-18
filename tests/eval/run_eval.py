#!/usr/bin/env python3
"""Run eval prompts through one engine arm with `claude -p`, no tools, isolated from local config.

    run_eval.py --engine ENGINE.txt --arm NAME --prompts P.json [--prompts P2.json] --out DIR
                [--model sonnet] [--jobs 4] [--ids A01,R3]

Writes DIR/NAME/<id>.md. Existing outputs are kept, so a rerun resumes.
"""
from __future__ import annotations

import argparse
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


def load_prompts(paths: list[str], ids: set[str] | None) -> list[dict]:
    items = [p for path in paths for p in json.loads(pathlib.Path(path).read_text(encoding="utf-8"))]
    return [p for p in items if not ids or p["id"] in ids]


def run_one(item: dict, engine: pathlib.Path, out_dir: pathlib.Path, model: str, timeout: int) -> str:
    out = out_dir / f"{item['id']}.md"
    if out.exists() and out.stat().st_size > 0:
        return f"{item['id']}: cached"
    # A leading "/esa" would make claude load the installed skill on top of the arm's engine.
    prompt = re.sub(r"^/\S+\s+", "", item["prompt"])
    start = time.time()
    proc = subprocess.run(
        ["claude", "-p", "--model", model, "--tools", "", "--no-session-persistence",
         "--strict-mcp-config", "--system-prompt-file", str(engine), prompt],
        capture_output=True, text=True, timeout=timeout, cwd=out_dir,
        env={**os.environ, **ISOLATED_ENV},
    )
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
    items = load_prompts(args.prompts, set(args.ids.split(",")) if args.ids else None)
    with ThreadPoolExecutor(args.jobs) as pool:
        for line in pool.map(lambda it: run_one(it, engine, out_dir, args.model, args.timeout), items):
            print(f"[{args.arm}] {line}", flush=True)


if __name__ == "__main__":
    main()
