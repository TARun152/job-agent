"""Gmail API client for send, OTP read, and reply tracking."""

from __future__ import annotations

import base64
from email.message import EmailMessage
from pathlib import Path

from job_agent.config import Settings, get_settings
from job_agent.constants.gmail_const import GMAIL_SCOPES
from job_agent.gmail.otp import extract_otp_from_text
from job_agent.logging_setup import get_logger

pclog = get_logger(__name__)


class GmailClient:
    """Thin wrapper around the Gmail API with local OAuth token storage."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Create a client bound to settings paths.

        Args:
            settings: Optional settings override.
        """
        self.settings = settings or get_settings()
        self._service = None

    def _build_service(self):
        """Build an authenticated Gmail API service.

        Returns:
            Google API ``Resource`` for Gmail.

        Raises:
            FileNotFoundError: If OAuth client secrets are missing.
            RuntimeError: If google-auth libraries fail to authorize.
        """
        if self._service is not None:
            return self._service

        credentials_path = Path(self.settings.gmail_credentials_path)
        token_path = Path(self.settings.gmail_token_path)
        if not credentials_path.exists():
            raise FileNotFoundError(
                f"Gmail OAuth client secrets missing at {credentials_path}. "
                "Download from Google Cloud Console and set GMAIL_CREDENTIALS_PATH."
            )

        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        creds = None
        if token_path.exists():
            # Reuse cached user token when present.
            creds = Credentials.from_authorized_user_file(str(token_path), list(GMAIL_SCOPES))
        if creds is None or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), list(GMAIL_SCOPES)
                )
                # Local browser consent for first-time setup.
                creds = flow.run_local_server(port=0)
            token_path.write_text(creds.to_json(), encoding="utf-8")
            pclog.info("Wrote Gmail OAuth token path=%s", token_path)

        self._service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        pclog.info("Gmail service ready")
        return self._service

    def send_email(self, to_addr: str, subject: str, body: str) -> str:
        """Send a plain-text email via Gmail.

        Args:
            to_addr: Recipient address.
            subject: Subject line.
            body: Plain-text body.

        Returns:
            Gmail message id.
        """
        service = self._build_service()
        message = EmailMessage()
        message["To"] = to_addr
        message["From"] = self.settings.gmail_sender or "me"
        message["Subject"] = subject
        message.set_content(body)
        encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
        # Send through the authenticated mailbox.
        sent = service.users().messages().send(userId="me", body={"raw": encoded}).execute()
        msg_id = sent.get("id", "")
        pclog.info("Sent Gmail message_id=%s to=%s", msg_id, to_addr)
        return msg_id

    def find_latest_otp(
        self, query: str = "newer_than:1d subject:(otp OR verification OR code)"
    ) -> str | None:
        """Search recent mail for a verification OTP.

        Args:
            query: Gmail search query.

        Returns:
            OTP string, or ``None``.
        """
        service = self._build_service()
        # List newest matching messages then inspect snippets/bodies.
        listed = service.users().messages().list(userId="me", q=query, maxResults=5).execute()
        messages = listed.get("messages") or []
        pclog.info("OTP search hits=%s query=%s", len(messages), query)
        for item in messages:
            full = (
                service.users().messages().get(userId="me", id=item["id"], format="full").execute()
            )
            snippet = full.get("snippet") or ""
            payload = full.get("payload") or {}
            body_text = snippet
            for part in payload.get("parts") or []:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    body_text += "\n" + base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8", errors="ignore"
                    )
            otp = extract_otp_from_text(body_text)
            if otp:
                return otp
        return None

    def list_replies(self, query: str, max_results: int = 10) -> list[dict]:
        """List recent threads/messages matching a reply-tracking query.

        Args:
            query: Gmail search query (e.g. from employers).
            max_results: Cap on messages returned.

        Returns:
            List of ``{id, threadId, snippet}`` dicts.
        """
        service = self._build_service()
        listed = (
            service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        )
        results = []
        for item in listed.get("messages") or []:
            meta = (
                service.users()
                .messages()
                .get(userId="me", id=item["id"], format="metadata")
                .execute()
            )
            results.append(
                {
                    "id": meta.get("id", ""),
                    "threadId": meta.get("threadId", ""),
                    "snippet": meta.get("snippet", ""),
                }
            )
        pclog.info("Listed Gmail replies count=%s", len(results))
        return results
