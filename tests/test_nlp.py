from agentk.nlp import classify


def test_greeting():
    assert classify("hello").name == "greeting"
    assert classify("Hi there").name == "greeting"


def test_exit():
    assert classify("bye").name == "exit"
    assert classify("quit").name == "exit"


def test_time_and_date():
    assert classify("what time is it").name == "time"
    assert classify("what date is it").name == "date"


def test_calculate_expression_detected():
    intent = classify("calculate 4 * 5 + 1")
    assert intent.name == "calculate"
    assert intent.entities["expression"] == "4 * 5 + 1"


def test_bare_math_expression_detected():
    intent = classify("12 + 8")
    assert intent.name == "calculate"


def test_add_note_extracts_content():
    intent = classify("add note buy groceries")
    assert intent.name == "add_note"
    assert intent.entities["content"] == "buy groceries"


def test_add_reminder_extracts_content():
    intent = classify("remind me to call mom")
    assert intent.name == "add_reminder"
    assert intent.entities["content"] == "call mom"


def test_unknown_for_unrelated_text():
    assert classify("tell me a joke about spreadsheets").name == "unknown"


def test_empty_input():
    assert classify("   ").name == "empty"


def test_add_deadline_parses_title_and_date():
    intent = classify("add deadline XYZ Internship on 2026-12-01")
    assert intent.name == "add_deadline"
    assert intent.entities["title"] == "XYZ Internship"
    assert intent.entities["date"] == "2026-12-01"


def test_add_deadline_malformed_without_on():
    intent = classify("add deadline XYZ Internship")
    assert intent.name == "add_deadline_malformed"


def test_list_deadlines():
    assert classify("list deadlines").name == "list_deadlines"
