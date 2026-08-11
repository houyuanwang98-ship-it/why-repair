"""Deterministic orchestration for the dual-agent proof-auditing harness."""

from .contracts import ContractError, validate_contract
from .controller import (
    DualAgentController,
    InvalidTransitionError,
    StaleVersionError,
)
from .integration import CheckerIntegrationError, ingest_person_a_result

__all__ = [
    "ContractError",
    "DualAgentController",
    "InvalidTransitionError",
    "StaleVersionError",
    "CheckerIntegrationError",
    "ingest_person_a_result",
    "validate_contract",
]

