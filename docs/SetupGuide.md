# 🛠️ Setup Guide — Renovation Tracker Automation POC

> **Estimated Setup Time:** 30–45 minutes (one-time)
> **Prerequisites:** Microsoft 365 account with Power Automate access

---

## Prerequisites Checklist

Before starting, confirm you have:

- [ ] Microsoft 365 account (Business or Enterprise — not personal)
- [ ] Access to **Power Automate** (make.powerautomate.com)
- [ ] **OneDrive for Business** or **SharePoint** available
- [ ] **Excel Online** access (Excel files open in browser)
- [ ] Permission to create Power Automate flows
- [ ] Office Scripts enabled for your account (check with IT if unsure)

---

## Part 1 — Prepare the Excel Files

### Step 1.1 — Create Master_Tracker.xlsx

1. Open **OneDrive for Business** (onedrive.com or via Microsoft 365 portal)
2. Navigate to (or create) this folder path:
   ```
   /Renovation/
   ```
3. Click **New → Excel Workbook**
4. Rename it to: `Master_Tracker.xlsx`
5. Rename the sheet tab to: **`Master Tracker`** (exactly — the script references this name)
6. Add the following header row in **Row 1**:

   | A | B | C | D | E |
   |---|---|---|---|---|
   | Unit ID | Property Address | Status | Original Finish Date | Revised Finish Date |

7. Copy and paste the 20 rows from `data/Master_Tracker_Data.csv`
8. **Format as Table:**
   - Select all data (A1:E21)
   - Home → Format as Table → choose a style
   - Confirm: "My table has headers" ✓
9. Save (Ctrl+S)

---

### Step 1.2 — Create Contractor_Update.xlsx

1. In OneDrive, navigate to:
   ```
   /Renovation/Incoming/
   ```
   *(Create the Incoming folder if it doesn't exist)*
2. Click **New → Excel Workbook**
3. Rename it to: `Contractor_Update.xlsx`
4. Add header row in **Row 1**:

   | A | B | C | D |
   |---|---|---|---|
   | Unit ID | New Status | Revised Finish Date | Notes |

5. Copy and paste the sample rows from `data/Contractor_Update_Data.csv`
6. Save (Ctrl+S)

> **Note:** Power Automate will overwrite this file each time a new email arrives. The initial content is just for testing.

---

## Part 2 — Set Up Office Scripts

### Step 2.1 — Add ParseContractorSheet Script

1. Open `Contractor_Update.xlsx` in **Excel Online** (in the browser)
2. Go to **Automate** tab → **New Script**
3. Clear the default code
4. Copy the entire contents of `scripts/ParseContractorSheet.ts`
5. Paste into the script editor
6. Rename the script to: `ParseContractorSheet`
7. Click **Save script** (floppy disk icon)
8. Click **Run** to verify no compilation errors

---

### Step 2.2 — Add UpdateMasterTracker Script

1. Open `Master_Tracker.xlsx` in **Excel Online**
2. Go to **Automate** tab → **New Script**
3. Clear the default code
4. Copy the entire contents of `scripts/UpdateMasterTracker.ts`
5. Paste into the script editor
6. Rename the script to: `UpdateMasterTracker`
7. Click **Save script**
8. **Do not click Run** — this script requires a parameter (`contractorDataJson`) that Power Automate will provide

> ✅ Scripts are stored inside each Excel file. They will appear in Power Automate's "Run script" action automatically.

---

## Part 3 — Build the Power Automate Flow

### Step 3.1 — Create New Flow

1. Go to **make.powerautomate.com**
2. Click **+ Create** → **Automated cloud flow**
3. Flow name: `Renovation Tracker — Process Contractor Email Update`
4. Search for trigger: `When a new email arrives (V3)` → Outlook
5. Click **Create**

---

### Step 3.2 — Configure Trigger

**When a new email arrives (V3)**

| Field | Value |
|-------|-------|
| Folder | Inbox |
| Include Attachments | Yes |
| Subject Filter | `Biweekly Renovation Update` |
| Importance | Any |
| Only with Attachments | Yes |

---

### Step 3.3 — Add All Actions

Follow the full step-by-step instructions in **PowerAutomateFlow.md**.

**Action summary:**
1. Apply to each → attachments
2. Condition → filename ends with `.xlsx`
3. Get attachment content
4. Create file → OneDrive `/Renovation/Incoming/Contractor_Update.xlsx`
5. Run script → `ParseContractorSheet` (on Contractor_Update.xlsx)
6. Run script → `UpdateMasterTracker` (on Master_Tracker.xlsx, pass result from step 5)
7. Parse JSON (on result from step 6)
8. Compose → HTML email body
9. Send email → coordinator

---

### Step 3.4 — Save and Test

1. Click **Save** (top right)
2. Click **Test** → **Manually** → **Test**
3. Send a test email from another account with:
   - Subject: `Biweekly Renovation Update`
   - Attachment: `Contractor_Update.xlsx` (with sample data)
4. Watch the flow run
5. Verify Master_Tracker.xlsx is updated
6. Check coordinator inbox for summary email

---

## Part 4 — Verify Everything Works

### Verification Checklist

- [ ] Flow shows **Succeeded** in run history
- [ ] Master_Tracker.xlsx: REN-001 Status changed from `In Progress` to `Awaiting Inspection`
- [ ] Master_Tracker.xlsx: REN-004 Status changed from `In Progress` to `Completed`
- [ ] Coordinator received summary email with correct counts
- [ ] Email subject includes today's date

---

## File Path Reference

| File | OneDrive Path |
|------|---------------|
| Master Tracker | `/Renovation/Master_Tracker.xlsx` |
| Contractor Update (incoming) | `/Renovation/Incoming/Contractor_Update.xlsx` |

---

## Common Issues and Fixes

### Office Scripts tab not visible in Excel Online
- Office Scripts requires a Microsoft 365 Business or Enterprise plan
- Contact IT admin to enable "Office Scripts" for your account
- Check: Microsoft 365 Admin Center → Settings → Org settings → Office Scripts

### Power Automate "Run script" action not showing scripts
- The scripts must be saved inside the specific Excel file
- The flow must use the same OneDrive account that has the scripts
- Try refreshing the action dropdown after saving scripts

### Flow trigger not firing
- Check spam/junk folder in Outlook — Power Automate reads from Inbox only
- Verify the subject filter matches exactly (case insensitive)
- Try removing the subject filter temporarily to confirm trigger works

---

*Setup Guide v1.0 — POC Demo | Estimated time: 30–45 minutes*
