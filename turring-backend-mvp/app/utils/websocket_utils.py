"""WebSocket utility functions for safe message sending."""

import json
from typing import Any, Optional

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState


async def ws_send(ws: WebSocket, kind: str, **payload: Any) -> bool:
    """
    Send a message through a WebSocket safely.

    Args:
        ws: The WebSocket connection
        kind: Message type identifier
        **payload: Additional message data

    Returns:
        True if send was successful, False otherwise
    """
    try:
        state = getattr(ws, "application_state", None)
        if state not in (None, WebSocketState.CONNECTED):
            return False
        await ws.send_text(json.dumps({"type": kind, **payload}))
        return True
    except (WebSocketDisconnect, RuntimeError):
        return False
    except Exception:
        return False


def ws_alive(ws: Optional[WebSocket]) -> bool:
    """
    Check if a WebSocket connection is alive.

    Args:
        ws: The WebSocket connection to check

    Returns:
        True if connection is alive and connected
    """
    return bool(
        ws and getattr(ws, "application_state", None) == WebSocketState.CONNECTED
    )
