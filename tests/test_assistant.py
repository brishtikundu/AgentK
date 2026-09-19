import pytest

from agentk.assistant import Assistant
from agentk.storage import Storage


@pytest.fixture
def assistant(tmp_path):
    storage = Storage(path=str(tmp_path / "data.json"))
    return Assistant(storage=storage)


def test_greeting_flow(assistant):
    response = assistant.respond("hi")
    assert "AgentK" in response


def test_note_round_trip(assistant):
    assistant.respond("add note finish resume")
    response = assistant.respond("list notes")
    assert "finish resume" in response


def test_calculate_flow(assistant):
    response = assistant.respond("calculate 10 / 2")
    assert "5" in response


def test_history_is_recorded(assistant):
    assistant.respond("hello")
    assistant.respond("time")
    assert len(assistant.history) == 2
    assert assistant.history[0][1] == "greeting"
    assert assistant.history[1][1] == "time"


def test_is_exit_detection(assistant):
    assert assistant.is_exit("bye") is True
    assert assistant.is_exit("hello") is False
