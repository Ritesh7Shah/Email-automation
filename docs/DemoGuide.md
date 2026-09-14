# 🎤 Demo Guide — 3-Minute Client Walkthrough (Python Version)

> **Purpose:** Exactly what to say and show during the client call.
> **Stack:** Python + Gmail (local simulation)
> **Total Time:** ~3 minutes

---

## Before the Call — Pre-Flight Checklist

Run through this **5 minutes before** the call:

- [ ] `python setup_data.py` has been run (data files exist)
- [ ] `python src/main.py --mode demo` has been tested at least once successfully
- [ ] `output/Master_Tracker_Updated.xlsx` exists from a previous run (fallback)
- [ ] Terminal window is open and ready in the project folder
- [ ] Browser tab is pre-opened with a **before** screenshot of the Master Tracker
- [ ] `data/Master_Tracker.xlsx` is open showing the **original statuses**

---

## Resetting the Demo Between Runs

Before the client call, reset the data so the demo shows a clear before/after:

```bash
# Reset tracker to original state
python setup_data.py

# Confirm REN-001 is "In Progress" (not yet updated)
```

---

## The 3-Minute Walkthrough Script

---

### ⏱️ MINUTE 1 — Set the Scene (0:00 – 1:00)

**Say:**
> *"Right now, every two weeks your team gets an Excel file from the contractor by email. Someone has to manually open both spreadsheets, find each unit by ID, compare the status, and type in the update. With 500 units, that's a couple of hours of manual work — and it's easy to make mistakes."*
>
> *"What I'm going to show you is that entire process happening automatically, in under a minute."*

**Show (screen share):**
- Open `data/Master_Tracker.xlsx` — point to a few rows
- Highlight: `REN-001` = `In Progress`, `REN-004` = `In Progress`, `REN-010` = `In Progress`

**Say:**
> *"This is your Master Tracker. These three units are all 'In Progress'. The contractor just sent us their biweekly update — let me show you what happens."*

---

### ⏱️ MINUTE 2 — Run the Automation (1:00 – 2:00)

**Show the terminal. Type:**
```bash
python src/main.py
```
*(or `--mode demo` explicitly for clarity)*

**Say:**
> *"I'm running the automation now. In a real scenario, this triggers automatically when the email arrives. For the demo, we're running it directly."*

**As it runs, narrate what the console shows:**
> *"It's loading the Master Tracker... reading the contractor's update... matching the Unit IDs... and applying the changes."*

*(Typical run time: 1–3 seconds)*

**When it finishes, point to the console output:**
> *"Done. 10 units updated. 2 skipped — their status hadn't changed, so we don't touch them. Zero errors."*

---

### ⏱️ MINUTE 3 — Show the Results (2:00 – 3:00)

**The browser should have auto-opened with the HTML report. Point to it:**

> *"This is the summary report that gets generated automatically — and in production, this would be emailed to your coordinator the moment the process finishes."*

**Show the report:**
- Point to the **stat cards**: Updated / Skipped / Not Found / Errors
- Point to the **Updated Units table**: Unit ID, previous status, arrow, new status
- Mention: *"Every change is logged — full audit trail."*

**Now open `output/Master_Tracker_Updated.xlsx`:**

> *"And here's the updated Master Tracker."*

**Point out:**
- `REN-001`: changed from `In Progress` → `Awaiting Inspection`
- `REN-004`: changed from `In Progress` → `Completed`
- `REN-010`: changed from `In Progress` → `Completed`

**Close with:**
> *"What your team does in 2 hours — this does in under 5 seconds. And it's running entirely within your existing Microsoft environment. No new software, no new subscriptions."*
>
> *"This is the demo version using Python locally. When we move to production, we replace the local file with your Outlook inbox and SharePoint — the core logic stays identical."*
>
> *"Any questions?"*

---

## Key Talking Points (If Asked)

### "Is this using AI?"
> *"No — and that's intentional. This is rule-based matching: Unit ID in → Status updated. It's deterministic, auditable, and doesn't need training data. Simple and reliable."*

### "What happens in production vs this demo?"
> *"In the demo, we run it locally from a terminal. In production, Power Automate triggers it the moment the contractor's email arrives — no one has to run anything manually."*

### "What if the contractor sends the wrong format?"
> *"The system logs any Unit ID it can't match — they appear in the 'Not Found' section of the report. Nothing is silently dropped."*

### "Does this need Microsoft 365?"
> *"The demo works with any Python environment. The production version will use your existing Microsoft 365 — no new licenses needed."*

### "What would the full production build look like?"
> *"Same architecture: email trigger, Excel processing, summary email. We'd add Power Automate as the scheduler, Outlook as the inbox, and SharePoint as the file store. The processing logic is already written."*

---

## What NOT to Say

- ❌ Don't say "prototype" — say "proof of concept"
- ❌ Don't say "this is just a script" — say "this is the automation engine"
- ❌ Don't open the Python code on screen — stay at the business level
- ❌ Don't apologise for using local files — frame it as "built for the demo environment"

---

## Demo Fallback (If Something Goes Wrong)

1. **If the script errors** — open `output/` and show the pre-generated files from the test run
2. **If the HTML report doesn't open** — manually open `output/summary_report.html` in Chrome
3. **If Excel shows no changes** — open `output/Master_Tracker_Updated.xlsx` (not the original `data/` file)

---

*Demo Guide v2.0 | Python Stack | Designed for 3-minute live client demo*
