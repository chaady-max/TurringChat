# Turing Chat Backend MVP

A sophisticated, production-ready FastAPI backend for a 5-minute Turing test game where players chat with either a human or an AI and must guess their opponent's nature.

[![CI](https://github.com/chaady-max/TurringChat/workflows/CI/badge.svg)](https://github.com/chaady-max/TurringChat/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.5-009688.svg)](https://fastapi.tiangolo.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🎯 Features

### Core Gameplay
- **5-minute rounds** with 30-second turn timers (server-authoritative)
- **Real-time WebSocket communication** at `/ws/match`
- **Human vs AI or Human vs Human matching**
- **Cryptographic commit-reveal** mechanism for fairness verification
- **Scoring system**: +100 correct guess, -200 incorrect, +100 opponent timeout

### AI Sophistication
- **GPT-4o-mini powered** responses with fallback to local bot
- **Advanced humanization**: typing indicators, realistic delays, typos
- **Dynamic persona generation**: unique personalities with backgrounds, jobs, hobbies
- **Adaptive conversation style**: matches user language (English/German)
- **Detection resistance**: sophisticated deflection of AI detection attempts

### Developer Experience
- **Modern FastAPI** architecture with Pydantic validation
- **Modular codebase**: utilities, config, models separated
- **Type hints** throughout for better IDE support
- **Docker & Docker Compose** for easy deployment
- **CI/CD** with GitHub Actions (linting, testing, Docker builds)
- **Development tools**: black, ruff, mypy, pytest configured

## 🚀 Quick Start

### Option 1: Local Development

```bash
# 1. Clone and navigate
git clone https://github.com/chaady-max/TurringChat.git
cd TurringChat/turring-backend-mvp

# 2. Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (optional)

# 5. Run the server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### Option 2: Docker (Recommended for Production)

```bash
# 1. Clone repository
git clone https://github.com/chaady-max/TurringChat.git
cd TurringChat/turring-backend-mvp

# 2. Create .env file
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# 3. Start with Docker Compose
docker-compose up --build

# The app will be available at http://localhost:8001
```

### Access the Application

Open http://127.0.0.1:8001 in your browser to access the built-in dev client.

- Click **"Start Match"** to join the matchmaking pool
- Chat with your opponent
- Click **"Guess HUMAN"** or **"Guess AI"** when ready
- Timer shows remaining time (green → orange → red as time runs out)

## 📁 Project Structure

```
turring-backend-mvp/
├── app/
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Pydantic settings (NEW)
│   ├── constants.py         # Game constants & types (NEW)
│   ├── utils/               # Utility functions (NEW)
│   │   ├── commit_reveal.py # Cryptographic fairness
│   │   ├── humanization.py  # Text humanization (typos, emojis)
│   │   └── websocket_utils.py # Safe WebSocket operations
│   ├── models/              # Data models (future expansion)
│   ├── routers/             # API routers (future expansion)
│   └── services/            # Business logic (future expansion)
├── static/
│   └── index.html           # Built-in dev client
├── tests/                   # Test suite (expandable)
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── Dockerfile               # Production Docker image
├── docker-compose.yml       # Local development stack
├── pyproject.toml           # Tool configurations
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
└── README.md                # This file
```

## ⚙️ Configuration

All settings are configured via environment variables in `.env`:

### Required Settings
```bash
# Optional - without it, uses local fallback bot
OPENAI_API_KEY=sk-...
```

### LLM Configuration
```bash
LLM_MODEL=gpt-4o-mini           # OpenAI model to use
LLM_TIMEOUT_SECONDS=10          # API timeout
LLM_TEMPERATURE=0.85            # Response creativity (0.0-2.0)
```

### Humanization Settings
```bash
LLM_MAX_WORDS=18                # Max words per response
HUMANIZE_TYPO_RATE=0.22         # Probability of typos (0.0-1.0)
HUMANIZE_MAX_TYPOS=2            # Max typos per message
HUMANIZE_MIN_DELAY=0.8          # Min typing delay (seconds)
HUMANIZE_MAX_DELAY=2.5          # Max typing delay (seconds)
```

### Game Configuration
```bash
ROUND_LIMIT_SECS=300            # 5 minute rounds
TURN_LIMIT_SECS=30              # 30 second turns
H2H_PROB=0.5                    # Human-to-human matching probability
MATCH_WINDOW_SECS=10            # Matchmaking window
```

### Infrastructure
```bash
APP_ENV=dev                     # Environment (dev/staging/prod)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
REDIS_URL=redis://localhost:6379/0  # Future use
```

## 🔌 API Endpoints

### HTTP Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dev client UI |
| GET | `/health` | Health check |
| GET | `/pool/count` | View waiting pool size |
| POST | `/pool/join` | Join matchmaking pool |
| POST | `/pool/leave` | Leave matchmaking pool |
| POST | `/match/request` | Request a match |
| GET | `/match/status?ticket=...` | Check match status |
| POST | `/match/cancel` | Cancel pending match |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/match?ticket=...` | AI opponent game session |
| `/ws/pair?pair_id=...&ticket=...` | Human vs Human game session |

## 🎮 Game Flow

### 1. Join Pool
```bash
curl -X POST http://localhost:8001/pool/join \
  -H "Content-Type: application/json" \
  -d '{"token": null}'
```

### 2. Request Match
```bash
curl -X POST http://localhost:8001/match/request \
  -H "Content-Type: application/json" \
  -d '{"token": "your-token"}'
```

### 3. Check Status
```bash
curl "http://localhost:8001/match/status?ticket=your-ticket"
```

### 4. Connect WebSocket
Connect to the `ws_url` returned in the match status response.

## 🔐 Commit-Reveal Fairness

The server uses cryptographic commitment to ensure fairness:

1. **On match start**: Server sends `commit_hash = SHA256(opponent|nonce|timestamp)`
2. **During game**: Opponent type remains secret
3. **On game end**: Server reveals `{opponent, nonce, timestamp}`
4. **Client verification**: Recompute hash to verify server didn't cheat

Example verification (JavaScript):
```javascript
const crypto = require('crypto');
const payload = `${opponent}|${nonce}|${timestamp}`;
const hash = crypto.createHash('sha256').update(payload).digest('hex');
console.log(hash === commit_hash ? 'Fair!' : 'Cheated!');
```

## 🧪 Development

### Install Development Dependencies
```bash
pip install -r requirements-dev.txt
```

### Run Tests
```bash
pytest --cov=app --cov-report=html
```

### Code Formatting
```bash
black app/ tests/
```

### Linting
```bash
ruff check app/ tests/
```

### Type Checking
```bash
mypy app/
```

### Run All Checks
```bash
black --check app/ tests/ && \
ruff check app/ tests/ && \
mypy app/ && \
pytest --cov=app
```

## 🐳 Docker Deployment

### Build Production Image
```bash
docker build -t turring-chat:latest .
```

### Run with Docker
```bash
docker run -d \
  -p 8001:8001 \
  -e OPENAI_API_KEY=sk-... \
  --name turring-chat \
  turring-chat:latest
```

### Development with Docker Compose
```bash
# Start services (app + Redis)
docker-compose up

# Rebuild after code changes
docker-compose up --build

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## 🤖 AI Behavior Customization

The AI uses sophisticated techniques to appear human:

### Persona Generation
Each game generates a unique persona with:
- Name, age, location, job
- Hobbies, music taste, food preferences
- Communication style (casual, sarcastic, enthusiastic, etc.)
- Micro-context (e.g., "spilled coffee earlier", "gym after work")

### Humanization Techniques
1. **Typos**: Keyboard-neighbor replacements, adjacent swaps, dropped characters
2. **Casual formatting**: Missing punctuation, lowercase starts, emoji
3. **Natural delays**: 0.8-2.5 seconds before responding
4. **Imperfect knowledge**: Says "idk", "not sure", "maybe"
5. **Questions back**: Shows curiosity about the player
6. **Conversational references**: Builds on previous messages

### Detection Resistance
When asked "are you AI?", the bot:
- Responds like a confused human: "lol what?", "uh no?", "weird question"
- Doesn't over-explain (real humans don't write essays defending humanity)
- May pivot conversation naturally

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Find process using port 8001
lsof -nP -iTCP:8001 -sTCP:LISTEN

# Kill it
kill -9 <PID>

# Or use a different port
uvicorn app.main:app --port 8002
```

### Module Not Found Errors
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### OpenAI API Errors
- Check your API key is valid
- Ensure you have credits in your OpenAI account
- Without API key, app falls back to simple local bot

### Docker Permission Issues
```bash
# If Docker requires sudo, add user to docker group
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

## 📊 Performance Notes

- In-memory state (pool, pending matches, pairs) resets on server restart
- For production with multiple instances, implement Redis-backed state
- Current setup handles ~100 concurrent games per instance
- WebSocket connections are lightweight (~10KB per connection)

## 🛣️ Roadmap

- [x] **Phase 1**: ✅ Modular utilities and configuration
- [ ] **Phase 2**: Extract routers, services, models into separate files
- [ ] **Phase 3**: Comprehensive test suite (>80% coverage)
- [ ] **Phase 4**: Frontend modernization (React/Vue)
- [ ] **Phase 5**: Redis-backed state for multi-instance deployment
- [ ] **Phase 6**: Prometheus metrics and observability
- [ ] **Phase 7**: Admin dashboard for monitoring games
- [ ] **Phase 8**: Machine learning for improved AI detection resistance

## 📝 License

This project is part of the TurringChat application.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters (`black`, `ruff`, `pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ using FastAPI, Python, and OpenAI GPT-4**
