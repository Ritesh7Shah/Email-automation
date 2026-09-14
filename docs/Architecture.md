# 🗺️ Architecture Overview — Renovation Tracker Automation POC

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TRIGGER LAYER                                │
│                                                                     │
│   🧑‍🔧 Contractor                                                    │
│        │                                                            │
│        │  Email: "Biweekly Renovation Update"                       │
│        │  Attachment: Contractor_Update.xlsx                        │
│        ▼                                                            │
│   📧 Microsoft Outlook (Microsoft 365)                              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                            │
│                                                                     │
│   ⚡ Power Automate Flow                                            │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  STEP 1: Trigger — "When email arrives"                     │  │
│   │          Filter: Subject = "Biweekly Renovation Update"     │  │
│   │                                                             │  │
│   │  STEP 2: Get Attachment Content                             │  │
│   │          Extract Contractor_Update.xlsx bytes               │  │
│   │                                                             │  │
│   │  STEP 3: Save Attachment to OneDrive/SharePoint             │  │
│   │          Path: /Renovation/Incoming/Contractor_Update.xlsx  │  │
│   │                                                             │  │
│   │  STEP 4: Run Office Script — ParseContractorSheet.ts        │  │
│   │          Input:  Contractor_Update.xlsx                     │  │
│   │          Output: JSON array of contractor rows              │  │
│   │                                                             │  │
│   │  STEP 5: Run Office Script — UpdateMasterTracker.ts         │  │
│   │          Input:  JSON array from Step 4                     │  │
│   │          Opens:  Master_Tracker.xlsx                        │  │
│   │          Output: Summary JSON                               │  │
│   │                                                             │  │
│   │  STEP 6: Compose Summary Email                              │  │
│   │          Parse summary JSON, format HTML                    │  │
│   │                                                             │  │
│   │  STEP 7: Send Email to Coordinator                          │  │
│   │          Subject: "Renovation Tracker Updated — [Date]"     │  │
│   └─────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       SCRIPT EXECUTION LAYER                        │
│                                                                     │
│   📜 Office Scripts (TypeScript — runs in Excel Online)             │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                                                             │  │
│   │  ParseContractorSheet.ts                                    │  │
│   │  ┌───────────────────────────────────────────────────────┐  │  │
│   │  │ Open Contractor_Update.xlsx                           │  │  │
│   │  │ Read all data rows                                    │  │  │
│   │  │ Return JSON: [{unitId, newStatus, date, notes}, ...]  │  │  │
│   │  └───────────────────────────────────────────────────────┘  │  │
│   │                           ↓                                 │  │
│   │  UpdateMasterTracker.ts                                     │  │
│   │  ┌───────────────────────────────────────────────────────┐  │  │
│   │  │ Open Master_Tracker.xlsx                              │  │  │
│   │  │ Build Unit ID → Row lookup map                        │  │  │
│   │  │ For each contractor row:                              │  │  │
│   │  │   → Match Unit ID                                     │  │  │
│   │  │   → Update Status + Revised Finish Date               │  │  │
│   │  │ Return summary JSON                                   │  │  │
│   │  └───────────────────────────────────────────────────────┘  │  │
│   └─────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                  │
│                                                                     │
│   📊 Excel Online Files (stored on SharePoint / OneDrive)          │
│                                                                     │
│   ┌─────────────────────────┐   ┌────────────────────────────────┐ │
│   │  Master_Tracker.xlsx    │   │  Contractor_Update.xlsx        │ │
│   │  ─────────────────────  │   │  ──────────────────────────    │ │
│   │  Unit ID (Key)          │   │  Unit ID                       │ │
│   │  Property Address       │   │  New Status                    │ │
│   │  Status  ◄── UPDATED    │   │  Revised Finish Date           │ │
│   │  Original Finish Date   │   │  Notes                         │ │
│   │  Revised Finish Date    │   │                                │ │
│   │    ◄── UPDATED          │   │  (Temporary — read only)       │ │
│   └─────────────────────────┘   └────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       OUTPUT / NOTIFICATION LAYER                   │
│                                                                     │
│   📧 Summary Email → Renovation Coordinator                         │
│                                                                     │
│   Subject: "Renovation Tracker Updated — 30 Jul 2025"              │
│   Body:                                                             │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  ✅ 12 updates received from contractor                     │  │
│   │  ✅ 10 units successfully updated                           │  │
│   │  ⚠️  2 units skipped (status unchanged)                    │  │
│   │  ❌  0 errors                                               │  │
│   │                                                             │  │
│   │  Updated Units:                                             │  │
│   │  • REN-001 | 142 Maple St 1A | In Progress → Awaiting Insp │  │
│   │  • REN-004 | 78 Oak Ave Unit 4 | In Progress → Completed   │  │
│   │  • ...                                                      │  │
│   └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Trigger — Microsoft Outlook
- Monitors the coordinator's inbox (or a shared mailbox)
- Listens for subject: `Biweekly Renovation Update`
- Supports optional filter on sender domain (e.g., `@contractor.com`)

### 2. Orchestrator — Power Automate
- Serverless, event-driven flow
- No infrastructure to manage
- Built-in retry and error handling
- Full run history and audit logs in Power Automate portal

### 3. Parsing Script — ParseContractorSheet.ts
- Office Script (runs inside Excel Online, no external runtime)
- Converts Excel rows → structured JSON
- Stateless, reusable, side-effect free

### 4. Update Script — UpdateMasterTracker.ts
- Office Script with read-write access to Master_Tracker.xlsx
- O(1) Unit ID lookup using a Map
- Returns detailed summary: updated, skipped, not-found counts

### 5. Data Store — Excel Online (SharePoint/OneDrive)
- Master_Tracker.xlsx is the single source of truth
- No database migration required
- Familiar format for staff — can still be edited manually if needed

### 6. Notification — Outlook Email
- HTML-formatted summary email delivered immediately after processing
- Gives coordinator instant visibility without opening any file

---

## Data Flow Summary

| Step | Input | Output |
|------|-------|--------|
| Email arrives | Contractor email + .xlsx attachment | Trigger fires |
| Save attachment | Email binary | .xlsx file on OneDrive |
| Parse script | Contractor_Update.xlsx | JSON array |
| Update script | JSON array + Master_Tracker.xlsx | Updated tracker + summary JSON |
| Send email | Summary JSON | HTML summary email |

---

## Security Notes (POC)
- Runs entirely within the organisation's Microsoft 365 tenant
- No external API calls or data leaving the tenant
- Power Automate connections use delegated OAuth (Microsoft account)
- File permissions managed via SharePoint/OneDrive standard ACLs

---

*Architecture v1.0 — POC Demo | Not a production design document*
