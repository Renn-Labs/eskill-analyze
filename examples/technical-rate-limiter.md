# Example — `/esa` on an API rate limiter (technical / standard)

A trimmed, illustrative run of Tier 1 (`eskill-analyze`). It shows the shape of the output: a triage line, only
the relevant sections, a **Premortem Cycle** (Phase P at standard scale), and a prioritized action table — not every
framework forced into the page.

---

**Input given to the skill**

- **Project / Product:** Public REST API
- **Focus Area:** The request rate limiter (fixed-window counter in Redis)
- **Current State:** One global fixed window per API key; bursts at the window edge let through ~2× the limit; no
  per-route limits; 429s return no `Retry-After`.
- **World-Class Definition:** Smooth limiting under burst, fair across routes, and a client can always tell when
  to retry.

---

## Analysis: API rate limiter

### Triage
**Type**: technical / **Scale**: standard
**Agents**: explore, analyst, architect
**Models**: First Principles · Scalability Ceiling · Feedback Loops · Coupling/Cohesion
**Phases**: Steps 1–8 (selected) · Phase P Premortem · Phase 9 Stress Test

### First-Principles View
A rate limiter exists to protect a shared resource while being *predictable* to honest clients. A fixed window
optimizes for cheap counting, not for the actual goal (bounded load + a fair, legible contract). The edge-burst
flaw isn't a bug to patch — it's inherent to fixed windows. The core question is which algorithm makes the
contract honest, not how to shave the existing one.

### Premortem Cycle

**Bet**: We replace fixed windows with sliding windows, emit honest 429 headers, and keep Redis latency within SLO.
**Horizon**: 30d
**Headline if failed**: "Edge-burst outage week — clients still stampede without Retry-After; Redis hot keys took down API."

| # | Failure mode | Mechanism | L | I | Early signal | Owner | Mitigation / cut |
|-|-|-|-|-|-|-|-|
| 1 | Edge-burst still reaches downstream | Partial rollout leaves fixed-window shards in the path | H | H | p99 accepted RPS > limit×1.05 at window edges in canary | eng | Action #1 + shadow compare old vs new counters |
| 2 | Clients hammer retries | 429s ship without Retry-After or with wrong Reset | H | M | Retry storm metrics spike within 1h of deploy | eng | Action #2 must ship same release as algorithm change |
| 3 | Redis becomes the bottleneck | Sliding window multiplies ZSET ops under 10× load | M | H | Redis CPU >70% or p99 limiter latency >5ms in load test | eng | Action #4 before full GA; kill GA if ceiling not proven |
| 4 | Hot route starves others | Shared key budget, no route-class split | M | H | One route class >80% of limited traffic | eng | Action #3 after global honesty lands |

**Kill criteria**
1. Abort GA if canary shows accepted RPS > configured limit × 1.05 at window edges for 15 consecutive minutes.
2. Abort GA if Redis p99 for limiter ops exceeds 5ms under 10× synthetic load.
3. Hold release if 429 responses lack `Retry-After` in integration tests.

**Action deltas from premortem**
- Tied #2 to the same release as #1 (was independent).
- Made #4 a hard gate before GA (not optional polish).
- Lowered confidence on #3 until load-test evidence exists.

### Prioritized Actions
| # | Action | Impact | Effort | Confidence | Reversible | Horizon | Why |
|-|-|-|-|-|-|-|-|
| 1 | Replace fixed window with a sliding-window log/counter in Redis | H | M | H | Y | Quick | Kills the 2× edge burst — the headline defect; mitigates premortem #1 |
| 2 | Return `Retry-After` + `X-RateLimit-Limit/Remaining/Reset` on 429 **in the same release as #1** | H | L | H | Y | Quick | Makes the contract legible; blocks premortem #2 |
| 3 | Add per-route-class buckets under each key | M | M | M | Y | Foundation | Fairness across routes once global limiting is honest; mitigates #4 |
| 4 | Load-test at 10× to find the Redis round-trip ceiling **before GA** | M | M | M | Y | Foundation | Kill criterion #2; conf rises after evidence |

### World-Class Criteria
- Sustained throughput never exceeds the configured limit by more than 5%, including at window edges.
- Every 429 carries a correct `Retry-After`; a naive client that honors it never gets a second 429.
- No single route can consume more than its share of a key's budget under contention.

---

> _Higher tiers produce the same structure, plus a panel that records where the configured reviewers agreed,
> diverged, or caught something the draft missed — including attacks on premortem kill criteria — and adjusts
> the Confidence column accordingly._
