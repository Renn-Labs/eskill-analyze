# Mental Model Toolkit

Apply as relevant — NOT every analysis needs every model. Pick 3-4 max.

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

## Selection by Type

| Analysis Type | Recommended Models |
|-|-|
| Technical / codebase | First Principles + Coupling/Cohesion + Complexity Budget + Scalability Ceiling |
| Technical / performance | Scalability Ceiling + First Principles + Feedback Loops + Complexity Budget |
| Technical / DX | DX Friction Mapping + First Principles + Feedback Loops |
| Technical / security | Security Surface + Inversion + Coupling/Cohesion |
| Technical / data-observability | First Principles + Feedback Loops + Scalability Ceiling + DX Friction Mapping |
| Product / growth | JTBD + Unit Economics + 7-Step Ahead + AAARRR |
| Product / UX | JTBD + Four Levels + Feedback Loops |
| Strategic / positioning | Inversion + Feedback Loops + Unit Economics + Reversibility |
| Comparative | First Principles + Inversion + Reversibility (applied to each option) |

Two sub-types of one type (onboarding = UX + growth): merge the sets and pick 4. A strong secondary type
(strategy with gnarly integration, a feature with security exposure): add 1 model from its set.

Codebase signals pre-select: `package.json` / `tsconfig.json` → DX Friction + Coupling/Cohesion;
`Cargo.toml` → Scalability Ceiling + Coupling/Cohesion; `pyproject.toml` / `setup.py` → Complexity Budget +
DX Friction; auth/, middleware/, RBAC → Security Surface + Inversion; no codebase → no technical models.
The user's stated focus overrides.

## Depth: Instruments Over Vocabulary

A model name is a question, not a method. Under the Depth lens, when a field instrument answers the same
question as a selected model, use it and name it: Scalability Ceiling → a load test with a stated load
profile; Unit Economics → cohort LTV/CAC from raw billing records; Inversion → a fault tree over the real
call graph. The model stays selected; the instrument does the work.

## Range: Borrow One Field

Under the Range lens, rewrite the deliverable's nouns as verbs ("a pricing page" → price, persuade, test),
find the field that does each verb best, and borrow one concrete technique from outside the task's own
field (queueing theory for a support backlog, survival analysis for churn, red-team drills for a launch
plan). Apply it and show what it changed. Do what that field's practitioners do; do not role-play them.
