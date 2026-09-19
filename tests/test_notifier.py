from agentk import notifier


def test_play_alert_sound_never_raises():
    # Should never throw even in a headless/no-audio environment.
    notifier.play_alert_sound()


def test_send_desktop_notification_never_raises():
    notifier.send_desktop_notification("Test title", "Test message")


def test_alert_combines_both_without_raising():
    notifier.alert("Test alert", "This should not crash.")
