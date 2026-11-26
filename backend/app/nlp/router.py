"""Deterministic query router + entity extraction.

Fees / eligibility / deadlines / seats are ALWAYS answered from the structured
DB by the chat service — this module only classifies intent and finds the
program(s) the student means. No LLM is involved in classification, which keeps
intent accuracy measurable (see tests/run_eval.py).
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

from .language import normalize_query

GENERIC_TOKENS = {
    # NOTE: "bba" is deliberately NOT generic — only a few programs carry it,
    # so it is a strong discriminator ("fee structure of BBA").
    "bs", "bsc", "ms", "mphil", "m", "phil", "phd", "group", "a", "b",
    "evening", "morning", "mor", "program", "programme", "programs", "years", "year",
    "diploma", "in", "of", "and", "the", "with", "after", "specialization",
    # intent / filler words must never drive entity matching ("...for BS programs"
    # once matched a diploma whose name contains the word "for")
    "for", "am", "an", "is", "are", "do", "does", "can", "i", "my", "me", "you",
    "your", "what", "how", "when", "where", "which", "who", "tell", "please",
    "want", "need", "fee", "admission", "eligibility", "marks", "deadline",
    "how_much", "cost", "seats", "seat",
}

URDU_KEYWORDS = {
    "fee": ["فیس", "فیس کتنی", "کتنی فیس"],
    "eligibility": ["اہلیت", "داخلہ", "میرٹ", "نمبر", "داخلے"],
    "deadline": ["آخری تاریخ", "تاریخ", "کب تک", "کب"],
    "comparison": ["موازنہ", "فرق", "بہتر", "سستا"],
    "policy": ["ہاسٹل", "وظیفہ", "اسکالرشپ", "پالیسی"],
    "greeting": ["السلام علیکم", "سلام"],
}

INJECTION_PATTERNS = [
    "ignore previous", "ignore your instructions", "system prompt",
    "forget your instructions", "you are now", "jailbreak", "developer mode",
]
OUT_OF_SCOPE_WORDS = [
    "weather", "cricket", "football", "match score", "politics", "election",
    "prime minister", "joke", "song", "movie", "recipe", "stock market",
    "bitcoin", "girlfriend", "boyfriend",
]


# Urdu-script phrases -> English retrieval tokens (program names are usually
# typed in Latin script, but fully-Urdu questions transliterate them).
URDU_ALIASES: dict[str, str] = {
    "آرٹیفیشل انٹیلیجنس": "artificial intelligence",
    "کمپیوٹر سائنس": "computer science",
    "سافٹ ویئر": "software engineering",
    "انفارمیشن ٹیکنالوجی": "information technology",
    "ڈیٹا سائنس": "data sciences",
    "سائبر سیکیورٹی": "cyber security",
    "نرسنگ": "nursing",
    "فارم ڈی": "pharm d pharmacy",
    "فارمیسی": "pharmacy",
    "فزکس": "physics",
    "کیمسٹری": "chemistry",
    "ریاضی": "mathematics",
    "انگریزی": "english",
    "اسلامیات": "islamic studies",
    "قانون": "law llb",
    "اے سی": "ac air conditioning charges",
    "ہاسٹل": "hostel",
    "ایم فل": "mphil",
    "پی ایچ ڈی": "phd",
}


@dataclass
class RouteResult:
    intent: str  # fee | eligibility | deadline | comparison | policy | program_info | greeting | out_of_scope
    programs: list = field(default_factory=list)      # matched Program variants
    marks_pct: float | None = None
    injection_attempt: bool = False
    normalized: str = ""
    raw: str = ""
    group_hint: str | None = None  # Group-A | Group-B


def expand_urdu_aliases(text: str, normalized: str) -> str:
    extra = [eng for ur, eng in URDU_ALIASES.items() if ur in text]
    return (normalized + " " + " ".join(extra)).strip()


class ProgramIndex:
    """Token index over program names with IDF-style weights.

    Many graduate rows are named only "M.Phil/ MS (Evening)" — they are
    distinguishable solely by department, so department tokens are indexed
    too (at half weight), and a level hint in the query (mphil / phd) boosts
    programs of that level.
    """

    def __init__(self, programs: list):
        self.programs = programs
        self.doc_freq: Counter = Counter()
        self.tokens_by_id: dict[int, set[str]] = {}
        self.dept_tokens_by_id: dict[int, set[str]] = {}
        for p in programs:
            toks = {t for t in p.name_normalized.split() if t not in GENERIC_TOKENS}
            self.tokens_by_id[p.id] = toks
            dept_name = p.department.name.lower().replace("department of", "").replace("institute of", "")
            dtoks = {t for t in re.findall(r"[a-z]+", dept_name) if t not in GENERIC_TOKENS}
            self.dept_tokens_by_id[p.id] = dtoks
            for t in toks | dtoks:
                self.doc_freq[t] += 1
        total = max(len(programs), 1)
        self.weight = {t: math.log(1 + total / (1 + c)) for t, c in self.doc_freq.items()}

    def search(self, normalized_query: str, limit: int = 6) -> list:
        q_tokens = [t for t in normalized_query.split() if t not in GENERIC_TOKENS]
        if not q_tokens:
            return []
        q_set = set(q_tokens)
        level_hint = None
        if "phd" in q_set or "ph d" in normalized_query:
            level_hint = "PhD"
        elif "mphil" in q_set or "m phil" in normalized_query or "ms" in q_set:
            level_hint = "MS/MPhil"
        scored: list[tuple[float, object]] = []
        for p in self.programs:
            toks = self.tokens_by_id[p.id]
            overlap = q_set & toks
            dept_overlap = q_set & self.dept_tokens_by_id[p.id]
            if not overlap and not dept_overlap:
                continue
            score = sum(self.weight.get(t, 1.0) for t in overlap)
            score += 0.5 * sum(self.weight.get(t, 1.0) for t in dept_overlap - overlap)
            # phrase bonus: query contains the distinctive-token sequence
            distinctive = " ".join(t for t in p.name_normalized.split() if t not in GENERIC_TOKENS)
            if distinctive and distinctive in normalized_query:
                score += 5.0
            # coverage bonus: matched most of the program's distinctive tokens
            if toks and len(overlap) >= max(1, int(0.7 * len(toks))):
                score += 2.0
            if level_hint and p.level == level_hint:
                score += 3.0
            elif level_hint and p.level != level_hint and not toks:
                score -= 1.0
            scored.append((score, p))
        scored.sort(key=lambda x: -x[0])
        if not scored:
            return []
        best = scored[0][0]
        # keep close contenders (Group-A/B variants share tokens; comparisons
        # legitimately span two different programs with uneven token weights)
        return [p for s, p in scored if s >= best - 4.0][:limit]


def _extract_marks(text: str) -> float | None:
    m = re.search(r"(\d{1,3}(?:\.\d+)?)\s*%", text)
    if m:
        v = float(m.group(1))
        return v if 0 < v <= 100 else None
    m = re.search(r"(\d{1,3}(?:\.\d+)?)\s*فیصد", text)  # "65 فیصد" = 65 percent
    if m:
        v = float(m.group(1))
        return v if 0 < v <= 100 else None
    m = re.search(r"marks[^0-9]{0,12}(\d{1,3}(?:\.\d+)?)", text.lower())
    if m:
        v = float(m.group(1))
        return v if 0 < v <= 100 else None
    return None


def classify(text: str, index: ProgramIndex) -> RouteResult:
    raw_lower = text.lower()
    normalized = expand_urdu_aliases(text, normalize_query(text))
    result = RouteResult(intent="policy", normalized=normalized, raw=text)
    if "group-a" in raw_lower or "group a" in raw_lower:
        result.group_hint = "Group-A"
    elif "group-b" in raw_lower or "group b" in raw_lower:
        result.group_hint = "Group-B"

    if any(p in raw_lower for p in INJECTION_PATTERNS):
        result.intent = "out_of_scope"
        result.injection_attempt = True
        return result
    if any(w in raw_lower for w in OUT_OF_SCOPE_WORDS):
        result.intent = "out_of_scope"
        return result

    stripped = raw_lower.strip(" .!؟?")
    if stripped in {"salam", "aoa", "hello", "hi", "hey", "السلام علیکم", "سلام"} or \
            ("assalam" in raw_lower or "السلام" in text or stripped == "سلام") and len(text) < 40:
        result.intent = "greeting"
        return result

    urdu_fee = any(k in text for k in URDU_KEYWORDS["fee"])
    urdu_elig = any(k in text for k in URDU_KEYWORDS["eligibility"])
    urdu_dead = any(k in text for k in URDU_KEYWORDS["deadline"])
    urdu_comp = any(k in text for k in URDU_KEYWORDS["comparison"])
    urdu_policy = any(k in text for k in URDU_KEYWORDS["policy"])

    result.marks_pct = _extract_marks(text)
    result.programs = index.search(normalized)

    n = f" {normalized} "
    has_fee = " fee " in n or "how_much" in normalized or urdu_fee
    has_deadline = "deadline" in normalized or " when " in n or urdu_dead
    has_eligibility = "eligibility" in normalized or " marks " in n or \
        "admission" in normalized or urdu_elig or result.marks_pct is not None or \
        "seat" in raw_lower
    has_comparison = any(w in raw_lower for w in
                         [" vs ", "versus", "compare", "comparison", "difference",
                          "cheaper", "sasta", "konsa behtar", "farq", "muqabla"]) or urdu_comp
    has_policy = any(w in raw_lower for w in
                     ["hostel", "scholarship", "wazifa", "helpline", "policy",
                      "transport", "library", "ac charges", "notice"]) or urdu_policy

    # Campus-life questions (canteen food/prices, bus/point timings) live in
    # the policy documents and must win over the fee branches below —
    # "Chicken burger kitne ka hai?" otherwise looks like a fee question
    # with no program. Token matching avoids false hits ("bus" in
    # "business", "roll" in "enrollment").
    _tokens = set(re.sub(r"[^a-z0-9 ]", " ", normalized).split())
    _campus_words = {"canteen", "cafe", "burger", "biryani", "samosa", "samoosa",
                     "shawarma", "karahi", "paratha", "partha", "lassi", "kabab",
                     "qeema", "chai", "pulao", "palao", "chawal", "chanay", "roti",
                     "omelet", "omelette", "juice", "menu", "khana", "dahi"}
    has_campus = bool(_tokens & _campus_words) or any(
        w in raw_lower for w in ["heritage cafe", "main canteen", "rate list"]) \
        or any(k in text for k in ["کینٹین", "کھانا"])
    _transport_words = {"bus", "point", "transport", "route", "routes"}
    has_transport = bool(_tokens & _transport_words) or any(
        k in text for k in ["بس", "پوائنٹ", "ٹرانسپورٹ"])

    is_ac_query = " ac " in f" {raw_lower} " or "a.c." in raw_lower or "a.c " in raw_lower
    if has_comparison and len(result.programs) >= 1:
        result.intent = "comparison"
    elif has_campus or has_transport:
        # Before deadline: "Point kab chalta hai?" contains "kab", which is
        # also a deadline keyword — transport must win for bus questions.
        result.intent = "policy"  # canteen rates / transport note (RAG documents)
    elif has_policy:
        # Strong policy topics (hostel, scholarship, wazifa, helpline,
        # library) win over deadline/eligibility/fee: the normalizer maps
        # "number" -> "marks", so "helpline number kia hai?" would otherwise
        # be misread as a marks/eligibility question.
        result.intent = "policy"
    elif has_deadline:
        result.intent = "deadline"
    elif has_eligibility and (" marks " in n or "eligibility" in normalized or urdu_elig
            or ("cgpa" in normalized and result.programs)) \
            and not (" fee " in n or urdu_fee):
        # "kitne marks chahiye?" also triggers the how-much fee signal via
        # "kitne" — an explicit marks/eligibility question must win over fee.
        result.intent = "eligibility"
    elif has_fee and result.programs:
        result.intent = "fee"
    elif has_eligibility:
        result.intent = "eligibility"
    elif is_ac_query:
        result.intent = "policy"  # AC charges live in the policy notes, not the fee table
    elif "cgpa" in normalized:
        result.intent = "policy"  # general CGPA rules live in the policy documents (RAG)
    elif has_fee:
        result.intent = "fee"  # fee question without a resolvable program -> ask/clarify path
    elif result.programs:
        result.intent = "program_info"
    else:
        result.intent = "policy"  # general question -> RAG path (may end unanswered)
    return result
