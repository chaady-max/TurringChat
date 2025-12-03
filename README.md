# TurringChat

A sophisticated, production-ready 5-minute Turing test game where players chat with either a human or an AI and must guess their opponent's nature.

[![CI](https://github.com/chaady-max/TurringChat/workflows/CI/badge.svg)](https://github.com/chaady-max/TurringChat/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.5-009688.svg)](https://fastapi.tiangolo.com)

## 🎯 What is TurringChat?

TurringChat is a FastAPI-based backend for a chat-based Turing test game. Players engage in 5-minute conversations and must determine whether they're talking to a human or an AI. The game features:

- **Real-time WebSocket communication** for instant messaging
- **Cryptographic commit-reveal** mechanism ensuring fairness
- **Advanced AI humanization** with realistic typing patterns, typos, and conversational style
- **Dynamic persona generation** creating unique AI personalities each game
- **Modern architecture** with Docker support, CI/CD, and comprehensive testing

## 🚀 Quick Start

### Option 1: Local Development

```bash
# 1. Clone and navigate to backend
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

## 🎮 How to Play

1. Open http://127.0.0.1:8001 in your browser
2. Click **"Start Match"** to join the matchmaking pool
3. Chat with your opponent (press Enter to send messages)
4. Try to determine if they're human or AI
5. Click **"Guess HUMAN"** or **"Guess AI"** when ready
6. See the reveal and your score!

**Scoring:**
- +100 points for correct guess
- -200 points for incorrect guess
- +100 points if opponent times out

## ✨ Key Features

### Sophisticated AI Behavior
- **GPT-4o-mini powered** responses with fallback to local bot
- **Enhanced humanization**:
  - Typing indicators with realistic delays (0.8-2.5 seconds)
  - Natural typos (22% rate, keyboard-neighbor replacements)
  - Casual formatting with emojis and internet slang
  - Conversational memory and context awareness
- **Dynamic personas**: Each game generates unique AI personalities with:
  - Name, age, location, occupation
  - Hobbies, music taste, food preferences
  - Communication style (casual, sarcastic, enthusiastic, etc.)
  - Micro-context (daily situations for authenticity)
- **Detection resistance**: Sophisticated deflection of AI detection attempts with 23 different trigger phrases

### Modern Architecture
- **Modular codebase**: Utilities, config, models cleanly separated
- **Type safety**: Full type hints throughout with mypy checking
- **Configuration management**: Pydantic Settings for robust config handling
- **Development tools**: black, ruff, mypy, pytest configured and ready
- **Docker support**: Production-ready Dockerfile and docker-compose.yml
- **CI/CD pipeline**: GitHub Actions for automated testing and builds

### Game Integrity
- **Server-authoritative timing**: 5-minute rounds, 30-second turns
- **Cryptographic fairness**: SHA256 commit-reveal prevents server cheating
- **WebSocket-based**: Real-time bidirectional communication at `/ws/match`

## 📁 Project Structure

```
TurringChat/
└── turring-backend-mvp/       # FastAPI Backend
    ├── app/
    │   ├── main.py            # FastAPI app initialization
    │   ├── config.py          # Pydantic settings
    │   ├── constants.py       # Game constants & types
    │   └── utils/             # Utility functions
    │       ├── commit_reveal.py
    │       ├── humanization.py
    │       └── websocket_utils.py
    ├── static/
    │   └── index.html         # Built-in dev client
    ├── tests/                 # Test suite
    ├── .github/workflows/     # CI/CD pipelines
    ├── Dockerfile             # Production image
    ├── docker-compose.yml     # Local dev stack
    └── README.md              # Detailed documentation
```

## ⚙️ Configuration

Key environment variables (see turring-backend-mvp/.env.example for complete list):

```bash
# Optional - without it, uses local fallback bot
OPENAI_API_KEY=sk-...

# LLM Configuration
LLM_MODEL=gpt-4o-mini           # OpenAI model to use
LLM_TEMPERATURE=0.85            # Response creativity (0.0-2.0)
LLM_MAX_WORDS=18                # Max words per response

# Humanization Settings
HUMANIZE_TYPO_RATE=0.22         # Probability of typos (0.0-1.0)
HUMANIZE_MAX_TYPOS=2            # Max typos per message
HUMANIZE_MIN_DELAY=0.8          # Min typing delay (seconds)
HUMANIZE_MAX_DELAY=2.5          # Max typing delay (seconds)

# Game Configuration
ROUND_LIMIT_SECS=300            # 5 minute rounds
TURN_LIMIT_SECS=30              # 30 second turns
H2H_PROB=0.5                    # Human-to-human matching probability
```

## 🔌 API Endpoints

### HTTP Endpoints
- `GET /` - Dev client UI
- `GET /health` - Health check
- `GET /pool/count` - View waiting pool size
- `POST /pool/join` - Join matchmaking pool
- `POST /match/request` - Request a match
- `GET /match/status?ticket=...` - Check match status

### WebSocket Endpoints
- `/ws/match?ticket=...` - AI opponent game session
- `/ws/pair?pair_id=...&ticket=...` - Human vs Human game session

## 🧪 Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests with coverage
pytest --cov=app --cov-report=html

# Code formatting
black app/ tests/

# Linting
ruff check app/ tests/

# Type checking
mypy app/

# Run all checks
black --check app/ tests/ && \
ruff check app/ tests/ && \
mypy app/ && \
pytest --cov=app
```

## 🐳 Docker Deployment

```bash
# Build production image
docker build -t turring-chat:latest ./turring-backend-mvp

# Run with Docker
docker run -d \
  -p 8001:8001 \
  -e OPENAI_API_KEY=sk-... \
  --name turring-chat \
  turring-chat:latest

# Development with Docker Compose
cd turring-backend-mvp
docker-compose up --build
```

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

## 🚨 Troubleshooting

### Port Already in Use
```bash
lsof -nP -iTCP:8001 -sTCP:LISTEN
kill -9 <PID>
# Or use a different port
uvicorn app.main:app --port 8002
```

### Module Not Found Errors
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### OpenAI API Errors
- Check your API key is valid
- Ensure you have credits in your OpenAI account
- Without API key, app falls back to simple local bot

## 🛣️ Roadmap

- [x] ✅ Modular utilities and configuration
- [ ] Extract routers, services, models into separate files
- [ ] Comprehensive test suite (>80% coverage)
- [ ] Frontend modernization (React/Vue)
- [ ] Redis-backed state for multi-instance deployment
- [ ] Prometheus metrics and observability
- [ ] Admin dashboard for monitoring games
- [ ] Machine learning for improved AI detection resistance

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

For detailed backend documentation, see [turring-backend-mvp/README.md](turring-backend-mvp/README.md)
