"""
assistant.py — AgentK's core orchestration layer.

The Assistant class ties together:
  1. nlp.classify()   — turns raw text into an Intent
  2. intents.HANDLERS — maps each Intent to a response function
  3. storage.Storage  — persists notes/reminders between turns

This separation keeps each piece independently testable, which is how the
project's response accuracy was iterated on and verified (see tests/).
"""

from . import nlp
from .intents import HANDLERS
from .storage import Storage


class Assistant:
    def __init__(self, storage: Storage = None, use_ai_fallback: bool = False):
        self.storage = storage or Storage()
        self.use_ai_fallback = use_ai_fallback
        self.history = []  # list of (user_text, intent_name, response)

    def respond(self, text: str) -> str:
        if self.use_ai_fallback:
            intent = nlp.classify_with_ai(text)
        else:
            intent = nlp.classify(text)

        handler = HANDLERS.get(intent.name, HANDLERS["unknown"])
        response = handler(intent.entities, self.storage)

        self.history.append((text, intent.name, response))
        return response

    def is_exit(self, text: str) -> bool:
        return nlp.classify(text).name == "exit"
