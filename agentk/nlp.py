"""
nlp.py — Intent classification for AgentK.

AgentK uses a lightweight, rule-based classifier by default so the assistant
runs fully offline with zero setup. If an OPENAI_API_KEY environment variable
is present, `classify_with_ai` can be used instead to fall back on an LLM for
messages the rule-based classifier can't confidently handle — this is the
"AI feature integration" layer referenced in the project design.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Intent:
    name: str
    entities: dict = field(default_factory=dict)
    confidence: float = 1.0


_GREETING_WORDS = {"hi", "hello", "hey", "hola", "yo"}
_EXIT_WORDS = {"bye", "exit", "quit", "goodbye", "see you"}
_MATH_EXPR_RE = re.compile(r"^[\d\s+\-*/().]+$")


def classify(text: str) -> Intent:
    """Classify raw user text into an Intent using keyword/pattern rules."""
    raw = text.strip()
    t = raw.lower()

    if not t:
        return Intent("empty")

    if t in _GREETING_WORDS or t.startswith(("hi ", "hello", "hey")):
        return Intent("greeting")

    if t in _EXIT_WORDS or any(t.startswith(w) for w in _EXIT_WORDS):
        return Intent("exit")

    if t in {"help", "commands", "?"}:
        return Intent("help")

    if "what time" in t or t == "time":
        return Intent("time")

    if "what date" in t or "today's date" in t or t == "date":
        return Intent("date")

    if t.startswith("calculate ") or _MATH_EXPR_RE.match(raw):
        expr = raw[10:].strip() if t.startswith("calculate ") else raw
        return Intent("calculate", {"expression": expr})

    if t.startswith("add note ") or t.startswith("note:"):
        content = raw.split(" ", 2)[2] if t.startswith("add note ") else raw.split(":", 1)[1].strip()
        return Intent("add_note", {"content": content.strip()})

    if t in {"list notes", "notes", "show notes"}:
        return Intent("list_notes")

    if t.startswith("delete note "):
        idx = raw[len("delete note "):].strip()
        return Intent("delete_note", {"index": idx})

    if t.startswith("remind me to "):
        content = raw[len("remind me to "):].strip()
        return Intent("add_reminder", {"content": content})

    if t in {"list reminders", "reminders", "show reminders"}:
        return Intent("list_reminders")

    if t.startswith("add deadline "):
        # format: add deadline <title> on <YYYY-MM-DD>
        body = raw[len("add deadline "):]
        if " on " in body:
            title, date_part = body.rsplit(" on ", 1)
            return Intent("add_deadline", {"title": title.strip(), "date": date_part.strip()})
        return Intent("add_deadline_malformed")

    if t in {"list deadlines", "deadlines", "show deadlines"}:
        return Intent("list_deadlines")

    return Intent("unknown", confidence=0.0)


def classify_with_ai(text: str, api_key: Optional[str] = None) -> Intent:
    """
    Optional fallback classifier using the OpenAI API for messages the
    rule-based engine can't handle confidently. Requires the `openai`
    package and a valid API key (env var OPENAI_API_KEY by default).

    Falls back silently to the rule-based classifier if no key is set,
    so the assistant never breaks in environments without AI access.
    """
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        return classify(text)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=key)
        prompt = (
            "Classify the user's message into exactly one intent from this list: "
            "greeting, exit, help, time, date, calculate, add_note, list_notes, "
            "delete_note, add_reminder, list_reminders, unknown. "
            f"Reply with only the intent name.\n\nMessage: {text}"
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0,
        )
        name = response.choices[0].message.content.strip().lower()
        return Intent(name, confidence=0.9)
    except Exception:
        # Network issues, missing package, bad key, etc. — degrade gracefully.
        return classify(text)
