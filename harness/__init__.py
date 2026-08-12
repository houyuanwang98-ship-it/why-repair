"""Deterministic orchestration for the dual-agent proof-auditing harness."""

from .contracts import ContractError, validate_contract
from .controller import (
    DualAgentController,
    InvalidTransitionError,
    StaleVersionError,
)
from .integration import CheckerIntegrationError, ingest_person_a_result
from .m3_alpha import AdapterResponse, M3AlphaError, evaluate_dataset, evaluate_module, run_module

__all__ = [
    "ContractError",
    "DualAgentController",
    "InvalidTransitionError",
    "StaleVersionError",
    "CheckerIntegrationError",
    "AdapterResponse",
    "M3AlphaError",
    "evaluate_dataset",
    "evaluate_module",
    "ingest_person_a_result",
    "run_module",
    "validate_contract",
]

