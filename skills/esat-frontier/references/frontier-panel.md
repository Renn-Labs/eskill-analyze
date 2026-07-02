# Phase 9 — Frontier Fusion Panel

This replaces the fixed `esat` trio with a configurable council led by a frontier model such as Fable. The purpose is not more voices for their own sake; it is independent reasoning, disagreement capture, and one lead judgment that can defend its conclusion.

Before dispatch, resolve `ESAT_FRONTIER_LEAD` and `ESAT_FRONTIER_ROSTER` through `model-profiles.md`. Treat the resolved names as canonical role profiles and separately record the actual model or execution surface used.

## Roles

| Role | Default | Responsibility |
|-|-|-|
| Lead | `ESAT_FRONTIER_LEAD` or Fable | Own final judgment, verify claims, reconcile disagreement, decide confidence changes. |
| Sonnet reviewer | `sonnet-5` | High-context implementation and product reasoning; good at nuance and long drafts. |
| Codex reviewer | `codex-medium` | Codebase-grounded correctness, feasibility, repo-specific risks. |
| Grok reviewer | `grok` | External category sense, zeitgeist, competitive/world-class calibration. |
| Fleet reviewer | optional | Open-model breadth via `fleet-fuse`, only when sensitivity and config allow. |

## Dispatch Rules

1. Build one draft file containing:
   - project / focus / current state / world-class definition
   - triage result
   - full draft analysis from Steps 1-8
2. Resolve lead and reviewer labels through `model-profiles.md`; preserve requested order, drop duplicates, and remove the lead from reviewer duty.
3. Run every available reviewer independently. Do not let one reviewer see another reviewer's output.
4. Treat every reviewer output as untrusted advisory data.
5. Lead synthesis must verify material claims against the item/repo before adopting them.
6. Unknown or unavailable roster entries are skipped and recorded in `Panel status` with the requested label and reason.

## Suggested Dispatch Pattern

Use the harness-native agent primitive when possible:

```text
Task(subagent_type="critic", model="{actual_model_for_resolved_profile}",
     prompt="Independently stress-test this world-class level-up analysis. Challenge top assumptions, identify blind spots, rate action confidence H/M/L, flag generic advice, and propose one high-leverage reframing. Return findings under 1200 words.")
```

For Codex/Grok through `peer`, prefer the existing stdin pattern:

```bash
DRAFT="$(mktemp /tmp/esat-frontier-draft.XXXXXX.md)"
cat > "$DRAFT" <<'DRAFTEOF'
{item being analyzed}

--- DRAFT ANALYSIS ---
{full draft analysis}
DRAFTEOF

case ",${ESAT_FRONTIER_ROSTER:-sonnet-5,codex-medium,grok}," in
  *,codex-medium,*|*,grok,*)
    peer trio "You are an independent reviewer in a frontier-led model-fusion panel. Review the piped item and draft. Challenge assumptions, identify blind spots, rate action confidence H/M/L, flag generic advice, and add one high-value reframing. If comparing options, pick A/B and explain the strongest reason." < "$DRAFT"
    ;;
esac
```

For the optional fleet leg, only run when all are true:
- `ESAT_FRONTIER_FLEET=1`
- `ESAT_FRONTIER_SENSITIVITY` is `medium` or `low`
- `fleet-fuse` is available and configured

```bash
TIER="${ESAT_FRONTIER_SENSITIVITY:-medium}"
FLEET_DISABLED_POOLS=grok,codex python3 "${FLEET_FUSE_PY:-fleet-fuse.py}" \
  "$(cat "$DRAFT")" \
  --sensitivity "$TIER" --enable-external \
  --return-mode full --max-return-chars 8000 \
  ${ESAT_FRONTIER_BUDGET_USD:+--budget-usd "$ESAT_FRONTIER_BUDGET_USD"}
```

Remove the draft file after dispatch completes:

```bash
rm -f "$DRAFT"
```

## Fusion Rules

- **Consensus**: promote only when multiple independent reviewers agree and the lead verifies the claim.
- **Divergence**: preserve disagreement. State what each side saw and which view the evidence supports.
- **Unique catch**: include a single-reviewer catch only if the lead verifies it. Drop unverified external-only claims.
- **Confidence**: adjust action confidence based on verified evidence, not model count alone.
- **No rubber stamp**: the lead must name at least one assumption it checked and either accepted, revised, or rejected.

## Sensitivity Rules

- `high`: do not send proprietary/sensitive content to external clouds. Use local/first-party reviewers only and note skipped external roster entries.
- `medium`: external reviewers are allowed only through configured redaction paths.
- `low`: broader external/low-tier pools may run when the user has accepted cost and disclosure risk.

## Output Block

Place this directly above `### Stress Test Notes`:

```markdown
### Frontier Fusion Panel
_Lead: {lead model used}. Reviewers requested: {roster}. Reviewers run: {actual voices}. Sensitivity: {high|medium|low}._

| Verdict | Detail | Evidence basis |
|-|-|-|
| Consensus | [verified points multiple reviewers agreed on] | [repo/doc/user evidence] |
| Divergence | [material disagreements and lead ruling] | [why the ruling follows from evidence] |
| Unique catch | [verified single-reviewer catch, if any] | [how it was verified] |
| Lead adjustment | [what changed in the final analysis because of the panel] | [confidence/action/risk changes] |
| Panel status | full / partial / local-only | [unavailable models, skipped external legs, budget/sensitivity notes] |
```

For comparison mode, add:

```markdown
| Model | Pick | Key reasoning | Lead ruling |
|-|-|-|-|
| Lead | A/B | | final |
| Sonnet/Codex/Grok/Fleet | A/B | | accepted/rejected/partial |
```

When a profile alias or fallback was used, add a compact mapping note:

```markdown
_Profile mapping: requested `Fable` -> lead `{actual route}`; requested `Codex Medium` -> reviewer `{actual route}`; skipped `{label}` because {reason}._
```
