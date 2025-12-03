"""Constants and type definitions for the Turing Chat application."""

from typing import Literal

# Type definitions
Role = Literal["A", "B"]
OpponentType = Literal["HUMAN", "AI"]

# Game constants
SCORE_CORRECT = 100
SCORE_WRONG = -200
SCORE_TIMEOUT_WIN = 100

# QWERTY keyboard neighbors for typo generation
QWERTY_NEIGHBORS = {
    "a": "qs",
    "b": "vn",
    "c": "xv",
    "d": "sf",
    "e": "wr",
    "f": "dg",
    "g": "fh",
    "h": "gj",
    "i": "uo",
    "j": "hk",
    "k": "jl",
    "l": "k",
    "m": "n",
    "n": "bm",
    "o": "ip",
    "p": "o",
    "q": "wa",
    "r": "et",
    "s": "ad",
    "t": "ry",
    "u": "yi",
    "v": "cb",
    "w": "qe",
    "x": "zc",
    "y": "tu",
    "z": "x",
}

# AI detection trigger words/phrases
DETECTION_TRIGGERS = [
    "are you a bot",
    "you a bot",
    "you bot",
    "ai?",
    "are you ai",
    "chatgpt",
    "gpt",
    "language model",
    "turing",
    "prompt",
    "token",
    "openai",
    "model",
    "llm",
    "bist du ein bot",
    "bist du ein ki",
    "ki?",
    "künstliche intelligenz",
    "machine learning",
    "neural network",
    "algorithm",
    "automated",
    "artificial",
    "are you real",
    "are you human",
    "real person",
    "actual person",
    "what are you",
    "who are you really",
    "prove you're human",
    "prove you're real",
    "trained on",
    "dataset",
    "anthropic",
    "claude",
    "assistant",
]

# Version query trigger words/phrases
VERSION_TRIGGERS = [
    "what version are you",
    "which version are you",
    "version?",
    "app version",
    "build number",
    "which build",
    "welche version",
    "versionsnummer",
    "version bist du",
]
