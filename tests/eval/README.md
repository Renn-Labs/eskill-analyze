# Depth eval

A before/after and ablation harness for engine prompt changes. It measures what the engine text makes a model write. With tools disabled, nothing can be read during a run, so it does not test tool-driven raw reads.

```bash
E=$(mktemp -d)
python3 tests/eval/build_engine.py <old-skills-dir> > $E/base.txt
python3 tests/eval/build_engine.py skills > $E/full.txt
python3 tests/eval/build_engine.py skills --drop deepen > $E/no-deepen.txt   # also: lenses, verifier

python3 tests/eval/run_eval.py --engine $E/base.txt --arm base --prompts tests/eval/prompts.json --out $E/runs
python3 tests/eval/run_eval.py --engine $E/full.txt --arm full --prompts tests/eval/prompts.json --out $E/runs
python3 tests/eval/judge.py   --runs $E/runs --a base --b full --prompts tests/eval/prompts.json
python3 tests/eval/judge.py   --runs $E/runs --a base --b full --report
python3 tests/eval/metrics.py $E/runs base full
```

- **Generation:** `run_eval.py` runs `claude -p` with no tools, no CLAUDE.md, all hooks disabled and no advisor; the prompt goes on stdin. It strips a leading `/esa` from each prompt so the installed skill can't override the arm's engine. Each arm directory is pinned to its engine's hash, so a changed engine needs a new arm name, and the script exits 1 if any run failed.
- **Judging:** `judge.py` uses `codex exec` with its shell, browser and app tools disabled and no user config by default (it first checks that the judge cannot read a planted file, and aborts if it can), a different model family from the generator (model and effort via `JUDGE_CODEX_MODEL`, `JUDGE_CODEX_EFFORT`; default `gpt-5.6-terra`, medium), or `--judge litellm:<model>` through a LiteLLM proxy (`LITELLM_URL`, `LITELLM_API_KEY`). It judges each pair twice with the order swapped, sending the analyses on stdin, and scores only prompts with a valid verdict in both orders. Criteria: expert move (D1), raw material (D2), instruments (D3), external verifier (D4), range (R), altitude (A), lean, shape and overall. Verdicts are cached per rubric.
- **Data egress:** judging sends every prompt and both analyses to the judge model's provider. Keep confidential prompts out of a judged run, or judge with a model you are allowed to send them to.
- **Routing checks:** `route_audit.py` checks outputs against `expected_routes.json` with no model calls and exits 1 on any miss. `route_stability.py` compares two runs of the same engine module by module.
- **Live smoke:** `build_engine.py skills --live` writes a preamble for runs with read-only tools; those runs are by hand with `claude -p --system-prompt-file <engine> --permission-mode dontAsk`, read-only `--allowedTools` and `--disallowedTools Write,Edit,NotebookEdit`, in the project being analysed.
- **Ablation:** `--drop deepen|lenses|verifier` removes one feature from the shipped engine; `test_structure.py` fails if an anchor goes stale.
- **Prompts:** `prompts.json` holds 20 adversarial prompts. Each one probes a type, scale, lens or trap: bloat, persona role-play, a pre-digested causal claim, creative altitude, or a vague ask. `entry_prompts.json` probes the four module entry points.
