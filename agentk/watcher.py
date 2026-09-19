"""
watcher.py — Background loop that makes the alerting automatic.

Runs continuously (started via `python main.py --watch`) and, on every
poll cycle:
  1. Checks Gmail for new messages and flags important-looking ones
     (internships, deadlines, applications) — fires a sound + desktop
     notification immediately, and creates a Gmail draft reply for review
  2. Checks stored deadlines and fires a sound + desktop notification
     when one crosses the 3-day / 1-day / due-today mark

Both checks are fully automatic once started — no manual triggering
needed. Only the actual *sending* of email replies stays manual, since
that step needs your judgment.
"""

import time

from . import deadlines
from .gmail_client import GmailClient, suggest_reply_text
from .notifier import alert
from .storage import Storage


def _seen_message_ids(storage: Storage) -> set:
    data = storage._read()
    return set(data.get("seen_gmail_ids", []))


def _mark_seen(storage: Storage, message_id: str) -> None:
    data = storage._read()
    seen = set(data.get("seen_gmail_ids", []))
    seen.add(message_id)
    data["seen_gmail_ids"] = list(seen)
    storage._write(data)


def check_gmail_once(gmail: GmailClient, storage: Storage, max_results: int = 10) -> int:
    """One pass over recent inbox messages. Returns how many new important
    messages were found and alerted on."""
    seen = _seen_message_ids(storage)
    messages = gmail.fetch_recent_messages(max_results=max_results)
    found = 0

    for msg in messages:
        if msg["id"] in seen:
            continue
        _mark_seen(storage, msg["id"])

        if gmail.is_important(msg["subject"], msg["snippet"]):
            found += 1
            alert(
                title="Important email — AgentK",
                message=f"{msg['subject']}\nfrom {msg['sender']}",
            )
            reply_text = suggest_reply_text(msg["subject"], msg["snippet"])
            gmail.create_draft_reply(
                message_id=msg["id"],
                thread_id=msg["threadId"],
                to=msg["sender"],
                subject=msg["subject"],
                body=reply_text,
            )
    return found


def check_deadlines_once(storage: Storage) -> int:
    """One pass over stored deadlines. Returns how many alerts fired."""
    due = deadlines.due_alerts(storage)
    for entry in due:
        when = "today" if entry["days_left"] == 0 else f"in {entry['days_left']} day(s)"
        alert(
            title="Deadline approaching — AgentK",
            message=f"{entry['title']} is due {when} ({entry['date']}).",
        )
    return len(due)


def run_watch_loop(poll_interval_minutes: int = 15, use_gmail: bool = True) -> None:
    """Starts the continuous watcher. Runs until you stop it (Ctrl+C)."""
    storage = Storage()
    gmail = GmailClient() if use_gmail else None

    if gmail:
        print("Authenticating with Gmail (a browser window may open the first time)...")
        gmail.authenticate()
        print("Gmail connected.")

    print(f"AgentK watcher started — checking every {poll_interval_minutes} minute(s). Press Ctrl+C to stop.\n")

    while True:
        try:
            if gmail:
                found = check_gmail_once(gmail, storage)
                if found:
                    print(f"[watcher] {found} new important email(s) — notified and draft reply created.")

            fired = check_deadlines_once(storage)
            if fired:
                print(f"[watcher] {fired} deadline alert(s) fired.")

            time.sleep(poll_interval_minutes * 60)
        except KeyboardInterrupt:
            print("\nWatcher stopped.")
            break
        except Exception as e:
            # Never let one bad poll (e.g. a temporary network hiccup) kill
            # the whole watcher — log it and keep going.
            print(f"[watcher] error during poll, will retry next cycle: {e}")
            time.sleep(poll_interval_minutes * 60)
