/**
 * ============================================================
 * Office Script: UpdateMasterTracker.ts
 * ============================================================
 * Purpose  : Reads contractor update data passed from Power Automate,
 *            matches rows to the Master Tracker by Unit ID, updates
 *            the Status and Revised Finish Date columns, and returns
 *            a structured summary object back to Power Automate.
 *
 * Called by: Power Automate → "Run script" action (Excel Online)
 * Returns  : JSON summary { updatedCount, skippedCount, errors[], rows[] }
 *
 * Author   : POC Demo – Renovation Automation
 * Version  : 1.0.0
 * ============================================================
 */

// ─── Type Definitions ────────────────────────────────────────────────────────

/** One row sent by the contractor (parsed from Contractor_Update.xlsx) */
interface ContractorRow {
  unitId: string;
  newStatus: string;
  revisedFinishDate: string; // ISO date string, e.g. "2025-09-15"
  notes: string;
}

/** Summary returned to Power Automate */
interface UpdateSummary {
  updatedCount: number;
  skippedCount: number;
  notFoundCount: number;
  errors: string[];
  updatedRows: UpdatedRowDetail[];
  skippedRows: string[];
  timestamp: string;
}

/** Detail record for each successfully updated row */
interface UpdatedRowDetail {
  unitId: string;
  address: string;
  previousStatus: string;
  newStatus: string;
  revisedFinishDate: string;
}

// ─── Column Index Constants (Master_Tracker.xlsx, 0-based) ───────────────────
const COL_UNIT_ID            = 0; // A – Unit ID
const COL_ADDRESS            = 1; // B – Property Address
const COL_STATUS             = 2; // C – Status
const COL_ORIGINAL_FINISH    = 3; // D – Original Finish Date
const COL_REVISED_FINISH     = 4; // E – Revised Finish Date

// ─── Main Entry Point ─────────────────────────────────────────────────────────

/**
 * main() is called automatically by Power Automate.
 *
 * @param workbook   - The active Excel workbook (Master_Tracker.xlsx)
 * @param contractorDataJson - Stringified JSON array of ContractorRow objects
 *                             passed from Power Automate after parsing the
 *                             contractor attachment.
 */
function main(
  workbook: ExcelScript.Workbook,
  contractorDataJson: string
): string {

  // ── 1. Initialise the summary object ───────────────────────────────────────
  const summary: UpdateSummary = {
    updatedCount:  0,
    skippedCount:  0,
    notFoundCount: 0,
    errors:        [],
    updatedRows:   [],
    skippedRows:   [],
    timestamp:     new Date().toISOString()
  };

  // ── 2. Parse the contractor JSON payload ───────────────────────────────────
  let contractorRows: ContractorRow[] = [];

  try {
    contractorRows = JSON.parse(contractorDataJson) as ContractorRow[];
  } catch (parseError) {
    summary.errors.push(`Failed to parse contractor data JSON: ${parseError}`);
    return JSON.stringify(summary);
  }

  if (!contractorRows || contractorRows.length === 0) {
    summary.errors.push("Contractor data is empty – nothing to process.");
    return JSON.stringify(summary);
  }

  // ── 3. Access the Master Tracker worksheet ─────────────────────────────────
  const sheet = workbook.getWorksheet("Master Tracker");

  if (!sheet) {
    summary.errors.push("Worksheet 'Master Tracker' not found in workbook.");
    return JSON.stringify(summary);
  }

  // ── 4. Read all data from the Master Tracker (including header row) ────────
  const usedRange      = sheet.getUsedRange();
  const allValues      = usedRange.getValues();   // 2-D array of cell values
  const totalRows      = allValues.length;

  // Skip the header row (index 0) – data starts at index 1
  if (totalRows < 2) {
    summary.errors.push("Master Tracker appears to have no data rows.");
    return JSON.stringify(summary);
  }

  // ── 5. Build a lookup map: unitId → row index (in allValues) ──────────────
  //       This makes matching O(1) instead of O(n²).
  const unitIdToRowIndex = new Map<string, number>();

  for (let i = 1; i < totalRows; i++) {
    const cellValue = allValues[i][COL_UNIT_ID];
    if (cellValue !== null && cellValue !== undefined && cellValue !== "") {
      // Normalise: trim whitespace, uppercase for case-insensitive matching
      const normalised = String(cellValue).trim().toUpperCase();
      unitIdToRowIndex.set(normalised, i);
    }
  }

  // ── 6. Process each contractor row ─────────────────────────────────────────
  for (const contractorRow of contractorRows) {

    // Validate incoming row has required fields
    if (!contractorRow.unitId || !contractorRow.newStatus) {
      summary.skippedCount++;
      summary.skippedRows.push(
        `Row skipped – missing unitId or newStatus: ${JSON.stringify(contractorRow)}`
      );
      continue;
    }

    const normalisedId = contractorRow.unitId.trim().toUpperCase();
    const masterRowIdx = unitIdToRowIndex.get(normalisedId);

    // ── 6a. No matching Unit ID found in Master Tracker ──────────────────────
    if (masterRowIdx === undefined) {
      summary.notFoundCount++;
      summary.skippedRows.push(`Unit ID not found in Master Tracker: ${contractorRow.unitId}`);
      continue;
    }

    // ── 6b. Capture existing values before update (for audit trail) ──────────
    const previousStatus    = String(allValues[masterRowIdx][COL_STATUS]   ?? "");
    const address           = String(allValues[masterRowIdx][COL_ADDRESS]  ?? "");

    // ── 6c. Skip if status hasn't actually changed (avoid noisy updates) ─────
    if (previousStatus.trim().toLowerCase() === contractorRow.newStatus.trim().toLowerCase()) {
      summary.skippedCount++;
      summary.skippedRows.push(
        `${contractorRow.unitId} – status unchanged ("${previousStatus}"), skipped.`
      );
      continue;
    }

    // ── 6d. Write updated values back to the sheet ───────────────────────────
    //        getCell() is 0-based relative to the used range start.
    //        Row 0 = header, so masterRowIdx maps directly.

    try {
      // Update Status column (C)
      usedRange.getCell(masterRowIdx, COL_STATUS).setValue(contractorRow.newStatus.trim());

      // Update Revised Finish Date column (E) only if provided
      if (contractorRow.revisedFinishDate && contractorRow.revisedFinishDate.trim() !== "") {
        usedRange.getCell(masterRowIdx, COL_REVISED_FINISH)
                 .setValue(contractorRow.revisedFinishDate.trim());
      }

      // ── 6e. Record the successful update in our summary ───────────────────
      summary.updatedRows.push({
        unitId:           contractorRow.unitId,
        address:          address,
        previousStatus:   previousStatus,
        newStatus:        contractorRow.newStatus.trim(),
        revisedFinishDate: contractorRow.revisedFinishDate ?? ""
      });

      summary.updatedCount++;

    } catch (writeError) {
      summary.errors.push(
        `Failed to update Unit ID ${contractorRow.unitId}: ${writeError}`
      );
    }
  }

  // ── 7. Return the summary as a JSON string ─────────────────────────────────
  //       Power Automate will parse this in the next step to build the email.
  return JSON.stringify(summary);
}
