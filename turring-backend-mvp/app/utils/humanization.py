"""Text humanization utilities for making AI responses feel more natural."""

import random
import re
from typing import Dict, Optional

from app.constants import QWERTY_NEIGHBORS


def _limit_words(text: str, max_words: int) -> str:
    """Limit text to a maximum number of words."""
    words = text.strip().split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words])


def _swap_adjacent(s: str) -> str:
    """Swap two adjacent characters in the string."""
    if len(s) < 4:
        return s
    i = random.randint(1, len(s) - 2)
    if s[i].isalpha() and s[i + 1].isalpha():
        return s[:i] + s[i + 1] + s[i] + s[i + 2 :]
    return s


def _neighbor_replace(s: str) -> str:
    """Replace a character with a keyboard neighbor."""
    chars = list(s)
    idxs = [i for i, ch in enumerate(chars) if ch.isalpha()]
    if not idxs:
        return s
    i = random.choice(idxs)
    ch = chars[i].lower()
    if ch in QWERTY_NEIGHBORS and QWERTY_NEIGHBORS[ch]:
        rep = random.choice(QWERTY_NEIGHBORS[ch])
        if chars[i].isupper():
            rep = rep.upper()
        chars[i] = rep
    return "".join(chars)


def _drop_random_char(s: str) -> str:
    """Drop a random alphabetic character from the string."""
    letters = [i for i, ch in enumerate(s) if ch.isalpha()]
    if not letters:
        return s
    i = random.choice(letters)
    return s[:i] + s[i + 1 :]


def _humanize_typos(text: str, rate: float, max_typos: int = 2) -> str:
    """
    Inject random typos into text to simulate human typing errors.

    Args:
        text: The text to add typos to
        rate: Probability of adding typos (0.0-1.0)
        max_typos: Maximum number of typos to inject

    Returns:
        Text with typos injected
    """
    if not text or random.random() > rate:
        return text
    ops = [_swap_adjacent, _neighbor_replace, _drop_random_char]
    n = random.randint(1, max(1, max_typos))
    s = text
    for _ in range(n):
        s = random.choice(ops)(s)
    if random.random() < 0.25 and s and s[0].isalpha():
        s = s[0].lower() + s[1:]
    return s


def humanize_reply(
    text: str,
    max_words: int = 18,
    typo_rate: float = 0.22,
    max_typos: int = 2,
    persona: Optional[Dict] = None,
) -> str:
    """
    Humanize an AI-generated reply with typos, emojis, and casual formatting.

    Args:
        text: The reply text to humanize
        max_words: Maximum number of words to allow
        typo_rate: Probability of injecting typos
        max_typos: Maximum number of typos per message
        persona: Optional persona dict with customization options

    Returns:
        Humanized reply text
    """
    s = (text or "").strip()
    s = re.sub(r"[.!?]{2,}", ".", s)
    s = s.replace("\n", " ")
    cap = (
        min(max_words, int(persona.get("reply_word_cap", max_words)))
        if persona
        else max_words
    )
    s = _limit_words(s, cap + 8)  # Allow more flexibility
    if len(s) > 180:  # Increased from 120
        s = s[:180].rstrip()

    # More varied typo rate
    actual_typo_rate = (
        persona.get("typo_rate", typo_rate) if persona else typo_rate
    )
    s = _humanize_typos(s, rate=float(actual_typo_rate), max_typos=max_typos)

    if persona:
        emoji_pool = persona.get("emoji_pool", [])
        emoji_rate = float(persona.get("emoji_rate", 0.0))
        laughter = str(persona.get("laughter", "")).strip()
        filler = persona.get("filler_words", [])

        # Increased emoji usage
        if emoji_pool and random.random() < emoji_rate * 2:  # Double emoji rate
            s = (s + " " + random.choice(emoji_pool)).strip()

        # More frequent casual additions (increased from 0.05 to 0.15)
        if random.random() < 0.15:
            if laughter and random.random() < 0.5:
                s = f"{s} {laughter}"
            elif filler and random.random() < 0.6:
                fw = random.choice(filler)
                if random.random() < 0.5:
                    s = f"{fw} {s}"
                else:
                    s = f"{s} {fw}"

        # Sometimes remove ending punctuation (10% chance) for casual feel
        if random.random() < 0.1 and s.endswith("."):
            s = s[:-1]

        # Occasionally lowercase the first letter (5% chance) for ultra-casual
        if (
            random.random() < 0.05
            and s
            and s[0].isupper()
            and not s.startswith(("I ", "I'"))
        ):
            s = s[0].lower() + s[1:]

    return s
