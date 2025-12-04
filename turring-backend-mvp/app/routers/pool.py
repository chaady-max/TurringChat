"""Player pool management router for TurringChat."""

import secrets
from typing import Optional

from fastapi import APIRouter, Body

from app.models.game import pool_tokens, pool_lock

router = APIRouter(prefix="/pool", tags=["pool"])


@router.get("/count")
async def pool_count():
    """Get the current number of players in the pool."""
    async with pool_lock:
        return {"count": len(pool_tokens)}


@router.post("/join")
async def pool_join(token: Optional[str] = Body(None, embed=True)):
    """Join the matchmaking pool.

    If no token is provided, a new one is created.
    Returns the token and whether it was newly created.
    """
    created = False
    async with pool_lock:
        if not token:
            token = secrets.token_hex(8)
            created = True
        pool_tokens.add(token)
        count = len(pool_tokens)
    return {"ok": True, "token": token, "created": created, "count": count}


@router.post("/leave")
async def pool_leave(token: Optional[str] = Body(None, embed=True)):
    """Leave the matchmaking pool."""
    async with pool_lock:
        if token and token in pool_tokens:
            pool_tokens.remove(token)
    return {"ok": True}
