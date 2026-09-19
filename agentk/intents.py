"""
intents.py — Response logic for each intent AgentK understands.

Each handler takes the classified Intent's entities and a Storage instance,
and returns the string response to show the user. Keeping these as small,
independent functions makes it easy to test each behaviour in isolation and
to add new capabilities later.
"""

import ast
import operator
import datetime as dt

from . import deadlines as deadlines_module
from .storage import Storage

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(expr: str):
    """Evaluate a basic arithmetic expression without using eval()."""
    def _eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](_eval(node.operand))
        raise ValueError("Unsupported expression")

    tree = ast.parse(expr, mode="eval")
    return _eval(tree.body)


def handle_greeting(entities: dict, storage: Storage) -> str:
    return "Hey there! I'm AgentK. Type 'help' to see what I can do."


def handle_exit(entities: dict, storage: Storage) -> str:
    return "Goodbye! 👋"


def handle_help(entities: dict, storage: Storage) -> str:
    return (
        "Here's what I can help with:\n"
        "  - time / date\n"
        "  - calculate <expression>  (e.g. 'calculate 12 * 4 + 1')\n"
        "  - add note <text>\n"
        "  - list notes\n"
        "  - delete note <number>\n"
        "  - remind me to <task>\n"
        "  - list reminders\n"
        "  - add deadline <title> on <YYYY-MM-DD>\n"
        "  - list deadlines\n"
        "  - exit\n\n"
        "Run 'python main.py --watch' separately to start automatic Gmail +\n"
        "deadline monitoring with sound/desktop notifications."
    )


def handle_time(entities: dict, storage: Storage) -> str:
    return f"It's currently {dt.datetime.now().strftime('%I:%M %p')}."


def handle_date(entities: dict, storage: Storage) -> str:
    return f"Today's date is {dt.date.today().strftime('%B %d, %Y')}."


def handle_calculate(entities: dict, storage: Storage) -> str:
    expr = entities.get("expression", "")
    try:
        result = _safe_eval(expr)
        return f"{expr} = {result}"
    except Exception:
        return f"Sorry, I couldn't evaluate '{expr}'. Try something like 'calculate 4 * 5'."


def handle_add_note(entities: dict, storage: Storage) -> str:
    content = entities.get("content", "").strip()
    if not content:
        return "What should the note say? Try 'add note buy groceries'."
    count = storage.add_note(content)
    return f"Noted (#{count}): {content}"


def handle_list_notes(entities: dict, storage: Storage) -> str:
    notes = storage.list_notes()
    if not notes:
        return "You don't have any notes yet."
    return "\n".join(f"{i+1}. {n}" for i, n in enumerate(notes))


def handle_delete_note(entities: dict, storage: Storage) -> str:
    raw_index = entities.get("index", "")
    try:
        index = int(raw_index) - 1
    except ValueError:
        return "Please give me a note number to delete, e.g. 'delete note 2'."
    if storage.delete_note(index):
        return f"Deleted note #{raw_index}."
    return f"I couldn't find note #{raw_index}."


def handle_add_reminder(entities: dict, storage: Storage) -> str:
    content = entities.get("content", "").strip()
    if not content:
        return "What should I remind you to do?"
    count = storage.add_reminder(content)
    return f"Reminder #{count} set: {content}"


def handle_list_reminders(entities: dict, storage: Storage) -> str:
    reminders = storage.list_reminders()
    if not reminders:
        return "You have no reminders."
    return "\n".join(f"{i+1}. {r}" for i, r in enumerate(reminders))


def handle_add_deadline(entities: dict, storage: Storage) -> str:
    title = entities.get("title", "").strip()
    date_str = entities.get("date", "").strip()
    try:
        deadlines_module.add_deadline(storage, title, date_str)
        return f"Deadline added: '{title}' on {date_str}. I'll alert you at 3 days, 1 day, and on the day."
    except ValueError:
        return "That date didn't look right — please use YYYY-MM-DD, e.g. 'add deadline XYZ Internship on 2026-10-15'."


def handle_add_deadline_malformed(entities: dict, storage: Storage) -> str:
    return "Use this format: add deadline <title> on <YYYY-MM-DD>, e.g. 'add deadline XYZ Internship on 2026-10-15'."


def handle_list_deadlines(entities: dict, storage: Storage) -> str:
    items = deadlines_module.list_deadlines(storage)
    if not items:
        return "You have no deadlines tracked yet."
    return "\n".join(f"{i+1}. {d['title']} — {d['date']}" for i, d in enumerate(items))


def handle_unknown(entities: dict, storage: Storage) -> str:
    return "I'm not sure how to help with that yet. Type 'help' to see what I can do."


def handle_empty(entities: dict, storage: Storage) -> str:
    return "Say something and I'll try to help!"


HANDLERS = {
    "greeting": handle_greeting,
    "exit": handle_exit,
    "help": handle_help,
    "time": handle_time,
    "date": handle_date,
    "calculate": handle_calculate,
    "add_note": handle_add_note,
    "list_notes": handle_list_notes,
    "delete_note": handle_delete_note,
    "add_reminder": handle_add_reminder,
    "list_reminders": handle_list_reminders,
    "add_deadline": handle_add_deadline,
    "add_deadline_malformed": handle_add_deadline_malformed,
    "list_deadlines": handle_list_deadlines,
    "unknown": handle_unknown,
    "empty": handle_empty,
}
