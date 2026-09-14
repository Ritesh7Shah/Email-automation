"""
src/core/models.py
==================
Pure data classes used throughout the system.
No dependencies on email providers, storage, or pandas — just plain Python.

These classes form the contract between the provider layer and the
business logic layer, ensuring the processing logic never needs to know
where the data came from.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ContractorRow:
    """
    One row from the contractor's update spreadsheet.
    Represents a single unit status update submitted by the contractor.
    """
    unit_id: str
    new_status: str
    revised_finish_date: str   # Raw string from Excel (e.g. "2025-08-05")
    notes: str = ""


@dataclass
class TrackerRow:
    """
    One row from the Master Tracker spreadsheet.
    Represents the current state of a single housing unit.
    """
    unit_id: str
    address: str
    status: str
    original_finish_date: str
    revised_finish_date: str
    row_index: int = 0         # 0-based index into the DataFrame (for updates)


@dataclass
class UpdateResult:
    """
    The outcome of processing one contractor row against the master tracker.
    """
    unit_id: str
    address: str
    previous_status: str
    new_status: str
    revised_finish_date: str
    action: str                # "updated" | "skipped" | "not_found" | "error"
    message: str = ""


@dataclass
class UpdateSummary:
    """
    The complete result returned after processing all contractor rows.
    This is what gets formatted into the console/HTML report.
    """
    updated_count: int = 0
    skipped_count: int = 0
    not_found_count: int = 0
    error_count: int = 0

    updated_rows: list[UpdateResult] = field(default_factory=list)
    skipped_rows: list[UpdateResult] = field(default_factory=list)
    not_found_rows: list[UpdateResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    timestamp: str = ""
    contractor_rows_received: int = 0

    def is_clean(self) -> bool:
        """Returns True if the run completed with no errors or not-found units."""
        return self.error_count == 0 and self.not_found_count == 0


@dataclass
class EmailMessage:
    """
    Lightweight representation of an email retrieved from any provider.
    The EmailProvider contract produces these; the rest of the system
    only ever sees EmailMessage objects — never raw API responses.
    """
    message_id: str
    subject: str
    sender: str
    received_at: str           # ISO datetime string
    attachment_filename: str
    attachment_bytes: Optional[bytes] = None
