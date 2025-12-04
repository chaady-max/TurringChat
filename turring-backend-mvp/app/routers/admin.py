"""Admin router for TurringChat.

Provides admin authentication and game monitoring endpoints.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Response
from pydantic import BaseModel

from app.models.game import pending_requests, pending_lock, pairs, pairs_lock, pool_tokens, pool_lock
from app.services.admin_service import verify_admin_password, create_admin_token, verify_admin_token
from app.services.conversation_logger import logger as conversation_logger
from app.services.openai_usage_tracker import tracker as usage_tracker

router = APIRouter(prefix="/admin", tags=["admin"])


class LoginRequest(BaseModel):
    """Admin login request."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Admin login response."""
    access_token: str
    token_type: str = "bearer"


def get_current_admin(authorization: Optional[str] = Header(None)) -> dict:
    """Verify admin token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = parts[1]
    payload = verify_admin_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload


@router.post("/login", response_model=LoginResponse)
async def admin_login(request: LoginRequest):
    """Admin login endpoint.

    Args:
        request: Login credentials

    Returns:
        JWT access token

    Raises:
        HTTPException: If credentials are invalid
    """
    if not verify_admin_password(request.username, request.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_admin_token(request.username)

    return LoginResponse(access_token=token)


@router.get("/verify")
async def verify_token(admin: dict = Header(default=None, alias="Authorization")):
    """Verify admin token is valid.

    Args:
        admin: Admin user from token

    Returns:
        Verification status
    """
    # The dependency will raise 401 if invalid
    get_current_admin(admin)
    return {"valid": True}


@router.get("/stats")
async def get_stats(authorization: Optional[str] = Header(None)):
    """Get real-time game statistics.

    Requires admin authentication.

    Args:
        authorization: Authorization header

    Returns:
        Game statistics
    """
    get_current_admin(authorization)

    async with pool_lock:
        pool_count = len(pool_tokens)

    async with pending_lock:
        pending_count = len(pending_requests)
        pending_list = [
            {
                "ticket": ticket,
                "status": req.status,
                "token": req.token,
                "created_at": req.now,
                "expires_at": req.expires_at
            }
            for ticket, req in pending_requests.items()
        ]

    async with pairs_lock:
        active_pairs_count = len(pairs)
        pairs_list = [
            {
                "pair_id": pair_id,
                "a_ticket": pair.a_ticket,
                "b_ticket": pair.b_ticket,
                "a_connected": pair.a_ws is not None,
                "b_connected": pair.b_ws is not None
            }
            for pair_id, pair in pairs.items()
        ]

    return {
        "pool_count": pool_count,
        "pending_matches": pending_count,
        "active_games": active_pairs_count,
        "pending_requests": pending_list,
        "active_pairs": pairs_list
    }


@router.get("/pending")
async def get_pending_requests(authorization: Optional[str] = Header(None)):
    """Get all pending match requests.

    Requires admin authentication.

    Args:
        authorization: Authorization header

    Returns:
        List of pending requests
    """
    get_current_admin(authorization)

    async with pending_lock:
        pending_list = [
            {
                "ticket": ticket,
                "status": req.status,
                "token": req.token,
                "created_at": req.now,
                "expires_at": req.expires_at,
                "opponent_type": req.status.replace("ready_", "") if req.status.startswith("ready_") else None
            }
            for ticket, req in pending_requests.items()
        ]

    return {"pending_requests": pending_list}


@router.get("/pairs")
async def get_active_pairs(authorization: Optional[str] = Header(None)):
    """Get all active game pairs.

    Requires admin authentication.

    Args:
        authorization: Authorization header

    Returns:
        List of active pairs
    """
    get_current_admin(authorization)

    async with pairs_lock:
        pairs_list = [
            {
                "pair_id": pair_id,
                "a_ticket": pair.a_ticket,
                "b_ticket": pair.b_ticket,
                "a_connected": pair.a_ws is not None,
                "b_connected": pair.b_ws is not None
            }
            for pair_id, pair in pairs.items()
        ]

    return {"active_pairs": pairs_list}


@router.get("/pool")
async def get_pool_info(authorization: Optional[str] = Header(None)):
    """Get player pool information.

    Requires admin authentication.

    Args:
        authorization: Authorization header

    Returns:
        Pool statistics
    """
    get_current_admin(authorization)

    async with pool_lock:
        tokens_list = list(pool_tokens)

    return {
        "count": len(tokens_list),
        "tokens": tokens_list
    }


@router.get("/sessions")
async def get_conversation_sessions(
    authorization: Optional[str] = Header(None),
    limit: int = 50,
    offset: int = 0
):
    """Get list of conversation sessions.

    Requires admin authentication.

    Args:
        authorization: Authorization header
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip

    Returns:
        List of session summaries
    """
    get_current_admin(authorization)

    sessions = conversation_logger.list_sessions(limit=limit, offset=offset)
    total = conversation_logger.get_sessions_count()

    return {
        "sessions": sessions,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/sessions/{session_id}")
async def get_conversation_session(
    session_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get full details of a conversation session.

    Requires admin authentication.

    Args:
        session_id: Session ID
        authorization: Authorization header

    Returns:
        Full conversation session details
    """
    get_current_admin(authorization)

    session = conversation_logger.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session.to_dict()


@router.get("/sessions/analytics")
async def get_sessions_analytics(authorization: Optional[str] = Header(None)):
    """Get analytics from logged sessions.

    Requires admin authentication.

    Args:
        authorization: Authorization header

    Returns:
        Analytics data
    """
    get_current_admin(authorization)

    return conversation_logger.analyze_sessions()


@router.get("/usage/summary")
async def get_usage_summary(
    authorization: Optional[str] = Header(None),
    days: Optional[int] = None
):
    """Get OpenAI API usage summary.

    Requires admin authentication.

    Args:
        authorization: Authorization header
        days: Optional number of days to look back (default: current month)

    Returns:
        Usage summary with totals and breakdown by model
    """
    get_current_admin(authorization)

    return usage_tracker.get_summary(days=days)


@router.get("/usage/daily")
async def get_usage_daily(
    authorization: Optional[str] = Header(None),
    days: int = 7
):
    """Get daily OpenAI API usage statistics.

    Requires admin authentication.

    Args:
        authorization: Authorization header
        days: Number of days to include (default: 7)

    Returns:
        List of daily usage statistics
    """
    get_current_admin(authorization)

    return {"daily_stats": usage_tracker.get_daily_stats(days=days)}


@router.get("/usage/recent")
async def get_usage_recent(
    authorization: Optional[str] = Header(None),
    limit: int = 50
):
    """Get recent OpenAI API calls.

    Requires admin authentication.

    Args:
        authorization: Authorization header
        limit: Maximum number of calls to return (default: 50)

    Returns:
        List of recent API calls with token usage and costs
    """
    get_current_admin(authorization)

    return {"recent_calls": usage_tracker.get_recent_calls(limit=limit)}
