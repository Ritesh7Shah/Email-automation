"""
src/providers/email_provider.py
================================
Abstract base class (ABC) for email providers.

The system only talks to this interface — never to Gmail or Outlook directly.
To switch from Gmail to Outlook, create an OutlookEmailProvider that
implements these same methods. Zero business logic changes required.

Contract:
  - fetch_unread_contractor_emails() → list[EmailMessage]
  - mark_as_processed(message_id)
"""

from abc import ABC, abstractmethod
from typing import Optional
from src.core.models import EmailMessage


class EmailProvider(ABC):
    """
    Provider-agnostic interface for receiving contractor emails.

    Demo implementation  : GmailEmailProvider (gmail_provider.py)
    Production implementation: OutlookEmailProvider (future — outlook_provider.py)
    """

    @abstractmethod
    def fetch_unread_contractor_emails(self) -> list[EmailMessage]:
        """
        Poll the inbox and return all unread emails that match the
        contractor update criteria (subject filter + has .xlsx attachment).

        Returns:
            List of EmailMessage objects. May be empty if no matching emails.
        """
        ...

    @abstractmethod
    def download_attachment(
        self,
        message_id: str,
        attachment_filename: str
    ) -> Optional[bytes]:
        """
        Download the binary content of a specific attachment.

        Args:
            message_id: Provider-specific identifier for the email.
            attachment_filename: Filename to look for in the attachments.

        Returns:
            Raw bytes of the attachment, or None if not found.
        """
        ...

    @abstractmethod
    def mark_as_processed(self, message_id: str) -> None:
        """
        Mark the email as read / processed so it is not picked up again
        on the next poll.

        Args:
            message_id: Provider-specific identifier for the email.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name of this provider (e.g. 'Gmail', 'Outlook')."""
        ...
