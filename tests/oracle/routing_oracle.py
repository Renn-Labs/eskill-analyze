"""Contract-level routing oracle for Phase-9 harness-aware model routing.

This evaluates the *documented* preference/policy algebra from
``skills/eskill-common/references/model-routing.md``.

It is **executable contract evidence**, not live harness conformance proof.
Stdlib only.
"""
from __future__ import annotations

import math
from typing import Any

PRECEDENCE = (
    "explicit-invocation",
    "session",
    "project",
    "user",
    "legacy-environment",
    "harness",
    "portable-default",
)

# Stronger restrictions first for sensitivity intersection.
SENSITIVITY_RANK = {
    "high": 3,
    "medium": 2,
    "low": 1,
}

VALID_CONSENT_SOURCES = frozenset({"current-invocation", "current-run-interactive"})
REJECTED_CONSENT = {
    "environment": "consent-env-rejected",
    "config": "consent-config-rejected",
    "project-config": "consent-config-rejected",
    "user-config": "consent-config-rejected",
    "inherited-shell": "consent-inherited-shell-rejected",
    "expired": "consent-expired",
    "prior-run": "consent-prior-run-rejected",
    "absent": "metered-consent-missing",
    None: "metered-consent-missing",
}

EXTERNAL_LANES = frozenset({"fleet", "peer-codex", "peer-grok", "peer-external"})

# Semantic defaults when fixtures omit lane specs. Fingerprints still prefer
# explicit provider + model/profile + route_class + context_class identity.
LANE_DEFAULTS: dict[str, dict[str, Any]] = {
    "critic": {
        "role": "critic",
        "requested_provider": "native",
        "requested_model": "critic",
        "route_class": "first-party",
        "context_class": "local",
    },
    "fleet": {
        "role": "fleet-breadth",
        "requested_provider": "openrouter",
        "requested_model": "oss-swarm",
        "route_class": "external",
        "context_class": "fleet-fuse",
    },
    "peer-codex": {
        "role": "code-reviewer",
        "requested_provider": "codex",
        "requested_model": "codex-default",
        "route_class": "external",
        "context_class": "peer",
    },
    "peer-grok": {
        "role": "calibration",
        "requested_provider": "grok",
        "requested_model": "grok-default",
        "route_class": "external",
        "context_class": "peer",
    },
    "peer-external": {
        "role": "external-reviewer",
        "requested_provider": "external",
        "requested_model": "external-default",
        "route_class": "external",
        "context_class": "peer",
    },
    "codex-medium": {
        "role": "code-reviewer",
        "requested_provider": "codex",
        "requested_model": "codex-medium",
        "route_class": "external",
        "context_class": "peer",
    },
    "grok": {
        "role": "calibration",
        "requested_provider": "grok",
        "requested_model": "grok",
        "route_class": "external",
        "context_class": "peer",
    },
}


