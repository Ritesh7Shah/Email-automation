"""
src/reporting/reporter.py
==========================
Generates the summary report in two formats:

  1. Console report  — coloured terminal output (always shown)
  2. HTML report     — saved to output/summary_report.html and auto-opened

No dependencies on email providers or storage — only takes an UpdateSummary.
"""

import logging
import os
import webbrowser
from datetime import datetime
from pathlib import Path

from colorama import Fore, Back, Style, init as colorama_init

from src.core.models import UpdateSummary, UpdateResult
from config import settings

# Initialise colorama (required for Windows terminal colour support)
colorama_init(autoreset=True)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Console Reporter
# ─────────────────────────────────────────────────────────────────────────────

def print_console_report(summary: UpdateSummary, provider_name: str = "") -> None:
    """
    Print a formatted, coloured summary to the terminal.
    """
    divider  = Fore.CYAN + "-" * 62 + Style.RESET_ALL
    bold     = Style.BRIGHT

    print()
    print(divider)
    print(f"{bold}{Fore.CYAN}  RENOVATION TRACKER -- AUTOMATION SUMMARY{Style.RESET_ALL}")
    print(divider)

    if provider_name:
        print(f"  Provider  : {Fore.YELLOW}{provider_name}{Style.RESET_ALL}")

    print(f"  Timestamp : {summary.timestamp}")
    print(f"  Rows Recv : {summary.contractor_rows_received} contractor update(s)")
    print()

    # ── Counts table ─────────────────────────────────────────────────────────
    print(f"  {bold}{'METRIC':<30}{'COUNT':>8}{Style.RESET_ALL}")
    print(f"  {'_'*38}")
    print(f"  {Fore.GREEN}{'[OK] Units Updated':<30}{summary.updated_count:>8}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{'[--] Units Skipped (no change)':<30}{summary.skipped_count:>8}{Style.RESET_ALL}")
    print(f"  {Fore.MAGENTA}{'[?]  Unit IDs Not Found':<30}{summary.not_found_count:>8}{Style.RESET_ALL}")
    print(f"  {Fore.RED}{'[X]  Errors':<30}{summary.error_count:>8}{Style.RESET_ALL}")
    print()

    # ── Updated rows detail ───────────────────────────────────────────────────
    if summary.updated_rows:
        print(f"  {bold}{Fore.GREEN}UPDATED UNITS:{Style.RESET_ALL}")
        for r in summary.updated_rows:
            print(
                f"  {Fore.GREEN}  * {r.unit_id:<10}{Style.RESET_ALL}"
                f"  {r.address:<35}"
                f"  {Fore.YELLOW}{r.previous_status}{Style.RESET_ALL}"
                f"  ->  {Fore.GREEN}{r.new_status}{Style.RESET_ALL}"
            )
        print()

    # ── Skipped rows detail ───────────────────────────────────────────────────
    if summary.skipped_rows:
        print(f"  {bold}{Fore.YELLOW}SKIPPED (STATUS UNCHANGED):{Style.RESET_ALL}")
        for r in summary.skipped_rows:
            print(
                f"  {Fore.YELLOW}  * {r.unit_id:<10}{Style.RESET_ALL}"
                f"  Status was already: '{r.previous_status}'"
            )
        print()

    # ── Not found rows detail ─────────────────────────────────────────────────
    if summary.not_found_rows:
        print(f"  {bold}{Fore.MAGENTA}NOT FOUND IN MASTER TRACKER:{Style.RESET_ALL}")
        for r in summary.not_found_rows:
            print(f"  {Fore.MAGENTA}  * {r.unit_id}{Style.RESET_ALL}")
        print()

    # ── Errors ────────────────────────────────────────────────────────────────
    if summary.errors:
        print(f"  {bold}{Fore.RED}ERRORS:{Style.RESET_ALL}")
        for e in summary.errors:
            print(f"  {Fore.RED}  ✗ {e}{Style.RESET_ALL}")
        print()

    # ── Final status ──────────────────────────────────────────────────────────
    if summary.is_clean():
        print(f"  {Fore.GREEN}{bold}[OK] Run completed successfully -- no errors.{Style.RESET_ALL}")
    else:
        print(f"  {Fore.YELLOW}{bold}[!] Run completed with warnings -- review above.{Style.RESET_ALL}")

    print(divider)
    print()


