"""Game session service for TurringChat.

This module handles the game session logic including:
- Running AI vs Human games
- Running Human vs Human games
- Managing WebSocket communication
- Turn management and timeouts
- Score calculation
"""

import asyncio
import json
import os
import random
import time
from typing import Any, Optional

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from app.models.game import GameState
from app.models.conversation import ConversationSession
from app.services.ai_service import ai_reply
from app.services.matchmaking_service import commit_selection
from app.services.conversation_logger import logger as conversation_logger
from app.utils.websocket_utils import ws_send
from app.utils.mood import analyze_user_style, update_mood


# --- Game scoring constants ---
ROUND_LIMIT_SECS = 5 * 60  # 5 minutes total
TURN_LIMIT_SECS = 30  # 30 seconds per turn
SCORE_CORRECT = 100
SCORE_WRONG = -200
SCORE_TIMEOUT_WIN = 100

# --- Humanization timing ---
HUMANIZE_MIN_DELAY = float(os.getenv("HUMANIZE_MIN_DELAY", "0.6"))
HUMANIZE_MAX_DELAY = float(os.getenv("HUMANIZE_MAX_DELAY", "1.6"))

# --- App version ---
APP_VERSION = os.getenv("APP_VERSION", "2")


async def run_game_ai(ws: WebSocket, preset_commit: Optional[dict[str, Any]] = None):
    """Run an AI vs Human game session.

    Args:
        ws: WebSocket connection for player A
        preset_commit: Optional preset commit-reveal data for fairness verification
    """
    game = GameState(ws_a=ws, ws_b=None, opponent_type="AI", preset_commit=preset_commit)

    # Create conversation log session
    import uuid
    session_id = f"ai_{str(uuid.uuid4())[:8]}_{int(time.time())}"
    conversation = ConversationSession(
        session_id=session_id,
        started_at=time.time(),
        opponent_type="ai",
        persona_name=game.persona.get("name", "Unknown"),
        persona_details=game.persona
    )

    await ws_send(
        ws,
        "match_start",
        role="A",
        commit_hash=game.commit_hash,
        round_seconds=ROUND_LIMIT_SECS,
        turn_seconds=TURN_LIMIT_SECS,
        opponent="AI",
        persona=game.persona.get("name", ""),
        version=APP_VERSION,
    )
    game.reset_turn_deadline()

    async def ticker():
        """Background task that sends tick updates and handles turn timeouts."""
        try:
            while not game.ended and game.time_left_round() > 0:
                await asyncio.sleep(1)
                payload = {"round_left": game.time_left_round(), "turn_left": game.time_left_turn(), "turn": game.turn}
                await ws_send(game.ws_a, "tick", **payload)
                if game.time_left_turn() <= 0:
                    winner = "B" if game.turn == "A" else "A"
                    if winner == "A":
                        game.score_a += SCORE_TIMEOUT_WIN
                    await ws_send(
                        game.ws_a, "end",
                        reason="timeout", winner=winner,
                        score_delta=game.score_a,
                        reveal=game.reveal(),
                    )
                    game.ended = True
                    break
        except Exception:
            pass

    ticker_task = asyncio.create_task(ticker())

    try:
        while not game.ended:
            raw = await ws.receive_text()
            try:
                data = json.loads(raw)
            except Exception:
                continue

            mtype = data.get("type")

            if mtype == "chat" and game.turn == "A":
                text = (data.get("text") or "").strip()[:280]
                if not text:
                    continue
                game.history.append(f"A: {text}")
                # Log player message
                conversation.add_message("player", text, time.time())

                # Analyze user style and update AI mood
                style = analyze_user_style(text)
                game.ai_mood = update_mood(game.ai_mood, style)

                game.swap_turn()

                if not game.ended:
                    await ws_send(game.ws_a, "typing", who="B", on=True)
                    pre = random.uniform(HUMANIZE_MIN_DELAY, HUMANIZE_MAX_DELAY)
                    pre = min(pre, max(0.0, game.time_left_turn() - 5.0))
                    if pre > 0:
                        await asyncio.sleep(pre)

                    reply = await ai_reply(game.history[-8:], game.persona, APP_VERSION, game.ai_mood)

                    post = min(0.6, max(0.0, game.time_left_turn() - 1.5))
                    if post > 0:
                        await asyncio.sleep(random.uniform(0.1, post))

                    await ws_send(game.ws_a, "typing", who="B", on=False)
                    game.history.append(f"B: {reply}")
                    # Log AI message
                    conversation.add_message("opponent", reply, time.time())
                    await ws_send(game.ws_a, "chat", from_="B", text=reply)
                    game.swap_turn()

            if mtype == "guess":
                guess = (data.get("guess") or "").upper()
                correct = (guess == "AI")
                delta = SCORE_CORRECT if correct else SCORE_WRONG
                game.score_a += delta

                # Log guess outcome
                conversation.set_outcome(player_guessed=guess.lower(), guess_correct=correct)

                await ws_send(
                    game.ws_a, "end",
                    reason="guess", correct=correct,
                    score_delta=game.score_a,
                    reveal=game.reveal(),
                )
                game.ended = True
                break

            if mtype == "state":
                await ws_send(
                    game.ws_a, "state",
                    opponent="AI",
                    round_left=game.time_left_round(),
                    turn_left=game.time_left_turn(),
                    turn=game.turn,
                )

    except WebSocketDisconnect:
        pass
    finally:
        if not ticker_task.done():
            ticker_task.cancel()

        # Save conversation log
        conversation.end_session(time.time())
        try:
            conversation_logger.save_session(conversation)
        except Exception as e:
            print(f"Error saving conversation {session_id}: {e}")


