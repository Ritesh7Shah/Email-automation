"""
src/providers/storage_provider.py
==================================
Abstract base class and local implementation for file storage.

The business logic never touches the filesystem or cloud storage directly.
It calls StorageProvider methods, which can be swapped between:

  Current demo  : LocalStorageProvider  (reads/writes local ./data and ./output)
  Production    : SharePointStorageProvider (future — uploads to SharePoint)
"""

from abc import ABC, abstractmethod
from pathlib import Path
import shutil
import io

import pandas as pd
from openpyxl import load_workbook

from config import settings


class StorageProvider(ABC):
    """
    Provider-agnostic interface for reading and writing Excel files.

    Demo implementation       : LocalStorageProvider
    Production implementation : SharePointStorageProvider (future)
    """

    @abstractmethod
    def read_master_tracker(self) -> pd.DataFrame:
        """
        Read the Master Tracker and return it as a DataFrame.
        The index is the default integer index (0-based row numbers).
        """
        ...

    @abstractmethod
    def read_contractor_update(self, source: bytes | None = None) -> pd.DataFrame:
        """
        Read the Contractor Update spreadsheet.

        Args:
            source: Raw bytes of the file (used when the file came from email).
                    If None, reads from the configured default path.
        Returns:
            DataFrame with contractor update rows.
        """
        ...

    @abstractmethod
    def save_master_tracker(self, df: pd.DataFrame) -> str:
        """
        Persist the updated Master Tracker DataFrame.

        Returns:
            Path or URL where the file was saved.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name (e.g. 'Local Storage', 'SharePoint')."""
        ...


# ─────────────────────────────────────────────────────────────────────────────
# Local Storage Implementation
# ─────────────────────────────────────────────────────────────────────────────

class LocalStorageProvider(StorageProvider):
    """
    Reads from ./data/ and writes updated files to ./output/.
    No cloud credentials required — perfect for local demo.
    """

    @property
    def provider_name(self) -> str:
        return "Local Storage"

    def read_master_tracker(self) -> pd.DataFrame:
        """
        Load Master_Tracker.xlsx from the configured path.
        Reads the sheet named in settings.MASTER_SHEET_NAME.
        String columns are stripped of whitespace.
        """
        path = settings.MASTER_TRACKER_PATH

        if not path.exists():
            raise FileNotFoundError(
                f"Master Tracker not found at: {path}\n"
                f"Run 'python setup_data.py' to generate the Excel files from CSVs."
            )

        df = pd.read_excel(
            path,
            sheet_name=settings.MASTER_SHEET_NAME,
            dtype=str,          # Keep everything as strings — we manage types ourselves
            engine="openpyxl"
        )

        # Normalise: strip whitespace from all string cells
        df = df.apply(lambda col: col.str.strip() if col.dtype == object else col)

        return df.fillna("")

    def read_contractor_update(self, source: bytes | None = None) -> pd.DataFrame:
        """
        Load Contractor_Update.xlsx — either from bytes (email attachment)
        or from the configured default path (demo mode).
        """
        if source is not None:
            # Bytes came from an email attachment
            df = pd.read_excel(
                io.BytesIO(source),
                dtype=str,
                engine="openpyxl"
            )
        else:
            path = settings.CONTRACTOR_UPDATE_PATH
            if not path.exists():
                raise FileNotFoundError(
                    f"Contractor Update not found at: {path}\n"
                    f"Run 'python setup_data.py' to generate the Excel files from CSVs."
                )
            df = pd.read_excel(path, dtype=str, engine="openpyxl")

        df = df.apply(lambda col: col.str.strip() if col.dtype == object else col)
        return df.fillna("")

    def save_master_tracker(self, df: pd.DataFrame) -> str:
        """
        Save the updated DataFrame to output/Master_Tracker_Updated.xlsx.
        Preserves the sheet name from settings.
        """
        output_dir = settings.OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / "Master_Tracker_Updated.xlsx"

        with pd.ExcelWriter(
            output_path,
            engine="openpyxl"
        ) as writer:
            df.to_excel(
                writer,
                sheet_name=settings.MASTER_SHEET_NAME,
                index=False
            )

            # Apply basic column width formatting so the file looks clean
            worksheet = writer.sheets[settings.MASTER_SHEET_NAME]
            for col in worksheet.columns:
                max_len = max(
                    len(str(cell.value or "")) for cell in col
                )
                worksheet.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

        return str(output_path)
