"""Unified explicit repair workflow and honest, session-owned cost accounting.

Callbacks supply evidence or candidates. This module has no model/provider client
and no automatic routing. A callback result is not proof of provider identity.
"""
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from time import perf_counter

from .m5_person_a_review import canonical_digest
from .repair_contract import _require
from .repair_search_ledger import search_ledger, charge
from .region_repair_search import RegionRepairSearch


TOKEN_FIELDS = ("input_tokens", "output_tokens", "reasoning_tokens", "cached_input_tokens", "total_tokens")


@dataclass(frozen=True)
class CallResult:
    response: object
    usage: dict | None = None
    evidence_kind: str = "unreported"


def checked_usage(usage):
    result = dict.fromkeys((*TOKEN_FIELDS, "cost", "currency"))
    if usage is None:
        return result
    _require(isinstance(usage, dict) and set(usage) <= set(result), "invalid usage fields")
    for key in TOKEN_FIELDS:
        value = usage.get(key)
        _require(value is None or type(value) is int and value >= 0, "tokens must be nonnegative integers or unavailable")
    result.update(deepcopy(usage))
    cost, currency = result["cost"], result["currency"]
    _require((cost is None) == (currency is None), "cost and currency must be supplied together")
    if cost is not None:
        _require(isinstance(cost, str) and len(cost) <= 64, "cost must be a bounded decimal string")
        try:
            value = Decimal(cost)
            _require(value.is_finite() and value >= 0 and abs(value.as_tuple().exponent) <= 12,
                     "cost must be finite, nonnegative and bounded")
        except InvalidOperation as exc:
            raise ValueError("invalid decimal cost") from exc
        _require(isinstance(currency, str) and len(currency) == 3 and currency.isascii() and
                 currency.isalpha() and currency.isupper(), "currency must be a three-letter code")
    return result


