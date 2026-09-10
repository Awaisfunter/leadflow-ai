# LeadFlow AI — Inbound SDR User Runbook (Day 3)

> **Role:** Non-Developer Inbound Sales Development Representative (SDR)  
> **System:** LeadFlow AI Operating System (Day 3 Core)  
> **Purpose:** Step-by-step guide to processing, reviewing, and approving inbound leads

---

## Welcome to LeadFlow AI

As an Inbound SDR, your goal is to respond to qualified prospects in minutes rather than spending 15+ minutes jumping across multiple browser tabs looking up company details, calculating qualification scores, and drafting outreach emails.

LeadFlow AI handles the repetitive research, domain verification, and initial email drafting for you—while keeping **you** in full control of every decision.

---

## 1. How to Start the System

You do not need to write code or configure complex servers.

### Step 1: Launch
Double-click `start.bat` in the `day2` or `day3/scripts` folder.  
A black window will open and display:
```
LeadFlow AI Dashboard available at: http://localhost:8000
```

### Step 2: Open Your Browser
Open Chrome, Edge, or Firefox and go to:
```
http://localhost:8000
```
You will see the **LeadFlow AI Dashboard**.

---

## 2. Processing an Inbound Lead

### Option A: Using Quick Test Presets
Click any of the preset buttons at the top of the form (e.g., **TC-01: Enterprise**, **TC-02: Mid-Market**, or **TC-03: Fast SMB**). The form will automatically populate with realistic lead data.

### Option B: Entering a New Lead Manually
Fill out the fields on the left:
- **First Name & Last Name**
- **Work Email** (e.g., `sarah.chen@acmecorp.com`)
- **Company Name** (e.g., `Acme Corporation`)
- **Job Role** (e.g., `VP of Sales Operations`)
- **Team Size** (Select from dropdown)
- **Inbound Notes / Context** (Paste any notes or form message)

### Step 3: Click "⚡ Process Inbound Lead"
Wait 1–3 seconds while LeadFlow AI checks the domain, looks up the company, calculates the score, and prepares your first-touch draft.

---

## 3. How to Read Your Results

Once processed, the right side of your screen will display 9 structured cards:

### A. Lead Summary
Shows the contact information and confirms the email domain parsed by the system.

### B. External Domain & Web Checks (Live Integrations)
This section shows results from **real public network checks**:
- **DNS Status (`public_dns`):**
  - `VERIFIED ✓`: The company domain exists on the internet and has valid server addresses.
  - `UNRESOLVED !`: The domain did not resolve. This might be a mistyped email or a test domain. The system will continue using internal records if available.
- **Website Reachable (`public_website`):**
  - Shows whether the company website responded (e.g. `Reachable (HTTP 200)`).
  - **HTTPS Security:** Confirms whether the site uses modern encrypted TLS.
  - **Page Title:** Displays the public title of the company's homepage.

### C. Account Enrichment (Synthetic Dataset)
Shows company firmographics from our verified internal account dataset:
- **Verified Headcount** (e.g. `1,250 employees`)
- **Industry** (e.g. `B2B Enterprise Software`)
- **Funding Stage** (e.g. `Series C`)
- **Tech Signals** (e.g. `Salesforce, HubSpot, Snowflake`)

### D. Deterministic ICP Qualification
Shows the objective fit score out of 100:
- **Tier 1 (80–100):** High-priority enterprise lead. Assigned to an Enterprise Account Executive with a **1-hour response SLA**.
- **Tier 2 (60–79):** Solid mid-market fit. Assigned to Commercial AE with a **4-hour response SLA**.
- **Tier 3 (30–59):** Fast SMB / self-serve candidate.
- **Score Breakdown:** Shows exact points awarded for Firmographics (+40 max), Seniority (+25 max), Commercial Intent (+20 max), and Urgency (+15 max).

### E. Risk & Safety Checks
- **Prompt Injection:** Warns if an adversarial prospect submitted hidden instructions designed to trick the system into promising unauthorized discounts.
- **Competitor Risk:** Flags if the lead is from a competing SaaS company phishing for rate cards.
- **Claim Validator:** Confirms that the outreach email draft does **not** contain unreleased product claims, unauthorized discounts, or fabricated customer references.

### F. First-Touch Email Draft
Personalized first-touch email drafted exclusively using verified company facts and approved value propositions.

---

## 4. Making Your Decision (Human Approval Gate)

LeadFlow AI will **never** automatically send an email or push an unverified lead to your CRM. You must take one of three actions:

### 1. ✓ Approve & Dispatch
- Click this button if the lead details, qualification tier, and email draft look good.
- The status updates to `APPROVED`, and the CRM payload updates from `PREVIEW_ONLY` to `APPROVED_FOR_DISPATCH`.

### 2. ✎ Edit Draft
- Click this button if you want to tweak the wording of the email.
- A popup will open allowing you to edit the draft.
- **Safety Feature:** The system will automatically re-check your edits to make sure no unauthorized discounts or forbidden claims were accidentally added.

### 3. ⚠ Quarantine
- Click this button if you suspect the lead is fraudulent, a competitor spying on pricing, or an academic researcher.
- Quarantining suppresses all outbound emails, locks the lead from sales routing, and alerts RevOps.

---

## 5. What to Do When an External Integration Fails

| What You See in the UI | What Happened | What You Should Do |
| :--- | :--- | :--- |
| **DNS Status: UNRESOLVED** | The domain could not be found via public DNS lookup. | Check if the prospect mistyped their email. If the company is verified in the enrichment card, you can still review and approve. |
| **Website: Unreachable** | The company website was unavailable or did not respond within the configured 5.0-second timeout. | No action needed; the system automatically falls back to internal account data. |
| **Claim Check: BLOCKED ⚠** | The draft contains an unauthorized claim (e.g. 50% discount or custom SLA). | Click **✎ Edit Draft**, remove the prohibited phrase, and submit. The claim validator will re-run automatically. |
| **Tier: QUARANTINED** | The system detected a competitor domain or prompt injection attack. | Do not approve. RevOps will review the security alert. |

---

## 6. Where Are Logs Stored?

Every submission, verification check, score calculation, and approval action is recorded in the append-only SQLite audit database at:
```
day2/logs/audit.db
```
You can review the total audit event count and processing time right in the **Audit Trail & Telemetry** card on your dashboard.
