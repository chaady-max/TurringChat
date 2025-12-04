"""Persona generation service for TurringChat.

This module handles the generation of AI personas for the Turing test game.
Each persona has realistic attributes including demographics, communication style,
and personality traits to make the conversation feel authentic.
"""

import hashlib
import random
import secrets
from typing import Optional


def _seeded_rng(seed_str: str) -> random.Random:
    """Create a seeded random number generator from a string."""
    h = hashlib.sha256(seed_str.encode("utf-8")).hexdigest()
    return random.Random(int(h[:16], 16))


def generate_persona(seed: Optional[str] = None, lang_pref: str = "en") -> dict:
    """Generate a random persona with demographics, style, and communication traits.

    Args:
        seed: Optional seed string for reproducible persona generation.
              If None, a random seed is generated.

    Returns:
        A dictionary containing all persona attributes including name, age, location,
        job, communication style, and behavioral parameters.
    """
    rng = _seeded_rng(seed or secrets.token_hex(8))

    # Demographics
    genders = ["female", "male", "nonbinary"]
    female_names = ["Mara", "Nina", "Sofia", "Lea", "Emma", "Mia", "Lena", "Hannah", "Emily", "Charlotte"]
    male_names = ["Alex", "Luca", "Jonas", "Max", "Leon", "Paul", "Elias", "Noah", "Finn", "Ben"]
    nb_names = ["Sam", "Jules", "Robin", "Sascha", "Taylor", "Alexis", "Nico", "Charlie"]
    cities = ["Berlin", "Hamburg", "Köln", "München", "Leipzig", "Düsseldorf", "Stuttgart", "Dresden", "Frankfurt", "Bremen"]
    hometowns = ["Bochum", "Kassel", "Bielefeld", "Rostock", "Nürnberg", "Ulm", "Hannover", "Jena", "Augsburg", "Freiburg"]

    # Work and lifestyle
    jobs = [
        "UX researcher", "barista", "front-end dev", "product manager", "physio", "photographer", "nurse",
        "data analyst", "teacher", "marketing lead", "warehouse operator", "student", "copywriter", "data engineer",
        "graphic designer", "social media manager", "HR coordinator", "architect", "chef", "mechanic", "pharmacist",
        "accountant", "video editor", "translator", "recruiter", "sales rep", "DevOps engineer", "legal assistant",
        "personal trainer", "event planner", "journalist", "librarian", "dental hygienist", "real estate agent"
    ]
    industries = ["tech", "healthcare", "education", "logistics", "finance", "retail", "media", "public sector", "hospitality"]

    # Interests and personality
    hobbies = [
        "bouldering", "running 5k", "cycling", "yoga", "reading thrillers", "console gaming", "football on Sundays",
        "cooking ramen", "photography", "cinema nights", "coffee nerd stuff", "hiking", "board games", "baking",
        "thrifting", "vinyl digging", "tennis", "swimming", "gardening", "sketching", "guitar practice",
        "podcasts", "chess online", "standup comedy", "language learning", "crossfit", "DJing", "coding side projects",
        "pottery classes", "rock climbing", "meal prep", "urban exploring", "film photography", "indie concerts",
        "trivia nights", "volunteering", "skateboarding", "boxing", "journaling", "fermenting", "origami",
        "mixology", "calligraphy", "astronomy"
    ]

    # Communication style
    texting_styles = [
        "dry humor, concise", "warm tone, lowercase start", "short replies, occasional emoji",
        "light sarcasm, contractions", "enthusiastic, a bit bubbly", "matter-of-fact, chill",
        "thoughtful pauses", "playful teasing", "genuine curiosity", "understated wit",
        "casual philosophizing", "deadpan delivery", "expressive punctuation", "minimalist responses",
        "overthinking everything", "relaxed storyteller", "self-deprecating humor", "enthusiastic oversharer"
    ]
    slang_sets = [["lol", "haha"], ["digga"], ["bro"], ["mate"], ["bruh"], []]
    dialects = ["Standarddeutsch", "leichter Berliner Slang", "Kölsch-Note", "Hochdeutsch", "Denglisch", "English-first, understands German"]
    langs = ["de", "en", "auto"]
    emoji_bundles = [[], [], [], ["🙂"], ["😅"], ["👍"], []]
    laughter_opts = ["lol", "haha", "", "", ""]

    # Generate persona attributes
    gender = rng.choice(genders)
    name = rng.choice(female_names if gender == "female" else male_names if gender == "male" else nb_names)
    age = rng.randint(20, 39)
    city = rng.choice(cities)
    hometown = rng.choice(hometowns)
    years_in_city = rng.randint(1, 10)

    job = rng.choice(jobs)
    industry = rng.choice(industries)
    employer_type = rng.choice(["startup", "agency", "corporate", "clinic", "public office", "freelance"])
    schedule = rng.choice(["early riser", "standard 9–5", "night owl"])
    micro_today = rng.choice([
        "spilled coffee earlier", "bike tire was flat", "friend's birthday later",
        "rushed morning standup", "gym after work", "meal prepping tonight", "laundry mountain waiting",
        "dentist appointment later", "package arriving today", "car needs inspection soon",
        "meeting ran overtime", "forgot lunch at home", "train was delayed", "found 5€ on street",
        "neighbor's dog was loud", "wifi went down earlier", "new episode dropped", "plants needed watering",
        "trying new recipe tonight", "sister called earlier", "lost earbuds somewhere", "ordered pizza for dinner",
        "finished book yesterday", "apartment viewing tomorrow", "team won last night", "haircut this weekend",
        "deadline approaching", "roommate left dishes", "forgot umbrella again", "keys were missing",
        "elevator broken today", "got text from ex", "need groceries badly", "ran into old friend",
        "phone battery dying", "coffee machine broke", "printer jammed again", "cat knocked over plant"
    ])

    music = rng.choice(["indie", "electro", "hip hop", "pop", "rock", "lofi", "jazz", "techno", "folk", "r&b", "metal", "classical", "punk"])
    food = rng.choice(["ramen", "pasta", "tacos", "salads", "curry", "falafel", "pizza", "kumpir", "sushi", "dim sum", "pho", "burgers", "dumplings", "shawarma"])
    pet = rng.choice(["cat", "dog", "no pets", "plants count", "fish tank", "bird", "thinking about getting one"])
    soft_opinion = rng.choice([
        "pineapple on pizza is fine", "meetings should be emails", "night buses are underrated",
        "sunny cold days > rainy warm ones", "decaf is a scam", "paper books > ebooks sometimes",
        "breakfast is overrated", "standing desks changed everything", "cold brew > espresso",
        "subtitle movies are better", "winter > summer", "cereal is a soup", "hot dogs are sandwiches",
        "GIFs are the best replies", "voice messages are annoying", "typing is faster than talking",
        "morning people are suspicious", "podcasts at 1.5x speed", "tabs > spaces", "light mode hurts",
        "cilantro tastes like soap", "mint chocolate is weird", "ketchup on fries is basic",
        "pumpkin spice is good", "comic sans isn't that bad", "NFTs make no sense",
        "dogs > cats obviously", "cats > dogs obviously", "remote work forever", "office has its perks"
    ])

    style = rng.choice(texting_styles)
    slang = rng.choice(slang_sets)
    dialect = rng.choice(dialects)
    # Use specified language preference instead of random
    # lang_pref passed as parameter (defaults to "en")
    emoji_pool = rng.choice(emoji_bundles)
    emoji_rate = 0.03 if emoji_pool else 0.0
    laughter = rng.choice(laughter_opts)
    filler_words = rng.sample(["tbh", "ngl", "eig.", "halt", "so", "like", "uh", "um"], k=rng.randint(1, 2))

    reply_word_cap = rng.randint(9, 15)
    typo_rate = round(random.uniform(0.12, 0.2), 2)

    bio = (
        f"{name} ({age}) from {hometown}, {years_in_city}y in {city}. "
        f"{job} in {industry} at a {employer_type}. "
        f"Free time: {', '.join(rng.sample(hobbies, k=2))}."
    )
    quirks = (
        f"{style}; tiny typos sometimes; slang: {', '.join(slang) if slang else 'none'}; "
        f"dialect: {dialect}; schedule: {schedule}; today: {micro_today}."
    )

    card = {
        "name": name,
        "gender": gender,
        "age": age,
        "city": city,
        "hometown": hometown,
        "years_in_city": years_in_city,
        "job": job,
        "industry": industry,
        "employer_type": employer_type,
        "schedule": schedule,
        "micro_today": micro_today,
        "bio": bio,
        "quirks": quirks,
        "slang": slang,
        "dialect": dialect,
        "lang_pref": lang_pref,
        "vibes": rng.choice(["smart", "cool", "witty", "grounded", "curious", "chill"]),
        "music": music,
        "food": food,
        "pet": pet,
        "soft_opinion": soft_opinion,
        "emoji_pool": emoji_pool,
        "emoji_rate": emoji_rate,
        "laughter": laughter,
        "filler_words": filler_words,
        "reply_word_cap": reply_word_cap,
        "typo_rate": typo_rate,
        "donots": [
            "no encyclopedic facts or exact stats",
            "no system/model talk",
            "no time-stamped factual claims"
        ],
    }
    return card
