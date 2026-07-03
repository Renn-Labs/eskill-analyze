---
name: Feature request
about: Suggest an improvement to eskill-analyze
title: "[feat] "
labels: enhancement
---

**The problem**
What's missing or painful? Lead with the problem, not the solution.

**Which area**
- [ ] Triage / framework selection
- [ ] A mental model or analysis step
- [ ] Phase 9 (single critic / trio / fleet / frontier fusion)
- [ ] Output template / comparison mode
- [ ] Install / portability / a specific harness

**Proposed approach** (optional)

**Invariant check**
eskill-analyze keeps a few hard invariants — does the idea hold them?
- [ ] **Selective, not exhaustive** — it can change a recommendation, not just add a section
- [ ] Tiers stay supersets: `esa` wraps `eskill-analyze`; `esat` reuses `eskill-analyze` verbatim; `esat-fleet` reuses `esat` verbatim; `esat-frontier` reuses the engine and only replaces Phase 9
- [ ] No new hard dependency; tiers degrade gracefully when `peer` / `fleet-fuse` / sub-agents are absent
- [ ] External model output stays untrusted advisory (maker ≠ checker)
