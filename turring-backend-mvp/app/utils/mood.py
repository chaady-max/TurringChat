"""AI Mood Meter for adaptive conversation style.

This module implements a lightweight mood system that allows the AI to adapt
its conversational tone and behavior based on the user's recent messages.

The system analyzes user messages for emotional cues (aggressive, emotional, logical)
and maintains an internal mood state that influences:
- System prompt tone adjustments
- LLM generation parameters (temperature, max words)
- Humanization settings (typo rate, playfulness)
"""

import re
from dataclasses import dataclass, field
from typing import Dict, Optional


# Keyword lists for style detection
AGGRESSIVE_KEYWORDS = [
    "fuck", "shit", "damn", "wtf", "stfu", "idiot", "stupid", "dumb", "moron",
    "shut up", "piss", "asshole", "bitch", "hell", "crap", "suck", "hate",
    "annoying", "ridiculous", "pathetic", "waste", "useless"
]

EMOTIONAL_KEYWORDS = [
    "feel", "felt", "feeling", "emotion", "sad", "happy", "excited", "angry",
    "frustrated", "love", "hate", "miss", "worried", "anxious", "scared",
    "nervous", "glad", "sorry", "hurt", "disappointed", "proud", "ashamed",
    "grateful", "hope", "wish", "care", "matter"
]

EMOTIONAL_PHRASES = [
    "i feel", "i'm so", "i am so", "this makes me", "makes me feel",
    "i'm really", "i am really", "it hurts", "i can't believe",
    "i'm sad", "i'm happy", "i'm excited", "i'm worried"
]

LOGICAL_KEYWORDS = [
    "therefore", "thus", "hence", "because", "since", "if", "then",
    "logically", "logic", "rational", "reason", "evidence", "proof",
    "consistent", "inconsistent", "contradict", "implies", "assume",
    "fact", "data", "analysis", "objective", "subjective", "argument"
]

# Emoji patterns
EMOTIONAL_EMOJIS = ["😂", "😭", "😡", "🥹", "❤️", "💔", "😢", "😊", "😃", "😍", "😤", "😠"]


@dataclass
class MoodState:
    """Represents the AI's current emotional/conversational state.

    All values are normalized to specific ranges for consistent behavior:
    - aggressiveness: -1.0 (calm) to +1.0 (tense/sarcastic)
    - empathy: 0.0 to 1.0 (how warm/understanding)
    - playfulness: 0.0 to 1.0 (how humorous/teasing)
    - analytical: 0.0 to 1.0 (how precise/logical)
    """

    aggressiveness: float = 0.0
    empathy: float = 0.0
    playfulness: float = 0.0
    analytical: float = 0.0

    def __post_init__(self):
        """Clamp all values to their valid ranges."""
        self.aggressiveness = max(-1.0, min(1.0, self.aggressiveness))
        self.empathy = max(0.0, min(1.0, self.empathy))
        self.playfulness = max(0.0, min(1.0, self.playfulness))
        self.analytical = max(0.0, min(1.0, self.analytical))


