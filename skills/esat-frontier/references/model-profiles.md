# Frontier Model Profile Contract

Use these profiles to keep `esat-frontier` portable across harnesses. A profile is a stable role label for this skill, not a promise that every machine exposes the same provider model ID. If the local harness uses different IDs, map the profile to the closest available model and disclose the actual model used in `Panel status`.

## Resolution Rules

1. Normalize labels by trimming whitespace, lowercasing, and replacing spaces/underscores with hyphens.
2. Resolve aliases to the canonical profile table below.
3. Preserve roster order after resolution.
4. Drop duplicate profiles after the first occurrence and note duplicates in `Panel status`.
5. Keep the lead out of the reviewer roster. If the resolved lead also appears as a reviewer, keep it as lead and drop it from reviewers with a note.
6. Skip unknown labels; never infer a provider ID from an unknown label.
7. A skipped or unavailable profile does not fail the analysis. Report `partial` or `local-only` panel status and continue with the remaining independent reviewers.

## Canonical Profiles

| Canonical profile | Accepted aliases | Default responsibility | Preferred execution surface | Fallback |
|-|-|-|-|-|
| `fable` | `fable-frontier`, `frontier`, `lead-frontier` | Lead judge: owns synthesis, verifies claims, reconciles disagreement. | Harness-native frontier lead model when exposed. | Strongest available frontier model, then current session leader with fallback noted. |
| `sonnet-5` | `sonnet`, `claude-sonnet-5`, `claude-sonnet`, `sonnet5` | High-context reviewer for product nuance, implementation judgment, and long-draft critique. | Harness-native reviewer/subagent with a Sonnet 5-equivalent model. | Harness-native critic without a model override; otherwise skip. |
| `codex-medium` | `codex`, `codex-med`, `codex-medium-reviewer`, `openai-codex` | Codebase-grounded reviewer for correctness, feasibility, repo risk, and implementation sequencing. | Codex native subagent, Codex CLI, or `peer` Codex lane. | Skip if no Codex-capable independent context is available. |
| `grok` | `grok-build`, `xai-grok`, `grok-reviewer` | External calibration reviewer for category sense, competitive framing, and contrarian blind spots. | `peer` Grok lane or harness-native Grok connector. | Skip when unavailable or when sensitivity disallows the external route. |
| `fleet` | `oss-fleet`, `openrouter-fleet`, `swarm` | Optional breadth reviewer across open-model voices. | `fleet-fuse` through `ESAT_FRONTIER_FLEET=1` or explicit roster entry. | Skip unless sensitivity and budget gates allow it. |

## Lead Selection

Default to `ESAT_FRONTIER_LEAD=fable`. If `fable` is unavailable, select the strongest available frontier profile in this order:

1. A harness-declared frontier lead/profile.
2. `sonnet-5` when it is the strongest available high-context model.
3. The current in-session leader when no separate frontier model can be routed.

Do not promote `codex-medium`, `grok`, or `fleet` to lead unless the local harness explicitly marks that profile as a frontier lead. Their default role is reviewer evidence, not final judgment.

## Sensitivity Gates

| Sensitivity | Allowed profile routes |
|-|-|
| `high` | Local/first-party harness routes only. Skip external `peer`, Grok cloud, and fleet/OpenRouter routes unless the harness explicitly marks them first-party for this environment. |
| `medium` | First-party routes plus redacted external reviewers. Use configured redaction before `peer`, Grok, or fleet/OpenRouter calls. |
| `low` | Broader external reviewers and low-tier pools are allowed when the user has accepted cost and disclosure risk. |

## Dispatch Disclosure

Record both the requested profile and actual execution surface:

```markdown
| Profile | Requested as | Actual route/model | Status |
|-|-|-|-|
| fable | ESAT_FRONTIER_LEAD=fable | {actual lead or fallback} | lead / fallback |
| sonnet-5 | sonnet-5 | {actual route} | ran / skipped |
| codex-medium | codex-medium | {actual route} | ran / skipped |
| grok | grok | {actual route} | ran / skipped |
```

Use this table as supporting detail in `Panel status` when the mapping is non-obvious, partial, or degraded.
