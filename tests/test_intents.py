import pytest

from agentk.storage import Storage
from agentk import intents


@pytest.fixture
def storage(tmp_path):
    return Storage(path=str(tmp_path / "data.json"))


def test_handle_calculate_valid(storage):
    result = intents.handle_calculate({"expression": "2 + 3 * 4"}, storage)
    assert "14" in result


def test_handle_calculate_invalid_expression(storage):
    result = intents.handle_calculate({"expression": "import os"}, storage)
    assert "couldn't evaluate" in result


def test_add_and_list_notes(storage):
    intents.handle_add_note({"content": "buy milk"}, storage)
    intents.handle_add_note({"content": "walk the dog"}, storage)
    result = intents.handle_list_notes({}, storage)
    assert "buy milk" in result
    assert "walk the dog" in result


def test_delete_note(storage):
    intents.handle_add_note({"content": "buy milk"}, storage)
    result = intents.handle_delete_note({"index": "1"}, storage)
    assert "Deleted note #1" in result
    assert storage.list_notes() == []


def test_delete_note_out_of_range(storage):
    result = intents.handle_delete_note({"index": "5"}, storage)
    assert "couldn't find" in result


def test_add_and_list_reminders(storage):
    intents.handle_add_reminder({"content": "call mom"}, storage)
    result = intents.handle_list_reminders({}, storage)
    assert "call mom" in result


def test_empty_note_prompts_for_content(storage):
    result = intents.handle_add_note({"content": ""}, storage)
    assert "What should the note say" in result


def test_add_and_list_deadline(storage):
    intents.handle_add_deadline({"title": "XYZ Internship", "date": "2026-12-01"}, storage)
    result = intents.handle_list_deadlines({}, storage)
    assert "XYZ Internship" in result
    assert "2026-12-01" in result


def test_add_deadline_bad_date(storage):
    result = intents.handle_add_deadline({"title": "Bad", "date": "nonsense"}, storage)
    assert "didn't look right" in result
