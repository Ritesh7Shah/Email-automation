"""
config/settings.py
==================
Central configuration for the Renovation Tracker Automation POC.

All values have safe defaults so the demo works with zero environment
variable setup (just run: python src/main.py --mode demo).

For Gmail integration, copy .env.example to .env and fill in the values.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env file if present (silently ignored if not found) ─────────────────
load_dotenv(override=False)

# ── Project root (parent of config/) ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Run mode ──────────────────────────────────────────────────────────────────
# "demo"  → reads local files directly, no email API needed
# "gmail" → polls Gmail inbox for contractor email, downloads attachment
RUN_MODE: str = os.getenv("RUN_MODE", "demo").lower()

# ── File paths ────────────────────────────────────────────────────────────────
MASTER_TRACKER_PATH: Path = PROJECT_ROOT / os.getenv(
    "MASTER_TRACKER_PATH", "data/Master_Tracker.xlsx"
)
CONTRACTOR_UPDATE_PATH: Path = PROJECT_ROOT / os.getenv(
    "CONTRACTOR_UPDATE_PATH", "data/Contractor_Update.xlsx"
)
OUTPUT_DIR: Path = PROJECT_ROOT / os.getenv("OUTPUT_DIR", "output")

# ── Gmail settings (only required when RUN_MODE=gmail) ────────────────────────
GMAIL_MONITOR_ADDRESS: str  = os.getenv("GMAIL_MONITOR_ADDRESS", "")
GMAIL_SUBJECT_FILTER: str   = os.getenv("GMAIL_SUBJECT_FILTER", "Biweekly Renovation Update")
GMAIL_ATTACHMENT_FILENAME: str = os.getenv("GMAIL_ATTACHMENT_FILENAME", "Contractor_Update.xlsx")
GMAIL_CREDENTIALS_FILE: Path = PROJECT_ROOT / os.getenv(
    "GMAIL_CREDENTIALS_FILE", "config/gmail_credentials.json"
)
GMAIL_TOKEN_FILE: Path = PROJECT_ROOT / os.getenv(
    "GMAIL_TOKEN_FILE", "config/gmail_token.json"
)

# ── Gmail OAuth2 scopes ───────────────────────────────────────────────────────
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",  # needed to mark as read
]

# ── Coordinator email (optional — for sending summary email) ──────────────────
COORDINATOR_EMAIL: str = os.getenv("COORDINATOR_EMAIL", "")

# ── Business rules ────────────────────────────────────────────────────────────
# Column names in Master_Tracker.xlsx (must match exactly)
MASTER_COL_UNIT_ID          = "Unit ID"
MASTER_COL_ADDRESS          = "Property Address"
MASTER_COL_STATUS           = "Status"
MASTER_COL_ORIGINAL_FINISH  = "Original Finish Date"
MASTER_COL_REVISED_FINISH   = "Revised Finish Date"

# Column names in Contractor_Update.xlsx (must match exactly)
CONTRACTOR_COL_UNIT_ID      = "Unit ID"
CONTRACTOR_COL_NEW_STATUS   = "New Status"
CONTRACTOR_COL_REVISED_DATE = "Revised Finish Date"
CONTRACTOR_COL_NOTES        = "Notes"

# Sheet name in Master_Tracker.xlsx (matches Office Script version)
MASTER_SHEET_NAME = "Master Tracker"
