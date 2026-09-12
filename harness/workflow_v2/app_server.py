"""One stdio Codex app-server per slot; fresh ephemeral thread for every call."""
from __future__ import annotations

from collections import deque
import json
import os
from pathlib import Path
import queue
import subprocess
import tempfile
import threading
import time
import tomllib

from harness.codex_cli import CodexCLIError, project_codex_output_schema
from .contracts import EXPERIMENT_MODEL, VALIDATION_MODEL, require, write_once
from .runtime import DISABLED_FEATURES


class PersistentServer:
    def __init__(self, folder, role, lane, *, command=None):
        self.folder = Path(folder)
        self.role, self.lane = role, lane
        self.model, self.effort = VALIDATION_MODEL if role == "validation" else EXPERIMENT_MODEL
        require(role in {"experiment", "validation"}, "unknown server role")
        self.command_override = command  # Only used by subprocess protocol tests.
        self.process = None
        self.pending = deque()
        self.incoming = queue.Queue()
        self.request_id = 0
        self.started_once = False
        self.healthy = True
        self.call_count = self.contexts_released = 0
        self.write_lock = threading.Lock()
        self.abort = threading.Event()
        self.active_thread = self.active_turn = None
        self.on_failure = None

    def start(self):
        require(not self.started_once, "server restart is forbidden")
        self.started_once = True
        self.folder.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="why-repair-slot-")
        config_file = Path.home() / ".codex/config.toml"
        config = tomllib.loads(config_file.read_text()) if config_file.exists() else {}
        settings = {"model": self.model, "model_reasoning_effort": self.effort,
                    "model_provider": "openai", "web_search": "disabled",
                    "project_doc_max_bytes": 0, "developer_instructions": "",
                    "history.persistence": "none", "agents.enabled": False,
                    "sqlite_home": str(self.folder / "state"),
                    "log_dir": str(self.folder / "logs"), "check_for_update_on_startup": False,
                    "thread_unload_delay_secs": 0}
        for name in config.get("mcp_servers", {}):
            require(all(c.isalnum() or c in "_-" for c in name), "unsupported MCP config key")
            settings[f"mcp_servers.{name}.enabled"] = False
        command = ["codex", "app-server", "--listen", "stdio://"]
        disabled = (*DISABLED_FEATURES, "memories", "goals", "shell_snapshot",
                    "unbounded_connection_retries", "workspace_dependencies",
                    "request_permissions_tool", "default_mode_request_user_input")
        for feature in disabled:
            command += ["--disable", feature]
        command += ["--enable", "skip_host_skill_discovery"]
        for key, value in settings.items():
            command += ["-c", key + "=" + json.dumps(value)]
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(("OPENAI_", "CODEX_MODEL", "CODEX_PROFILE", "CODEX_API_KEY"))}
        env["TOKIO_WORKER_THREADS"] = "2"
        self.stderr = (self.folder / "stderr.log").open("a", encoding="utf-8")
        self.wire = (self.folder / "rpc.jsonl").open("a", encoding="utf-8")
        self.process = subprocess.Popen(self.command_override or command, cwd=self.temp.name,
            env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr,
            text=True, encoding="utf-8", bufsize=1, start_new_session=True)
        threading.Thread(target=self._reader, daemon=True).start()
        write_once(self.folder / "process.json", {"pid": self.process.pid, "role": self.role,
            "lane": self.lane, "model": self.model, "effort": self.effort,
            "server_starts": 1, "restart_policy": "never", "command": self.command_override or command})
        result = self.request("initialize", {"clientInfo": {"name": "why_repair_scheduler",
            "version": "2.1"}, "capabilities": {"experimentalApi": True}}, timeout=60)
        self.send({"method": "initialized", "params": {}})
        write_once(self.folder / "initialized.json", result)

    def check_ready(self):
        """No turn/start: verify catalog membership and immediate context disposal."""
        catalog, cursor = [], None
        while True:
            page = self.request("model/list", {"includeHidden": True, "limit": 100, "cursor": cursor})
            catalog.extend(page["data"])
            cursor = page.get("nextCursor")
            if not cursor:
                break
        matches = [m for m in catalog if m["model"] == self.model]
        available = bool(matches) and any(r["reasoningEffort"] == self.effort
            for m in matches for r in m["supportedReasoningEfforts"])
        # Even an unavailable model can be configured locally. Use an empty thread to test lifecycle,
        # then fail the catalog gate before any generation request is permitted.
        thread = self.request("thread/start", {"model": self.model,
            "allowProviderModelFallback": False, "ephemeral": True, "cwd": self.temp.name,
            "approvalPolicy": "never", "sandbox": "read-only", "environments": [],
            "baseInstructions": "Lifecycle preflight. No model generation will be requested.",
            "developerInstructions": "", "config": {"model_reasoning_effort": self.effort,
                                                         "project_doc_max_bytes": 0}})
        require(thread["model"] == self.model and thread.get("reasoningEffort") == self.effort,
                "startup thread changed fixed model/effort")
        require(not thread.get("instructionSources"), "unexpected startup instruction files")
        before = self.contexts_released
        self.release(thread["thread"]["id"])
        result = {"model": self.model, "effort": self.effort, "catalog_available": available,
                  "context_unload_verified": self.contexts_released == before+1, "model_calls": 0,
                  "catalog_models": [m["model"] for m in catalog],
                  "configured_unload_delay_seconds": 0}
        write_once(self.folder / "readiness.json", result)
        return result

    def _reader(self):
        try:
            for line in self.process.stdout:
                self.incoming.put(json.loads(line))
        except Exception as exc:
            self.incoming.put(exc)
        finally:
            self.incoming.put(EOFError("app-server exited; automatic restart is forbidden"))

    def send(self, message):
        with self.write_lock:
            self.wire.write(json.dumps({"time": time.time(), "direction": "send", "message": message}) + "\n")
            self.wire.flush()
            self.process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
            self.process.stdin.flush()

    def receive(self, deadline):
        while True:
            if self.abort.is_set():
                raise InterruptedError("scheduler cancellation")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("app-server RPC/turn deadline exceeded")
            try:
                message = self.incoming.get(timeout=min(1, remaining))
                break
            except queue.Empty:
                continue
        if isinstance(message, Exception):
            self.healthy = False
            raise message
        with self.write_lock:
            self.wire.write(json.dumps({"time": time.time(), "direction": "receive", "message": message}) + "\n")
            self.wire.flush()
        if "id" in message and "method" in message:
            self.send({"id": message["id"], "error": {"code": -32601,
                       "message": "Model tools and approval requests are disabled in this experiment"}})
            raise RuntimeError("forbidden server request: " + message["method"])
        return message

    def request(self, method, params, timeout=30):
        self.request_id += 1
        identity = self.request_id
        self.send({"id": identity, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        while True:
            message = self.receive(deadline)
            if message.get("id") == identity:
                if "error" in message:
                    raise RuntimeError(method + ": " + json.dumps(message["error"], ensure_ascii=False))
                return message["result"]
            self.pending.append(message)

    def release(self, thread_id):
        response = self.request("thread/unsubscribe", {"threadId": thread_id})
        require(response["status"] in {"unsubscribed", "notLoaded"}, "thread unsubscribe failed")
        # Observe actual unloading, not merely the unsubscribe acknowledgement.
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            loaded = self.request("thread/loaded/list", {"limit": 100})
            if thread_id not in loaded["data"] and not loaded.get("nextCursor"):
                self.contexts_released += 1
                self.pending.clear()
                return
            time.sleep(0.25)
        raise TimeoutError("thread context was not unloaded")

    def __call__(self, *, model, prompt, input_payload, max_output_tokens, sampling,
                 output_schema, timeout_seconds):
        require((model, sampling["reasoning_effort"]) == (self.model, self.effort), "slot model mismatch")
        require(self.healthy and self.process.poll() is None, "slot unavailable; no restart")
        self.call_count += 1
        started = time.monotonic()
        deadline = started + timeout_seconds
        self.pending.clear()
        raw = {"runtime": "codex_app_server", "requested_model": model, "model": None,
            "server_pid": self.process.pid, "lane": self.lane, "role": self.role,
            "events": [], "rpc_events": [], "usage": {}, "cost_usd": None,
            "output_text": "", "return_code": 1, "output_token_cap": "soft_accounted_after_response",
            "requested_max_output_tokens": max_output_tokens, "context_released": False}
        failure = None
        try:
            response = self.request("thread/start", {"model": model, "modelProvider": "openai",
                "allowProviderModelFallback": False, "ephemeral": True, "cwd": self.temp.name,
                "baseInstructions": "You are a mathematical reasoning component. Return only the requested structured result. Do not use tools.",
                "developerInstructions": prompt, "approvalPolicy": "never", "sandbox": "read-only",
                "dynamicTools": [], "environments": [], "runtimeWorkspaceRoots": [],
                "config": {"model_reasoning_effort": self.effort, "project_doc_max_bytes": 0}},
                timeout=max(1, deadline-time.monotonic()))
            self.active_thread = response["thread"]["id"]
            raw["thread_start"] = response
            require(response["model"] == model and response.get("reasoningEffort") == self.effort,
                    "server changed the fixed model/effort")
            require(not response.get("instructionSources"), "unexpected instruction files")
            require(not response["thread"].get("turns"), "fresh thread already has context")
            raw["codex_thread_id"] = self.active_thread
            # This confirms server configuration, not an independently verified backend snapshot.
            raw["server_configured_model"] = response["model"]
            turn = self.request("turn/start", {"threadId": self.active_thread,
                "model": model, "effort": self.effort,
                "input": [{"type": "text", "text": json.dumps(input_payload, ensure_ascii=False),
                           "text_elements": []}],
                "outputSchema": project_codex_output_schema(output_schema)},
                timeout=max(1, deadline-time.monotonic()))
            self.active_turn = turn["turn"]["id"]
            final_messages = {}
            while True:
                message = self.pending.popleft() if self.pending else self.receive(deadline)
                raw["rpc_events"].append(message)
                name, params = message.get("method"), message.get("params", {})
                if params.get("threadId") != self.active_thread:
                    continue
                if name in {"item/started", "item/completed"}:
                    item = params["item"]
                    require(item["type"] in {"userMessage", "agentMessage", "reasoning"},
                            "tool or unknown activity violates isolated experiment: " + item["type"])
                    if name == "item/completed" and item["type"] == "agentMessage":
                        final_messages[item["id"]] = item
                elif name == "thread/tokenUsage/updated":
                    tokens = params["tokenUsage"]["total"]  # Fresh one-turn thread: includes all response usage.
                    raw["usage"] = {"input_tokens": tokens["inputTokens"],
                        "output_tokens": tokens["outputTokens"],
                        "reasoning_output_tokens": tokens["reasoningOutputTokens"],
                        "cached_input_tokens": tokens["cachedInputTokens"]}
                elif name == "turn/completed":
                    require(params["turn"]["id"] == self.active_turn, "turn identity mismatch")
                    for item in params["turn"].get("items", []):
                        require(item["type"] in {"userMessage", "agentMessage", "reasoning"}, "unexpected completed tool")
                        if item["type"] == "agentMessage":
                            final_messages[item["id"]] = item
                    raw["turn_status"] = params["turn"]["status"]
                    raw["provider_error"] = params["turn"].get("error")
                    if raw["turn_status"] != "completed":
                        raise RuntimeError("provider turn failed: " + json.dumps(raw["provider_error"], ensure_ascii=False))
                    raw["return_code"] = 0
                    break
            finals = [i for i in final_messages.values() if i.get("phase") in (None, "final_answer")]
            require(bool(finals), "no final assistant message")
            raw["output_text"] = finals[-1]["text"]
        except Exception as exc:
            failure = exc
            if self.on_failure is not None:
                self.on_failure(str(exc))
            if isinstance(exc, (TimeoutError, EOFError, InterruptedError)):
                self.healthy = False
            if self.active_thread and self.active_turn:
                try:
                    self.send({"id": "cancel-" + str(self.call_count), "method": "turn/interrupt",
                        "params": {"threadId": self.active_thread, "turnId": self.active_turn}})
                except Exception:
                    pass
        finally:
            if self.active_thread and not self.abort.is_set():
                try:
                    self.release(self.active_thread)
                    raw["context_released"] = True
                except Exception as exc:
                    self.healthy = False
                    failure = failure or exc
                    raw["cleanup_error"] = str(exc)
            self.active_thread = self.active_turn = None
            raw["latency_seconds"] = time.monotonic() - started
            if raw["usage"]:
                raw["events"].append({"type": "turn.completed", "usage": raw["usage"]})
        if failure:
            raise CodexCLIError(str(failure), raw_response=raw, retryable=False)
        return raw

    def close(self):
        if self.process is not None:
            self.abort.set()
            if self.process.poll() is None:
                try:
                    self.process.stdin.close()
                    self.process.wait(timeout=3)
                except (OSError, subprocess.TimeoutExpired):
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait()
            self.process.stdout.close()
            try:
                self.process.stdin.close()
            except OSError:
                pass
        for name in ("stderr", "wire"):
            if hasattr(self, name):
                getattr(self, name).close()
        if hasattr(self, "temp"):
            self.temp.cleanup()
