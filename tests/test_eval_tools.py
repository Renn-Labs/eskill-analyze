#!/usr/bin/env python3
"""Unit checks for the depth-eval scripts in tests/eval/: the numbers they print must be right."""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "eval"))
import judge  # noqa: E402
import route_audit  # noqa: E402
import route_stability  # noqa: E402

ACTIONS_THEN_RISKS = """### Prioritized Actions
| # | Action | Verifier |
|-|-|-|
| 1 | a | t |
| 2 | b | t |

### Failure Modes
| Risk | Likelihood | Impact | Prevention |
|-|-|-|-|
| x | H | H | y |
| z | M | M | w |
"""


def test_action_rows_stop_at_the_table_end():
    assert route_audit.action_rows(ACTIONS_THEN_RISKS) == 2


def test_modules_split_on_commas_only():
    assert route_audit.modules_in(" quick · modules: Actions + Verifier · models: none") == 1
    assert route_audit.modules_in(" std · modules: evidence, premortem, actions · models: x") == 3
    assert route_audit.modules_in(" quick · modules: none · models: none") == 0


def test_stability_counts_unknown_modules_as_modules(tmp_path):
    f = tmp_path / "x.md"
    f.write_text("**Route**: technical/standard · modules: Steps 1-2, System Map · models: x\n")
    assert not route_stability.parse(f)["inline"]
    f.write_text("**Route**: technical/quick · modules: none · models: none\n")
    assert route_stability.parse(f)["inline"]


def _row(pid, order, overall, **extra):
    row = {"id": pid, "order": order, "overall": overall, "why": ""}
    row.update({c: overall for c in judge.CRITERIA if c not in extra and c != "overall"})
    row.update(extra)
    return row


def test_report_scores_only_complete_pairs_and_latest_rerun(tmp_path, capsys):
    rows = [
        _row("P1", "ab", "b"), _row("P1", "ba", "b"),            # complete: b wins
        _row("P2", "ab", "b"),                                    # one order only: not scored
        _row("P3", "ab", "a"), _row("P3", "ab", "b"), _row("P3", "ba", "b"),  # rerun replaces ab
        {"id": "P4", "order": "ab", "error": "x"}, _row("P4", "ba", "b"),
    ]
    legacy = _row("P5", "ab", "a")
    del legacy["shape"]                                           # written before `shape` existed
    rows += [legacy, _row("P5", "ba", "a")]
    path = tmp_path / "judge.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    judge.report(path, "a", "b")
    out = capsys.readouterr().out
    assert "3 prompts with both orders" in out and "P2" in out and "P4" in out
    assert "| overall | 2 | 0 | 1 | 67% |" in out


def test_parse_verdict_survives_braces_in_why():
    verdict = {c: "1" for c in judge.CRITERIA} | {"why": "uses {placeholders} well"}
    assert judge.parse_verdict("noise " + json.dumps(verdict))["overall"] == "1"
    assert judge.parse_verdict("no json here") is None
