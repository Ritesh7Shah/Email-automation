"""
src/providers/gmail_provider.py
=================================
Gmail implementation of EmailProvider.

Supports two sub-modes:

  1. LOCAL SIMULATION (demo_inbox/ folder)
     ─────────────────────────────────────
     For client demos where you don't want to configure the Gmail API.
     Drop Contractor_Update.xlsx into the demo_inbox/ folder.
     The provider picks it up as if it came from an email.
     No credentials, no internet connection needed.

  2. REAL GMAIL API
     ───────────────
     Polls your actual Gmail inbox via the Gmail REST API.
     Uses OAuth2 with a credentials.json from Google Cloud Console.
     Requires GMAIL_CREDENTIALS_FILE and GMAIL_TOKEN_FILE in .env.

Usage (controlled by the --mode flag in main.py):
  --mode demo   → Uses local simulation (no Gmail API)
  --mode gmail  → Uses real Gmail API
"""

import base64
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.providers.email_provider import EmailProvider
from src.core.models import EmailMessage
from config import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Mode 1 — Local Simulation Provider
# ─────────────────────────────────────────────────────────────────────────────

class LocalSimulationEmailProvider(EmailProvider):
    """
    Simulates an email inbox by watching a local folder (demo_inbox/).

    For the client demo:
      1. Place Contractor_Update.xlsx in the demo_inbox/ folder.
      2. Run: python src/main.py --mode demo
      3. The script picks it up, processes it, and moves it to demo_inbox/processed/

    This is the most reliable mode for a live client demonstration.
    No internet connection, no credentials, no API limits.
    """

    DEMO_INBOX_DIR = settings.PROJECT_ROOT / "demo_inbox"
    PROCESSED_DIR  = settings.PROJECT_ROOT / "demo_inbox" / "processed"

    @property
    def provider_name(self) -> str:
        return "Local Simulation (Demo Mode)"

    def _ensure_dirs(self) -> None:
        self.DEMO_INBOX_DIR.mkdir(parents=True, exist_ok=True)
        self.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    def fetch_unread_contractor_emails(self) -> list[EmailMessage]:
        """
        Scan demo_inbox/ for .xlsx files.
        Each file is treated as a contractor email attachment.
        """
        self._ensure_dirs()
        messages = []

        for xlsx_file in self.DEMO_INBOX_DIR.glob("*.xlsx"):
            msg = EmailMessage(
                message_id=xlsx_file.name,
                subject=settings.GMAIL_SUBJECT_FILTER,
                sender="contractor@demo.local",
                received_at=datetime.now().isoformat(),
                attachment_filename=xlsx_file.name,
                attachment_bytes=xlsx_file.read_bytes()
            )
            messages.append(msg)
            logger.info(f"[Demo Inbox] Found: {xlsx_file.name}")

        if not messages:
            logger.warning(
                f"[Demo Inbox] No .xlsx files found in: {self.DEMO_INBOX_DIR}\n"
                f"  -> Using the default Contractor_Update.xlsx from data/ instead."
            )

        return messages

    def download_attachment(
        self,
        message_id: str,
        attachment_filename: str
    ) -> Optional[bytes]:
        """
        Returns the bytes already loaded during fetch.
        The LocalSimulation provider eagerly loads attachment bytes in fetch().
        """
        file_path = self.DEMO_INBOX_DIR / message_id
        if file_path.exists():
            return file_path.read_bytes()
        return None

    def mark_as_processed(self, message_id: str) -> None:
        """
        Move the processed file to demo_inbox/processed/ so it won't be
        picked up again on the next run.
        """
        self._ensure_dirs()
        src = self.DEMO_INBOX_DIR / message_id
        dst = self.PROCESSED_DIR / message_id

        if src.exists():
            src.rename(dst)
            logger.info(f"[Demo Inbox] Moved to processed: {message_id}")


# ─────────────────────────────────────────────────────────────────────────────
# Mode 2 — Real Gmail API Provider
# ─────────────────────────────────────────────────────────────────────────────

