"""
src/core/processor.py
======================
ContractorUpdateProcessor — the heart of the business logic.

This class is completely independent of:
  - Where the data came from (Gmail / Outlook / local file)
  - Where the data will be saved (local disk / SharePoint)
  - How the results will be displayed (console / HTML / email)

It receives DataFrames, applies the business rules, and returns an
UpdateSummary. Nothing more.

Business Rules:
  1. Match contractor rows to master tracker rows by Unit ID (case-insensitive).
  2. If Unit ID found AND status changed → UPDATE Status + Revised Finish Date.
  3. If Unit ID found AND status unchanged → SKIP (logged in summary).
  4. If Unit ID not found in master tracker → LOG as not_found.
  5. Return UpdateSummary with full counts and row-level details.
"""

import logging
from datetime import datetime

import pandas as pd

from src.core.models import (
    ContractorRow,
    UpdateResult,
    UpdateSummary,
)
from config import settings

logger = logging.getLogger(__name__)


class ContractorUpdateProcessor:
    """
    Stateless processor: call process() with two DataFrames, get a summary back.

    Example:
        processor = ContractorUpdateProcessor()
        updated_df, summary = processor.process(master_df, contractor_df)
    """

    def process(
        self,
        master_df: pd.DataFrame,
        contractor_df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, UpdateSummary]:
        """
        Main entry point.

        Args:
            master_df: Full Master Tracker DataFrame (all rows, all columns).
            contractor_df: Contractor Update DataFrame (rows to apply).

        Returns:
            Tuple of (updated master_df, UpdateSummary).
            The returned master_df has updated Status and Revised Finish Date
            values applied in-place (a copy is returned — original is not mutated).
        """
        summary = UpdateSummary(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            contractor_rows_received=len(contractor_df),
        )

        # Work on a copy — never mutate the caller's DataFrame
        updated_df = master_df.copy()

        # ── Build Unit ID → row index lookup map ─────────────────────────────
        # Normalise: uppercase + strip whitespace for case-insensitive matching
        id_col = settings.MASTER_COL_UNIT_ID
        unit_id_map: dict[str, int] = {}

        for idx, row in updated_df.iterrows():
            raw_id = str(row.get(id_col, "")).strip()
            if raw_id:
                unit_id_map[raw_id.upper()] = int(idx)

        logger.info(f"Master Tracker loaded: {len(unit_id_map)} unique Unit IDs")

        # ── Parse contractor rows into ContractorRow objects ──────────────────
        contractor_rows = self._parse_contractor_df(contractor_df)

        # ── Process each contractor row ───────────────────────────────────────
        for c_row in contractor_rows:
            result = self._apply_row(updated_df, unit_id_map, c_row)

            if result.action == "updated":
                summary.updated_count += 1
                summary.updated_rows.append(result)

            elif result.action == "skipped":
                summary.skipped_count += 1
                summary.skipped_rows.append(result)

            elif result.action == "not_found":
                summary.not_found_count += 1
                summary.not_found_rows.append(result)

            elif result.action == "error":
                summary.error_count += 1
                summary.errors.append(result.message)

        return updated_df, summary

    # ─────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _parse_contractor_df(self, df: pd.DataFrame) -> list[ContractorRow]:
        """
        Convert the raw contractor DataFrame into a list of ContractorRow objects.
        Skips rows with empty Unit IDs or missing status.
        """
        rows: list[ContractorRow] = []

        for _, row in df.iterrows():
            unit_id   = str(row.get(settings.CONTRACTOR_COL_UNIT_ID,   "")).strip()
            new_status = str(row.get(settings.CONTRACTOR_COL_NEW_STATUS, "")).strip()
            revised    = str(row.get(settings.CONTRACTOR_COL_REVISED_DATE, "")).strip()
            notes      = str(row.get(settings.CONTRACTOR_COL_NOTES,       "")).strip()

            if not unit_id:
                logger.debug("Skipping row with empty Unit ID")
                continue

            if not new_status:
                logger.warning(f"Row for {unit_id} has no New Status — skipping")
                continue

            rows.append(ContractorRow(
                unit_id=unit_id,
                new_status=new_status,
                revised_finish_date=revised,
                notes=notes,
            ))

        logger.info(f"Parsed {len(rows)} valid contractor rows")
        return rows

    def _apply_row(
        self,
        df: pd.DataFrame,
        unit_id_map: dict[str, int],
        c_row: ContractorRow,
    ) -> UpdateResult:
        """
        Apply one contractor row to the master DataFrame.
        Returns an UpdateResult describing what happened.
        """
        normalised_id = c_row.unit_id.upper()
        row_idx = unit_id_map.get(normalised_id)

        # ── Not found ─────────────────────────────────────────────────────────
        if row_idx is None:
            logger.warning(f"Unit ID not found in Master Tracker: {c_row.unit_id}")
            return UpdateResult(
                unit_id=c_row.unit_id,
                address="",
                previous_status="",
                new_status=c_row.new_status,
                revised_finish_date=c_row.revised_finish_date,
                action="not_found",
                message=f"Unit ID '{c_row.unit_id}' not in Master Tracker",
            )

        # ── Read current values ───────────────────────────────────────────────
        current_status = str(df.at[row_idx, settings.MASTER_COL_STATUS]).strip()
        address        = str(df.at[row_idx, settings.MASTER_COL_ADDRESS]).strip()

        # ── Skip if status unchanged ──────────────────────────────────────────
        if current_status.lower() == c_row.new_status.lower():
            logger.debug(f"{c_row.unit_id}: status unchanged ('{current_status}') — skipping")
            return UpdateResult(
                unit_id=c_row.unit_id,
                address=address,
                previous_status=current_status,
                new_status=c_row.new_status,
                revised_finish_date=c_row.revised_finish_date,
                action="skipped",
                message=f"Status already '{current_status}' — no change needed",
            )

        # ── Apply update ──────────────────────────────────────────────────────
        try:
            df.at[row_idx, settings.MASTER_COL_STATUS] = c_row.new_status

            if c_row.revised_finish_date:
                df.at[row_idx, settings.MASTER_COL_REVISED_FINISH] = c_row.revised_finish_date

            logger.info(
                f"Updated {c_row.unit_id}: '{current_status}' -> '{c_row.new_status}'"
            )

            return UpdateResult(
                unit_id=c_row.unit_id,
                address=address,
                previous_status=current_status,
                new_status=c_row.new_status,
                revised_finish_date=c_row.revised_finish_date,
                action="updated",
                message="",
            )

        except Exception as exc:
            error_msg = f"Failed to update {c_row.unit_id}: {exc}"
            logger.error(error_msg)
            return UpdateResult(
                unit_id=c_row.unit_id,
                address=address,
                previous_status=current_status,
                new_status=c_row.new_status,
                revised_finish_date=c_row.revised_finish_date,
                action="error",
                message=error_msg,
            )
