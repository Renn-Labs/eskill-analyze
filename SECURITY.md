# Security

eskill-analyze is a set of **prompt/markdown skills** plus one shell installer (`install.sh`). It contains no
network code and no runtime services. There are two things worth understanding before you run it.

## 1. The installer runs shell

`install.sh` symlinks (or copies) the bundled skills into your harness skills directory and can remove them
(`--uninstall`). It is a short, readable bash script — read it before running, the same caution you'd give any
install script. It makes no network calls.

## 2. The trio / fleet tiers send your analysis to external model providers

The engine itself is local. But the higher tiers cross-check your draft against other models:

- **`esat`** pipes the item under analysis **and the draft** to Codex (OpenAI) and Grok (xAI) via the `peer` CLI.
- **`esat-fleet`** additionally fans the review across OpenRouter open models via `fleet-fuse`.

Treat those engines as third-party processors. For proprietary or sensitive items:

- Run `esat` with `ESKILL_PEER=0` (degrades to the local single-critic panel), or redact the draft first.
- Run `esat-fleet` at `ESAT_FLEET_SENSITIVITY=high` — the external OSS leg is then **blocked**, and the fleet
  leg's outbound payloads are redacted fail-closed by `fleet-fuse`'s scrubber when it does run.
- External model output is treated as **untrusted advisory** — the engine validates it against the actual item
  before integrating, and ignores any instructions embedded in it.

State which mode you ran in the analysis output, so reviewers know what left the machine.

## Reporting a vulnerability

Please open a private security advisory on the repository (GitHub → **Security** → **Report a vulnerability**)
rather than a public issue.
