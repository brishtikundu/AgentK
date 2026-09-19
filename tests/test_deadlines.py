import datetime as dt
import pytest

from agentk.storage import Storage
from agentk import deadlines


@pytest.fixture
def storage(tmp_path):
    return Storage(path=str(tmp_path / "data.json"))


def test_add_and_list_deadline(storage):
    deadlines.add_deadline(storage, "XYZ Internship", "2026-12-01")
    items = deadlines.list_deadlines(storage)
    assert len(items) == 1
    assert items[0]["title"] == "XYZ Internship"
    assert items[0]["date"] == "2026-12-01"


def test_add_deadline_rejects_bad_date(storage):
    with pytest.raises(ValueError):
        deadlines.add_deadline(storage, "Bad Date Test", "not-a-date")


def test_due_alerts_fires_at_three_day_threshold(storage):
    today = dt.date(2026, 1, 1)
    target = (today + dt.timedelta(days=3)).isoformat()
    deadlines.add_deadline(storage, "Program X", target)

    due = deadlines.due_alerts(storage, today=today)
    assert len(due) == 1
    assert due[0]["days_left"] == 3


def test_due_alerts_does_not_refire_same_threshold(storage):
    today = dt.date(2026, 1, 1)
    target = (today + dt.timedelta(days=1)).isoformat()
    deadlines.add_deadline(storage, "Program Y", target)

    first = deadlines.due_alerts(storage, today=today)
    second = deadlines.due_alerts(storage, today=today)
    assert len(first) == 1
    assert len(second) == 0  # already alerted for this threshold


def test_due_alerts_ignores_past_deadlines(storage):
    today = dt.date(2026, 1, 10)
    past = dt.date(2026, 1, 1).isoformat()
    deadlines.add_deadline(storage, "Old Deadline", past)

    due = deadlines.due_alerts(storage, today=today)
    assert due == []


def test_due_alerts_ignores_far_future_deadlines(storage):
    today = dt.date(2026, 1, 1)
    far = (today + dt.timedelta(days=30)).isoformat()
    deadlines.add_deadline(storage, "Far Off", far)

    due = deadlines.due_alerts(storage, today=today)
    assert due == []
