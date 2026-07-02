# Example — `/esa` on an API rate limiter (technical / standard)

A trimmed, illustrative run of Tier 1 (`eskill-analyze`). It shows the shape of the output: a triage line, only
the relevant sections, and a prioritized action table — not every framework forced into the page.

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

### First-Principles View
A rate limiter exists to protect a shared resource while being *predictable* to honest clients. A fixed window
optimizes for cheap counting, not for the actual goal (bounded load + a fair, legible contract). The edge-burst
flaw isn't a bug to patch — it's inherent to fixed windows. The core question is which algorithm makes the
contract honest, not how to shave the existing one.

### Failure Modes (Pre-Mortem)
| Risk | Likelihood | Impact | Prevention |
|-|-|-|-|
| Edge bursts overwhelm a downstream at 2× limit | High | High | Sliding-window or token bucket; the window edge stops being special |
| One hot route starves others under a shared key budget | Med | High | Per-route buckets keyed `(key, route-class)` |
| Clients hammer retries with no backoff signal | High | Med | Emit `Retry-After` + `X-RateLimit-*` headers |

### Prioritized Actions
| # | Action | Impact | Effort | Confidence | Reversible | Horizon | Why |
|-|-|-|-|-|-|-|-|
| 1 | Replace fixed window with a sliding-window log/counter in Redis | H | M | H | Y | Quick | Kills the 2× edge burst — the headline defect |
| 2 | Return `Retry-After` + `X-RateLimit-Limit/Remaining/Reset` on 429 | H | L | H | Y | Quick | Makes the contract legible; biggest client-side win per hour spent |
| 3 | Add per-route-class buckets under each key | M | M | M | Y | Foundation | Fairness across routes once global limiting is honest |
| 4 | Load-test at 10× to find the Redis round-trip ceiling | M | M | M | Y | Foundation | Confirms the algorithm holds before it's the bottleneck |

### World-Class Criteria
- Sustained throughput never exceeds the configured limit by more than 5%, including at window edges.
- Every 429 carries a correct `Retry-After`; a naive client that honors it never gets a second 429.
- No single route can consume more than its share of a key's budget under contention.

---

> _Higher tiers produce the same structure, plus a panel that records where the configured reviewers agreed,
> diverged, or caught something the draft missed — and adjusts the Confidence column accordingly._