def analyze_user_style(message: str) -> Dict[str, float]:
    """Analyze a user message to detect conversational style cues.

    Examines the message for indicators of:
    - Aggressive tone (swearing, caps, excessive punctuation)
    - Emotional content (feelings, emotional keywords, emojis)
    - Logical reasoning (analytical keywords, structured arguments)

    Args:
        message: The user's message text

    Returns:
        Dictionary with three style scores, each normalized to 0.0-1.0:
        {
            "aggressive": float,
            "emotional": float,
            "logical": float
        }
    """
    if not message:
        return {"aggressive": 0.0, "emotional": 0.0, "logical": 0.0}

    message_lower = message.lower()
    message_length = len(message.split())

    # === AGGRESSIVE DETECTION ===
    aggressive_score = 0.0

    # Check for aggressive keywords
    aggressive_count = sum(1 for word in AGGRESSIVE_KEYWORDS if word in message_lower)
    aggressive_score += min(1.0, aggressive_count * 0.3)

    # Check for ALL CAPS (but not if message is very short)
    if message_length > 3:
        caps_words = sum(1 for word in message.split() if word.isupper() and len(word) > 2)
        caps_ratio = caps_words / message_length
        aggressive_score += min(0.5, caps_ratio * 2)

    # Check for excessive punctuation
    excessive_punct = len(re.findall(r'[!?]{2,}', message))
    aggressive_score += min(0.4, excessive_punct * 0.2)

    # Clamp aggressive to [0, 1]
    aggressive_score = min(1.0, aggressive_score)

    # === EMOTIONAL DETECTION ===
    emotional_score = 0.0

    # Check for emotional keywords
    emotional_count = sum(1 for word in EMOTIONAL_KEYWORDS if f" {word} " in f" {message_lower} ")
    emotional_score += min(0.6, emotional_count * 0.15)

    # Check for emotional phrases
    phrase_count = sum(1 for phrase in EMOTIONAL_PHRASES if phrase in message_lower)
    emotional_score += min(0.5, phrase_count * 0.25)

    # Check for emotional emojis
    emoji_count = sum(1 for emoji in EMOTIONAL_EMOJIS if emoji in message)
    emotional_score += min(0.4, emoji_count * 0.2)

    # Clamp emotional to [0, 1]
    emotional_score = min(1.0, emotional_score)

    # === LOGICAL DETECTION ===
    logical_score = 0.0

    # Check for logical keywords
    logical_count = sum(1 for word in LOGICAL_KEYWORDS if word in message_lower)
    logical_score += min(0.7, logical_count * 0.2)

    # Check for numbered lists or bullet patterns
    list_patterns = len(re.findall(r'(?:^|\n)\s*[\d\-\*]\s*[\.)]?\s+', message))
    logical_score += min(0.4, list_patterns * 0.2)

    # Check for "if...then" structure
    if "if " in message_lower and ("then" in message_lower or "," in message):
        logical_score += 0.3

    # Clamp logical to [0, 1]
    logical_score = min(1.0, logical_score)

    return {
        "aggressive": aggressive_score,
        "emotional": emotional_score,
        "logical": logical_score
    }


def update_mood(mood: MoodState, style: Dict[str, float], alpha: float = 0.3) -> MoodState:
    """Update the AI's mood state based on user style analysis.

    Uses exponential moving average to smooth mood transitions, preventing
    sudden personality shifts while still being responsive to user input.

    Args:
        mood: Current mood state
        style: Style analysis from analyze_user_style()
        alpha: Smoothing factor (0.0 = no change, 1.0 = instant change)
            Default 0.3 provides good balance between responsiveness and stability

    Returns:
        Updated MoodState with clamped values
    """
    # Clamp alpha to valid range
    alpha = max(0.0, min(1.0, alpha))

    # Extract style components
    aggressive = style.get("aggressive", 0.0)
    emotional = style.get("emotional", 0.0)
    logical = style.get("logical", 0.0)

    # Update aggressiveness (can go negative when user is calm)
    # When user is aggressive, AI becomes more tense/sarcastic
    # When user is calm, AI relaxes back toward neutral
    target_aggression = aggressive - 0.2  # Slight negative bias for natural decay
    new_aggressiveness = mood.aggressiveness * (1 - alpha) + target_aggression * alpha

    # Update empathy (increases with emotional content)
    # Empathy should also slightly increase with non-aggressive interaction
    base_empathy = emotional * 0.8 + (1 - aggressive) * 0.2
    new_empathy = mood.empathy * (1 - alpha) + base_empathy * alpha

    # Update playfulness (high when emotional + low aggressive)
    # Playful when conversation is light and engaging
    base_playfulness = emotional * (1 - aggressive) * 0.7
    new_playfulness = mood.playfulness * (1 - alpha) + base_playfulness * alpha

    # Update analytical (directly tied to logical signals)
    new_analytical = mood.analytical * (1 - alpha) + logical * alpha

    # Return new mood with clamped values
    return MoodState(
        aggressiveness=new_aggressiveness,
        empathy=new_empathy,
        playfulness=new_playfulness,
        analytical=new_analytical
    )


