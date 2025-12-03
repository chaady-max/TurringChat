"""Cryptographic commit-reveal mechanism for fair game outcomes."""

import hashlib
import secrets
import time
from typing import Tuple

from app.constants import OpponentType


def commit_selection(opponent_type: OpponentType) -> Tuple[str, str, int]:
    """
    Create a cryptographic commitment to an opponent type selection.

    Args:
        opponent_type: The opponent type to commit to ("HUMAN" or "AI")

    Returns:
        Tuple of (commit_hash, nonce, timestamp_ms)
    """
    nonce = secrets.token_hex(16)
    ts_ms = int(time.time() * 1000)
    h = hashlib.sha256(f"{opponent_type}|{nonce}|{ts_ms}".encode("utf-8")).hexdigest()
    return h, nonce, ts_ms


def commit_assignment(assign_value: str, nonce: str, ts_ms: int) -> str:
    """
    Create a cryptographic commitment hash for a given value.

    Args:
        assign_value: The value to commit to
        nonce: Random nonce for security
        ts_ms: Timestamp in milliseconds

    Returns:
        SHA256 hash of the commitment
    """
    payload = f"{assign_value}|{nonce}|{ts_ms}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
