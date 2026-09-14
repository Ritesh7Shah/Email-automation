# 🏗️ Renovation Tracker Automation — POC Demo

> **Python + Gmail | Designed for Microsoft 365 Migration**

---

## 📋 Overview

This Proof of Concept (POC) demonstrates how a renovation management company can **automatically process contractor Excel updates** received by email — eliminating the manual effort of comparing spreadsheets every two weeks.

| Item | Detail |
|------|--------|
| **Client Context** | Renovation company managing ~500 housing units |
| **Current Pain Point** | Manual comparison of contractor Excel vs. master tracker (2+ hrs/cycle) |
| **Demo Stack** | Python + pandas + Gmail API (local simulation or real Gmail) |
| **Future Stack** | Microsoft Power Automate + Outlook + SharePoint (same business logic) |
| **Scope** | Task 1 — Email detection → Excel update → Summary report |

---

## 📁 Project Structure

```
email-automation/
│
├── src/
│   ├── providers/
│   │   ├── email_provider.py        ← EmailProvider ABC (interface)
│   │   ├── gmail_provider.py        ← GmailEmailProvider + LocalSimulation
│   │   └── storage_provider.py      ← StorageProvider ABC + LocalStorageProvider
│   │
│   ├── core/
│   │   ├── models.py                ← Data classes (pure Python)
│   │   └── processor.py             ← Business logic (provider-agnostic)
│   │
│   ├── reporting/
│   │   └── reporter.py              ← Console + HTML report generation
│   │
│   └── main.py                      ← Entry point
│
├── data/
│   ├── Master_Tracker.xlsx          ← Source of truth (20 units)
│   ├── Contractor_Update.xlsx       ← Contractor's biweekly submission
│   ├── Master_Tracker_Data.csv      ← Raw data for setup_data.py
│   └── Contractor_Update_Data.csv   ← Raw data for setup_data.py
│
├── demo_inbox/                      ← Drop .xlsx here to simulate email
│   └── processed/                   ← Processed files moved here
│
├── output/                          ← Generated files (after each run)
│   ├── Master_Tracker_Updated.xlsx  ← Updated tracker
│   └── summary_report.html          ← HTML report (auto-opens in browser)
│
├── scripts/                         ← Office Scripts (for future M365 phase)
│   ├── UpdateMasterTracker.ts
│   └── ParseContractorSheet.ts
│
├── docs/
│   ├── Architecture.md
│   ├── DemoGuide.md
│   ├── SetupGuide.md
│   └── PowerAutomateFlow.md         ← Future production reference
│
├── config/
│   └── settings.py                  ← All configuration
│
├── setup_data.py                    ← One-time data setup
├── requirements.txt
├── .env.example                     ← Config template
└── README.md
```

---

## 🚀 Quick Start

### Step 1 — Install dependencies
```bash
cd email-automation
pip install -r requirements.txt
```

### Step 2 — Set up data files
```bash
python setup_data.py
```

### Step 3 — Run the demo
```bash
python src/main.py
```

That's it. The HTML report opens in your browser automatically.

---

## ⚡ Run Modes

### Demo Mode (Recommended for client presentation)
```bash
python src/main.py --mode demo
```
- Reads `Contractor_Update.xlsx` directly from `data/`
- **OR** reads from `demo_inbox/` folder (simulates email arrival)
- No Gmail account needed
- Works offline
- Most reliable for live demos

### Gmail Mode (Real email integration)
```bash
python src/main.py --mode gmail
```
- Polls your Gmail inbox for subject: `Biweekly Renovation Update`
- Downloads `.xlsx` attachment automatically
- Requires Gmail API credentials (see `docs/SetupGuide.md`)

---

## 🔄 How Provider Abstraction Works

```
EmailProvider (ABC)              StorageProvider (ABC)
├── LocalSimulation (demo)       └── LocalStorageProvider (demo)
├── GmailEmailProvider           [future] SharePointStorageProvider
└── [future] OutlookEmailProvider

          ↓ both feed into ↓

     ContractorUpdateProcessor
     (zero knowledge of providers)

          ↓ outputs to ↓

     Reporter (console + HTML)
```

**To migrate to Microsoft 365:** Add `OutlookEmailProvider` and `SharePointStorageProvider`. Zero changes to `processor.py`, `models.py`, or `reporter.py`.

---

## 📊 What the Demo Shows

After running, check:

| Output | Location | What to look at |
|--------|----------|-----------------|
| Console | Terminal | Coloured update summary |
| HTML Report | `output/summary_report.html` | Full visual report |
| Updated Tracker | `output/Master_Tracker_Updated.xlsx` | REN-001 → "Awaiting Inspection", REN-004 → "Completed" |

---

## ⚠️ POC Limitations (By Design)

- No production error retry logic
- No database — Excel is the data store
- Gmail credentials setup is manual (one-time browser auth)
- Designed for demo reliability, not enterprise scale

---

*POC Version 2.0 | Python Stack | Ready for Microsoft 365 Migration*
