"""
main.py — Run AgentK from the command line.

Usage:
    python main.py

Type 'help' once it starts to see available commands, or 'exit' to quit.
Set the OPENAI_API_KEY environment variable and pass --ai to enable the
optional AI fallback for messages the rule-based engine can't classify.
"""

import argparse

from agentk.assistant import Assistant


def main():
    parser = argparse.ArgumentParser(description="AgentK — an intelligent assistant.")
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Enable OpenAI-powered fallback classification (requires OPENAI_API_KEY).",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Start the background watcher: auto-notifies on important Gmail messages "
             "and upcoming deadlines, and drafts (but never sends) email replies.",
    )
    parser.add_argument(
        "--no-gmail",
        action="store_true",
        help="With --watch, skip Gmail checks and only monitor deadlines.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=15,
        help="With --watch, how often to poll, in minutes (default 15).",
    )
    args = parser.parse_args()

    if args.watch:
        from agentk.watcher import run_watch_loop
        run_watch_loop(poll_interval_minutes=args.interval, use_gmail=not args.no_gmail)
        return

    assistant = Assistant(use_ai_fallback=args.ai)

    print("AgentK is ready. Type 'help' for commands, 'exit' to quit.\n")
    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAgentK: Goodbye! 👋")
            break

        if not user_input:
            continue

        response = assistant.respond(user_input)
        print(f"AgentK: {response}\n")

        if assistant.is_exit(user_input):
            break


if __name__ == "__main__":
    main()