class RepairSearch:
    """Create before diagnosis; begin a fresh episode after each confirmed error.

    Low-level constrained APIs share search budgets and feedback. Callback costs
    are complete only for operations routed through this facade; supplied responses
    and direct low-level work must be reported as unavailable, never zero-cost.
    """
    def __init__(self, session, *, max_attempts=None, max_routes=None, max_feedback=None):
        self.session = session
        self._ledger = search_ledger(session, attempts=max_attempts, routes=max_routes, feedback=max_feedback)
        if not hasattr(session, "_repair_cost_events"):
            session._repair_cost_events = []
        self._costs = session._repair_cost_events
        self._episode = None

    def _call(self, phase, request, callback):
        event = {"event_id": len(self._costs) + 1, "phase": phase,
                 "request_digest": canonical_digest(request), "revision": self.session.revision,
                 "status": "started", "evidence_kind": "unreported", "usage": checked_usage(None),
                 "latency_seconds": None}
        self._costs.append(event)
        start = perf_counter()
        try:
            result = callback(deepcopy(request))
            if isinstance(result, CallResult):
                _require(result.evidence_kind in {"fixture", "external", "human", "unreported"}, "invalid evidence kind")
                event["evidence_kind"] = result.evidence_kind
                event["usage"] = checked_usage(result.usage)
                result = result.response
            event["status"] = "returned"
            return result
        except Exception as exc:
            event.update(status="failed", error_type=type(exc).__name__)
            raise
        finally:
            event["latency_seconds"] = perf_counter() - start

    def evaluate(self, reviewer=None, *, max_calls=8, responses=None):
        # Imported responses have unknown external costs. Record every submission,
        # including duplicates/unused responses, rather than inventing free calls.
        imported = []
        for key in (responses or {}):
            self._costs.append({"event_id": len(self._costs) + 1, "phase": "imported_review",
                               "request_digest": key, "revision": self.session.revision,
                               "status": "supplied", "evidence_kind": "unreported",
                               "usage": checked_usage(None), "latency_seconds": None})
            imported.append(self._costs[-1])
        def adapter(request):
            phase = "final_review" if request["input"]["target"]["node_id"] == "__proof_goal__" else (
                "diagnosis" if self.session.revision == 1 else "revalidation")
            return self._call(phase, request, reviewer)
        first_event = len(self.session._events)
        try:
            return self.session.evaluate(adapter if reviewer is not None else None, max_calls=max_calls, responses=responses)
        finally:
            admissions = [e for e in self.session._events[first_event:] if e["event"] == "imported_review_attempt"]
            for cost, admission in zip(imported, admissions):
                cost["admitted"] = admission["admitted"]

    def begin(self):
        self._episode = RegionRepairSearch(self.session)
        return self._episode.contract()

    def _active(self):
        _require(self._episode is not None, "begin an episode after confirmed localization")
        self._episode._current()
        return self._episode

    def contract(self):
        return self._active().contract()

    def select_route(self, mode):
        return self._active().select_route(mode)

    def route_options(self):
        episode = self._active()
        refuted = False
        if episode._proposal is not None:
            from .repair_search_ledger import interface_refuted
            refuted = interface_refuted(self._ledger, episode.contract(), episode._proposal)
        used, limits = self._ledger["used"], self._ledger["limits"]
        exhausted = used["attempts"] >= limits["attempts"] or used["feedback"] >= limits["feedback"]
        interface_ready = episode._interface_review is not None
        trigger = "contract_refuted" if refuted else (
            "search_exhausted" if exhausted else ("review_undetermined" if not interface_ready else "explicit_choice"))
        return {"trigger": trigger, "automatic_routing": False,
                "continue_local_available": not refuted and not exhausted and interface_ready,
                "route_budget_remaining": limits["routes"] - used["routes"],
                "choices": ["continue_local", "expand", "rewrite", "await_evidence", "stop_budget"],
                "estimated_remaining_tokens": None,
                "reason": "Explicit choice required. Budget exhaustion is not mathematical irreparability."}

    def interface_request(self, statements):
        return self._active().interface_request(statements)

    def review_interface(self, statements, reviewer):
        episode = self._active()
        request = episode.interface_request(statements)
        self._feedback_available()
        cost_id = len(self._costs) + 1
        first_event = len(self._ledger["events"])
        try:
            response = self._call("contract_review", request, reviewer)
        except Exception:
            charge(self._ledger, "feedback")
            # A failed new review revokes previously accepted interface evidence.
            episode._interface_review = None
            episode._pending.clear()
            self._ledger["events"].append({"event": "interface_review", "status": "review_failed",
                                          "cost_event_id": cost_id})
            raise
        try:
            return episode.accept_interface(statements, response)
        finally:
            for event in self._ledger["events"][first_event:]:
                if event["event"] == "interface_review":
                    event["cost_event_id"] = cost_id

    def _feedback_available(self):
        _require(self._ledger["used"]["feedback"] < self._ledger["limits"]["feedback"], "feedback budget exhausted")

    def generator_input(self, **kwargs):
        return self._active().generator_input(**kwargs)

    def generate_and_prepare(self, generator, *, policy="region-body-replacement-v1"):
        episode = self._active()
        request = episode.generator_input(policy=policy)
        # The protocol envelope is controller-owned, not left for a callback to guess.
        request["base_digest"] = episode._base["proof_digest"]
        request["generator_id"] = self.session.generator_id
        event = episode._begin_attempt()
        event["cost_event_id"] = len(self._costs) + 1
        try:
            patch = self._call("candidate_generation", request, generator)
            return episode._prepare_attempt(patch, event)
        except Exception as exc:
            event.update(status="rejected", error_type=type(exc).__name__, reason=str(exc))
            raise

    def review_candidate(self, request_digest, reviewer):
        episode = self._active()
        episode._ready()
        _require(request_digest in episode._pending, "unknown or consumed candidate")
        request, _ = episode._candidate_request(episode._pending[request_digest])
        _require(request["input_digest"] == request_digest, "stale candidate review")
        self._feedback_available()
        cost_id = len(self._costs) + 1
        first_event = len(self._ledger["events"])
        try:
            response = self._call("candidate_review", request, reviewer)
        except Exception:
            charge(self._ledger, "feedback")
            episode._pending.pop(request_digest, None)
            self._ledger["events"].append({"event": "region_review", "request_digest": request_digest,
                                          "status": "review_failed", "cost_event_id": cost_id})
            raise
        try:
            return episode.decide(request_digest, response)
        finally:
            for event in self._ledger["events"][first_event:]:
                if event["event"] == "region_review":
                    event["cost_event_id"] = cost_id

    def record_counterexample(self, witness):
        return self._active().record_counterexample(witness)

    def snapshot(self):
        external_events = {"interface_review", "region_candidate", "candidate_attempt", "region_review", "boundary_review"}
        unmetered = [i for i, e in enumerate(self._ledger["events"])
                     if e["event"] in external_events and "cost_event_id" not in e]
        recorded_scans = sum(e["phase"] in {"diagnosis", "revalidation", "final_review"} or
                             e["phase"] == "imported_review" and e.get("admitted", False) for e in self._costs)
        unmetered_scans = max(0, self.session.snapshot()["review_calls"] - recorded_scans)
        known = {key: (sum(event["usage"][key] or 0 for event in self._costs)
                       if any(event["usage"][key] is not None for event in self._costs) else None)
                 for key in TOKEN_FIELDS}
        totals = {key: (known[key] if self._costs and all(event["usage"][key] is not None for event in self._costs)
                        else None) for key in TOKEN_FIELDS}
        currencies = {event["usage"]["currency"] for event in self._costs if event["usage"]["cost"] is not None}
        with localcontext() as context:
            context.prec = 80 + len(str(len(self._costs)))
            subtotals = {currency: str(sum((Decimal(e["usage"]["cost"]) for e in self._costs
                                          if e["usage"]["currency"] == currency), Decimal(0))) for currency in currencies}
        complete_cost = bool(self._costs) and len(currencies) == 1 and all(e["usage"]["cost"] is not None for e in self._costs)
        totals["cost"] = next(iter(subtotals.values())) if complete_cost else None
        totals["currency"] = next(iter(currencies)) if complete_cost else None
        totals["latency_seconds"] = (sum(e["latency_seconds"] for e in self._costs)
                                     if self._costs and all(e["latency_seconds"] is not None for e in self._costs) else None)
        if unmetered or unmetered_scans:
            totals = dict.fromkeys(totals)
        return deepcopy({"proof": self.session.snapshot(), "search_ledger": self._ledger,
                         "episode": self._episode.snapshot() if self._episode is not None else None,
                         "cost_events": self._costs, "measured_subtotals": {**known, "cost_by_currency": subtotals},
                         "totals": totals, "missing_usage_events": [e["event_id"] for e in self._costs
                             if any(v is None for v in e["usage"].values())],
                         "unmetered_search_event_indices": unmetered, "unmetered_localization_calls": unmetered_scans,
                         "cost_scope": "Facade callback attempts and supplied responses only; unavailable fields are null. Reasoning/cached token fields may overlap other fields and are never added into total_tokens. Low-level APIs and unreported external calls are not fully metered.",
                         "automatic_routing": False})
