"""WebSocket router for TurringChat game sessions."""

from typing import Optional

from fastapi import APIRouter, WebSocket, Query

from app.models.game import (
    GameState,
    pending_requests,
    pending_lock,
    pairs,
    pairs_lock,
    pool_tokens,
    pool_lock,
)
from app.services.game_service import run_game_ai, run_game_h2h
from app.services.matchmaking_service import commit_selection
from app.utils.websocket_utils import ws_alive

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/match")
async def ws_match(ws: WebSocket, ticket: Optional[str] = Query(None)):
    """WebSocket endpoint for AI vs Human games.

    Connects a player to an AI opponent based on their match ticket.
    """
    await ws.accept()

    # Find the resolved ticket (ready_ai) and build preset commit
    preset = None
    tok = None
    lang_pref = "en"
    if ticket:
        async with pending_lock:
            req = pending_requests.get(ticket)
            if req and req.status == "ready_ai":
                preset = {"opponent_type": "AI", "hash": req.commit_hash, "nonce": req.commit_nonce, "ts": req.commit_ts, "lang": req.lang_pref}
                lang_pref = req.lang_pref
                tok = req.token

    # remove from visible pool on match start
    if tok:
        async with pool_lock:
            pool_tokens.discard(tok)

    await run_game_ai(ws, preset_commit=preset, lang_pref=lang_pref)


@router.websocket("/ws/pair")
async def ws_pair(ws: WebSocket, pair_id: str = Query(...), ticket: str = Query(...)):
    """WebSocket endpoint for Human vs Human games.

    Pairs two players together for a game session.
    Both players connect to this endpoint with their pair_id and ticket.
    """
    await ws.accept()
    # Attach to pair; when both present, run H2H and clear
    async with pairs_lock:
        pair = pairs.get(pair_id)
        if not pair or (pair.a_ticket != ticket and pair.b_ticket != ticket):
            await ws.close()
            return
        if pair.a_ticket == ticket:
            pair.a_ws = ws
        else:
            pair.b_ws = ws

        ready = pair.a_ws is not None and pair.b_ws is not None

    # Clean pool visibility for both tickets
    async with pending_lock:
        a_req = pending_requests.get(pair.a_ticket) if pair else None
        b_req = pending_requests.get(pair.b_ticket) if pair else None
    async with pool_lock:
        for req in (a_req, b_req):
            if req and req.token:
                pool_tokens.discard(req.token)

    if ready:
        # Preflight: make sure both sockets are still alive
        if not (ws_alive(pair.a_ws) and ws_alive(pair.b_ws)):
            # Fallback the alive one to AI match
            alive_ws = pair.a_ws if ws_alive(pair.a_ws) else (pair.b_ws if ws_alive(pair.b_ws) else None)
            if alive_ws:
                # Get lang_pref from whichever player is alive
                alive_ticket = pair.a_ticket if ws_alive(pair.a_ws) else pair.b_ticket
                alive_lang = "en"
                async with pending_lock:
                    alive_req = pending_requests.get(alive_ticket)
                    if alive_req:
                        alive_lang = alive_req.lang_pref
                h, n, ts = commit_selection("AI")
                preset = {"opponent_type": "AI", "hash": h, "nonce": n, "ts": ts, "lang": alive_lang}
                await run_game_ai(alive_ws, preset_commit=preset, lang_pref=alive_lang)
            async with pairs_lock:
                pairs.pop(pair_id, None)
            return

        # Build preset commit from either req (both HUMAN)
        async with pending_lock:
            a_req2 = pending_requests.get(pair.a_ticket)
            if a_req2 and a_req2.commit_hash:
                preset = {"opponent_type": "HUMAN", "hash": a_req2.commit_hash, "nonce": a_req2.commit_nonce, "ts": a_req2.commit_ts}
            else:
                # fallback (shouldn't happen): create a fresh HUMAN commit
                h, n, ts = commit_selection("HUMAN")
                preset = {"opponent_type": "HUMAN", "hash": h, "nonce": n, "ts": ts}

        game = GameState(ws_a=pair.a_ws, ws_b=pair.b_ws, opponent_type="HUMAN", preset_commit=preset)
        await run_game_h2h(game)

        # cleanup
        async with pairs_lock:
            pairs.pop(pair_id, None)