class GmailEmailProvider(EmailProvider):
    """
    Real Gmail API integration using OAuth2.

    Setup:
      1. Go to https://console.cloud.google.com/
      2. Create a project → Enable Gmail API
      3. Create OAuth2 Desktop credentials → Download credentials.json
      4. Place credentials.json at the path in GMAIL_CREDENTIALS_FILE (.env)
      5. Run once: python src/main.py --mode gmail
         → Browser will open for OAuth consent
         → Token is cached in GMAIL_TOKEN_FILE for future runs

    Scopes used:
      - gmail.readonly  : read emails and attachments
      - gmail.modify    : mark emails as read after processing
    """

    def __init__(self) -> None:
        self._service = None

    @property
    def provider_name(self) -> str:
        return "Gmail API"

    def _get_service(self):
        """
        Lazily initialise the Gmail API service.
        On first call, performs OAuth2 flow (opens browser for consent).
        Subsequent calls reuse the cached token.
        """
        if self._service is not None:
            return self._service

        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError(
                "Google API libraries not installed. Run:\n"
                "  pip install google-api-python-client google-auth-oauthlib"
            )

        creds = None
        token_path = settings.GMAIL_TOKEN_FILE

        # Load cached token if available
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(
                str(token_path), settings.GMAIL_SCOPES
            )

        # Refresh or re-authorise if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                creds_path = settings.GMAIL_CREDENTIALS_FILE
                if not creds_path.exists():
                    raise FileNotFoundError(
                        f"Gmail credentials not found at: {creds_path}\n"
                        f"Download from Google Cloud Console and set GMAIL_CREDENTIALS_FILE in .env"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(creds_path), settings.GMAIL_SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Cache the token for future runs
            token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(token_path, "w") as f:
                f.write(creds.to_json())

        from googleapiclient.discovery import build
        self._service = build("gmail", "v1", credentials=creds)
        return self._service

    def fetch_unread_contractor_emails(self) -> list[EmailMessage]:
        """
        Query Gmail for unread emails matching the subject filter
        that also have an Excel attachment.
        """
        service = self._get_service()

        # Build Gmail search query
        query = (
            f'subject:"{settings.GMAIL_SUBJECT_FILTER}" '
            f'is:unread '
            f'has:attachment'
        )

        logger.info(f"[Gmail] Searching with query: {query}")

        results = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=10
        ).execute()

        raw_messages = results.get("messages", [])
        logger.info(f"[Gmail] Found {len(raw_messages)} matching email(s)")

        email_messages = []

        for raw in raw_messages:
            msg_id = raw["id"]
            full_msg = service.users().messages().get(
                userId="me", id=msg_id, format="full"
            ).execute()

            headers = {
                h["name"]: h["value"]
                for h in full_msg["payload"].get("headers", [])
            }

            subject   = headers.get("Subject", "")
            sender    = headers.get("From", "")
            date_str  = headers.get("Date", "")

            # Find the xlsx attachment
            attachment_part = self._find_attachment_part(
                full_msg["payload"],
                settings.GMAIL_ATTACHMENT_FILENAME
            )

            if attachment_part is None:
                logger.warning(f"[Gmail] Email {msg_id} matched but has no .xlsx attachment — skipping")
                continue

            email_messages.append(EmailMessage(
                message_id=msg_id,
                subject=subject,
                sender=sender,
                received_at=date_str,
                attachment_filename=attachment_part.get("filename", "attachment.xlsx"),
                attachment_bytes=None  # Loaded lazily via download_attachment()
            ))

        return email_messages

    def _find_attachment_part(
        self, payload: dict, expected_filename: str
    ) -> Optional[dict]:
        """
        Recursively search email parts for the xlsx attachment.
        Returns the message part dict if found, else None.
        """
        # Check this part
        filename = payload.get("filename", "")
        if filename.lower().endswith(".xlsx"):
            return payload

        # Recurse into nested parts
        for part in payload.get("parts", []):
            result = self._find_attachment_part(part, expected_filename)
            if result:
                return result

        return None

    def download_attachment(
        self,
        message_id: str,
        attachment_filename: str
    ) -> Optional[bytes]:
        """
        Download the raw bytes of the xlsx attachment from Gmail.
        """
        service = self._get_service()

        full_msg = service.users().messages().get(
            userId="me", id=message_id, format="full"
        ).execute()

        attachment_part = self._find_attachment_part(
            full_msg["payload"], attachment_filename
        )

        if attachment_part is None:
            return None

        # The attachment data may be inline or referenced by attachment ID
        body = attachment_part.get("body", {})
        attachment_id = body.get("attachmentId")

        if attachment_id:
            # Fetch by attachment ID (large attachments are stored separately)
            attachment = service.users().messages().attachments().get(
                userId="me", messageId=message_id, id=attachment_id
            ).execute()
            data = attachment["data"]
        else:
            # Small attachment — data is inline in the body
            data = body.get("data", "")

        if not data:
            return None

        # Gmail uses URL-safe base64 encoding
        return base64.urlsafe_b64decode(data + "==")

    def mark_as_processed(self, message_id: str) -> None:
        """
        Remove the UNREAD label from the processed email.
        """
        service = self._get_service()
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()
        logger.info(f"[Gmail] Marked as read: {message_id}")