async def run_game_h2h(game: GameState):
    """Run a Human vs Human game session.

    Both clients see themselves as "A" and their opponent as "B".

    Args:
        game: GameState with both ws_a and ws_b connections
    """
    # Initial kickoff sends (guarded)
    ok_a = await ws_send(
        game.ws_a,
        "match_start",
        role="A",
        commit_hash=game.commit_hash,
        round_seconds=ROUND_LIMIT_SECS,
        turn_seconds=TURN_LIMIT_SECS,
        opponent="HUMAN",
        persona=game.persona.get("name", ""),
        version=APP_VERSION,
    )
    ok_b = await ws_send(
        game.ws_b,
        "match_start",
        role="A",
        commit_hash=game.commit_hash,
        round_seconds=ROUND_LIMIT_SECS,
        turn_seconds=TURN_LIMIT_SECS,
        opponent="HUMAN",
        persona=game.persona.get("name", ""),
        version=APP_VERSION,
    )

    # If one side already dropped, fallback the alive one to AI to avoid instant end.
    if not ok_a or not ok_b:
        alive_ws = game.ws_a if ok_a else (game.ws_b if ok_b else None)
        if alive_ws:
            h, n, ts = commit_selection("AI")
            preset = {"opponent_type": "AI", "hash": h, "nonce": n, "ts": ts}
            await run_game_ai(alive_ws, preset_commit=preset)
        game.ended = True
        return

    game.reset_turn_deadline()

    q: asyncio.Queue[tuple[str, dict]] = asyncio.Queue()

    async def reader(tag: str, ws: WebSocket):
        """Read messages from a WebSocket and put them in the queue."""
        try:
            while not game.ended:
                raw = await ws.receive_text()
                try:
                    data = json.loads(raw)
                except Exception:
                    continue
                await q.put((tag, data))
        except WebSocketDisconnect:
            if not game.ended:
                winner = "A" if tag == "B" else "B"
                if winner == "A":
                    game.score_a += SCORE_TIMEOUT_WIN
                else:
                    game.score_b += SCORE_TIMEOUT_WIN
                await ws_send(game.ws_a, "end", reason="disconnect", winner=winner,
                              score_delta=game.score_a, reveal=game.reveal())
                await ws_send(game.ws_b, "end", reason="disconnect", winner=winner,
                              score_delta=game.score_b, reveal=game.reveal())
                game.ended = True

    ta = asyncio.create_task(reader("A", game.ws_a))
    tb = asyncio.create_task(reader("B", game.ws_b))

    async def ticker():
        """Background task that sends tick updates and handles turn timeouts."""
        try:
            while not game.ended and game.time_left_round() > 0:
                await asyncio.sleep(1)
                payload = {"round_left": game.time_left_round(), "turn_left": game.time_left_turn(), "turn": game.turn}
                await ws_send(game.ws_a, "tick", **payload)
                await ws_send(game.ws_b, "tick", **payload)
                if game.time_left_turn() <= 0:
                    winner = "B" if game.turn == "A" else "A"
                    if winner == "A":
                        game.score_a += SCORE_TIMEOUT_WIN
                    else:
                        game.score_b += SCORE_TIMEOUT_WIN
                    await ws_send(game.ws_a, "end", reason="timeout", winner=winner,
                                  score_delta=game.score_a, reveal=game.reveal())
                    await ws_send(game.ws_b, "end", reason="timeout", winner=winner,
                                  score_delta=game.score_b, reveal=game.reveal())
                    game.ended = True
                    break
        except Exception:
            pass

    tt = asyncio.create_task(ticker())

    try:
        while not game.ended:
            tag, data = await q.get()
            mtype = data.get("type")

            if mtype == "chat":
                if (tag == "A" and game.turn == "A") or (tag == "B" and game.turn == "B"):
                    text = (data.get("text") or "").strip()[:280]
                    if not text:
                        continue
                    game.history.append(f"{tag}: {text}")
                    other = game.ws_b if tag == "A" else game.ws_a
                    me = game.ws_a if tag == "A" else game.ws_b
                    await ws_send(other, "chat", from_="B", text=text)
                    await ws_send(me, "chat", from_="A", text=text)
                    game.swap_turn()

            if mtype == "guess":
                guess = (data.get("guess") or "").upper()
                correct = (guess == "HUMAN")
                delta = SCORE_CORRECT if correct else SCORE_WRONG
                if tag == "A":
                    game.score_a += delta
                else:
                    game.score_b += delta
                await ws_send(game.ws_a, "end", reason="guess", correct=correct,
                              score_delta=game.score_a, reveal=game.reveal())
                await ws_send(game.ws_b, "end", reason="guess", correct=correct,
                              score_delta=game.score_b, reveal=game.reveal())
                game.ended = True
                break

            if mtype == "state":
                who = game.ws_a if tag == "A" else game.ws_b
                await ws_send(
                    who, "state",
                    opponent="HUMAN",
                    round_left=game.time_left_round(),
                    turn_left=game.time_left_turn(),
                    turn=game.turn,
                )

    finally:
        if not tt.done():
            tt.cancel()
        if not ta.done():
            ta.cancel()
        if not tb.done():
            tb.cancel()
