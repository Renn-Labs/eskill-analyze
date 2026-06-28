---
name: eskill-analyze
aliases: [orchestrate, eo, esa]
description: "World-class level-up analysis with first-principles thinking, systems mapping, and strategic frameworks. Produces prioritized action plans with project-level impact assessment. Absorbs eskill-orchestrate routing."
---

# eSkill: Analyze — World-Class Level-Up Analyzer

First-principles analysis engine that identifies what elevates any product, feature, or system to world-class status. Produces a prioritized action plan ready for sprint execution.

## Quality Principles

Read `~/.claude/skills/eskill-common/references/quality-principles.md`

## Input Parameters

Extract at start. If any are missing, ask before proceeding.

**Scope check:**
- **Bug/incident?** If the prompt describes broken behavior ("isn't working", "broke", "crashed", "dropped", "why did X fail") — clarify intent. If the user wants diagnosis, route to a debugger agent. eskill-analyze is for elevation, not incident triage.
- **Non-software?** If the prompt is about hiring, org structure, team process, or other non-product/non-system topics — only First Principles, Inversion, and Reversibility models apply. Skip all system-specific steps (System Mapping, AAARRR, 7-Step Path, Competitive Analysis). Keep the analysis lightweight and framework-driven rather than forcing product/technical structure onto people or process decisions.

| Parameter | Description | Required |
|-|-|-|
| **Project/Product** | What are we analyzing? | Yes |
| **Focus Area** | Specific aspect to deep-dive | Yes |
| **Current State** | What exists, what's built, what's broken | Yes |
| **World-Class Definition** | What does "done" look like? | Yes |
| **Constraints** | Timeline, resources, team size | No |

## Triage (After Parameters Confirmed)

Read `${CLAUDE_SKILL_DIR}/references/triage-guide.md`

**Gate:** Do not triage until the required Input Parameters above are extracted or confirmed. If the prompt is too vague to determine Project, Focus Area, Current State, or World-Class Definition — ask first. Triage with missing context wastes agent dispatches on the wrong problem.

Classify the prompt:
1. **Type**: technical / product / strategic / comparative
2. **Scale**: quick / standard / deep
3. **Agents**: which of the 6 agents to activate
4. **Models**: which 3-4 mental models to apply
5. **Phases**: which phases are active (Phase 0, Steps 1-8, Phase 9)

State the triage result before proceeding. This determines everything that follows.

## Delegation Strategy

Spawn only the agents triage activates. All eligible agents run in parallel.

### Always Active
```
Task(subagent_type="oh-my-claudecode:analyst", model="opus",
     prompt="Analyze requirements and hidden constraints for: {focus_area}.
     Final response under 2000 characters. List findings, not process.")

Task(subagent_type="oh-my-claudecode:explore", model="sonnet",
     prompt="Map existing codebase structure relevant to: {focus_area}.
     Final response under 2000 characters. List findings, not process.")
```

### Activated by Triage
```
# Technical analysis
Task(subagent_type="oh-my-claudecode:architect", model="opus",
     prompt="Map system boundaries, interfaces, and long-term tradeoffs for: {focus_area}.
     Final response under 2000 characters.")

# Product or strategic analysis
Task(subagent_type="oh-my-claudecode:document-specialist", model="sonnet",
     prompt="Research world-class benchmarks and best practices for: {domain}/{focus_area}.
     Final response under 2000 characters.")

# When quantitative data exists
Task(subagent_type="oh-my-claudecode:scientist", model="sonnet",
     prompt="Analyze available metrics, logs, usage data for: {focus_area}.
     Final response under 2000 characters.")

# When security keywords detected
Task(subagent_type="oh-my-claudecode:security-reviewer", model="sonnet",
     prompt="Assess security surface, threat model, and blast radius for: {focus_area}.
     Final response under 2000 characters.")
```

Run all activated agents in parallel. Synthesize their outputs before proceeding to analysis.

## Framework Selection

NOT every analysis needs every framework. After triage:

1. Read `${CLAUDE_SKILL_DIR}/references/mental-models.md`
2. Use the auto-selection logic based on triage type
3. Pick 3-4 frameworks max from the recommended set
4. Skip the rest — do not generate empty or forced sections

## Analysis Protocol

Read `${CLAUDE_SKILL_DIR}/references/analysis-protocol.md`

Execute in order:
1. **Phase 0: Evidence Gathering** — if triage activated it, run the evidence agents and synthesize
2. **Steps 1-8: Core Analysis** — apply only selected frameworks, skip irrelevant steps entirely
3. **Phase 9: Stress Test** — if triage activated it (standard/deep scale), run the critic agent and integrate feedback

## Comparison Mode

When triage classifies as `comparative`:

1. Cap at 2 options. For 3+, shortlist to 2 finalists first with a quick-triage pass
2. Run triage + delegation for each option, but adapt per option:
   - **Existing option** (code exists): run explore + architect + analyst
   - **Hypothetical option** (no codebase): run document-specialist + analyst (skip explore)
3. Use the Comparison Mode template from `${CLAUDE_SKILL_DIR}/assets/output-template.md`
4. Produce a side-by-side table across key dimensions
5. State a clear recommendation with tradeoffs and conditions to reconsider
6. Generate prioritized actions for the recommended option only

## World-Class Signals

Read `${CLAUDE_SKILL_DIR}/references/world-class-signals.md`

## Project-Level Impact

Read `~/.claude/skills/eskill-common/references/project-impact-protocol.md`

If `{project}/.omc/project-context.json` and `{project}/.omc/business-context.md` exist, connect every recommended action to project priorities and business impact in the output.

## Output Format

Read `${CLAUDE_SKILL_DIR}/assets/output-template.md`

Present the analysis using the appropriate template variant:
- **Standard template**: for technical/product/strategic analyses
- **Comparison template**: for comparative analyses

Include only the sections that are relevant:
- Triage header: always
- Evidence Summary: only when Phase 0 ran
- Stress Test Notes: only when Phase 9 surfaced material changes
- Confidence column: only when stress test ran
- Mermaid diagrams: only when system relationships are complex (3+ components)

## Post-Analysis Routing

After presenting the prioritized action list:

> "Here are the prioritized actions. Which do you want to execute?
> - All of them
> - Top N (specify)
> - Specific items (list numbers)
>
> Want to run this as an overnight sprint? Say `/eskill-overnight` with the confirmed list."

**Auto-routing:**
- < 10 tasks confirmed → invoke `/eskill-sprint`
- 10+ tasks confirmed → invoke `/eskill-overnight`
- User says "overnight" → always `/eskill-overnight`

Save the analysis output to `.omc/plans/analysis-{date}-{focus}.md` for reference during execution.

## Execution Principles

1. **Never accept "good enough"** — Ask "what would world-class look like?"
2. **Start with why** — Reconnect to first principles before proposing
3. **Think in systems** — Single features don't create world-class; ecosystems do
4. **Assume competition copies** — Make it hard to replicate
5. **Name the flywheel** — Can't describe compounding? Not ready.
