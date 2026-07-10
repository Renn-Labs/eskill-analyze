# Frontier Model Profile Contract

Use these profiles to keep `esat-frontier` portable across harnesses. A profile is a stable role label for this skill, not a promise that every machine exposes the same provider model ID.

Load `${CLAUDE_SKILL_DIR}/../eskill-common/references/model-routing.md` for precedence, policy, manifest, and harness mappings. This file defines profile aliases and preferred execution surfaces only.

## Resolution Rules

1. Normalize labels by trimming whitespace, lowercasing, and replacing spaces/underscores with hyphens.
2. Resolve aliases to the canonical profile table below **before** dispatch.
3. Preserve roster order after resolution.
4. Drop duplicate profiles after the first planned occurrence (pre-dispatch fingerprint suppression) and note duplicates in the plan/results.
5. Keep the lead out of the reviewer roster. If the resolved lead also appears as a reviewer, keep it as lead and drop it from reviewers with a note.
6. Skip unknown labels; never infer a provider ID from an unknown label.
7. A skipped or unavailable profile does not fail the analysis. Record a terminal result (`observed_route: null` when never dispatched) and report `partial` or `local-only` panel status after all lanes have results.
8. **Explicit exact-model pins are strict.** If the pin is unavailable, fail/skip that lane with an explicit reason — never silently substitute another model.
9. **Automatic defaults** may fall back only with both requested and actual disclosed.
10. Disclose **actual model or account default**; never print a guessed fixed provider version in panel templates.

## Canonical Profiles

| Canonical profile | Accepted aliases | Default responsibility | Preferred execution surface | Fallback |
|-|-|-|-|-|
| `fable` | `fable-frontier`, `frontier`, `lead-frontier` | Lead judge: owns synthesis, verifies claims, reconciles disagreement. | Harness-native frontier lead model when exposed. | Strongest available frontier model, then current session leader with fallback noted. |
| `sonnet-5` | `sonnet`, `claude-sonnet-5`, `claude-sonnet`, `sonnet5` | High-context reviewer for product nuance, implementation judgment, and long-draft critique. | Harness-native reviewer/subagent with a Sonnet-class model when advertised. | Harness-native critic without a model override; otherwise skip. |
| `codex-medium` | `codex`, `codex-med`, `codex-medium-reviewer`, `openai-codex` | Codebase-grounded reviewer for correctness, feasibility, repo risk, and implementation sequencing. | Codex native subagent, Codex CLI, or **`peer codex`** (independent lane). | Skip if no Codex-capable independent context is available. |
| `grok` | `grok-build`, `xai-grok`, `grok-reviewer` | External calibration reviewer for category sense, competitive framing, and contrarian blind spots. | **`peer grok`** or harness-native Grok connector (independent lane). | Skip when unavailable or when sensitivity disallows the external route. |
| `fleet` | `oss-fleet`, `openrouter-fleet`, `swarm` | Optional breadth reviewer across open-model voices. | `fleet-fuse` through `ESAT_FRONTIER_FLEET=1` or explicit roster entry, only after consent/policy gates. | Skip unless sensitivity, redaction, permission, budget, and metered consent allow it. |

## Lead Selection

Default to `ESAT_FRONTIER_LEAD=fable`. If `fable` is unavailable, select the strongest available frontier profile in this order:

1. A harness-declared frontier lead/profile.
2. `sonnet-5` when it is the strongest available high-context model.
3. The current in-session leader when no separate frontier model can be routed.

Do not promote `codex-medium`, `grok`, or `fleet` to lead unless the local harness explicitly marks that profile as a frontier lead. Their default role is reviewer evidence, not final judgment.

Preserve the **current host model as host**. Managed reviewer roles resolve independently.

## Independent peer lanes (not `peer trio`)

| Profile | Peer command when using peer | Must not use |
|-|-|-|
| `codex-medium` only | `peer codex` | `peer trio`, `peer grok` |
| `grok` only | `peer grok` | `peer trio`, `peer codex` |
| both | `peer codex` and `peer grok` as **separate** dispatches | roster-driven `peer trio` |

Selecting either Codex or Grok alone must not over-dispatch the other lane.

## Sensitivity

| Sensitivity | Allowed profile routes |
|-|-|
| `high` | Local/first-party harness routes only. Schedule **zero** external `peer`, Grok cloud, and fleet/OpenRouter routes unless the harness explicitly marks them first-party for this environment. |
| `medium` | First-party routes plus external reviewers **only** through an identified redaction path. Without a redactor, block external lanes. |
| `low` | Broader external reviewers and low-tier pools are allowed when the user has accepted cost and disclosure risk. |
| invalid | Fail closed for external routes (`invalid-sensitivity`). |

Strongest restriction wins across multiple policy scopes. Denied external-route permission blocks external dispatch.

## Dispatch Disclosure

Record both the requested profile and actual execution surface in the two-stage manifest:

```markdown
| Profile | Requested as | Preference source | Actual route/model | Status | Independent |
|-|-|-|-|-|-|
| fable | ESAT_FRONTIER_LEAD=fable | legacy-environment | {actual lead or fallback} | lead / fallback | n/a |
| sonnet-5 | sonnet-5 | portable-default | {actual route} | ran / skipped | yes/no |
| codex-medium | codex-medium | … | {peer codex / native / null} | ran / skipped / blocked | yes/no |
| grok | grok | … | {peer grok / native / null} | ran / skipped / blocked | yes/no |
```

Use this table as supporting detail in `Panel status` when the mapping is non-obvious, partial, or degraded. Blocked/skipped pre-dispatch lanes use `observed_route: null`.
