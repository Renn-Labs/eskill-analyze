# Mental Model Toolkit

Apply as relevant — NOT every analysis needs every model.

| Model | Question It Answers |
|-|-|
| **First Principles** | What's fundamentally true? Strip everything away. |
| **Jobs-to-be-Done** | What job is the user hiring this for? |
| **Inversion** | What would guarantee failure? Avoid that. (Seeds **Phase P Premortem**; full cycle is not this model alone.) |
| **7-Step Ahead** | What happens at each stage of the causal chain? |
| **Feedback Loops** | What compounds? What decays? What's the flywheel? |
| **Unit Economics** | CAC, LTV, payback — does this math work? |
| **Four Levels** | Functional, emotional, social, life — which matters? |
| **Reversibility** | Can we reverse this decision easily? Move fast if yes. |

### Technical Models

| Model | Question It Answers |
|-|-|
| **Coupling/Cohesion** | How entangled are components? What breaks when one thing changes? |
| **DX Friction Mapping** | Where do developers lose time, context, or motivation? |
| **Complexity Budget** | Is complexity spent on user value or accidental? What can be eliminated? |
| **Scalability Ceiling** | What breaks first at 10x scale? Where are the bottlenecks? |
| **Security Surface** | What's exposed? What's the blast radius of a breach? |

## Selection Guide

- Codebase / architecture: Coupling/Cohesion + Complexity Budget + Scalability Ceiling
- Developer experience: DX Friction Mapping + First Principles + Feedback Loops
- Security review: Security Surface + Inversion + Coupling/Cohesion
- Technical feature: First Principles + Inversion + Feedback Loops
- Product/growth question: JTBD + Unit Economics + 7-Step Ahead
- Competitive positioning: Inversion + Four Levels + Reversibility
- Comparative analysis: First Principles + Inversion + Reversibility (per option)

## Depth: Instruments Over Vocabulary

A model name is a question, not a method. Under the Depth lens, when a field instrument answers the same
question as a selected model, use it and name it: Scalability Ceiling → a load test with a stated load
profile; Unit Economics → cohort LTV/CAC from raw billing records; Inversion → a fault tree over the real
call graph. The model stays selected; the instrument does the work.

## Range: Borrow One Field

Under the Range lens, rewrite the deliverable's nouns as verbs ("a pricing page" → price, persuade, test),
find the field that does each verb best, and borrow one concrete technique from outside the task's own
field (queueing theory for a support backlog, survival analysis for churn, red-team drills for a launch
plan). Name the field, the technique, and what it changed in the analysis. Do what that field's
practitioners do; do not role-play them.

## Auto-Selection

Detect project type from codebase signals and pre-select the relevant category:
- `package.json` / `tsconfig.json` → JS/TS project → DX Friction + Coupling/Cohesion
- `Cargo.toml` → Rust → Scalability Ceiling + Coupling/Cohesion
- `pyproject.toml` / `setup.py` → Python → Complexity Budget + DX Friction
- Security-related files (auth/, middleware/, RBAC) → Security Surface + Inversion
- No codebase (pure strategy) → skip technical models entirely

Override with user-specified focus area.
