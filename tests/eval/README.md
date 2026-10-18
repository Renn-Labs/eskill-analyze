# Depth eval

A before/after and ablation harness for engine prompt changes. It measures what the engine text makes a model write. With tools disabled, nothing can be read during a run, so it does not test tool-driven raw reads.

```bash
E=/tmp/depth-eval; mkdir -p $E
python3 tests/eval/build_engine.py <old-skills-dir> > $E/base.txt
python3 tests/eval/build_engine.py skills > $E/full.txt
python3 tests/eval/build_engine.py skills --drop deepen > $E/no-deepen.txt   # also: lenses, verifier

python3 tests/eval/run_eval.py --engine $E/base.txt --arm base --prompts tests/eval/prompts.json --out $E/runs
python3 tests/eval/run_eval.py --engine $E/full.txt --arm full --prompts tests/eval/prompts.json --out $E/runs
python3 tests/eval/judge.py   --runs $E/runs --a base --b full --prompts tests/eval/prompts.json
python3 tests/eval/judge.py   --runs $E/runs --a base --b full --report
python3 tests/eval/metrics.py $E/runs base full
```

- **Generation:** `run_eval.py` runs `claude -p` with no tools, no CLAUDE.md, no hooks and no advisor. It strips a leading `/esa` from each prompt so the installed skill can't override the arm's engine.
- **Judging:** `judge.py` uses `peer codex`, which is a different model family from the generator. It judges each pair twice with the order swapped, sending the analyses on stdin. It scores expert move (D1), raw material (D2), instruments (D3), external verifier (D4), range (R), altitude (A), lean and overall.
- **Prompts:** `prompts.json` holds 20 adversarial prompts. Each one probes a type, scale, lens or trap: bloat, persona role-play, a pre-digested causal claim, creative altitude, or a vague ask.
