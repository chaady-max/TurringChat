"""Game state models for TurringChat."""

import asyncio
import secrets
import time
from typing import Any, Dict, Optional

from fastapi import WebSocket

from app.constants import OpponentType, Role
from app.utils.commit_reveal import commit_assignment
from app.utils.mood import MoodState


# In-memory state stores
pool_tokens: set[str] = set()
pool_lock = asyncio.Lock()

pending_requests: Dict[str, "PendingReq"] = {}
pending_lock = asyncio.Lock()

pairs: Dict[str, "PairSlot"] = {}
pairs_lock = asyncio.Lock()


class PendingReq:
    """Represents a pending match request."""

    __slots__ = ("ticket", "token", "created_at", "expires_at", "status", "reserved_ai",
                 "pair_id", "opponent_type", "commit_hash", "commit_nonce", "commit_ts")

    def __init__(self, ticket: str, token: Optional[str], now: float):
        from app.config import settings

        self.ticket = ticket
        self.token = token
        self.created_at = now
        self.expires_at = now + settings.match_window_secs
        self.status: str = "pending"  # pending | ready_ai | ready_h2h | canceled
        self.reserved_ai: bool = False
        self.pair_id: Optional[str] = None
        # commit–reveal (filled when resolved)
        self.opponent_type: Optional[OpponentType] = None
        self.commit_hash: Optional[str] = None
        self.commit_nonce: Optional[str] = None
        self.commit_ts: Optional[int] = None


class PairSlot:
    """Represents a paired human vs human match."""

    __slots__ = ("pair_id", "a_ticket", "b_ticket", "a_ws", "b_ws", "deadline")

    def __init__(self, pair_id: str, a_ticket: str, b_ticket: str):
        self.pair_id = pair_id
        self.a_ticket = a_ticket
        self.b_ticket = b_ticket
        self.a_ws: Optional[WebSocket] = None
        self.b_ws: Optional[WebSocket] = None
        self.deadline = time.time() + 20.0  # if one never connects, time out


class GameState:
    """Represents the state of an active game session."""

    def __init__(
        self,
        ws_a: WebSocket,
        ws_b: Optional[WebSocket],
        opponent_type: OpponentType,
        preset_commit: Optional[dict[str, Any]] = None,
        generate_persona_func: Optional[Any] = None,
    ):
        from app.config import settings

        self.ws_a = ws_a
        self.ws_b = ws_b
        self.opponent_type = opponent_type
        self.started_at = int(time.time())
        self.round_deadline = self.started_at + settings.round_limit_secs
        self.turn_deadline: Optional[int] = None
        self.turn: Role = "A"
        self.history: list[str] = []
        self.score_a = 0
        self.score_b = 0
        self.ended = False

        # AI mood state (for adaptive conversation)
        self.ai_mood = MoodState()

        # Persona per match
        self.nonce = secrets.token_hex(16)
        self.commit_ts = int(time.time() * 1000)
        self.commit_hash = commit_assignment(self.opponent_type, self.nonce, self.commit_ts)
        seed = f"{self.opponent_type}:{self.commit_hash}:{self.nonce}"

        # Import generate_persona here to avoid circular import
        if generate_persona_func is None:
            from app.services.persona_service import generate_persona
            generate_persona_func = generate_persona
        self.persona = generate_persona_func(seed)

        # If preset commit is provided (from /match resolution), use it
        if preset_commit:
            self.opponent_type = preset_commit["opponent_type"]  # type: ignore
            self.nonce = preset_commit["nonce"]                  # type: ignore
            self.commit_ts = preset_commit["ts"]                 # type: ignore
            self.commit_hash = preset_commit["hash"]             # type: ignore
            seed = f"{self.opponent_type}:{self.commit_hash}:{self.nonce}"
            self.persona = generate_persona_func(seed)

    def time_left_round(self) -> int:
        """Calculate seconds remaining in the round."""
        return max(0, self.round_deadline - int(time.time()))

    def reset_turn_deadline(self):
        """Reset the turn timer."""
        from app.config import settings
        self.turn_deadline = int(time.time()) + settings.turn_limit_secs

    def time_left_turn(self) -> int:
        """Calculate seconds remaining in the current turn."""
        from app.config import settings
        if self.turn_deadline is None:
            return settings.turn_limit_secs
        return max(0, self.turn_deadline - int(time.time()))

    def swap_turn(self):
        """Switch to the other player's turn."""
        self.turn = "B" if self.turn == "A" else "A"
        self.reset_turn_deadline()

    def reveal(self) -> dict:
        """Return the commit-reveal data for fairness verification."""
        return {
            "opponent_type": self.opponent_type,
            "nonce": self.nonce,
            "commit_ts": self.commit_ts
        }
