"""
gmail_client.py — Gmail integration for AgentK.

Uses the official Gmail API (OAuth 2.0) to:
  1. Read recent messages from your inbox
  2. Flag ones that look important (internships, deadlines, applications)
  3. Create a DRAFT reply for you to review — it never sends on its own

Setup required before this will work (see README.md "Gmail setup"):
  1. Create a Google Cloud project and enable the Gmail API
  2. Download the OAuth client file and save it as credentials.json in
     this project's root folder
  3. Run the assistant once with --watch; a browser window will open for
     you to sign in and grant access. A token.json file is then saved
     locally so you don't have to log in again.

credentials.json and token.json are both listed in .gitignore — never
commit them, since they grant access to your real inbox.
"""

import base64
import os
from email.mime.text import MIMEText
from typing import List, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail asks you to explicitly grant each scope you use. These two are the
# minimum needed: read messages, and create (but not send) drafts.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]

# Keywords used to flag a message as "important" for internship/program
# deadlines. Edit this list to match what matters to you.
IMPORTANT_KEYWORDS = [
    "internship", "registration", "deadline", "apply", "application",
    "selection", "admit card", "last date", "shortlisted", "interview",
    "offer letter", "registration closes", "submission deadline",
]


class GmailClient:
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None

    def authenticate(self) -> None:
        """Handles the OAuth flow. Opens a browser the first time; reuses
        the saved token silently on every run after that."""
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"'{self.credentials_path}' not found. See README.md 'Gmail setup' "
                        "for how to get this file from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.token_path, "w") as f:
                f.write(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds)

    def fetch_recent_messages(self, max_results: int = 10) -> List[Dict]:
        """Returns the most recent inbox messages as simple dicts."""
        if not self.service:
            self.authenticate()

        results = self.service.users().messages().list(
            userId="me", labelIds=["INBOX"], maxResults=max_results
        ).execute()
        message_refs = results.get("messages", [])

        messages = []
        for ref in message_refs:
            msg = self.service.users().messages().get(
                userId="me", id=ref["id"], format="metadata",
                metadataHeaders=["Subject", "From", "Date"],
            ).execute()
            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
            messages.append({
                "id": msg["id"],
                "threadId": msg["threadId"],
                "subject": headers.get("Subject", "(no subject)"),
                "sender": headers.get("From", "unknown"),
                "date": headers.get("Date", ""),
                "snippet": msg.get("snippet", ""),
            })
        return messages

    @staticmethod
    def is_important(subject: str, snippet: str) -> bool:
        """Simple keyword match against subject + preview text."""
        text = f"{subject} {snippet}".lower()
        return any(keyword in text for keyword in IMPORTANT_KEYWORDS)

    def create_draft_reply(self, message_id: str, thread_id: str, to: str, subject: str, body: str) -> str:
        """Creates a draft reply in Gmail. Does NOT send it — the message
        will sit in your Drafts folder until you review and send it
        yourself."""
        if not self.service:
            self.authenticate()

        reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = reply_subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        draft = self.service.users().drafts().create(
            userId="me",
            body={"message": {"raw": raw, "threadId": thread_id}},
        ).execute()
        return draft["id"]


def suggest_reply_text(subject: str, snippet: str) -> str:
    """Generates a short, safe placeholder reply for you to edit before
    sending. Kept deliberately generic rather than guessing specifics,
    since an AI-guessed reply to something like an internship offer could
    easily say the wrong thing if sent without review."""
    return (
        "Hi,\n\n"
        "Thank you for reaching out. I've seen this message and will "
        "respond with more detail shortly.\n\n"
        "Best regards,\n"
        "Brishti"
    )
