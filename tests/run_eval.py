"""Evaluation runner for the UniAssist chatbot.

Runs tests/eval_questions.json (50 questions + 1 follow-up turn: 15 English,
15 Roman Urdu, 10 Urdu script, 10 mixed) through the real API and reports,
per language and overall:
  - intent accuracy
  - answer correctness (expected facts present + expected answered/unanswered)
  - retrieval hit@5 (proxy: for fee/policy questions, sources or a fee table returned)
  - average latency

The deterministic router/SQL path is evaluated (LLM_PROVIDER=none): the LLM
layer only rephrases, so factual correctness is a property of this path.

Usage (from repo root, venv active):  python tests/run_eval.py
Writes tests/eval_report.json and prints a summary table.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmp.name}")
os.environ.setdefault("JWT_SECRET", "eval-secret")
os.environ["LLM_PROVIDER"] = "none"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

LANG_OK = {
    "mixed": {"mixed", "roman_ur", "en"},
    "roman_ur": {"roman_ur", "mixed"},
    "en": {"en"},
    "ur": {"ur"},
}


def main() -> int:
    questions = json.loads((ROOT / "tests" / "eval_questions.json").read_text(encoding="utf-8"))
    per_lang: dict[str, dict] = defaultdict(lambda: {
        "n": 0, "intent_ok": 0, "lang_ok": 0, "correct": 0, "hit5": 0, "latency_ms": []})
    failures = []
    with TestClient(app) as client:
        session_id = None
        for item in questions:
            if not item.get("follow_up"):
                session_id = None
            start = time.perf_counter()
            r = client.post("/api/chat", json={"message": item["q"], "session_id": session_id})
            latency = (time.perf_counter() - start) * 1000
            assert r.status_code == 200, r.text
            out = r.json()
            session_id = out["session_id"]
            bucket = per_lang[item["language"]]
            bucket["n"] += 1
            bucket["latency_ms"].append(latency)
            intent_ok = out["intent"] == item["intent"]
            lang_ok = out["language"] in LANG_OK[item["language"]]
            contains_ok = all(c in out["answer"] for c in item["must_contain"])
            answered_ok = item["expected_answered"] is None or out["answered"] == item["expected_answered"]
            correct = contains_ok and answered_ok
            hit5 = bool(out.get("sources") or out.get("fee_table")) if item["intent"] in {
                "fee", "policy", "program_info", "comparison", "eligibility"} else True
            bucket["intent_ok"] += intent_ok
            bucket["lang_ok"] += lang_ok
            bucket["correct"] += correct
            bucket["hit5"] += hit5
            if not (intent_ok and correct):
                failures.append({
                    "q": item["q"], "lang": item["language"],
                    "expected_intent": item["intent"], "got_intent": out["intent"],
                    "expected_answered": item["expected_answered"], "got_answered": out["answered"],
                    "must_contain": item["must_contain"],
                    "answer_excerpt": out["answer"][:220],
                })

    report = {"per_language": {}, "failures": failures}
    totals = {"n": 0, "intent_ok": 0, "lang_ok": 0, "correct": 0, "hit5": 0, "latency_ms": []}
    print(f"{'language':<10} {'n':>3} {'intent%':>8} {'lang%':>7} {'correct%':>9} {'hit@5%':>8} {'avg_ms':>8}")
    for lang, b in sorted(per_lang.items()):
        for k in totals:
            totals[k] += b[k] if k != "latency_ms" else []
        totals["latency_ms"] += b["latency_ms"]
        n = b["n"]
        row = {
            "n": n,
            "intent_accuracy": round(100 * b["intent_ok"] / n, 1),
            "language_accuracy": round(100 * b["lang_ok"] / n, 1),
            "answer_correctness": round(100 * b["correct"] / n, 1),
            "retrieval_hit_at_5": round(100 * b["hit5"] / n, 1),
            "avg_latency_ms": round(sum(b["latency_ms"]) / n, 1),
        }
        report["per_language"][lang] = row
        print(f"{lang:<10} {n:>3} {row['intent_accuracy']:>8} {row['language_accuracy']:>7} "
              f"{row['answer_correctness']:>9} {row['retrieval_hit_at_5']:>8} {row['avg_latency_ms']:>8}")
    n = totals["n"]
    overall = {
        "n": n,
        "intent_accuracy": round(100 * totals["intent_ok"] / n, 1),
        "language_accuracy": round(100 * totals["lang_ok"] / n, 1),
        "answer_correctness": round(100 * totals["correct"] / n, 1),
        "retrieval_hit_at_5": round(100 * totals["hit5"] / n, 1),
        "avg_latency_ms": round(sum(totals["latency_ms"]) / n, 1),
    }
    report["overall"] = overall
    print(f"{'OVERALL':<10} {n:>3} {overall['intent_accuracy']:>8} {overall['language_accuracy']:>7} "
          f"{overall['answer_correctness']:>9} {overall['retrieval_hit_at_5']:>8} {overall['avg_latency_ms']:>8}")
    (ROOT / "tests" / "eval_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nFailures: {len(failures)} (details in tests/eval_report.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
