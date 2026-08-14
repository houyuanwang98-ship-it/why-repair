"""M4 controller compatibility profile with explicit pending lifecycle evidence."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .contracts import ContractError
from .m4_controller import M4CounterexampleController


M4_CONTROLLER_PROFILE_V03 = "m4-counterexample-controller-v0.3"
VERIFICATION_ENVIRONMENT = {
    "engine": "python_stdlib_ast_fraction_exact",
    "engine_profile": "m4-counterexample-person-b-v0.1",
    "max_ast_nodes": 128,
    "max_expression_length": 2000,
    "max_integer_bits": 4096,
    "max_abs_exponent": 64,
    "timeout_policy": "no_external_process; deterministic resource bounds fail to undetermined",
}


class M4CounterexampleControllerV03(M4CounterexampleController):
    """Add an observable pending state while retaining the frozen v0.2 logic."""

    def process(self, context_id: str, certificate: dict[str, Any], **kwargs) -> dict[str, Any]:
        if context_id not in self._contexts:
            raise ContractError(f"unknown M4 context: {context_id}")
        certificate_id = certificate.get("certificate_id") if isinstance(certificate, dict) else None
        if not isinstance(certificate_id, str) or not certificate_id.strip():
            raise ContractError("candidate certificate_id must be nonempty")
        self._events.append({
            "event": "m4_pending_verification",
            "context_id": context_id,
            "certificate_id": certificate_id,
            "state": "pending_verification",
        })
        try:
            result = super().process(context_id, certificate, **kwargs)
        except Exception as exc:
            self._events.append({
                "event": "m4_candidate_rejected_before_terminal_result",
                "context_id": context_id,
                "certificate_id": certificate_id,
                "state": "rejected",
                "error_type": type(exc).__name__,
            })
            raise
        enriched = {
            **result,
            "profile_version": M4_CONTROLLER_PROFILE_V03,
            "verification_environment": deepcopy(VERIFICATION_ENVIRONMENT),
        }
        self._results[certificate_id] = deepcopy(enriched)
        return deepcopy(enriched)

    def snapshot(self) -> dict[str, Any]:
        snapshot = super().snapshot()
        snapshot["profile_version"] = M4_CONTROLLER_PROFILE_V03
        snapshot["verification_environment"] = deepcopy(VERIFICATION_ENVIRONMENT)
        return snapshot