def resolve_harness(harness: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve harness identity: explicit/host outrank CLI presence."""
    harness = harness or {}
    explicit = harness.get("explicit")
    host = harness.get("host")
    available = list(harness.get("available_clis") or [])

    if explicit:
        identity = explicit
        source = "explicit"
    elif host:
        identity = host
        source = "host-declared"
    else:
        # Absent/unknown identity reports generic; never infer from available_clis.
        identity = "generic"
        source = "unknown"

    # Explicit/host known identities win; unknown declared names fall through
    # to the mappings default below (still generic profile, not CLI-inferred).
    if identity not in ("claude", "codex", "grok") and source == "unknown":
        identity = "generic"

    mappings = {
        "claude": {
            "native_subagents": True,
            "host_hot_swap": False,
            "pin_only_if_advertised": True,
            "routes": ["native-subagent"],
        },
        "codex": {
            "native_subagents": True,
            "host_hot_swap": False,
            "account_default_ok_without_pin": True,
            "routes": ["native-child", "codex-cli", "peer-codex"],
        },
        "grok": {
            "native_subagents": True,
            "host_hot_swap": False,
            "exact_pin_requires_listing": True,
            "routes": ["native", "grok-cli", "peer-grok"],
        },
        "generic": {
            "native_subagents": False,
            "host_hot_swap": False,
            "retain_session_leader": True,
            "routes": [],  # only discovered external routes
        },
    }
    profile = mappings.get(identity, mappings["generic"])
    if identity not in mappings:
        identity = "generic"
        profile = mappings["generic"]
        if source == "unknown":
            source = "unknown"

    return {
        "identity": identity,
        "identity_source": source,
        "available_clis": available,
        "profile": profile,
    }


def resolve_preference(
    preference_sources: list[dict[str, Any]], key: str
) -> dict[str, Any] | None:
    """Pick highest-precedence preference for *key*.

    Accepts either:

    - Direct key on the entry: ``{"source": "...", "model": "x"}`` when
      *key* is ``"model"``.
    - Structured form: ``{"source": "...", "key": "model", "value": "x"}`` —
      accepted **only** when ``item["key"]`` exactly equals the requested key.

    A higher-precedence entry for a *different* key must not steal resolution
    for the requested key.
    """
    best = None
    best_rank = len(PRECEDENCE) + 1
    for item in preference_sources or []:
        src = item.get("source")
        if src not in PRECEDENCE:
            continue

        if key in item:
            value = item[key]
        elif "value" in item:
            # Structured {source, key, value}: exact key match required.
            if item.get("key") != key:
                continue
            value = item.get("value")
        else:
            continue

        rank = PRECEDENCE.index(src)
        if rank < best_rank:
            best_rank = rank
            best = {"source": src, "value": value, "key": key}
    return best


def intersect_sensitivity(scopes: list[str] | None) -> tuple[str | None, str | None]:
    """Strongest restriction wins. Returns (tier, error_reason)."""
    scopes = list(scopes or [])
    if not scopes:
        return "medium", None
    rank = -1
    chosen = None
    for s in scopes:
        if s not in SENSITIVITY_RANK:
            return None, "invalid-sensitivity"
        if SENSITIVITY_RANK[s] > rank:
            rank = SENSITIVITY_RANK[s]
            chosen = s
    return chosen, None


def evaluate_consent(metered_consent: dict[str, Any] | None) -> dict[str, Any]:
    mc = metered_consent or {"source": "absent", "status": "missing"}
    source = mc.get("source")
    status = mc.get("status")

    if source in VALID_CONSENT_SOURCES and status == "valid":
        return {"accepted": True, "class": source, "reason": None}

    if status == "expired" or source == "expired":
        return {"accepted": False, "class": "consent-expired", "reason": "consent-expired"}

    if source in REJECTED_CONSENT:
        reason = REJECTED_CONSENT[source]
        return {"accepted": False, "class": reason, "reason": reason}

    if status in ("missing", "invalid", None) or source in (None, "absent"):
        return {
            "accepted": False,
            "class": "metered-consent-missing",
            "reason": "metered-consent-missing",
        }

    return {
        "accepted": False,
        "class": "metered-consent-missing",
        "reason": "metered-consent-missing",
    }


def evaluate_budget(budget_usd: Any) -> dict[str, Any]:
    """Validate optional budget cap.

    Absent means only JSON null / truly unset (``None``). Empty string,
    whitespace, NaN, Infinity, non-numeric, zero, and negative are invalid.
    """
    if budget_usd is None:
        return {
            "ok": True,
            "cap": None,
            "disclosure": "provider/account cap only",
            "reason": None,
        }
    if isinstance(budget_usd, bool):
        # Reject bools: they are not numeric budget caps (bool is a int subclass).
        return {
            "ok": False,
            "cap": None,
            "disclosure": None,
            "reason": "invalid-budget",
        }
    if isinstance(budget_usd, str):
        if budget_usd.strip() == "":
            return {
                "ok": False,
                "cap": None,
                "disclosure": None,
                "reason": "invalid-budget",
            }
    try:
        val = float(budget_usd)
    except (TypeError, ValueError):
        return {
            "ok": False,
            "cap": None,
            "disclosure": None,
            "reason": "invalid-budget",
        }
    if not math.isfinite(val) or val <= 0:
        return {
            "ok": False,
            "cap": None,
            "disclosure": None,
            "reason": "invalid-budget",
        }
    return {
        "ok": True,
        "cap": val,
        "disclosure": f"budget-usd={val}",
        "reason": None,
    }


def evaluate_external_route_permission(permission: Any) -> dict[str, Any]:
    """Accept only allow/deny; any other value fails closed for external lanes."""
    if permission == "allow":
        return {"ok": True, "value": "allow", "reason": None}
    if permission == "deny":
        return {"ok": True, "value": "deny", "reason": None}
    return {
        "ok": False,
        "value": permission,
        "reason": "invalid-external-route-permission",
    }


def _default_route_class(lane: str) -> str:
    defaults = LANE_DEFAULTS.get(lane)
    if defaults:
        return str(defaults["route_class"])
    if lane in EXTERNAL_LANES or str(lane).startswith("peer") or lane == "fleet":
        return "external"
    return "first-party"


def _default_context_class(lane: str) -> str:
    defaults = LANE_DEFAULTS.get(lane)
    if defaults:
        return str(defaults["context_class"])
    if lane == "fleet" or str(lane).endswith("-fleet"):
        return "fleet-fuse"
    if lane in EXTERNAL_LANES or str(lane).startswith("peer"):
        return "peer"
    return "local"


def _default_provider(lane: str) -> str:
    defaults = LANE_DEFAULTS.get(lane)
    if defaults:
        return str(defaults["requested_provider"])
    if lane.startswith("peer-"):
        return lane[len("peer-") :]
    return lane


def _default_model(lane: str) -> str:
    defaults = LANE_DEFAULTS.get(lane)
    if defaults:
        return str(defaults["requested_model"])
    return lane


def _default_role(lane: str) -> str:
    defaults = LANE_DEFAULTS.get(lane)
    if defaults:
        return str(defaults["role"])
    return lane


def planned_route_fingerprint(
    *,
    provider: str,
    requested_model: str,
    route_class: str,
    context_class: str,
) -> str:
    """Stable identity: provider + model/profile + route class + context class.

    Same-provider / different-model lanes must not collide.
    """
    return f"{provider}|{requested_model}|{route_class}|{context_class}"


def _lane_is_external(lane: str, route_class: str | None = None) -> bool:
    """External derivation prefers explicit route_class."""
    if route_class == "external":
        return True
    if route_class == "first-party":
        return False
    if route_class == "ambiguous":
        return True  # treat as needing external gates
    return lane in EXTERNAL_LANES or lane.startswith("peer-") or lane == "fleet"


def _result_is_external(result: dict[str, Any]) -> bool:
    """Derive external/local from explicit route_class on the result record."""
    rc = result.get("route_class")
    if rc in ("external", "first-party", "ambiguous"):
        return _lane_is_external(result.get("lane", ""), rc)
    return _lane_is_external(result.get("lane", ""), None)


def _effective_redaction_gate(
    lane: str,
    *,
    route_class: str | None,
    context_class: str | None,
) -> str:
    """Lane-specific redaction path after route_class / identity is known.

    - fleet / fleet-fuse → FleetFuse scrubber
    - other external → IDENTIFIED_REDACTION_PATH (peer path)
    - first-party / local → not applicable
    """
    rc = route_class or _default_route_class(lane)
    cc = context_class or _default_context_class(lane)
    if lane == "fleet" or str(lane).endswith("-fleet") or cc == "fleet-fuse":
        return "fleet-scrub"
    if _lane_is_external(lane, rc):
        return "identified-redaction-path"
    return "n/a"


def _policy_snapshot(
    *,
    sensitivity: str | None,
    sensitivity_error: str | None,
    external_route_permission: str,
    consent: dict[str, Any],
    budget: dict[str, Any],
    peer_redactor_available: bool,
    fleet_scrubber_available: bool,
    effective_redaction_gate: str,
    effective_redaction_available: bool,
) -> dict[str, Any]:
    """Self-sufficient per-lane policy snapshot (no shared opaque policy object)."""
    return {
        "sensitivity": sensitivity,
        "sensitivity_error": sensitivity_error,
        "external_route_permission": external_route_permission,
        "consent_accepted": bool(consent.get("accepted")),
        "consent_class": consent.get("class"),
        "budget_ok": bool(budget.get("ok")),
        "budget_disclosure": budget.get("disclosure"),
        "peer_redactor_available": bool(peer_redactor_available),
        "fleet_scrubber_available": bool(fleet_scrubber_available),
        "effective_redaction_gate": effective_redaction_gate,
        "effective_redaction_available": bool(effective_redaction_available),
    }


def plan_lane(
    lane: str,
    *,
    sensitivity: str | None,
    sensitivity_error: str | None,
    external_route_permission: str,
    external_permission_ok: bool = True,
    external_permission_reason: str | None = None,
    redactor_available: bool,
    fleet_scrubber_available: bool | None = None,
    consent: dict[str, Any],
    budget: dict[str, Any],
    fleet_enabled: bool = True,
    peer_available: bool = True,
    fleet_fuse_available: bool = True,
    pin: dict[str, Any] | None = None,
    route_class: str | None = None,
    context_class: str | None = None,
    planned_fingerprint: str | None = None,
    route_available: bool = True,
    auto_fallback: bool = False,
    role: str | None = None,
    requested_provider: str | None = None,
    requested_model: str | None = None,
    preference_source: str | None = None,
    required: bool = True,
    countable: bool = True,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a structurally self-sufficient readiness plan for one lane."""
    rc = route_class or _default_route_class(lane)
    cc = context_class or _default_context_class(lane)
    provider = requested_provider or _default_provider(lane)
    model = requested_model or _default_model(lane)
    role_name = role or _default_role(lane)
    # Fleet scrubber is independent of IDENTIFIED_REDACTION_PATH (peer path).
    # When unset, fall back to redactor_available for fixture compatibility.
    fleet_scrub = (
        redactor_available
        if fleet_scrubber_available is None
        else bool(fleet_scrubber_available)
    )
    fp = planned_fingerprint or planned_route_fingerprint(
        provider=provider,
        requested_model=model,
        route_class=rc,
        context_class=cc,
    )
    # Per-lane redaction gate after route_class / identity is known.
    redaction_gate = _effective_redaction_gate(
        lane, route_class=rc, context_class=cc
    )
    if redaction_gate == "fleet-scrub":
        redaction_avail = fleet_scrub
    elif redaction_gate == "identified-redaction-path":
        redaction_avail = bool(redactor_available)
    else:
        redaction_avail = True  # n/a — redaction path not required for this lane
    pol = policy or _policy_snapshot(
        sensitivity=sensitivity,
        sensitivity_error=sensitivity_error,
        external_route_permission=external_route_permission,
        consent=consent,
        budget=budget,
        peer_redactor_available=bool(redactor_available),
        fleet_scrubber_available=fleet_scrub,
        effective_redaction_gate=redaction_gate,
        effective_redaction_available=redaction_avail,
    )
    base = {
        "lane": lane,
        "role": role_name,
        "requested_provider": provider,
        "requested_model": model,
        "preference_source": preference_source,
        "policy": pol,
        "route_class": rc,
        "context_class": cc,
        "required": bool(required),
        "countable": bool(countable),
        "planned_route_fingerprint": fp,
        "readiness": "ready",
        "reason": None,
    }

    external = _lane_is_external(lane, rc)

    # Strongest policy restrictions first — never mask high/invalid behind availability.
    if sensitivity_error and external:
        return {**base, "readiness": "blocked", "reason": sensitivity_error}

    if rc == "ambiguous" and external:
        return {**base, "readiness": "blocked", "reason": "ambiguous-route-class"}

    if pin and pin.get("strict") and not pin.get("available", True):
        return {**base, "readiness": "blocked", "reason": "explicit-pin-unavailable"}

    def _external_permission_block() -> dict[str, Any] | None:
        if not external_permission_ok:
            return {
                **base,
                "readiness": "blocked",
                "reason": external_permission_reason
                or "invalid-external-route-permission",
            }
        if external_route_permission == "deny":
            return {**base, "readiness": "blocked", "reason": "external-route-denied"}
        return None

    def _availability_skip() -> dict[str, Any] | None:
        if not route_available and not (
            auto_fallback and not (pin and pin.get("strict"))
        ):
            if pin and pin.get("strict"):
                return {
                    **base,
                    "readiness": "blocked",
                    "reason": "explicit-pin-unavailable",
                }
            return {**base, "readiness": "skipped", "reason": "route-unavailable"}
        return None

    if lane == "fleet" or lane.endswith("-fleet"):
        # Policy restrictions first so strongest restriction stays visible
        # (high must not be masked by fleet-disabled / fuse-unavailable).
        if sensitivity == "high":
            return {**base, "readiness": "blocked", "reason": "high-sensitivity"}
        perm_block = _external_permission_block()
        if perm_block is not None:
            return perm_block
        # Fleet medium gate: FleetFuse scrubber availability, not IDENTIFIED_REDACTION_PATH.
        if sensitivity == "medium" and not fleet_scrub:
            return {**base, "readiness": "blocked", "reason": "redactor-unavailable"}
        if not budget["ok"]:
            return {**base, "readiness": "blocked", "reason": budget["reason"]}
        if not consent["accepted"]:
            return {**base, "readiness": "blocked", "reason": consent["reason"]}
        # Availability after policy
        if not fleet_enabled:
            return {**base, "readiness": "skipped", "reason": "fleet-disabled"}
        if not fleet_fuse_available:
            return {**base, "readiness": "skipped", "reason": "fleet-fuse-unavailable"}
        avail = _availability_skip()
        if avail is not None:
            return avail
        return base

    # peer external lanes
    if lane in ("peer-codex", "peer-grok", "codex-medium", "grok") or (
        rc == "external"
    ):
        if external:
            # Policy first (high before peer-unavailable / route-unavailable).
            if sensitivity == "high":
                return {**base, "readiness": "blocked", "reason": "high-sensitivity"}
            perm_block = _external_permission_block()
            if perm_block is not None:
                return perm_block
            # Peer medium gate: IDENTIFIED_REDACTION_PATH (redactor_available).
            if sensitivity == "medium" and not redactor_available:
                return {**base, "readiness": "blocked", "reason": "redactor-unavailable"}
        if lane.startswith("peer") and not peer_available:
            return {**base, "readiness": "skipped", "reason": "peer-unavailable"}
        avail = _availability_skip()
        if avail is not None:
            return avail
        return base

    avail = _availability_skip()
    if avail is not None:
        return avail
    return base


def dedupe_planned(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pre-dispatch: first fingerprint wins; later duplicates skipped."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for p in plans:
        fp = p["planned_route_fingerprint"]
        if fp in seen:
            out.append(
                {
                    **p,
                    "readiness": "skipped",
                    "reason": "duplicate-planned-fingerprint",
                    # Duplicates are not countable for fullness / quorum.
                    "countable": False,
                }
            )
        else:
            seen.add(fp)
            out.append(p)
    return out


def _observed_dedup_key(
    *,
    observed_provider: str | None,
    observed_model: str | None,
    route_class: str,
    context_class: str,
    observed_route: Any,
    observed_key: str | None,
) -> str:
    """Post-exec identity from explicit fields (no hidden name heuristics)."""
    if observed_key:
        return str(observed_key)
    if observed_provider is not None or observed_model is not None:
        return (
            f"{observed_provider}|{observed_model}|{route_class}|{context_class}"
        )
    return f"{observed_route}|{route_class}|{context_class}"


def build_results(
    plans: list[dict[str, Any]],
    route_outcomes: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Exactly one terminal result per planned lane — explicit schema."""
    route_outcomes = route_outcomes or {}
    results: list[dict[str, Any]] = []
    observed_keys: dict[str, int] = {}

    for p in plans:
        lane = p["lane"]
        route_class = p.get("route_class") or _default_route_class(lane)
        context_class = p.get("context_class") or _default_context_class(lane)
        required = bool(p.get("required", True))
        # Pre-dispatch duplicate skips are not countable.
        countable = bool(p.get("countable", True))
        if p.get("reason") == "duplicate-planned-fingerprint":
            countable = False

        terminal_base = {
            "lane": lane,
            "role": p.get("role") or _default_role(lane),
            "observed_provider": None,
            "observed_model": None,
            "route_class": route_class,
            "context_class": context_class,
            "required": required,
            "countable": countable,
            "observed_route": None,
            "outcome": p["readiness"],
            "reason": p["reason"],
            "independent": False,
        }

        if p["readiness"] in ("blocked", "skipped"):
            results.append(terminal_base)
            continue

        outcome_spec = route_outcomes.get(
            lane, {"outcome": "ran", "observed_route": lane}
        )
        outcome = outcome_spec.get("outcome", "ran")
        observed = outcome_spec.get("observed_route", lane)
        reason = outcome_spec.get("reason")
        obs_provider = outcome_spec.get("observed_provider")
        obs_model = outcome_spec.get("observed_model")

        if outcome in ("failed", "timeout", "skipped", "blocked"):
            # Non-ran: observed_route null unless explicitly supplied.
            if "observed_route" not in outcome_spec:
                observed = None
            results.append(
                {
                    **terminal_base,
                    "observed_provider": obs_provider,
                    "observed_model": obs_model,
                    "observed_route": observed,
                    "outcome": outcome,
                    "reason": reason or outcome,
                    "independent": False,
                }
            )
            continue

        # ran — post-execution dedupe by explicit observed identity fields
        if obs_provider is None and observed is not None:
            # Compat: allow fixtures that only set observed_route string.
            obs_provider = outcome_spec.get(
                "observed_provider", p.get("requested_provider")
            )
        if obs_model is None and observed is not None:
            obs_model = outcome_spec.get("observed_model", observed)

        obs_key = _observed_dedup_key(
            observed_provider=obs_provider,
            observed_model=obs_model,
            route_class=route_class,
            context_class=context_class,
            observed_route=observed,
            observed_key=outcome_spec.get("observed_key"),
        )
        count = observed_keys.get(obs_key, 0)
        independent = count == 0
        observed_keys[obs_key] = count + 1
        results.append(
            {
                **terminal_base,
                "observed_provider": obs_provider,
                "observed_model": obs_model,
                "observed_route": observed,
                "outcome": "ran",
                "reason": reason,
                "independent": independent,
            }
        )
    return results


def _is_external_lane(lane: str) -> bool:
    return (
        lane in EXTERNAL_LANES
        or str(lane).startswith("peer")
        or lane == "fleet"
    )


def derive_panel_status(results: list[dict[str, Any]]) -> str:
    """Derive status only after all terminal results exist.

    External/local is taken from each result's explicit ``route_class``.
    Fullness is computed over records that are both ``required`` and
    ``countable`` (pre-dispatch fingerprint duplicates set countable=false).

    Status rules:
    - ``full``: every required+countable lane ran independently
    - ``partial``: at least one *external* independent voice ran, panel degraded
    - ``local-only``: local/first-party independent voice(s) ran and no external
      independent voice ran; also when all external lanes are blocked/skipped
      with nothing external independent
    - ``blocked``: policy prevented meaningful execution
    """
    if not results:
        return "blocked"

    # Fullness set: required AND countable (duplicates are not countable).
    fullness = [
        r
        for r in results
        if r.get("required", True)
        and r.get("countable", True)
        and r.get("reason") != "duplicate-planned-fingerprint"
    ]
    # Broader countable view (includes optional non-required lanes).
    countable = [
        r
        for r in results
        if r.get("countable", True)
        and r.get("reason") != "duplicate-planned-fingerprint"
    ]
    independent_ran = [
        r for r in countable if r.get("outcome") == "ran" and r.get("independent")
    ]
    any_ran = [r for r in results if r.get("outcome") == "ran"]
    failedish = [
        r
        for r in countable
        if r.get("outcome") in ("blocked", "skipped", "failed", "timeout")
        or (r.get("outcome") == "ran" and not r.get("independent"))
    ]
    external_attempted = [r for r in results if _result_is_external(r)]
    external_independent_ran = [
        r for r in independent_ran if _result_is_external(r)
    ]
    local_independent_ran = [
        r for r in independent_ran if not _result_is_external(r)
    ]

    # Full: every required+countable lane ran as an independent voice.
    if fullness and all(
        r.get("outcome") == "ran" and r.get("independent") for r in fullness
    ):
        return "full"

    # Partial only when an external independent voice ran but the panel degraded.
    if external_independent_ran:
        return "partial"

    # Local independent voice(s) ran, no external independent → local-only
    # (e.g. high sensitivity: critic ran, external lanes blocked).
    if local_independent_ran:
        return "local-only"

    # Non-independent external runs only (duplicates without a second independent)
    # still count as a degraded external panel when an external voice ran at all.
    external_any_ran = [r for r in any_ran if _result_is_external(r)]
    if external_any_ran:
        return "partial"

    if any_ran:
        # Local non-independent-only runs still local-only.
        return "local-only"

    # Nothing ran successfully
    if external_attempted and not external_independent_ran and all(
        r.get("outcome") in ("blocked", "skipped") for r in external_attempted
    ):
        return "local-only"

    if failedish and not independent_ran:
        # All external blocked with no local voices → local-only; else blocked
        local_lanes = [r for r in countable if not _result_is_external(r)]
        if not local_lanes:
            return "local-only"
        return "blocked"

    return "blocked"


def _lane_spec_lookup(
    lane: str,
    lane_specs: dict[str, Any],
    route_classes: dict[str, Any],
    fingerprints: dict[str, Any],
) -> dict[str, Any]:
    """Merge per-lane fixture overrides with semantic defaults."""
    spec = dict(lane_specs.get(lane) or {})
    if "route_class" not in spec and lane in route_classes:
        spec["route_class"] = route_classes[lane]
    if "planned_route_fingerprint" not in spec and lane in fingerprints:
        spec["planned_route_fingerprint"] = fingerprints[lane]
    return spec


def evaluate(scenario: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a fixture input block → plan, results, status, meta."""
    inp = scenario.get("input") or scenario
    harness = resolve_harness(inp.get("harness"))
    pref_sources = inp.get("preference_sources") or []
    requested_routes = list(inp.get("requested_routes") or [])
    sensitivity, sens_err = intersect_sensitivity(inp.get("sensitivity_scopes"))
    # Default allow only when the key is truly absent; explicit null/other fail closed.
    if "external_route_permission" in inp:
        external_perm_raw = inp.get("external_route_permission")
    else:
        external_perm_raw = "allow"
    external_perm_eval = evaluate_external_route_permission(external_perm_raw)
    external_perm = (
        external_perm_eval["value"] if external_perm_eval["ok"] else external_perm_raw
    )
    # Peer redactor (IDENTIFIED_REDACTION_PATH) vs FleetFuse scrubber are distinct.
    redactor = bool(inp.get("redactor_available", True))
    if "fleet_scrubber_available" in inp:
        fleet_scrubber: bool | None = bool(inp.get("fleet_scrubber_available"))
    else:
        # Fixture compat: single flag applied to both paths when fleet flag absent.
        fleet_scrubber = None
    consent = evaluate_consent(inp.get("metered_consent"))
    budget = evaluate_budget(inp.get("budget_usd"))
    fleet_enabled = inp.get("fleet_enabled", True)
    peer_available = inp.get("peer_available", True)
    fleet_fuse_available = inp.get("fleet_fuse_available", True)
    route_outcomes = inp.get("route_outcomes") or {}
    pins = inp.get("pins") or {}
    route_classes = inp.get("route_classes") or {}
    fingerprints = inp.get("fingerprints") or {}
    route_available_map = inp.get("route_available") or {}
    auto_fallback_map = inp.get("auto_fallback") or {}
    lane_specs = inp.get("lane_specs") or {}

    # Resolved model preference: wins for planned requested_model/profile and
    # therefore planned_route_fingerprint, unless a lane_spec sets a more
    # specific per-lane requested_model / requested_profile.
    model_pref = resolve_preference(pref_sources, "model")
    preference_source = model_pref["source"] if model_pref else None
    preference_value = model_pref["value"] if model_pref else None
    external_perm_str = (
        external_perm if isinstance(external_perm, str) else str(external_perm)
    )

    plans: list[dict[str, Any]] = []
    for lane in requested_routes:
        pin = pins.get(lane)
        spec = _lane_spec_lookup(lane, lane_specs, route_classes, fingerprints)
        # Explicit per-lane model/profile is more specific than global preference.
        lane_explicit_model = (
            "requested_model" in spec or "requested_profile" in spec
        )
        if lane_explicit_model:
            req_model = spec.get("requested_model") or spec.get("requested_profile")
            # Lane did not inherit the global preference for its model value.
            lane_pref_source = (
                spec["preference_source"]
                if "preference_source" in spec
                else None
            )
        elif preference_value is not None:
            req_model = preference_value
            lane_pref_source = (
                spec["preference_source"]
                if "preference_source" in spec
                else preference_source
            )
        else:
            req_model = None
            lane_pref_source = (
                spec["preference_source"]
                if "preference_source" in spec
                else preference_source
            )
        plans.append(
            plan_lane(
                lane,
                sensitivity=sensitivity,
                sensitivity_error=sens_err,
                external_route_permission=external_perm_str,
                external_permission_ok=external_perm_eval["ok"],
                external_permission_reason=external_perm_eval["reason"],
                redactor_available=redactor,
                fleet_scrubber_available=fleet_scrubber,
                consent=consent,
                budget=budget,
                fleet_enabled=fleet_enabled,
                peer_available=peer_available,
                fleet_fuse_available=fleet_fuse_available,
                pin=pin,
                route_class=spec.get("route_class"),
                context_class=spec.get("context_class"),
                # Explicit fingerprint override still wins (e.g. T10 dedup fixtures);
                # otherwise plan_lane derives fingerprint from applied model.
                planned_fingerprint=spec.get("planned_route_fingerprint"),
                route_available=route_available_map.get(lane, True),
                auto_fallback=bool(auto_fallback_map.get(lane, False)),
                role=spec.get("role"),
                requested_provider=spec.get("requested_provider"),
                requested_model=req_model,
                preference_source=lane_pref_source,
                required=spec.get("required", True),
                countable=spec.get("countable", True),
                # Do not pass a shared global policy — plan_lane builds a
                # self-sufficient per-lane snapshot after route identity is known.
                policy=None,
            )
        )

    plans = dedupe_planned(plans)
    results = build_results(plans, route_outcomes)
    status = derive_panel_status(results)

    # Command-contract helpers for metered branch
    metered_branch_entered = any(
        p["lane"] == "fleet" and p["readiness"] == "ready" for p in plans
    ) and consent["accepted"]

    expected_plan = {
        p["lane"]: {"readiness": p["readiness"], "reason": p["reason"]} for p in plans
    }

    return {
        "harness": harness,
        "model_preference": model_pref,
        "sensitivity": sensitivity,
        "sensitivity_error": sens_err,
        "consent": consent,
        "budget": budget,
        "plan": expected_plan,
        "plans": plans,
        "results": results,
        "panel_status": status,
        "metered_branch_entered": metered_branch_entered,
        "yes_metered_allowed": metered_branch_entered,
        "contract_evidence_only": True,
    }


def assert_matches_expected(actual: dict[str, Any], fixture: dict[str, Any]) -> None:
    """Raise AssertionError if actual diverges from fixture expectations."""
    if "expected_plan" in fixture:
        for lane, exp in fixture["expected_plan"].items():
            assert lane in actual["plan"], f"missing plan lane {lane}"
            got = actual["plan"][lane]
            assert got["readiness"] == exp["readiness"], (
                f"{lane} readiness: got {got['readiness']}, expected {exp['readiness']}"
            )
            if "reason" in exp:
                assert got["reason"] == exp["reason"], (
                    f"{lane} reason: got {got['reason']}, expected {exp['reason']}"
                )

    if "expected_results" in fixture:
        exp_results = fixture["expected_results"]
        assert len(actual["results"]) == len(exp_results), (
            f"result count {len(actual['results'])} != {len(exp_results)}: "
            f"{actual['results']}"
        )
        for got, exp in zip(actual["results"], exp_results):
            for k, v in exp.items():
                assert got.get(k) == v, (
                    f"result[{got.get('lane')}].{k}: got {got.get(k)!r}, "
                    f"expected {v!r}"
                )

    if "expected_panel_status" in fixture:
        assert actual["panel_status"] == fixture["expected_panel_status"], (
            f"panel_status: got {actual['panel_status']}, "
            f"expected {fixture['expected_panel_status']}"
        )

    if "expected_yes_metered" in fixture:
        assert actual["yes_metered_allowed"] == fixture["expected_yes_metered"], (
            f"yes_metered: got {actual['yes_metered_allowed']}, "
            f"expected {fixture['expected_yes_metered']}"
        )

    if "expected_harness_identity" in fixture:
        assert actual["harness"]["identity"] == fixture["expected_harness_identity"], (
            f"harness identity: got {actual['harness']['identity']}, "
            f"expected {fixture['expected_harness_identity']}"
        )

    if "expected_preference_source" in fixture:
        mp = actual["model_preference"]
        assert mp is not None, "expected a resolved model preference"
        assert mp["source"] == fixture["expected_preference_source"], (
            f"preference source: got {mp['source']}, "
            f"expected {fixture['expected_preference_source']}"
        )
        if "expected_preference_value" in fixture:
            exp_val = fixture["expected_preference_value"]
            exp_src = fixture["expected_preference_source"]
            assert mp["value"] == exp_val
            # Preference must drive planned model + fingerprint, not only
            # top-level model_preference metadata.
            for p in actual["plans"]:
                # Skip lanes with explicit per-lane model overrides in the fixture.
                lane_specs = (fixture.get("input") or {}).get("lane_specs") or {}
                lane_spec = lane_specs.get(p["lane"]) or {}
                if "requested_model" in lane_spec or "requested_profile" in lane_spec:
                    continue
                assert p["requested_model"] == exp_val, (
                    f"plan[{p['lane']}].requested_model: got {p['requested_model']!r}, "
                    f"expected preference value {exp_val!r}"
                )
                assert p["preference_source"] == exp_src, (
                    f"plan[{p['lane']}].preference_source: got {p['preference_source']!r}, "
                    f"expected {exp_src!r}"
                )
                assert exp_val in p["planned_route_fingerprint"], (
                    f"plan[{p['lane']}].planned_route_fingerprint must contain "
                    f"preference model {exp_val!r}: {p['planned_route_fingerprint']!r}"
                )
                expected_fp = planned_route_fingerprint(
                    provider=p["requested_provider"],
                    requested_model=exp_val,
                    route_class=p["route_class"],
                    context_class=p["context_class"],
                )
                # When the fixture did not pin an explicit fingerprint override,
                # the derived fingerprint must equal the preference-applied one.
                inp_fps = (fixture.get("input") or {}).get("fingerprints") or {}
                if p["lane"] not in inp_fps and "planned_route_fingerprint" not in lane_spec:
                    assert p["planned_route_fingerprint"] == expected_fp, (
                        f"plan[{p['lane']}].planned_route_fingerprint: "
                        f"got {p['planned_route_fingerprint']!r}, expected {expected_fp!r}"
                    )


def independent_voices_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Derive panel voice lists from terminal results (no template slogans).

    Returns independent voices that actually ran, plus requested lanes that
    were blocked/skipped. Used by output-contract tests so high/local-only
    never claims trio/frontier/Codex/Grok ran when they did not.
    """
    independent = [
        {
            "lane": r["lane"],
            "observed_route": r.get("observed_route"),
            "observed_provider": r.get("observed_provider"),
            "observed_model": r.get("observed_model"),
        }
        for r in results
        if r.get("outcome") == "ran" and r.get("independent")
    ]
    blocked_or_skipped = [
        {
            "lane": r["lane"],
            "outcome": r.get("outcome"),
            "reason": r.get("reason"),
        }
        for r in results
        if r.get("outcome") in ("blocked", "skipped")
    ]
    return {
        "independent_voices": independent,
        "blocked_or_skipped": blocked_or_skipped,
    }
