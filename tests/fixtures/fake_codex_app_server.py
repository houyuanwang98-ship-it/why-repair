"""Local JSON-RPC test double. Makes no network or model calls."""
import json
import hashlib
import sys

loaded = set()
count = 0
model = effort = None


def emit(value):
    print(json.dumps(value), flush=True)


def notify(method, params):
    emit({"method": method, "params": params})


for line in sys.stdin:
    request = json.loads(line)
    method, params = request["method"], request.get("params", {})
    if "id" not in request:
        continue
    if method == "initialize":
        result = {"userAgent": "fake-codex-no-model-calls"}
    elif method == "model/list":
        result = {"data": [{"model": "gpt-5.6-sol", "supportedReasoningEfforts": [{"reasoningEffort": "xhigh"}]}], "nextCursor": None}
        if "--with-validator" in sys.argv:
            result["data"].append({"model": "gpt-6-astra", "supportedReasoningEfforts": [{"reasoningEffort": "high"}]})
    elif method == "thread/start":
        count += 1
        identity = f"thread-{count}"
        loaded.add(identity)
        model, effort = params["model"], params["config"]["model_reasoning_effort"]
        assert params["ephemeral"] and not params["allowProviderModelFallback"]
        result = {"thread": {"id": identity, "turns": []}, "model": model,
                  "reasoningEffort": effort, "instructionSources": []}
    elif method == "turn/start":
        identity = params["threadId"]
        payload = json.loads(params["input"][0]["text"])
        if payload.get("crash"):
            sys.exit(9)
        item = {"type": "agentMessage", "id": f"item-{count}", "phase": "final_answer",
                "text": json.dumps({"kind": "proof", "text": "Fixture proof", "reason": "fixture"})}
        if "sample_id" in payload:
            assert model == "gpt-6-astra" and effort == "high"
            assert set(payload) == {"sample_id", "theorem", "assumptions", "domain", "explicit_subgoals", "candidate_text"}
            input_digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            value = {"sample_id": payload["sample_id"], "input_digest": input_digest, "candidate_kind": "proof",
                     "validity": "valid", "rigor": "pass", "problem_preservation": "pass", "goal_coverage": "pass",
                     "counterexample_validity": "not_applicable", "findings": [], "unresolved_obligations": [],
                     "evidence_scope": "model_only", "reason": "Scripted judge fixture; not mathematical evidence"}
            item["text"] = json.dumps(value)
        if payload.get("tool"):
            item = {"type": "commandExecution", "id": "bad"}
        notify("item/started", {"threadId": identity, "item": item})
        notify("item/completed", {"threadId": identity, "item": item})
        if not payload.get("missing_usage"):
            notify("thread/tokenUsage/updated", {"threadId": identity, "turnId": str(count),
                "tokenUsage": {"total": {"inputTokens": 31, "outputTokens": 17,
                    "cachedInputTokens": 3, "reasoningOutputTokens": 5}}})
        notify("turn/completed", {"threadId": identity,
               "turn": {"id": str(count), "status": "completed", "items": [item]}})
        result = {"turn": {"id": str(count)}}
    elif method == "thread/unsubscribe":
        loaded.discard(params["threadId"])
        result = {"status": "unsubscribed"}
        notify("thread/closed", {"threadId": params["threadId"]})
    elif method == "thread/loaded/list":
        result = {"data": sorted(loaded), "nextCursor": None}
    elif method == "turn/interrupt":
        result = {}
    else:
        raise RuntimeError(method)
    emit({"id": request["id"], "result": result})
