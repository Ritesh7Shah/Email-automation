/**
 * ============================================================
 * Office Script: ParseContractorSheet.ts
 * ============================================================
 * Purpose  : Reads the Contractor_Update.xlsx workbook (saved
 *            temporarily to OneDrive by Power Automate) and
 *            converts the data into a JSON string array that
 *            UpdateMasterTracker.ts can consume.
 *
 * Called by: Power Automate → "Run script" action (step before
 *            UpdateMasterTracker.ts)
 * Returns  : Stringified JSON array of ContractorRow objects.
 *
 * Author   : POC Demo – Renovation Automation
 * Version  : 1.0.0
 * ============================================================
 */

// ─── Column Index Constants (Contractor_Update.xlsx, 0-based) ─────────────────
const CONTR_COL_UNIT_ID       = 0; // A – Unit ID
const CONTR_COL_NEW_STATUS    = 1; // B – New Status
const CONTR_COL_REVISED_DATE  = 2; // C – Revised Finish Date
const CONTR_COL_NOTES         = 3; // D – Notes

/** Shape of one parsed contractor row */
interface ContractorRow {
  unitId: string;
  newStatus: string;
  revisedFinishDate: string;
  notes: string;
}

/**
 * main() reads the Contractor_Update workbook and returns a JSON
 * array string for use in the next Power Automate script action.
 *
 * @param workbook - The Contractor_Update.xlsx workbook (opened by Power Automate)
 */
function main(workbook: ExcelScript.Workbook): string {

  const rows: ContractorRow[] = [];

  // ── 1. Get the first sheet (contractor files only have one sheet) ──────────
  const sheet = workbook.getFirstWorksheet();

  if (!sheet) {
    return JSON.stringify({ error: "No worksheet found in Contractor_Update.xlsx" });
  }

  const usedRange = sheet.getUsedRange();

  // If the file is blank or only has a header, return empty array
  if (!usedRange) {
    return JSON.stringify([]);
  }

  const values    = usedRange.getValues();
  const totalRows = values.length;

  // ── 2. Parse rows (skip header row at index 0) ────────────────────────────
  for (let i = 1; i < totalRows; i++) {
    const row = values[i];

    // Skip completely empty rows
    if (!row[CONTR_COL_UNIT_ID] && !row[CONTR_COL_NEW_STATUS]) {
      continue;
    }

    const contractorRow: ContractorRow = {
      unitId:            String(row[CONTR_COL_UNIT_ID]      ?? "").trim(),
      newStatus:         String(row[CONTR_COL_NEW_STATUS]    ?? "").trim(),
      revisedFinishDate: String(row[CONTR_COL_REVISED_DATE]  ?? "").trim(),
      notes:             String(row[CONTR_COL_NOTES]         ?? "").trim()
    };

    // Only include rows that have at minimum a Unit ID
    if (contractorRow.unitId !== "") {
      rows.push(contractorRow);
    }
  }

  // ── 3. Return as JSON string ──────────────────────────────────────────────
  return JSON.stringify(rows);
}
