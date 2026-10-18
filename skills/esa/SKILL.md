---
name: esa
description: "Short Tier-1 entry point for the original eskill-analyze native world-class analysis engine. Use for /esa, $esa, ESA, e-skill analyze, or when the user wants the single in-session analyzer without esat, esat-fleet, esat-frontier, peer, Grok, fleet, Fable, or multi-model fusion."
---

# ESA — Native eSkill Analyze

Use this as the short callable wrapper for the original `eskill-analyze` engine.

Run `${CLAUDE_SKILL_DIR}/../eskill-analyze/SKILL.md` exactly as written.

That engine's router runs **Phase P (Premortem Cycle)** whenever it finds a decision that is
expensive to undo or premortem keywords, and always at `deep`. Phase P is not optional then.
Module entry points (`/esa deepen`, `evidence`, `premortem`, `verify`) run one module alone.

## Boundary

- Do not run the `esat`, `esat-fleet`, or `esat-frontier` panel.
- Do not call `peer`, Grok, Fable, OpenRouter, or `fleet-fuse`.
- Use only the current harness/session plus whatever local subagents the base `eskill-analyze` router activates.
- Save output using the base `eskill-analyze` output rule: `.omc/plans/analysis-{date}-{focus}.md`.
