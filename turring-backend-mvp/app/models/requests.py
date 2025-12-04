"""Pydantic request models for TurringChat API."""

from typing import Optional

from pydantic import BaseModel


class PoolJoinRequest(BaseModel):
    """Request to join the matchmaking pool."""
    token: Optional[str] = None


class PoolLeaveRequest(BaseModel):
    """Request to leave the matchmaking pool."""
    token: Optional[str] = None


class MatchRequestBody(BaseModel):
    """Request to start matchmaking."""
    token: Optional[str] = None


class MatchCancelRequest(BaseModel):
    """Request to cancel a pending match."""
    ticket: str
