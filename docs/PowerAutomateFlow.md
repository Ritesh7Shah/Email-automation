# ⚡ Power Automate Flow — Complete Design Guide

> **Flow Name:** `Renovation Tracker — Process Contractor Email Update`
> **Type:** Automated Cloud Flow
> **Trigger:** When a new email arrives in Outlook

---

## Flow Overview

```
[TRIGGER]  When email arrives (Outlook)
     ↓
[ACTION 1] Get attachment content
     ↓
[ACTION 2] Create file in OneDrive (save attachment)
     ↓
[ACTION 3] Run script — ParseContractorSheet (Excel)
     ↓
[ACTION 4] Run script — UpdateMasterTracker (Excel)
     ↓
[ACTION 5] Parse JSON — read summary result
     ↓
[ACTION 6] Compose — build HTML email body
     ↓
[ACTION 7] Send email — notify coordinator
```

---

## Step-by-Step Configuration

---

### 🔵 TRIGGER — When a new email arrives (V3)

**Connector:** Office 365 Outlook

| Setting | Value |
|---------|-------|
| **Account** | Your Microsoft 365 account / shared mailbox |
| **Folder** | Inbox |
| **Include Attachments** | Yes |
| **Subject Filter** | `Biweekly Renovation Update` |
| **From Filter** | *(optional)* `contractor@renovationcompany.com` |

> **Why:** This trigger fires only when a matching email arrives, keeping the flow efficient and avoiding false triggers.

**Dynamic values produced:**
- `Body` — email body HTML
- `From` — sender address
- `Subject` — email subject
- `Attachments` — array of attachments

---

### 🟠 ACTION 1 — Apply to each (loop over attachments)

**Control Action:** Apply to each

| Setting | Value |
|---------|-------|
| **Select An Output** | `Attachments` (from trigger) |

> **Why:** Emails can technically have multiple attachments. The loop ensures we only process `.xlsx` files.

**Inside the loop, add a Condition:**

```
Condition: Attachments Name — ends with — .xlsx
```

All subsequent actions go inside the **"Yes"** branch.

---

### 🟠 ACTION 2 — Get attachment content (V2)

**Connector:** Office 365 Outlook — *Get attachment (V2)*

| Setting | Value |
|---------|-------|
| **Message ID** | `Message ID` (dynamic from trigger) |
| **Attachment ID** | `ID` (dynamic from loop item) |

**Dynamic values produced:**
- `Content of the attachment` — binary file content (Base64)

---

### 🟠 ACTION 3 — Create file (save attachment to OneDrive)

**Connector:** OneDrive for Business — *Create file*

| Setting | Value |
|---------|-------|
| **Folder Path** | `/Renovation/Incoming` |
| **File Name** | `Contractor_Update.xlsx` |
| **File Content** | `Content of the attachment` (from Action 2) |

> **Why:** Office Scripts require the file to exist in OneDrive/SharePoint. This step saves the attachment so the script can open it.
>
> **Note for demo:** The file will be overwritten on each run. For production, append a timestamp to the filename for versioning.

---

### 🟠 ACTION 4 — Run script — ParseContractorSheet

**Connector:** Excel Online (Business) — *Run script*

| Setting | Value |
|---------|-------|
| **Location** | OneDrive for Business |
| **Document Library** | OneDrive |
| **File** | `/Renovation/Incoming/Contractor_Update.xlsx` |
| **Script** | `ParseContractorSheet` |
| **Script Parameters** | *(none — script reads from workbook directly)* |

**Dynamic values produced:**
- `result` — JSON string (array of contractor rows)

> **What happens:** The script opens the contractor Excel file, reads all data rows, and returns a JSON array string like:
> ```json
> [{"unitId":"REN-001","newStatus":"Awaiting Inspection","revisedFinishDate":"2025-08-05","notes":"..."}]
> ```

---

### 🟠 ACTION 5 — Run script — UpdateMasterTracker

**Connector:** Excel Online (Business) — *Run script*

| Setting | Value |
|---------|-------|
| **Location** | OneDrive for Business |
| **Document Library** | OneDrive |
| **File** | `/Renovation/Master_Tracker.xlsx` |
| **Script** | `UpdateMasterTracker` |
| **contractorDataJson** | `result` (dynamic output from Action 4) |

**Dynamic values produced:**
- `result` — JSON string (update summary)

> **What happens:** The script opens the Master Tracker, builds a Unit ID lookup map, iterates over contractor rows, updates Status and Revised Finish Date columns for matched rows, and returns:
> ```json
> {
>   "updatedCount": 10,
>   "skippedCount": 2,
>   "notFoundCount": 0,
>   "errors": [],
>   "updatedRows": [...],
>   "skippedRows": [...],
>   "timestamp": "2025-07-30T12:00:00.000Z"
> }
> ```

