"""Deterministic orchestration for the dual-agent proof-auditing harness."""

from .contracts import ContractError, validate_contract
from .controller import (
    DualAgentController,
    InvalidTransitionError,
    StaleVersionError,
)

__all__ = [
    "ContractError",
    "DualAgentController",
    "InvalidTransitionError",
    "StaleVersionError",
    "validate_contract",
]

