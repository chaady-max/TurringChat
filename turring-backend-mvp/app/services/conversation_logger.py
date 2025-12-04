"""Conversation logging service for TurringChat.

Manages storage and retrieval of chat sessions.
"""

import os
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from app.models.conversation import ConversationSession

# Storage directory for conversation logs
LOGS_DIR = os.getenv("CONVERSATION_LOGS_DIR", "conversation_logs")


class ConversationLogger:
    """Service for logging and retrieving conversations."""

    def __init__(self, logs_dir: str = LOGS_DIR):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)

    def _get_session_path(self, session_id: str) -> Path:
        """Get file path for a session."""
        return self.logs_dir / f"{session_id}.json"

    def save_session(self, session: ConversationSession):
        """Save a conversation session to disk."""
        path = self._get_session_path(session.session_id)
        with open(path, 'w') as f:
            f.write(session.to_json())

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve a conversation session by ID."""
        path = self._get_session_path(session_id)
        if not path.exists():
            return None

        with open(path, 'r') as f:
            return ConversationSession.from_json(f.read())

    def list_sessions(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """List all conversation sessions with metadata (newest first)."""
        sessions = []

        for path in sorted(self.logs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)

                # Return minimal metadata for list view
                sessions.append({
                    "session_id": data["session_id"],
                    "started_at": data["started_at"],
                    "ended_at": data.get("ended_at"),
                    "opponent_type": data.get("opponent_type", "unknown"),
                    "persona_name": data.get("persona_name"),
                    "total_messages": data.get("total_messages", 0),
                    "player_guessed": data.get("player_guessed"),
                    "guess_correct": data.get("guess_correct"),
                    "reveal_happened": data.get("reveal_happened", False)
                })
            except Exception as e:
                print(f"Error loading session {path.name}: {e}")
                continue

        # Apply pagination
        return sessions[offset:offset + limit]

    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session."""
        path = self._get_session_path(session_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def get_sessions_count(self) -> int:
        """Get total number of logged sessions."""
        return len(list(self.logs_dir.glob("*.json")))

    def analyze_sessions(self) -> dict:
        """Generate analytics from logged sessions."""
        total = 0
        ai_games = 0
        human_games = 0
        correct_guesses = 0
        incorrect_guesses = 0
        total_messages = 0

        for path in self.logs_dir.glob("*.json"):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)

                total += 1
                total_messages += data.get("total_messages", 0)

                if data.get("opponent_type") == "ai":
                    ai_games += 1
                elif data.get("opponent_type") == "human":
                    human_games += 1

                if data.get("reveal_happened"):
                    if data.get("guess_correct"):
                        correct_guesses += 1
                    else:
                        incorrect_guesses += 1

            except Exception:
                continue

        return {
            "total_sessions": total,
            "ai_opponent_sessions": ai_games,
            "human_opponent_sessions": human_games,
            "correct_guesses": correct_guesses,
            "incorrect_guesses": incorrect_guesses,
            "total_messages": total_messages,
            "avg_messages_per_session": total_messages / total if total > 0 else 0,
            "guess_accuracy": correct_guesses / (correct_guesses + incorrect_guesses) if (correct_guesses + incorrect_guesses) > 0 else 0
        }


# Global logger instance
logger = ConversationLogger()