---

### 🟠 ACTION 6 — Parse JSON

**Control Action:** Parse JSON

| Setting | Value |
|---------|-------|
| **Content** | `result` (output from Action 5) |
| **Schema** | *(paste schema below)* |

**JSON Schema to paste:**
```json
{
  "type": "object",
  "properties": {
    "updatedCount":  { "type": "integer" },
    "skippedCount":  { "type": "integer" },
    "notFoundCount": { "type": "integer" },
    "errors":        { "type": "array", "items": { "type": "string" } },
    "updatedRows": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "unitId":           { "type": "string" },
          "address":          { "type": "string" },
          "previousStatus":   { "type": "string" },
          "newStatus":        { "type": "string" },
          "revisedFinishDate":{ "type": "string" }
        }
      }
    },
    "skippedRows": { "type": "array", "items": { "type": "string" } },
    "timestamp":   { "type": "string" }
  }
}
```

> **Why:** This action unpacks the JSON string into individual dynamic values that can be used to build the email.

---

### 🟠 ACTION 7 — Compose (build HTML email body)

**Control Action:** Compose

**Inputs expression (paste into "Inputs" field):**

```
<h2 style="color:#2C6E49;font-family:Arial,sans-serif;">
  🏗️ Renovation Tracker — Automated Update Report
</h2>
<p style="font-family:Arial,sans-serif;color:#333;">
  The Master Tracker has been automatically updated from the contractor's biweekly submission.
</p>
<table style="border-collapse:collapse;font-family:Arial,sans-serif;width:100%;">
  <tr style="background:#2C6E49;color:white;">
    <td style="padding:8px 12px;"><strong>Metric</strong></td>
    <td style="padding:8px 12px;"><strong>Count</strong></td>
  </tr>
  <tr style="background:#f0f7f4;">
    <td style="padding:8px 12px;">✅ Units Updated</td>
    <td style="padding:8px 12px;"><strong>@{body('Parse_JSON')?['updatedCount']}</strong></td>
  </tr>
  <tr>
    <td style="padding:8px 12px;">⏭️ Units Skipped (no change)</td>
    <td style="padding:8px 12px;"><strong>@{body('Parse_JSON')?['skippedCount']}</strong></td>
  </tr>
  <tr style="background:#f0f7f4;">
    <td style="padding:8px 12px;">❓ Unit IDs Not Found</td>
    <td style="padding:8px 12px;"><strong>@{body('Parse_JSON')?['notFoundCount']}</strong></td>
  </tr>
  <tr>
    <td style="padding:8px 12px;">❌ Errors</td>
    <td style="padding:8px 12px;"><strong>@{length(body('Parse_JSON')?['errors'])}</strong></td>
  </tr>
</table>
<br/>
<p style="font-family:Arial,sans-serif;color:#666;font-size:12px;">
  Processed at: @{body('Parse_JSON')?['timestamp']}
</p>
<p style="font-family:Arial,sans-serif;color:#999;font-size:11px;">
  This email was generated automatically by Power Automate. No action required.
</p>
```

---

### 🟠 ACTION 8 — Send an email (V2)

**Connector:** Office 365 Outlook — *Send an email (V2)*

| Setting | Value |
|---------|-------|
| **To** | `coordinator@yourcompany.com` |
| **Subject** | `Renovation Tracker Updated — @{formatDateTime(utcNow(), 'dd MMM yyyy')}` |
| **Body** | `Outputs` (dynamic from Action 7 — Compose) |
| **Is HTML** | Yes |

---

## Flow Settings

| Setting | Recommended Value |
|---------|-------------------|
| **Run-only users** | Coordinator account |
| **Concurrency control** | Off (for POC) |
| **Timeout** | 30 minutes |
| **Error threshold** | Do nothing (POC) |

---

## Testing the Flow

### Manual Test Steps
1. Open Power Automate → My Flows → find your flow
2. Click **Test** → **Manually**
3. Send a test email from a second account with subject `Biweekly Renovation Update` and attach `Contractor_Update.xlsx`
4. Watch the flow run in real time
5. Check:
   - Master_Tracker.xlsx for updated values
   - Coordinator inbox for the summary email

### Expected Run Time
- Typical execution: **15–45 seconds** end-to-end

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Flow doesn't trigger | Subject filter mismatch | Check for exact subject text match |
| Script fails on file | File path wrong | Verify OneDrive path matches what was configured |
| Empty update count | Column mismatch in xlsx | Ensure contractor file header row matches expected columns |
| Summary email not sent | Email action auth error | Re-authenticate Outlook connection |

---

*Power Automate Flow Design v1.0 — POC Demo*
