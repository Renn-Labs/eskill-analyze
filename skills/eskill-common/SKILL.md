---
name: eskill-common
description: "Shared non-invocable references for the eskill suite: anti-slop rules, quality principles, project-impact protocol, and Phase-9 harness-aware model routing (semantic role vs requested vs actual route, preference precedence, policy gates, two-stage manifest). Not a user-callable skill — execution and analysis skills compose these references. Triggers are none; do not invoke as a slash command."
---

# eskill-common — Shared Execution Principles

Non-invocable shared principles and contracts. Analysis and execution skills compose these references; this skill is **not user-invocable** and has no slash entry point.

## References

| Reference | Purpose |
|-|-|
| anti-slop-rules.md | 10 non-negotiable rules for execution quality |
| quality-principles.md | Analysis quality principles (selective, actionable, fewer) |
| project-impact-protocol.md | How execution skills evaluate and log project-level impact |
| model-routing.md | Phase-9 shared routing/manifest contract (roles, precedence, policy, consent, two-stage plan/results, deduplication) |

Higher tiers (`esat-fleet`, `esat-frontier`) load `model-routing.md` before Phase-9 dispatch. Tier 2 (`esat`) remains a fixed trio product and does not become configurable through this reference.
