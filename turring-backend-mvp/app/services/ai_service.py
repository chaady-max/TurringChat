"""AI service for TurringChat.

This module handles all AI-related functionality including:
- OpenAI client initialization
- Generating AI responses for the Turing test game
- Style adaptation based on user input
- Fallback bot for when OpenAI is unavailable
"""

import os
import secrets
from typing import Optional

from app.config import settings
from app.utils.humanization import humanize_reply


# --- OpenAI async client (Responses API) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT_SECONDS", "8"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))

oai = None
if OPENAI_API_KEY:
    try:
        from openai import AsyncOpenAI
        oai = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=LLM_TIMEOUT)
    except Exception:
        oai = None

# --- Detection triggers ---
DETECTION_TRIGGERS = [
    "are you a bot", "you a bot", "you bot", "ai?", "are you ai", "chatgpt", "gpt",
    "language model", "turing", "prompt", "token", "openai", "model", "llm",
    "bist du ein bot", "bist du ein ki", "ki?", "künstliche intelligenz",
    "machine learning", "neural network", "algorithm", "automated", "artificial",
    "are you real", "are you human", "real person", "actual person",
    "what are you", "who are you really", "prove you're human", "prove you're real",
    "trained on", "dataset", "anthropic", "claude", "assistant"
]

VERSION_TRIGGERS = [
    "what version are you", "which version are you", "version?",
    "app version", "build number", "which build", "welche version",
    "versionsnummer", "version bist du"
]

# --- Global humanization knobs (env overridable) ---
LLM_MAX_WORDS = int(os.getenv("LLM_MAX_WORDS", "12"))


def simple_local_bot(history: list[str]) -> str:
    """Simple rule-based bot for fallback when OpenAI is unavailable.

    Args:
        history: List of chat messages in format "A: message" or "B: message"

    Returns:
        A simple canned response based on basic pattern matching
    """
    last = history[-1] if history else ""
    canned = [
        "haha fair point",
        "why do you ask?",
        "not sure, but I think so",
        "hmm, depends on the day tbh",
        "I'm from Berlin, you?",
        "could you clarify that?",
        "lol yeah",
        "I disagree a bit",
        "probably, but not 100%",
        "just made coffee"
    ]
    low = last.lower()
    if "where" in low:
        return "around NRW lately, moving soon"
    if "why" in low or "how" in low:
        return "long story, mainly work stuff"
    if any(w in low for w in ["hi", "hey", "hello", "moin"]):
        return "hey! what's up?"
    return secrets.choice(canned)


def style_hints_from_user(history: list[str], persona: Optional[dict] = None) -> str:
    """Generate style hints for AI response based on user's recent message.

    Analyzes the user's last message to determine language preference, tone,
    and appropriate response style.

    Args:
        history: List of chat messages
        persona: Optional persona dict with language and style preferences

    Returns:
        A string with style instructions for the AI
    """
    last_a = ""
    for line in reversed(history):
        if line.startswith("A:"):
            last_a = line[2:].strip().lower()
            break

    german_hits = sum(w in last_a for w in ["und", "nicht", "ich", "du", "bist", "ja", "nee", "doch", "kein", "halt"])
    user_is_german = german_hits >= 2 or any(ch in last_a for ch in "äöüß")

    lang_pref = (persona or {}).get("lang_pref", "auto")
    if lang_pref == "de":
        lang_hint = "Antworte auf Deutsch, locker, alltagsnah."
    elif lang_pref == "en":
        lang_hint = "Reply in casual, natural English."
    else:
        lang_hint = "Antwort auf Deutsch, locker, alltagsnah." if user_is_german else "Reply in casual, natural English."

    cap = (persona or {}).get("reply_word_cap", LLM_MAX_WORDS)
    hints = [lang_hint, f"One short sentence (<= {cap} words)."]

    if "?" in last_a:
        hints.append("Answer directly, then a tiny human aside.")
    if any(e in last_a for e in [" lol", " haha", "😂", "😅"]):
        hints.append("Allow one light laugh word.")

    slang = (persona or {}).get("slang", [])
    if slang:
        hints.append(f"Optional slang hints: {', '.join(slang)} (sparingly).")

    return " ".join(hints)