# ─────────────────────────────────────────────────────────────────────────────
# HTML Reporter
# ─────────────────────────────────────────────────────────────────────────────

def generate_html_report(
    summary: UpdateSummary,
    output_path: Path | None = None,
    auto_open: bool = True,
    provider_name: str = "",
) -> str:
    """
    Generate a polished HTML summary report and save it to disk.

    Args:
        summary: The UpdateSummary from the processor.
        output_path: Where to save the HTML file. Defaults to output/summary_report.html
        auto_open: If True, opens the file in the default browser after saving.
        provider_name: Label to show in the report header.

    Returns:
        Absolute path to the saved HTML file.
    """
    if output_path is None:
        output_dir = settings.OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "summary_report.html"

    html = _build_html(summary, provider_name)
    output_path.write_text(html, encoding="utf-8")

    logger.info(f"HTML report saved to: {output_path}")

    if auto_open:
        webbrowser.open(f"file:///{output_path.resolve()}")

    return str(output_path)


def _build_html(summary: UpdateSummary, provider_name: str) -> str:
    """Build the complete HTML string for the report."""

    updated_rows_html   = _rows_to_html(summary.updated_rows,   "updated")
    skipped_rows_html   = _rows_to_html(summary.skipped_rows,   "skipped")
    not_found_rows_html = _rows_to_html(summary.not_found_rows, "not_found")

    errors_html = ""
    if summary.errors:
        error_items = "".join(f"<li>{e}</li>" for e in summary.errors)
        errors_html = f"""
        <div class="section error-section">
            <h3>❌ Errors</h3>
            <ul class="error-list">{error_items}</ul>
        </div>"""

    status_badge = (
        '<span class="badge badge-success">✅ Clean Run</span>'
        if summary.is_clean() else
        '<span class="badge badge-warning">⚠️ Review Required</span>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Renovation Tracker — Automation Report</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #0f1e36;
            color: #e0e8f0;
            min-height: 100vh;
            padding: 32px 16px;
        }}

        .container {{ max-width: 900px; margin: 0 auto; }}

        header {{
            background: linear-gradient(135deg, #1a3a5c 0%, #0f2744 100%);
            border: 1px solid #2a4a6c;
            border-radius: 12px;
            padding: 28px 32px;
            margin-bottom: 24px;
        }}

        header h1 {{
            font-size: 1.6rem;
            color: #00d4c8;
            margin-bottom: 8px;
        }}

        header p {{ color: #94a8c0; font-size: 0.9rem; }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}

        .stat-card {{
            background: #1a3a5c;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            border: 1px solid #2a4a6c;
        }}

        .stat-card .number {{
            font-size: 2.4rem;
            font-weight: 700;
            line-height: 1;
        }}

        .stat-card .label {{ font-size: 0.8rem; color: #94a8c0; margin-top: 6px; }}

        .stat-card.updated  .number {{ color: #4caf50; }}
        .stat-card.skipped  .number {{ color: #ff9800; }}
        .stat-card.notfound .number {{ color: #ab47bc; }}
        .stat-card.errors   .number {{ color: #f44336; }}

        .section {{
            background: #1a3a5c;
            border: 1px solid #2a4a6c;
            border-radius: 10px;
            padding: 20px 24px;
            margin-bottom: 20px;
        }}

        .section h3 {{
            font-size: 1rem;
            margin-bottom: 14px;
            color: #00d4c8;
        }}

        table {{ width: 100%; border-collapse: collapse; }}

        th {{
            text-align: left;
            font-size: 0.75rem;
            font-weight: 600;
            color: #94a8c0;
            padding: 8px 12px;
            border-bottom: 1px solid #2a4a6c;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        td {{ padding: 10px 12px; font-size: 0.85rem; border-bottom: 1px solid #162e4a; }}
        tr:last-child td {{ border-bottom: none; }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .badge-success {{ background: #1b5e20; color: #a5d6a7; }}
        .badge-warning  {{ background: #4e342e; color: #ffcc80; }}

        .arrow {{ color: #00d4c8; font-weight: bold; }}

        .status-updated  {{ color: #4caf50; font-weight: 600; }}
        .status-skipped  {{ color: #ff9800; }}
        .status-notfound {{ color: #ab47bc; }}

        .error-section {{ border-color: #c62828; }}
        .error-section h3 {{ color: #ef9a9a; }}
        .error-list {{ padding-left: 20px; }}
        .error-list li {{ margin-bottom: 6px; color: #ef9a9a; font-size: 0.85rem; }}

        .empty-state {{ color: #4a6a8a; font-size: 0.85rem; font-style: italic; }}

        footer {{
            text-align: center;
            margin-top: 24px;
            color: #4a6a8a;
            font-size: 0.75rem;
        }}
    </style>
</head>
<body>
    <div class="container">

        <header>
            <h1>🏗️ Renovation Tracker — Automation Report</h1>
            <p>
                Generated: {summary.timestamp} &nbsp;|&nbsp;
                Provider: {provider_name or 'Local Demo'} &nbsp;|&nbsp;
                {status_badge}
            </p>
        </header>

        <div class="stats-grid">
            <div class="stat-card updated">
                <div class="number">{summary.updated_count}</div>
                <div class="label">✅ Units Updated</div>
            </div>
            <div class="stat-card skipped">
                <div class="number">{summary.skipped_count}</div>
                <div class="label">⏭️ Skipped</div>
            </div>
            <div class="stat-card notfound">
                <div class="number">{summary.not_found_count}</div>
                <div class="label">❓ Not Found</div>
            </div>
            <div class="stat-card errors">
                <div class="number">{summary.error_count}</div>
                <div class="label">❌ Errors</div>
            </div>
        </div>

        {updated_rows_html}
        {skipped_rows_html}
        {not_found_rows_html}
        {errors_html}

        <footer>
            Renovation Tracker Automation POC &nbsp;|&nbsp;
            Microsoft Power Platform Demo &nbsp;|&nbsp;
            {summary.contractor_rows_received} contractor row(s) received
        </footer>

    </div>
</body>
</html>"""


def _rows_to_html(rows: list[UpdateResult], row_type: str) -> str:
    """Generate the HTML section for a list of result rows."""

    title_map = {
        "updated":   "✅ Updated Units",
        "skipped":   "⏭️ Skipped (Status Unchanged)",
        "not_found": "❓ Unit IDs Not Found in Master Tracker",
    }

    if not rows:
        if row_type == "updated":
            return f"""
        <div class="section">
            <h3>{title_map[row_type]}</h3>
            <p class="empty-state">No units were updated in this run.</p>
        </div>"""
        return ""  # Don't show empty skipped/not-found sections

    if row_type == "updated":
        rows_html = "".join(f"""
                <tr>
                    <td><strong>{r.unit_id}</strong></td>
                    <td>{r.address}</td>
                    <td>{r.previous_status}</td>
                    <td class="arrow">→</td>
                    <td class="status-updated">{r.new_status}</td>
                    <td>{r.revised_finish_date or '—'}</td>
                </tr>""" for r in rows)

        return f"""
        <div class="section">
            <h3>{title_map[row_type]}</h3>
            <table>
                <thead>
                    <tr>
                        <th>Unit ID</th>
                        <th>Address</th>
                        <th>Previous Status</th>
                        <th></th>
                        <th>New Status</th>
                        <th>Revised Date</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>"""

    elif row_type == "skipped":
        rows_html = "".join(f"""
                <tr>
                    <td><strong>{r.unit_id}</strong></td>
                    <td>{r.address}</td>
                    <td class="status-skipped">{r.previous_status}</td>
                    <td>{r.message}</td>
                </tr>""" for r in rows)

        return f"""
        <div class="section">
            <h3>{title_map[row_type]}</h3>
            <table>
                <thead>
                    <tr>
                        <th>Unit ID</th>
                        <th>Address</th>
                        <th>Status</th>
                        <th>Reason</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>"""

    elif row_type == "not_found":
        rows_html = "".join(f"""
                <tr>
                    <td class="status-notfound"><strong>{r.unit_id}</strong></td>
                    <td>{r.message}</td>
                </tr>""" for r in rows)

        return f"""
        <div class="section">
            <h3>{title_map[row_type]}</h3>
            <table>
                <thead>
                    <tr>
                        <th>Unit ID</th>
                        <th>Detail</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>"""

    return ""