def build_mood_instructions(mood: MoodState) -> str:
    """Generate tone instructions based on current mood state.

    Converts the mood state into natural language instructions that will
    be added to the system prompt to adjust the AI's conversational style.

    Args:
        mood: Current mood state

    Returns:
        String with tone/behavior instructions, or empty string if mood is neutral
    """
    instructions = []

    # Aggressiveness threshold
    if mood.aggressiveness > 0.4:
        instructions.append(
            "You feel slightly defensive. Respond with subtle sarcasm or dry humor, "
            "but stay calm and never be toxic or hostile. Keep it light and human."
        )
    elif mood.aggressiveness < -0.3:
        instructions.append(
            "You're feeling very relaxed and calm. Be extra chill and easygoing in your responses."
        )

    # Empathy threshold
    if mood.empathy > 0.5:
        instructions.append(
            "You're warm and empathetic. Acknowledge and validate their feelings. "
            "Show you understand where they're coming from."
        )

    # Analytical threshold
    if mood.analytical > 0.5:
        instructions.append(
            "You're thinking analytically. Be more precise and logical in your responses. "
            "Focus on clear reasoning and structure your thoughts."
        )

    # Playfulness threshold
    if mood.playfulness > 0.5:
        instructions.append(
            "You're feeling playful and teasing. Add some light humor or playful banter, "
            "but stay natural and don't overdo it."
        )

    # If multiple moods are active, combine them naturally
    if len(instructions) == 0:
        return ""

    return " ".join(instructions)


def get_generation_params(mood: MoodState, base_temperature: float = 0.7,
                          base_max_words: int = 12) -> Dict[str, float]:
    """Adjust LLM generation parameters based on mood state.

    Modifies temperature and response length to match the conversational style
    implied by the current mood.

    Args:
        mood: Current mood state
        base_temperature: Default temperature (typically 0.7)
        base_max_words: Default max words (typically 12-18)

    Returns:
        Dictionary with adjusted parameters:
        {
            "temperature": float (0.2 to 1.5),
            "max_words": int (8 to 30),
            "typo_rate": float (0.0 to 0.5)
        }
    """
    # Start with base values
    temperature = base_temperature
    max_words = base_max_words
    typo_rate = 0.22  # Default humanization typo rate

    # === ANALYTICAL ADJUSTMENTS ===
    if mood.analytical > 0.3:
        # More analytical = lower temperature, slightly longer responses
        temperature -= mood.analytical * 0.3
        max_words += int(mood.analytical * 6)  # Up to +6 words
        typo_rate -= mood.analytical * 0.1  # Fewer typos when being precise

    # === PLAYFULNESS ADJUSTMENTS ===
    if mood.playfulness > 0.3:
        # More playful = higher temperature, normal length
        temperature += mood.playfulness * 0.4
        typo_rate += mood.playfulness * 0.15  # More typos adds to playfulness

    # === AGGRESSIVENESS ADJUSTMENTS ===
    if mood.aggressiveness > 0.4:
        # More tense = shorter, snappier responses
        max_words -= int(mood.aggressiveness * 4)  # Up to -4 words
        temperature += mood.aggressiveness * 0.2  # Slightly less predictable
    elif mood.aggressiveness < -0.3:
        # Very calm = slightly longer, more relaxed
        max_words += 2
        temperature -= 0.1

    # === EMPATHY ADJUSTMENTS ===
    if mood.empathy > 0.5:
        # More empathetic = slightly longer to be thorough
        max_words += 3
        typo_rate -= 0.05  # Slightly more careful when being supportive

    # Clamp all values to safe ranges
    temperature = max(0.2, min(1.5, temperature))
    max_words = max(8, min(30, max_words))
    typo_rate = max(0.0, min(0.5, typo_rate))

    return {
        "temperature": round(temperature, 2),
        "max_words": max_words,
        "typo_rate": round(typo_rate, 3)
    }
