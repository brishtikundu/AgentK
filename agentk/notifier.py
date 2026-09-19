"""
notifier.py — Desktop notifications and sound alerts for AgentK.

Used to flag important Gmail messages and upcoming deadlines the moment
they're detected, without requiring the terminal window to be in focus.
Degrades gracefully on any platform/environment where sound or desktop
notifications aren't available, so the watcher loop never crashes because
of a missing audio device or display.
"""

import platform
import sys


def play_alert_sound() -> None:
    """Play a short alert sound. Falls back to the terminal bell if the
    platform-specific sound API isn't available."""
    system = platform.system()
    try:
        if system == "Windows":
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        elif system == "Darwin":  # macOS
            import os
            os.system("afplay /System/Library/Sounds/Glass.aiff")
        else:  # Linux and anything else
            import os
            os.system("paplay /usr/share/sounds/freedesktop/stereo/bell.oga 2>/dev/null")
    except Exception:
        # No audio device / library available — fall back to the terminal bell.
        sys.stdout.write("\a")
        sys.stdout.flush()


def send_desktop_notification(title: str, message: str) -> None:
    """Show a desktop popup notification. Falls back to printing to the
    console if the `plyer` library or OS notification service isn't
    available (e.g. running over SSH or in a headless environment)."""
    try:
        from plyer import notification
        notification.notify(title=title, message=message, app_name="AgentK", timeout=10)
    except Exception:
        print(f"[AgentK notification] {title}: {message}")


def alert(title: str, message: str) -> None:
    """Convenience helper: sound + desktop notification together."""
    play_alert_sound()
    send_desktop_notification(title, message)
