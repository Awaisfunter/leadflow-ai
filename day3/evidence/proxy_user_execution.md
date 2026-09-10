# Proxy-User Execution Evidence — Day 3

> **Document Type:** First proxy-user UI execution record  
> **Project:** LeadFlow AI — Inbound Lead Operating System (v0)  
> **Sprint Milestone:** Day 3 of 5-Day Remote AI OS Sprint  
> **Date:** September 8, 2026  
> **Classification:** `[OBSERVED / MEASURED]`

---

## Proxy-User Details

| Field | Value |
|:---|:---|
| **Proxy User** | Awais Saeed — SDR Proxy / Sprint Candidate |
| **Role Simulated** | Non-Developer Inbound SDR |
| **Operating System** | Windows 11 |
| **Python Version** | Python 3.13.5 |
| **Server** | FastAPI + Uvicorn (localhost:8000) |
| **Browser** | Google Chrome |
| **Test Case Selected** | TC-01: Enterprise Buyer (Tier 1) |

---

## Execution Steps

### Step 1 — Start Application
- **Action**: Double-clicked `day2/start.bat`
- **Observed**: Terminal opened. Server printed startup messages. Uvicorn bound to `http://0.0.0.0:8000`.
- **Result**: ✅ Server running

### Step 2 — Open Browser
- **Action**: Navigated to `http://localhost:8000` in Chrome
- **Observed**: LeadFlow AI SDR Dashboard loaded. Dark-mode interface with header, lead input panel, and empty results area visible.
- **Result**: ✅ UI loaded without errors

### Step 3 — Select Test Case Preset
- **Action**: Clicked the **TC-01: Enterprise** preset chip in the input form
- **Observed**: All form fields auto-populated:
  - First Name: `Sarah`
  - Last Name: `Chen`
  - Email: `sarah.chen@acmecorp.com`
  - Company: `Acme Corporation`
  - Role: `VP of Sales Operations`
  - Team Size: `500-1000`
  - Notes: *"We are replacing our legacy lead qualification tool across 80 reps in Q4..."*
- **Result**: ✅ Preset populated correctly

### Step 4 — Process Lead
- **Action**: Clicked **"⚡ Process Inbound Lead"** button
- **Observed**: Pipeline execution stepper animated through all 8 stages sequentially:
  1. `✓ Validated`
  2. `✓ DoH DNS`
  3. `✓ Website Check`
  4. `✓ Synthetic Enriched`
  5. `✓ Scored`
  6. `✓ Drafted`
  7. `✓ Claim Check`
  8. `✓ Approval`
- **Total pipeline execution time**: 2,691 ms
- **Result**: ✅ Pipeline completed without errors

### Step 5 — Review External Verification (Section D)
- **Action**: Scrolled to Section D (External Verification)
- **Observed**:
  - DNS Status: **VERIFIED** (green badge)
  - Resolved IPs: `['104.16.132.229', '104.16.133.229']`
  - DNS Latency: **285 ms**
  - Website Reachable: **Yes** (HTTP 200)
  - HTTPS: **Yes** (TLS confirmed)
  - Page Title: `"Cloudflare: Build for the agent era"` (bounded extraction)
  - Website Response Time: **1,944 ms**
- **Result**: ✅ External verification data displayed correctly

### Step 6 — Review Qualification Score (Section F)
- **Action**: Scrolled to Section F (Qualification)
- **Observed**:
  - ICP Score: **100 / 100**
  - Tier Badge: **Tier 1** (green)
  - Scoring Breakdown: Firmographic (40) + Role (25) + Intent (20) + Tech (15) = 100
  - Routing Decision: `ROUTE_ENTERPRISE_AE`
  - SLA: 1 Hour
- **Result**: ✅ Score and routing matched Day 1 expected values exactly

### Step 7 — Review Risk & Safety (Section G)
- **Action**: Scrolled to Section G (Risk & Safety)
- **Observed**:
  - Prompt Injection: **Not Detected**
  - Competitor Flag: **Clear**
  - Claim Validation: **PASSED** (green)
- **Result**: ✅ No risk flags raised for clean enterprise lead

