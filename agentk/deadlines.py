"""
deadlines.py — Internship / program registration deadline tracking.

Deadlines are kept in the same JSON storage file as notes and reminders.
Each deadline records whether it has already triggered an alert at each
threshold (3 days before, 1 day before, on the day) so you're not spammed
with repeated notifications for the same deadline.
"""

import datetime as dt
from typing import List, Dict

from .storage import Storage

ALERT_THRESHOLDS_DAYS = [3, 1, 0]  # days-before-deadline to send an alert


def _ensure_deadlines_key(storage: Storage) -> None:
    data = storage._read()
    if "deadlines" not in data:
        data["deadlines"] = []
        storage._write(data)


def add_deadline(storage: Storage, title: str, date_str: str) -> Dict:
    """date_str must be in YYYY-MM-DD format."""
    dt.datetime.strptime(date_str, "%Y-%m-%d")  # raises ValueError if malformed
    _ensure_deadlines_key(storage)
    data = storage._read()
    entry = {"title": title, "date": date_str, "alerted_thresholds": []}
    data["deadlines"].append(entry)
    storage._write(data)
    return entry


def list_deadlines(storage: Storage) -> List[Dict]:
    _ensure_deadlines_key(storage)
    return storage._read()["deadlines"]


def due_alerts(storage: Storage, today: dt.date = None) -> List[Dict]:
    """Returns deadlines that just crossed an alert threshold (3/1/0 days
    out) and haven't been alerted for that threshold yet. Marks them as
    alerted so the same threshold doesn't fire twice."""
    today = today or dt.date.today()
    _ensure_deadlines_key(storage)
    data = storage._read()
    due = []

    for entry in data["deadlines"]:
        deadline_date = dt.datetime.strptime(entry["date"], "%Y-%m-%d").date()
        days_left = (deadline_date - today).days

        if days_left < 0:
            continue  # already passed

        for threshold in ALERT_THRESHOLDS_DAYS:
            if days_left == threshold and threshold not in entry["alerted_thresholds"]:
                due.append({**entry, "days_left": days_left})
                entry["alerted_thresholds"].append(threshold)

    storage._write(data)
    return due
