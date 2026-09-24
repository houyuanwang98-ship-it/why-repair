"""Session-owned search limits and exact feedback memory shared by both APIs.

This is a serial, in-process ledger, not a durable or tamper-proof authority.
Stored witnesses are replayed against new obligations; labels are never migrated.
"""
from copy import deepcopy

from .m5_person_a_review import canonical_digest
from .repair_contract import _require
from .repair_counterexample import replay_counterexample


def search_ledger(session, *, attempts=None, routes=None, feedback=None):
    supplied = {"attempts": attempts, "routes": routes, "feedback": feedback}
    for limit in supplied.values():
        _require(limit is None or type(limit) is int and limit > 0, "positive budgets required")
    if not hasattr(session, "_repair_search_ledger"):
        defaults = {"attempts": 8, "routes": 4, "feedback": 20}
        limits = {key: value if value is not None else defaults[key] for key, value in supplied.items()}
        session._repair_search_ledger = {
            "limits": limits, "used": dict.fromkeys(limits, 0), "events": [],
            "seen_candidates": [], "refuted_interfaces": [], "witnesses": [], "replays": [],
        }
    ledger = session._repair_search_ledger
    _require(all(value is None or ledger["limits"][key] == value for key, value in supplied.items()),
             "cannot reset session search budgets")
    return ledger


def charge(ledger, kind):
    _require(ledger["used"][kind] < ledger["limits"][kind], f"{kind} budget exhausted")
    ledger["used"][kind] += 1


def remember_counterexample(ledger, contract, proposal, witness):
    charge(ledger, "feedback")
    record = replay_counterexample(contract, proposal, witness)
    ledger["events"].append({"event": "counterexample", "record": deepcopy(record)})
    if record["status"] == "refuted":
        digest = proposal["proposal_digest"]
        if digest not in ledger["refuted_interfaces"]:
            ledger["refuted_interfaces"].append(digest)
        if not any(row["witness"] == witness for row in ledger["witnesses"]):
            ledger["witnesses"].append(deepcopy(record))
    return record


def interface_refuted(ledger, contract, proposal):
    digest = proposal["proposal_digest"]
    if digest in ledger["refuted_interfaces"]:
        return True
    for previous in list(ledger["witnesses"]):
        key = canonical_digest({"interface": digest, "witness": previous["witness"]})
        if key in ledger["replays"]:
            continue
        # Recompute every current premise/output, including changed region scope.
        record = remember_counterexample(ledger, contract, proposal, previous["witness"])
        ledger["replays"].append(key)
        if record["status"] == "refuted":
            return True
    return False