### Step 8 — Review AI Draft (Section H)
- **Action**: Scrolled to Section H (First-Touch Draft)
- **Observed**:
  - Subject line and email body displayed
  - Generation provenance: `deterministic_fallback` (no LLM key in environment)
  - Draft did not contain any blocked commercial commitments
- **Result**: ✅ Draft generated and claim-validated

### Step 9 — Approve & Dispatch (Section I)
- **Action**: Clicked **"✓ Approve & Dispatch"** button
- **Observed**:
  - Approval state changed from `PENDING_REVIEW` → **APPROVED**
  - CRM Status watermark updated from `PREVIEW_ONLY` → **APPROVED_FOR_DISPATCH**
  - `approved_by: "awais_sdr"` populated in CRM metadata
  - Approval timestamp recorded
- **Result**: ✅ Human approval gate completed successfully

### Step 10 — Verify Audit Trail (Section K)
- **Action**: Scrolled to Section K (Audit & Telemetry)
- **Observed**:
  - Audit event count: **11 events** recorded
  - Events included: `LEAD_RECEIVED`, `VALIDATION_PASSED`, `DOMAIN_CHECK_COMPLETED`, `WEBSITE_CHECK_COMPLETED`, `ENRICHMENT_COMPLETED`, `ICP_SCORED`, `DRAFT_GENERATED`, `CLAIM_VALIDATED`, `APPROVAL_STATE_CHANGED`, `CRM_PAYLOAD_GENERATED`
  - SQLite persistence: **Active** (`logs/audit.db`)
- **Result**: ✅ Append-only audit trail confirmed

---

## Observed vs Expected: TC-01 Summary

| Checkpoint | Expected | Observed | Match |
|:---|:---|:---|:---|
| Pipeline completes without error | Yes | Yes | ✅ PASS |
| DNS status | VERIFIED | VERIFIED | ✅ PASS |
| Website reachable | Yes | Yes (HTTP 200) | ✅ PASS |
| ICP score | 100 | 100 | ✅ PASS |
| ICP tier | Tier 1 | Tier 1 | ✅ PASS |
| Routing action | ROUTE_ENTERPRISE_AE | ROUTE_ENTERPRISE_AE | ✅ PASS |
| Claim validation | PASSED | PASSED | ✅ PASS |
| Pre-approval CRM state | PREVIEW_ONLY | PREVIEW_ONLY | ✅ PASS |
| Post-approval CRM state | APPROVED_FOR_DISPATCH | APPROVED_FOR_DISPATCH | ✅ PASS |
| Audit events recorded | ≥ 10 | 11 | ✅ PASS |

---

## Visual Evidence Artifacts

The following live execution screenshots were captured directly during this proxy-user session and are packaged in `day3/evidence/screenshots/`:

1. **`01_tc01_preset_selected.png`**  
   *Initial state:* SDR dashboard loaded, TC-01 preset clicked, form auto-populated with Acme Corporation enterprise lead details.
2. **`02_external_verification_and_qualification.png`**  
   *Processing state:* Pipeline stepper green across stages; Section D displaying real Cloudflare DoH DNS verification (status: VERIFIED, latency: 285ms) and HTTP website inspection (status: 200 OK, HTTPS: active); Section F displaying ICP Score 100/100 (Tier 1).
3. **`03_approved_crm_and_audit.png`**  
   *Approved state:* Human approval gate clicked ("✓ Approve & Dispatch"); approval status confirmed; CRM payload watermark updated to `APPROVED_FOR_DISPATCH`; Section K displaying 11 audit events persisted in append-only SQLite.
4. **`04_full_dashboard_execution.png`**  
   *Full panorama:* Complete end-to-end dashboard panorama capturing all 11 cards in the approved state.

---

## Overall Execution Result

**STATUS: PASS**

The target user (SDR proxy) was able to:
1. Start the application without developer assistance using a single double-click.
2. Select a pre-configured test case without reading documentation.
3. Process a lead end-to-end in under 3 seconds.
4. Interpret all verification, scoring, and risk outputs without technical background.
5. Execute the human approval gate and observe the resulting state change in the CRM preview.
6. Confirm the audit trail recorded all events correctly.

**Answer to the Day 3 key question:**  
*"Can someone else run the core workflow when you are not beside them?"*  
**Yes — demonstrated by this proxy-user execution record.**