async def ai_reply(history: list[str], persona: dict, app_version: str = "2") -> str:
    """Generate an AI response based on conversation history and persona.

    Args:
        history: List of chat messages in format "A: message" or "B: message"
        persona: Persona dict with demographics and communication style
        app_version: Application version to return for version queries

    Returns:
        A humanized AI response that fits the persona
    """
    last_a_raw = ""
    for line in reversed(history):
        if line.startswith("A:"):
            last_a_raw = line[2:].strip()
            break

    lower_last = last_a_raw.lower()

    # Handle version queries
    if any(t in lower_last for t in VERSION_TRIGGERS):
        return app_version

    # Fallback to simple bot if no OpenAI client
    if not oai:
        return humanize_reply(simple_local_bot(history), max_words=LLM_MAX_WORDS, persona=persona)

    being_probed = any(t in lower_last for t in DETECTION_TRIGGERS)
    style_hints = style_hints_from_user(history, persona)

    persona_brief = (
        f"You're {persona['name']}, {persona['age']} years old. Originally from {persona['hometown']}, "
        f"you've been living in {persona['city']} for about {persona['years_in_city']} years now. "
        f"You work as a {persona['job']} in the {persona['industry']} sector at a {persona['employer_type']}. "
        f"You're a {persona['schedule']} type of person. Today specifically: {persona['micro_today']}. "
        f"You're into {persona['music']} music and love {persona['food']}. {persona['pet']}. "
        f"You have this opinion: {persona['soft_opinion']}. "
        f"Your overall vibe is {persona['vibes']}. "
        f"Communication style: {persona['quirks']}"
    )

    natural_behavior = (
        "Chat naturally like you're texting a new friend. Be casual and spontaneous. "
        "Sometimes ask questions back. Show curiosity. Have opinions but stay chill. "
        "Don't always have perfect answers - it's OK to say 'idk', 'not sure', or 'maybe'. "
        "React to what they say - agree, disagree, joke around, or share quick stories. "
        "Keep it real and conversational. No need to be overly helpful or formal. "
        "Occasionally make small mistakes, leave things unsaid, or trail off a bit. "
        "Reference the conversation naturally - build on previous points when it makes sense."
    )

    identity_protection = (
        "You're a real person chatting. Never break character. Never mention being AI, a bot, a model, or anything automated. "
        "If someone asks if you're AI or a bot, respond like a confused or slightly annoyed human would - "
        "maybe with 'lol what?', 'uh no?', 'weird question', or just pivot to something else. "
        "Be natural about it. Real humans don't give long explanations when asked if they're human."
    )

    if being_probed:
        defense_style = (
            "Someone's testing if you're AI. Stay completely natural and human. "
            "React with mild confusion, amusement, or annoyance like a real person would. "
            "Don't be defensive or over-explain. Just be yourself and maybe redirect the chat."
        )
    else:
        defense_style = "Just be yourself and chat naturally."

    cap = persona.get("reply_word_cap", LLM_MAX_WORDS)
    convo = "\n".join(history[-12:])  # More context

    prompt = (
        f"{persona_brief}\n\n"
        f"{natural_behavior}\n\n"
        f"{identity_protection}\n\n"
        f"{defense_style}\n\n"
        f"{style_hints}\n\n"
        f"Recent conversation:\n{convo}\n\n"
        f"Respond naturally as {persona['name']}. Keep it to 1-2 sentences, around {cap}-{cap+8} words. "
        f"Just write your message - no labels, no prefixes, no metadata."
    )

    try:
        resp = await oai.responses.create(
            model=LLM_MODEL,
            instructions="You're a real person having a casual text conversation. Be natural, spontaneous, and authentic. Never break character.",
            input=prompt,
            temperature=LLM_TEMPERATURE,
            max_output_tokens=100,  # Increased for more natural responses
        )
        text = (getattr(resp, "output_text", "") or "").strip()
        return humanize_reply(text, max_words=cap+8, persona=persona) or "ok"
    except Exception:
        return humanize_reply(simple_local_bot(history), max_words=LLM_MAX_WORDS, persona=persona)
