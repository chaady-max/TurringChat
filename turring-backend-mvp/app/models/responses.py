"""Pydantic response models for TurringChat API."""

from typing import Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    env: str
    version: str


class PoolCountResponse(BaseModel):
    """Response showing number of players in the pool."""
    count: int


class PoolJoinResponse(BaseModel):
    """Response after joining the pool."""
    ok: bool
    token: str
    created: bool
    count: int


class PoolLeaveResponse(BaseModel):
    """Response after leaving the pool."""
    ok: bool


class MatchRequestResponse(BaseModel):
    """Response after requesting a match."""
    ok: bool
    ticket: str
    expires_at: float
    window_secs: int


class MatchStatusResponse(BaseModel):
    """Response showing match status."""
    status: str  # pending | ready_ai | ready_h2h | canceled | gone
    ws_url: Optional[str] = None
    commit_hash: Optional[str] = None


class MatchCancelResponse(BaseModel):
    """Response after canceling a match."""
    ok: bool
