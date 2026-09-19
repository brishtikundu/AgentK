# AgentK — Intelligent Assistant

AgentK is a Python command-line assistant that understands natural-language
requests — greetings, quick math, notes, and reminders — and responds through
a small, testable intent-classification pipeline. It runs fully offline by
default, with an optional AI-powered fallback for messages the rule-based
engine can't confidently classify.

## How it works

AgentK processes every message through three stages:

```
User input
    │
    ▼
1. nlp.classify()      → figures out what the user wants (an "Intent")
    │
    ▼
2. intents.HANDLERS    → runs the matching handler function
    │
    ▼
3. storage.Storage     → reads/writes notes & reminders as needed
    │
    ▼
Response back to user
```

**1. Intent classification (`agentk/nlp.py`)**
Incoming text is matched against a set of keyword and pattern rules — e.g.
`"remind me to <x>"` → `add_reminder`, or a bare arithmetic expression →
`calculate`. This keeps the assistant fast, dependency-free, and fully
predictable for testing.

An optional `classify_with_ai()` function is also included: if an
`OPENAI_API_KEY` is set and the assistant is started with `--ai`, unmatched
messages are sent to an LLM for classification instead of falling through to
"unknown." This is the AI-feature-integration layer, isolated behind a single
function so the assistant works with or without it.

**2. Intent handlers (`agentk/intents.py`)**
Each intent (greeting, calculate, add_note, list_reminders, etc.) has its own
small, pure function that takes the extracted entities and returns a response
string. Keeping these isolated made it straightforward to test — and fix —
each behaviour individually while iterating on response accuracy.

**3. Storage (`agentk/storage.py`)**
Notes and reminders persist to a local JSON file (`data/agentk_data.json`),
so they survive between runs without needing a database.

**4. Orchestration (`agentk/assistant.py`)**
The `Assistant` class wires the three pieces together and keeps a
conversation history, so its behaviour can be inspected or replayed in tests.

## Getting started

```bash
git clone https://github.com/brishtikundu/AgentK.git
cd AgentK
pip install -r requirements.txt
python main.py
```

Example session:

```
AgentK is ready. Type 'help' for commands, 'exit' to quit.

you> hi
AgentK: Hey there! I'm AgentK. Type 'help' to see what I can do.

you> calculate 8 * 6
AgentK: 8 * 6 = 48

you> remind me to submit assignment
AgentK: Reminder #1 set: submit assignment

you> list reminders
AgentK: 1. submit assignment
```

### Optional: enable the AI fallback

```bash
export OPENAI_API_KEY=your_key_here
python main.py --ai
```

## Running the tests

Response accuracy is verified with a suite of unit and integration tests —
21 tests covering the classifier, each intent handler, and full
conversation flows through the `Assistant` class:

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Project structure

```
AgentK/
├── agentk/
│   ├── __init__.py
│   ├── assistant.py    # orchestrates classify → handle → respond
│   ├── nlp.py           # rule-based classifier + optional AI fallback
│   ├── intents.py       # one handler function per intent
│   └── storage.py       # JSON-backed notes & reminders
├── tests/
│   ├── test_nlp.py
│   ├── test_intents.py
│   └── test_assistant.py
├── main.py               # CLI entry point
├── requirements.txt
└── README.md
```

## Watch mode — automatic Gmail & deadline alerts

Beyond the interactive chat, AgentK can run in the background and **automatically**
notify you (sound + desktop popup) when:

- A new Gmail message looks important (matches keywords like "internship",
  "deadline", "application", "shortlisted", "admit card", etc.), and
  automatically creates a **draft** reply in Gmail for you to review
- A tracked deadline is 3 days away, 1 day away, or due today

```bash
python main.py --watch
```

Options:
- `--interval 30` — check every 30 minutes instead of the default 15
- `--no-gmail` — only monitor deadlines, skip Gmail entirely

**Important:** this never sends emails automatically. It creates drafts in
your Gmail Drafts folder so you stay in control of what actually gets sent —
an AI misreading context on something like an internship offer could easily
say the wrong thing if it were allowed to send on its own.

### Gmail setup (one-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/), create a
   new project, and enable the **Gmail API**.
2. Go to "Credentials" → "Create Credentials" → "OAuth client ID" → choose
   "Desktop app".
3. Download the resulting JSON file, rename it to `credentials.json`, and
   place it in this project's root folder (next to `main.py`).
4. Run `python main.py --watch` — a browser window will open asking you to
   sign in and grant access. After the first successful login, a
   `token.json` file is saved so you won't need to log in again.

`credentials.json` and `token.json` are both already in `.gitignore` —
**never commit either file**, since they grant access to your real inbox.

### Tracking deadlines

From the normal chat mode:

```
you> add deadline XYZ Internship on 2026-12-01
AgentK: Deadline added: 'XYZ Internship' on 2026-12-01. I'll alert you at 3 days, 1 day, and on the day.

you> list deadlines
AgentK: 1. XYZ Internship — 2026-12-01
```

Once added, `--watch` mode checks these automatically and fires a
notification at each threshold — no need to keep the chat open.

## Possible next steps

- Swap the JSON storage for SQLite as data grows
- Extract candidate deadline dates directly from flagged emails
- Wrap the assistant in a small Flask API for a web front end
