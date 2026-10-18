---
name: eskill-analyze
description: "World-class level-up analysis with first-principles thinking, systems mapping, and strategic frameworks. Elastic: a router runs only the modules a question needs (deepen, evidence, models, premortem, stress test, actions), and each module is callable alone. Produces prioritized action plans with project-level impact assessment. Absorbs eskill-orchestrate routing. Also known as orchestrate, eo, or the long-form native analyzer; for the short Tier-1 entry point prefer /esa."
---

# eSkill: Analyze — World-Class Level-Up Analyzer

First-principles analysis engine that finds what would make a product, feature, or system world-class, and does the least work that gets there. A router decides which modules a question needs; nothing runs by default.

## Quality Principles

Read `${CLAUDE_SKILL_DIR}/../eskill-common/references/quality-principles.md`

## Entry Points

| Invocation | Runs |
|-|-|
| `/esa <ask>` or `eskill-analyze <ask>` | The router (`references/triage-guide.md`), then the modules it picks |
| `/esa deepen <ask>` | Router Step 0; prints the four answers and the deepened ask |
| `/esa evidence <ask>` | Step 0 to name the rawest source, then Phase 0; prints the Evidence Summary and open gaps |
| `/esa premortem <plan>` | Phase P on the given plan, which is the action list; prints only the Premortem Cycle block |
| `/esa verify <draft>` | Phase 9 at this skill's tier on the given draft; prints Stress Test Notes, not a rewrite |
| Another skill's step | The one module that step names; follow that module's output contract |

An orchestrator may run router Wave 1 itself and skip this skill when the ask can be answered from context.

## Inputs

Infer Project, Focus Area, Current State, and World-Class Definition from the ask and the session. Ask only when one is missing **and** its answer would change the route.

**Scope check:**
- **Bug/incident?** Broken behavior ("isn't working", "crashed", "why did X fail") — clarify intent; route diagnosis to a debugger agent. This skill is for elevation, not incident triage.
- **Non-software?** Hiring, org structure, team process — only First Principles, Inversion, Reversibility, plus one borrowed field technique when the Range lens produces an atom. Skip system-specific modules.

## Route

Read `${CLAUDE_SKILL_DIR}/references/triage-guide.md` (the router). It atomizes the ask in three waves, selects modules, and prints one **Route** line before any spend. That line determines everything that follows.

## Modules

Defined in `${CLAUDE_SKILL_DIR}/references/analysis-protocol.md` and `${CLAUDE_SKILL_DIR}/references/mental-models.md`. Spawn only the agents a running module names; run independent modules in parallel.

| Module | Name in protocol |
|-|-|
| Evidence (raw first) | Phase 0 |
| Core analysis: first principles, models, system map, path, competition, funnel | Steps 1-8 (only the steps the route lists) |
| Instruments (Depth) and Borrow (Range) | mental-models.md rules, applied inside Step 2 |
| Premortem | Phase P |
| Stress test | Phase 9 (higher tiers replace it with their panel) |
| Compare | Comparison Mode below |
| Actions + Verifier, Project impact | Output template; `${CLAUDE_SKILL_DIR}/../eskill-common/references/project-impact-protocol.md` |

## Comparison Mode

When the router finds a real choice (atom a4): cap at 2 options (shortlist first for 3+). Per option, existing code gets explore + architect + analyst; a hypothetical option gets document-specialist + analyst. Use the Comparison template, state a winner with tradeoffs and flip conditions, and list actions for the winner only.

## World-Class Signals

Read `${CLAUDE_SKILL_DIR}/references/world-class-signals.md` when the route includes World-Class Criteria.

## Output Format

Read `${CLAUDE_SKILL_DIR}/assets/output-template.md`. Show results, not process: the Route line, then only the sections whose module ran. The four deepening answers surface inside those sections, never as their own block.

## Post-Analysis Routing

Only when the Actions module ran:

> "Which do you want to execute? All / top N / specific numbers. For an overnight sprint, say `/eskill-overnight` with the list."

Fewer than 10 confirmed tasks → `/eskill-sprint`; 10+ or "overnight" → `/eskill-overnight`. Save the analysis to `.omc/plans/analysis-{date}-{focus}.md`.

## Execution Principles

1. **Deeper, not bigger** — one layer down beats one more section.
2. **Start with why** — reconnect to first principles before proposing.
3. **Think in systems** — single features don't create world-class; ecosystems do.
4. **Assume competition copies** — make it hard to replicate.
5. **Name the flywheel** — can't describe compounding? Not ready.
