"""Optional LLM rephrasing layer.

The LLM NEVER supplies facts. The chat service builds a complete, correct
answer from the database first; if an LLM provider is configured in .env
(Gemini / Groq / Ollama), the model may only rephrase that answer into the
user's language — and any failure falls back to the template answer.
With LLM_PROVIDER=none (default) the system is fully functional offline.
"""
from __future__ import annotations

import json
import urllib.request

from ..core.config import settings

SYSTEM_RULE = (
    "You rephrase university information for a student. Use ONLY the facts in the "
    "provided answer. Never add, change or guess any fee, date, mark or rule. "
    "Keep all numbers exactly as given. Reply in the same language and script as "
    "the student's question. Keep the source citation and the verification note."
)


def _post(url: str, payload: dict, headers: dict, timeout: int = 20) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (configured provider URL)
        return json.loads(resp.read().decode("utf-8"))


def rephrase(question: str, factual_answer: str) -> str | None:
    """Return a rephrased answer, or None when no provider is configured / on any error."""
    provider = (settings.llm_provider or "none").lower()
    if provider == "none" or not factual_answer.strip():
        return None
    prompt = f"Student question: {question}\n\nFactual answer to rephrase:\n{factual_answer}"
    try:
        if provider == "gemini":
            model = settings.llm_model or "gemini-1.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.llm_api_key}"
            data = _post(url, {
                "system_instruction": {"parts": [{"text": SYSTEM_RULE}]},
                "contents": [{"parts": [{"text": prompt}]}],
            }, {})
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        if provider == "groq":
            model = settings.llm_model or "llama-3.1-8b-instant"
            data = _post("https://api.groq.com/openai/v1/chat/completions", {
                "model": model,
                "messages": [{"role": "system", "content": SYSTEM_RULE},
                             {"role": "user", "content": prompt}],
            }, {"Authorization": f"Bearer {settings.llm_api_key}"})
            return data["choices"][0]["message"]["content"].strip()
        if provider == "ollama":
            model = settings.llm_model or "llama3.1"
            data = _post(f"{settings.ollama_base_url}/api/chat", {
                "model": model, "stream": False,
                "messages": [{"role": "system", "content": SYSTEM_RULE},
                             {"role": "user", "content": prompt}],
            }, {})
            return data["message"]["content"].strip()
    except Exception:
        return None
    return None
