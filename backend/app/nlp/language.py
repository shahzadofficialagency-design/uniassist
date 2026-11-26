"""Language detection + Roman Urdu normalisation.

Languages: 'ur' (Urdu script / Nastaliq), 'en' (English),
'roman_ur' (Roman Urdu), 'mixed' (Roman Urdu + English code-switching).
"""
from __future__ import annotations

import re

URDU_SCRIPT_RE = re.compile(r"[\u0600-\u06FF]")

# Words that strongly signal Roman Urdu.
ROMAN_URDU_WORDS = {
    "kitni", "kitna", "kitne", "hai", "hy", "hain", "hein", "mein", "ma", "mai",
    "ka", "ki", "kay", "ke", "kya", "kab", "kahan", "kaisa", "kaisi", "batao",
    "bataen", "batayein", "dakhla", "dakhlay", "chahiye", "chahye", "mera",
    "meri", "mere", "mujhe", "mujhay", "sakta", "sakti", "sakte", "wala",
    "wali", "walay", "aur", "bhi", "nahi", "nhi", "kar", "kr", "raha", "rahi",
    "ho", "hoga", "hogi", "ga", "gi", "ye", "yeh", "wo", "woh", "kon", "kaun",
    "konsa", "konsi", "lena", "leni", "chah", "krna", "karna", "krni",
    "universiti", "youniversity", "talib", "ilm", "akhr", "aakhri", "tareekh",
    "fees", "paise", "rupay", "mahina", "saal",
}

ENGLISH_QUESTION_WORDS = {
    "what", "how", "when", "where", "which", "who", "is", "are", "the", "of",
    "for", "in", "admission", "fee", "fees", "cost", "deadline", "eligible",
    "eligibility", "compare", "difference", "between", "please", "tell",
}

# Spelling-variant / synonym map -> canonical token(s). Applied token-wise.
SYNONYMS: dict[str, str] = {
    # fee variants
    "fees": "fee", "feez": "fee", "fece": "fee", "charges": "fee", "charge": "fee",
    "tuition": "fee", "dues": "fee", "cost": "fee", "price": "fee", "pese": "fee",
    "paise": "fee", "rupay": "fee", "rs": "fee", "pkr": "fee",
    # how-much variants
    "kitni": "how_much", "kitna": "how_much", "kitne": "how_much",
    "kitny": "how_much",
    # admission variants
    "dakhla": "admission", "dakhlay": "admission", "dakhila": "admission",
    "dakhl": "admission", "admissions": "admission", "apply": "admission",
    "application": "admission", "enroll": "admission", "enrollment": "admission",
    # time / deadline variants
    "kab": "when", "aakhri": "deadline", "akhri": "deadline", "akhr": "deadline",
    "tareekh": "deadline", "tarekh": "deadline", "last": "deadline",
    "date": "deadline", "dates": "deadline",
    # eligibility variants
    "eligible": "eligibility", "eligiblity": "eligibility", "qualify": "eligibility",
    "marks": "marks", "number": "marks", "numbar": "marks", "percent": "marks",
    "percentage": "marks", "aggregate": "marks",
    # be-verb variants (dropped after normalisation)
    "hy": "hai", "h": "hai", "ha": "hai", "hein": "hai", "hain": "hai",
    # in / me variants
    "ma": "mein", "mai": "mein", "may": "mein",
    # program aliases
    "ai": "artificial intelligence", "cs": "computer science",
    "se": "software engineering", "ds": "data sciences", "it": "information technology",
    "bba": "bba", "dpt": "physical therapy",
}

DROP_TOKENS = {"hai", "mein", "ka", "ki", "ke", "kay", "the", "a", "an", "of",
               "is", "are", "batao", "bataen", "please", "mujhe", "tell", "me"}


def detect_language(text: str) -> str:
    """Return 'ur' | 'en' | 'roman_ur' | 'mixed'."""
    if URDU_SCRIPT_RE.search(text):
        # Urdu script with some English words is still answered in Urdu script.
        return "ur"
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    if not tokens:
        return "en"
    roman_hits = sum(1 for t in tokens if t in ROMAN_URDU_WORDS)
    english_hits = sum(1 for t in tokens if t in ENGLISH_QUESTION_WORDS)
    if roman_hits and english_hits >= 2 and roman_hits >= 2:
        return "mixed"
    if roman_hits >= 1 and roman_hits >= english_hits:
        return "roman_ur"
    if roman_hits and english_hits:
        return "mixed"
    return "en"


def normalize_query(text: str) -> str:
    """Canonical form for retrieval: lowercase, synonyms mapped, filler dropped.

    Urdu-script input is returned lowercased but otherwise intact — Urdu keyword
    matching uses URDU_KEYWORDS in the router.
    """
    text = text.lower().strip()
    # '.' is a separator so degree names split: "m.phil" -> ["m", "phil"]
    tokens = re.findall(r"[a-zA-Z0-9%\u0600-\u06FF]+", text)
    out: list[str] = []
    for tok in tokens:
        mapped = SYNONYMS.get(tok, tok)
        for part in mapped.split():
            if part not in DROP_TOKENS:
                out.append(part)
    return " ".join(out)
