"""Retrieval over unstructured policy documents.

Default engine: BM25 implemented in pure Python over PolicyDocument rows, so
the system runs anywhere with zero heavy dependencies. If ChromaDB +
sentence-transformers (multilingual-e5) are installed, they can be plugged in
behind this same interface (see requirements-optional.txt); the chat service
only depends on `search()` returning (title, text, source, score) tuples.

`rebuild()` re-indexes in memory — the Admin import endpoint calls it so new
documents become searchable without a restart.
"""
from __future__ import annotations

import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"[a-zA-Z0-9\u0600-\u06FF]+")


def _tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


class BM25Retriever:
    def __init__(self) -> None:
        self.docs: list[dict] = []
        self._idf: dict[str, float] = {}
        self._doc_freq: Counter = Counter()
        self._avg_len = 1.0

    def rebuild(self, documents: list[dict]) -> None:
        """documents: [{title, text, source}]"""
        self.docs = []
        self._doc_freq = Counter()
        total_len = 0
        for d in documents:
            toks = _tokens(d["title"] + " " + d["text"])
            self.docs.append({**d, "_toks": toks, "_tf": Counter(toks)})
            total_len += len(toks)
            for t in set(toks):
                self._doc_freq[t] += 1
        n = max(len(self.docs), 1)
        self._avg_len = max(total_len / n, 1.0)
        self._idf = {
            t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in self._doc_freq.items()
        }

    def search(self, query: str, top_k: int = 5, threshold: float = 0.5) -> list[dict]:
        q = _tokens(query)
        if not q or not self.docs:
            return []
        k1, b = 1.5, 0.75
        scored = []
        for d in self.docs:
            tf, dl = d["_tf"], len(d["_toks"])
            score = 0.0
            for term in set(q):
                if term not in tf:
                    continue
                idf = self._idf.get(term, 0.0)
                denom = tf[term] + k1 * (1 - b + b * dl / self._avg_len)
                score += idf * (tf[term] * (k1 + 1)) / denom
            if score >= threshold:
                scored.append({
                    "title": d["title"], "text": d["text"],
                    "source": d["source"], "score": round(score, 3),
                })
        scored.sort(key=lambda x: -x["score"])
        return scored[:top_k]


# Process-wide singleton used by the app; seeded/rebuilt by services.seed and admin import.
retriever = BM25Retriever()
