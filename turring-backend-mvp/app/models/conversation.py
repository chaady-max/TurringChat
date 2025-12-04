"""Conversation logging models for TurringChat.

Stores chat sessions for admin review and AI improvement.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json


@dataclass
class Message:
    """A single chat message."""
    sender: str  # 'player', 'opponent', 'system'
    content: str
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "sender": self.sender,
            "content": self.content,
            "timestamp": self.timestamp
        }


@dataclass
class ConversationSession:
    """A complete chat session with metadata."""
    session_id: str  # pair_id or ticket
    started_at: float
    ended_at: Optional[float] = None
    opponent_type: str = "unknown"  # 'ai' or 'human'
    persona_name: Optional[str] = None
    persona_details: Optional[dict] = None
    messages: List[Message] = field(default_factory=list)

    # Game outcome
    player_guessed: Optional[str] = None  # 'ai' or 'human'
    guess_correct: Optional[bool] = None
    reveal_happened: bool = False

    # Metadata for analysis
    total_messages: int = 0
    player_message_count: int = 0
    opponent_message_count: int = 0
    avg_response_time: Optional[float] = None

    def add_message(self, sender: str, content: str, timestamp: float):
        """Add a message to the conversation."""
        msg = Message(sender, content, timestamp)
        self.messages.append(msg)
        self.total_messages += 1

        if sender == "player":
            self.player_message_count += 1
        elif sender == "opponent":
            self.opponent_message_count += 1

    def end_session(self, ended_at: float):
        """Mark session as ended."""
        self.ended_at = ended_at

    def set_outcome(self, player_guessed: str, guess_correct: bool):
        """Record game outcome."""
        self.player_guessed = player_guessed
        self.guess_correct = guess_correct
        self.reveal_happened = True

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "opponent_type": self.opponent_type,
            "persona_name": self.persona_name,
            "persona_details": self.persona_details,
            "messages": [msg.to_dict() for msg in self.messages],
            "player_guessed": self.player_guessed,
            "guess_correct": self.guess_correct,
            "reveal_happened": self.reveal_happened,
            "total_messages": self.total_messages,
            "player_message_count": self.player_message_count,
            "opponent_message_count": self.opponent_message_count,
            "avg_response_time": self.avg_response_time
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationSession":
        """Load from dictionary."""
        session = cls(
            session_id=data["session_id"],
            started_at=data["started_at"],
            ended_at=data.get("ended_at"),
            opponent_type=data.get("opponent_type", "unknown"),
            persona_name=data.get("persona_name"),
            persona_details=data.get("persona_details"),
            player_guessed=data.get("player_guessed"),
            guess_correct=data.get("guess_correct"),
            reveal_happened=data.get("reveal_happened", False),
            total_messages=data.get("total_messages", 0),
            player_message_count=data.get("player_message_count", 0),
            opponent_message_count=data.get("opponent_message_count", 0),
            avg_response_time=data.get("avg_response_time")
        )

        # Restore messages
        for msg_data in data.get("messages", []):
            session.messages.append(Message(**msg_data))

        return session

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ConversationSession":
        """Deserialize from JSON."""
        return cls.from_dict(json.loads(json_str))
