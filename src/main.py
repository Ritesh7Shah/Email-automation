"""
src/main.py
============
Entry point for the Renovation Tracker Automation POC.

Run modes:
  python src/main.py                  → demo mode (reads local files)
  python src/main.py --mode demo      → same as above
  python src/main.py --mode gmail     → real Gmail API integration

The script:
  1. Selects the correct email + storage providers based on --mode
  2. Fetches contractor update file (email attachment or local)
  3. Runs the ContractorUpdateProcessor (business logic)
  4. Saves the updated Master Tracker to output/
  5. Prints a coloured console report
  6. Generates and auto-opens an HTML summary report

Usage:
  cd email-automation
  python src/main.py
  python src/main.py --mode gmail
"""

import argparse
import logging
import sys
from pathlib import Path

# ── Add project root to sys.path so all imports work from any CWD ─────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── Now import project modules ─────────────────────────────────────────────────
from config import settings
from src.core.models import EmailMessage
from src.core.processor import ContractorUpdateProcessor
from src.providers.email_provider import EmailProvider
from src.providers.storage_provider import LocalStorageProvider
from src.providers.gmail_provider import LocalSimulationEmailProvider, GmailEmailProvider
from src.reporting.reporter import print_console_report, generate_html_report

# ── Configure logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Renovation Tracker Automation — POC Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py                    # Demo mode (local files)
  python src/main.py --mode demo        # Same as above
  python src/main.py --mode gmail       # Real Gmail API
  python src/main.py --no-browser       # Skip auto-opening HTML report
        """
    )
    parser.add_argument(
        "--mode",
        choices=["demo", "gmail"],
        default=settings.RUN_MODE,
        help="Run mode: 'demo' (local files) or 'gmail' (Gmail API). Default: demo",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        default=False,
        help="Do not auto-open the HTML report in the browser.",
    )
    return parser.parse_args()


def build_email_provider(mode: str) -> EmailProvider:
    """Factory: return the correct email provider for the given mode."""
    if mode == "gmail":
        logger.info("Mode: Gmail API")
        return GmailEmailProvider()
    else:
        logger.info("Mode: Local Simulation (Demo)")
        return LocalSimulationEmailProvider()


def run(mode: str, auto_open_browser: bool) -> None:
    """
    Main automation pipeline.

    1. Select providers
    2. Fetch contractor update (email or local)
    3. Process updates (business logic)
    4. Save updated tracker
    5. Report results
    """

    print()
    print("=" * 62)
    print("  RENOVATION TRACKER AUTOMATION POC")
    print("=" * 62)
    print(f"  Mode: {mode.upper()}")
    print()

    # ── 1. Initialise providers ────────────────────────────────────────────────
    email_provider   = build_email_provider(mode)
    storage_provider = LocalStorageProvider()
    processor        = ContractorUpdateProcessor()

    logger.info(f"Email Provider  : {email_provider.provider_name}")
    logger.info(f"Storage Provider: {storage_provider.provider_name}")

    # ── 2. Load Master Tracker ─────────────────────────────────────────────────
    logger.info("Loading Master Tracker...")
    try:
        master_df = storage_provider.read_master_tracker()
        logger.info(f"Master Tracker: {len(master_df)} rows loaded")
    except FileNotFoundError as e:
        print(f"\n❌  {e}\n")
        sys.exit(1)

    # ── 3. Get contractor update ───────────────────────────────────────────────
    contractor_bytes: bytes | None = None

    if mode == "demo":
        # In demo mode, check the demo_inbox/ folder first.
        # If nothing there, fall back to the default data/ path.
        messages = email_provider.fetch_unread_contractor_emails()

        if messages:
            msg = messages[0]
            logger.info(f"Using file from demo_inbox: {msg.attachment_filename}")
            contractor_bytes = msg.attachment_bytes
            email_provider.mark_as_processed(msg.message_id)
        else:
            # Fallback: use the file directly from data/
            logger.info(f"Falling back to: {settings.CONTRACTOR_UPDATE_PATH}")
            contractor_bytes = None  # LocalStorageProvider will read from data/

    else:
        # Gmail mode: poll inbox
        logger.info("Polling Gmail inbox for contractor email...")
        messages = email_provider.fetch_unread_contractor_emails()

        if not messages:
            print("\n⚠️  No unread contractor emails found in Gmail inbox.")
            print("    Make sure the contractor has sent the email with subject:")
            print(f"    '{settings.GMAIL_SUBJECT_FILTER}'")
            print()

            # Fall back to local file for demo continuity
            logger.info("Falling back to local Contractor_Update.xlsx for demo")
            contractor_bytes = None

        else:
            msg = messages[0]
            logger.info(f"Found email from: {msg.sender} | Subject: {msg.subject}")
            contractor_bytes = email_provider.download_attachment(
                msg.message_id,
                msg.attachment_filename
            )
            email_provider.mark_as_processed(msg.message_id)

    # ── 4. Load contractor update DataFrame ────────────────────────────────────
    logger.info("Loading Contractor Update...")
    try:
        contractor_df = storage_provider.read_contractor_update(source=contractor_bytes)
        logger.info(f"Contractor Update: {len(contractor_df)} rows loaded")
    except FileNotFoundError as e:
        print(f"\n❌  {e}\n")
        sys.exit(1)

    # ── 5. Run the business logic processor ───────────────────────────────────
    logger.info("Processing updates...")
    updated_df, summary = processor.process(master_df, contractor_df)

    # ── 6. Save updated Master Tracker ────────────────────────────────────────
    logger.info("Saving updated Master Tracker...")
    saved_path = storage_provider.save_master_tracker(updated_df)
    logger.info(f"Updated tracker saved to: {saved_path}")

    # ── 7. Print console report ────────────────────────────────────────────────
    print_console_report(summary, provider_name=email_provider.provider_name)

    # ── 8. Generate HTML report ────────────────────────────────────────────────
    html_path = generate_html_report(
        summary,
        auto_open=auto_open_browser,
        provider_name=email_provider.provider_name,
    )

    # ── 9. Final summary ───────────────────────────────────────────────────────
    print(f"  [+] Updated tracker -> {saved_path}")
    print(f"  [+] HTML report     -> {html_path}")
    print()


def main() -> None:
    args = parse_args()
    run(
        mode=args.mode,
        auto_open_browser=not args.no_browser,
    )


if __name__ == "__main__":
    main()
