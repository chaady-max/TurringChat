"""Matchmaking router for TurringChat."""

import secrets
import time
from typing import Optional

from fastapi import APIRouter, Body, Query

from app.models.game import PendingReq, pending_requests, pending_lock
from app.services.matchmaking_service import (
    try_pair_with_oldest,
    resolve_match_status,
    cancel_match as cancel_match_service,
)

router = APIRouter(prefix="/match", tags=["matchmaking"])


@router.post("/request")
async def match_request(token: Optional[str] = Body(None, embed=True)):
    """Request a match from the matchmaking system.

    Creates a pending request and attempts to pair with another waiting player.
    Returns a ticket that can be used to poll for match status.
    """
    now = time.time()
    ticket = secrets.token_hex(10)
    req = PendingReq(ticket=ticket, token=token, now=now)
    async with pending_lock:
        pending_requests[ticket] = req
        await try_pair_with_oldest(ticket)
    return {"ticket": ticket, "expires_at": req.expires_at}


@router.get("/status")
async def match_status(ticket: str = Query(...)):
    """Check the status of a pending match request.

    Returns one of: gone, pending, ready_ai, ready_h2h, canceled
    If ready, includes the WebSocket URL and commit hash for verification.
    """
    async with pending_lock:
        req = pending_requests.get(ticket)
        if not req:
            return {"status": "gone"}

        return await resolve_match_status(req)


@router.post("/cancel")
async def match_cancel(ticket: str = Body(..., embed=True)):
    """Cancel a pending match request.

    If the request was paired for H2H, converts the other player to AI.
    """
    return await cancel_match_service(ticket)
