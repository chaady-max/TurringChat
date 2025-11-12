Here’s an updated README.md you can drop in:

Turring Backend MVP (FastAPI)

A minimal, runnable backend for the Turring Test App with a built-in dev client.

What it is

A 5-minute, chat-based Turing-test game. You (A) are matched with either a human or an AI. You can guess HUMAN or AI at any time. The server commits cryptographically to your opponent type at the start and reveals it at the end.

Features
	•	FastAPI + WebSocket at /ws/match
	•	5 min round timer, 30s per-turn timer (server-authoritative)
	•	Guess anytime (HUMAN/AI). Scoring: +100 correct, −200 wrong, +100 if the opponent times out
	•	Commit–reveal fairness: server sends commit_hash at start and reveals (opponent|nonce|ts) at end
	•	Typing indicator + small human-like delays
	•	Stealth AI opponent with human personas (short, casual replies, occasional tiny typos)
	•	Simple HTML dev client served at / (Enter-to-send, color-coded turn timer)

Quick start

# 1) go into the project folder
cd turring-backend-mvp

# 2) create & activate a venv
python3.11 -m venv .venv
source .venv/bin/activate

# 3) install deps
pip install -r requirements.txt

# 4) configure environment
cp .env.example .env
# edit .env and set at least:
#   OPENAI_API_KEY=sk-...        # optional; without it, the local fallback bot is used

# 5) run the server (hot reload on code changes)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

Open http://127.0.0.1:8001
	•	Click Start Match
	•	Type a message (press Enter to send)
	•	Watch the typing… indicator, try to guess HUMAN/AI
	•	Timer badge colors: green (20–30s), orange (10–20s), red (0–10s)

Configuration (.env)

All of these are optional; sensible defaults are provided.

# Core
OPENAI_API_KEY=sk-...          # if empty → local heuristic bot is used
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=8
LLM_TEMPERATURE=0.7

# Humanization knobs (feel free to tune)
LLM_MAX_WORDS=12               # keep replies super short
HUMANIZE_TYPO_RATE=0.18        # 18% messages get tiny imperfections
HUMANIZE_MAX_TYPOS=2
HUMANIZE_MIN_DELAY=0.6         # seconds, pre-reply jitter
HUMANIZE_MAX_DELAY=1.6

# CORS, Redis (for future multi-user matchmaking)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
REDIS_URL=redis://localhost:6379/0

Changing .env doesn’t always trigger a reload. Either restart the server, or run uvicorn with a watcher:

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001 --reload-include ".env"



Dev client controls (served at /)
	•	Enter sends the message (or click Send)
	•	Guess HUMAN / Guess AI ends the game early
	•	Timer badge color shifts as time runs down (green → orange → red)

Endpoints
	•	GET / — dev client
	•	GET /health — simple health check (JSON)
	•	GET /static/* — static assets for the dev client
	•	WS /ws/match — game socket

Commit–reveal fairness
	•	On match_start, server sends commit_hash = sha256(opponent|nonce|ts_ms).
	•	On end, server reveals {opponent, nonce, ts_ms} so you can verify the hash in the client log.

Notes & Roadmap
	•	Human-vs-human pairing is in-process only in this MVP. Use Redis to back a cross-process waiting pool when you want real multi-user matchmaking.
	•	AI replies are constrained to short, casual lines and sometimes include tiny typos for realism—while never admitting it’s AI.
	•	Turn limit is 30s (both backend enforcement and frontend display).
	•	The round ends on guess, timeout, or after 5 minutes.

PyCharm run config (optional)
	•	Interpreter: …/turring-backend-mvp/.venv/bin/python
	•	Run → Edit Configurations → + → Python
	•	Script path: uvicorn
	•	Parameters: app.main:app --reload --host 127.0.0.1 --port 8001
	•	Working directory: the project folder (turring-backend-mvp)

Troubleshooting
	•	ModuleNotFoundError: fastapi/uvicorn — your venv isn’t active. Run source .venv/bin/activate and reinstall deps.
	•	Address already in use — another process has the port.

lsof -nP -iTCP:8001 -sTCP:LISTEN
kill -9 <PID>

or use a different port: --port 8002.

	•	No OpenAI replies — set OPENAI_API_KEY in .env. Without it, the local fallback bot answers.

That’s it—start the server, open the page, and play!
