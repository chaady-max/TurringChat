import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Import routers
from app.routers import health, pool, matchmaking, websocket

# =========================
# App version (answers "what version are you")
# =========================
APP_VERSION = "2"

# --- .env support ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

APP_ENV = os.getenv("APP_ENV", "dev")
CORS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
MATCH_WINDOW_SECS = float(os.getenv("MATCH_WINDOW_SECS", "10"))

# ------------------------------------------------------------------------------
# FastAPI + static
# ------------------------------------------------------------------------------
app = FastAPI(title="Turring Backend MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_here = os.path.dirname(__file__)
_static_root = os.path.join(os.path.dirname(_here), "static")
if not os.path.isdir(_static_root):
    os.makedirs(_static_root, exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_root), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = os.path.join(_static_root, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("""
<!doctype html><meta charset="utf-8"><title>Turring MVP</title>
<h1>Turring MVP</h1>
<p>Static dev client missing. Place <code>static/index.html</code> in the project.</p>
""".strip())


# ------------------------------------------------------------------------------
# Include routers
# ------------------------------------------------------------------------------
app.include_router(health.router)
app.include_router(pool.router)
app.include_router(matchmaking.router)
app.include_router(websocket.router)
