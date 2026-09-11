# LeadFlow AI Quick Start Guide

## What Is LeadFlow AI?

LeadFlow AI automatically qualifies inbound sales leads in seconds instead of 16+ minutes of manual research. It verifies company domains, enriches lead data, calculates fit scores, generates personalized email drafts, and enforces human approval before any sales outreach.

## Who Is It For?

**Primary User:** Sales Development Representatives (SDRs) who need to quickly qualify and respond to inbound leads

**Secondary User:** Revenue Operations managers who need audit trails and governance over sales communications

## What Does It Do?

1. **Takes** an inbound lead form submission
2. **Verifies** the company domain exists and is reachable
3. **Checks** the company website for basic metadata
4. **Enriches** with company data (headcount, industry, funding)
5. **Calculates** an ICP fit score (0-100) using business rules
6. **Generates** a personalized first-touch email draft
7. **Validates** the draft doesn't contain unauthorized claims
8. **Requires** human approval before any CRM dispatch
9. **Logs** every decision for audit purposes

## Requirements

- **Python 3.11 or higher**
- **Modern web browser** (Chrome, Edge, Firefox, Safari)
- **Internet connection** (for domain verification)
- **Windows, Mac, or Linux**

## Install

### Step 1: Install Dependencies

Open a terminal/command prompt and navigate to the project:

```bash
cd day2
pip install -r requirements.txt
```

If you get permission errors, try:
```bash
pip install --user -r requirements.txt
```

## Start

### Step 2: Start the Application

**Windows (Easy Way):**
Double-click `start_leadflow.bat` in the project root directory

**Manual Way (Any Platform):**
```bash
cd day2
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see output like:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Open UI

### Step 3: Open the Web Interface

Open your web browser and go to:
```
http://localhost:8000
```

You should see the LeadFlow AI dashboard with:
- A dropdown to select test leads
- A "Process Inbound Lead" button
- Areas for results and approval actions

## Process First Lead

### Step 4: Try the System

1. **Select a test case** from the dropdown (e.g., "TC-01: Enterprise Buyer")

2. **Click "Process Inbound Lead"**

3. **Watch the system work** - you'll see:
   - Domain verification status
   - Website check results
   - Company enrichment data
   - ICP score calculation (0-100)
   - Tier classification (Tier 1, 2, or 3)
   - Routing recommendation
   - Generated email draft

4. **Review the results** - check if the information looks accurate

5. **Check claim validation** - see if any commercial policy violations were detected

## Approve / Edit / Quarantine

### Step 5: Take Human Action

The system requires human approval. You have three options:

**✓ Approve & Dispatch**
- Use when the lead and draft look good
- Changes status from `PREVIEW_ONLY` to `APPROVED_FOR_DISPATCH`
- Generates final CRM payload (not sent to live CRM in this version)

**✎ Edit Draft**
- Use when you want to modify the email before approval
- Edit the draft text in the text area
- System will re-validate your edits for policy violations
- Then approve or make more changes

**🚫 Quarantine**
- Use for competitors, spam, or inappropriate leads
- Marks lead as quarantined in audit log
- Prevents any sales outreach

### What You'll See After Approval

- **Status changes** from `PENDING_REVIEW` to `APPROVED`
- **Dispatch authorization** changes from `False` to `True`
- **CRM status** changes from `PREVIEW_ONLY` to `APPROVED_FOR_DISPATCH`
- **Audit events** logged to database
- **CRM payload** displayed (structured data ready for CRM)

## Run Tests

### Verify Everything Works

To make sure your installation is working correctly:

**Run automated tests:**
```bash
cd day2
pytest backend/tests/test_pipeline.py -v
```
You should see: `56 passed`

**Run benchmark suite:**
```bash
python day3/benchmark/run_12_case_benchmark.py
```
You should see: `12/12 cases PASSED`

## Stop Application

### When You're Done

To stop the application:
- Press `Ctrl+C` in the terminal where it's running
- Or close the terminal window

The web interface will stop working when the application stops.

## Common Issues

### Port Already in Use
If you see "port 8000 already in use":
- Try: `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload`
- Then go to `http://localhost:8001`

### Module Not Found Errors
If you see import errors:
- Make sure you're in the `day2` directory
- Try: `pip install --upgrade -r requirements.txt`

### DNS/Website Timeouts
If domain verification takes a long time:
- This is normal - external websites can be slow
- The system has a 5-second timeout to prevent hanging
- Results will show "UNRESOLVED" or "UNREACHABLE" for failed checks

### Browser Shows "This site can't be reached"
- Make sure the application is still running in the terminal
- Check you're using the right URL: `http://localhost:8000`
- Try refreshing the page

## Next Steps

Once you have the basic system running:

1. **Try different test cases** to see various scenarios
2. **Read the User Guide** at `docs/user_readme.md` for detailed explanations
3. **Check the audit log** at `day2/logs/audit.db` (SQLite database)
4. **Review the architecture** at `docs/architecture.md`
5. **Run the 5-minute demo** using `demo/demo_script.md`

## Need Help?

- **Technical Issues:** See `docs/troubleshooting.md`
- **System Operations:** See `operations/operator_runbook.md`
- **Understanding Results:** See `docs/user_readme.md`
- **System Architecture:** See `docs/architecture.md`