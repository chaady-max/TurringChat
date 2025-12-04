"""Matchmaking service for TurringChat.

This module handles the matchmaking logic including:
- Pairing players for human-to-human games
- Reserving AI opponents
- Commit-reveal cryptography for fair opponent assignment
- Match resolution based on pool availability
"""

import hashlib
import os
import random
import secrets
import time
from typing import Optional

from app.constants import OpponentType
from app.models.game import (
    PendingReq,
    PairSlot,
    pending_requests,
    pending_lock,
    pairs,
    pairs_lock,
)


# --- Matchmaking configuration ---
H2H_PROB = float(os.getenv("H2H_PROB", "0.5"))  # Probability of H2H vs AI match


def commit_selection(opponent_type: OpponentType) -> tuple[str, str, int]:
    """Create a cryptographic commitment for opponent type selection.

    Args:
        opponent_type: Either "HUMAN" or "AI"

    Returns:
        Tuple of (commit_hash, nonce, timestamp_ms)
    """
    nonce = secrets.token_hex(16)
    ts_ms = int(time.time() * 1000)
    h = hashlib.sha256(f"{opponent_type}|{nonce}|{ts_ms}".encode("utf-8")).hexdigest()
    return h, nonce, ts_ms


async def try_pair_with_oldest(cur_ticket: str):
    """Attempt to pair current ticket with the oldest pending request.

    Looks for the oldest pending request (not reserved, not expired) and performs
    a probabilistic coin flip with H2H_PROB to decide between human-to-human pairing
    or AI reservation.

    Args:
        cur_ticket: The current ticket to attempt pairing for
    """
    now = time.time()
    candidate_ticket = None
    oldest_t = 1e30

    for t, req in pending_requests.items():
        if t == cur_ticket:
            continue
        if req.status != "pending":
            continue
        if req.reserved_ai:
            continue
        if req.expires_at <= now:
            continue
        if req.created_at < oldest_t:
            oldest_t = req.created_at
            candidate_ticket = t

    if not candidate_ticket:
        return  # nobody overlapped

    heads = (random.random() < H2H_PROB)  # True => H2H now
    if heads:
        # Pair H2H now
        pair_id = secrets.token_hex(8)
        a = pending_requests[candidate_ticket]
        b = pending_requests[cur_ticket]
        a.status = "ready_h2h"
        b.status = "ready_h2h"
        a.pair_id = pair_id
        b.pair_id = pair_id
        # selection commits
        for req in (a, b):
            h, n, ts = commit_selection("HUMAN")
            req.opponent_type = "HUMAN"
            req.commit_hash = h
            req.commit_nonce = n
            req.commit_ts = ts
        async with pairs_lock:
            pairs[pair_id] = PairSlot(pair_id, a_ticket=candidate_ticket, b_ticket=cur_ticket)
    else:
        # Reserve AI for exactly one of the two (uniformly)
        chosen = pending_requests[cur_ticket] if random.random() < 0.5 else pending_requests[candidate_ticket]
        chosen.reserved_ai = True  # chosen one flips to AI at expiry or immediate resolve


def time_left(req: PendingReq) -> float:
    """Calculate time remaining until request expires.

    Args:
        req: The pending request

    Returns:
        Seconds remaining (>= 0)
    """
    return max(0.0, req.expires_at - time.time())


async def resolve_match_status(req: PendingReq) -> dict:
    """Resolve the status of a match request.

    Args:
        req: The pending request to resolve

    Returns:
        Dictionary with status information including ws_url and commit_hash if ready
    """
    # Already resolved states
    if req.status == "ready_h2h":
        return {
            "status": "ready_h2h",
            "ws_url": f"/ws/pair?pair_id={req.pair_id}&ticket={req.ticket}",
            "commit_hash": req.commit_hash,
            "time_left": time_left(req),
        }

    if req.status == "ready_ai":
        return {
            "status": "ready_ai",
            "ws_url": f"/ws/match?ticket={req.ticket}",
            "commit_hash": req.commit_hash,
            "time_left": time_left(req),
        }

    if req.status == "canceled":
        return {"status": "canceled"}

    # Still pending
    tl = time_left(req)
    if tl > 0:
        return {"status": "pending", "time_left": tl}

    # Expired → resolve to AI
    if req.reserved_ai:
        req.status = "ready_ai"
        h, n, ts = commit_selection("AI")
        req.opponent_type = "AI"
        req.commit_hash = h
        req.commit_nonce = n
        req.commit_ts = ts
        return {
            "status": "ready_ai",
            "ws_url": f"/ws/match?ticket={req.ticket}",
            "commit_hash": req.commit_hash,
            "time_left": 0.0,
        }

    # nobody paired and not reserved → AI by default at expiry
    req.status = "ready_ai"
    h, n, ts = commit_selection("AI")
    req.opponent_type = "AI"
    req.commit_hash = h
    req.commit_nonce = n
    req.commit_ts = ts
    return {
        "status": "ready_ai",
        "ws_url": f"/ws/match?ticket={req.ticket}",
        "commit_hash": req.commit_hash,
        "time_left": 0.0,
    }


async def cancel_match(ticket: str) -> dict:
    """Cancel a pending match request.

    If the request is in H2H pairing, converts the other player to AI immediately.

    Args:
        ticket: The ticket to cancel

    Returns:
        Dictionary with ok: True
    """
    async with pending_lock:
        req = pending_requests.get(ticket)
        if not req:
            return {"ok": True}

        if req.status == "pending":
            req.status = "canceled"
        elif req.status == "ready_h2h":
            # if paired, convert the other to AI immediately
            pid = req.pair_id
            if pid and pid in pairs:
                pair = pairs[pid]
                other_ticket = pair.b_ticket if pair.a_ticket == ticket else pair.a_ticket
                other = pending_requests.get(other_ticket)
                if other and other.status == "ready_h2h":
                    other.status = "ready_ai"
                    other.pair_id = None
                    h, n, ts = commit_selection("AI")
                    other.opponent_type = "AI"
                    other.commit_hash = h
                    other.commit_nonce = n
                    other.commit_ts = ts
                async with pairs_lock:
                    pairs.pop(pid, None)
            req.status = "canceled"

    return {"ok": True}
