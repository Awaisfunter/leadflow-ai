# Proxy User Feedback

Proxy User:
Awais Saeed — SDR Proxy

Date/Environment:
2026-09-08 / Windows 11 local workstation (FastAPI backend + Vanilla JS/HTML UI, Port 8000)

---

## What Was Tested
The complete end-to-end inbound SDR workflow on the LeadFlow AI dashboard across 3 realistic lead profiles:
1. **Adversarial Lead:** Prompt injection attempting unauthorized discount via notes (`DarkCorp`).
2. **High-Value Enterprise Lead:** Tier 1 lead requiring review and authorization (`Acme Corporation`).
3. **Low-Fit Inbound Lead:** Tier 3 self-serve inquiry (`TinyBiz Shop`).

Testing evaluated lead presentation clarity, review latency, the human approval gate state transitions, and the CRM payload preview.

---

## Feedback 1
Observation:
When a new inbound lead is processed and presented on screen, the CRM-Ready JSON Payload panel displays `PREVIEW_ONLY`, but the Human SDR Decision action box did not clearly indicate whether the lead was currently safe or whether any action had already taken place. It was easy to mistake the pre-approval state for a completed action because the outreach draft was already visible.

Problem:
A non-developer SDR might not immediately realize that the CRM dispatch is completely locked until they explicitly click "Approve & Dispatch". Furthermore, if an SDR wanted to confirm whether the CRM payload was ready to transmit or still held in draft mode, they had to read the raw JSON structure (`dispatch_authorized: false`) inside the pre block.

Change:
Added an explicit, dynamic visual badge (`res-approval-badge`) directly inside the Human SDR Decision bar displaying `AWAITING REVIEW` (with state text: `Pre-approval state: PENDING_REVIEW (CRM dispatch locked)`). Added a companion lock indicator `(Dispatch Locked 🔒)` right next to the `PREVIEW_ONLY` badge in the CRM card header, along with an SDR Safety Lock explanatory callout. When the SDR clicks "Approve & Dispatch", the badge flips to `DISPATCH AUTHORIZED` (green), the indicator updates to `(Dispatch Authorized ✓)`, and the Approve button is safely disabled to prevent duplicate submissions.

Before:
- Approval bar showed static text: "Review output above. Approval authorizes synthetic CRM payload generation."
- CRM header only displayed `PREVIEW_ONLY` with no explanation of the dispatch lock.
- No visual feedback in the approval bar confirming state change upon approval.

After:
- Approval bar displays dynamic badge: `AWAITING REVIEW` (blue) → flips to `DISPATCH AUTHORIZED` (green) upon approval, or `QUARANTINED (LOCKED)` (red) on high-risk leads.
- Subtitle explicitly informs: `Pre-approval state: PENDING_REVIEW (CRM dispatch locked). Click Approve & Dispatch to authorize payload.`
- CRM header displays companion status: `(Dispatch Locked 🔒)` → flips to `(Dispatch Authorized ✓)`.
- Explanatory callout added: `ℹ SDR Safety Lock: Pre-approval payloads are generated with dispatch_authorized=false and crm_status=PREVIEW_ONLY. No outreach is transmitted until explicit human approval.`

Verification:
Tested via browser inspection and proxy SDR test execution. Observed initial state with `AWAITING REVIEW` and `(Dispatch Locked 🔒)`. Upon clicking "Approve & Dispatch", observed instant transition to `DISPATCH AUTHORIZED` and `(Dispatch Authorized ✓)`, with `dispatch_authorized=true` confirmed in the updated CRM payload.

---

## Feedback 2
Observation:
When an external company website took longer than expected to respond (e.g. timeout on slow or non-routable targets), the error message in the external checks card previously referenced technical network terminology.

Problem:
Inbound SDRs are non-technical commercial representatives who need clear operational instructions (whether they should disqualify the lead, ask for clarification, or continue with synthetic account facts), rather than technical socket error codes.

Change:
Standardized the timeout notification to: `"The company website did not respond within 5.0 seconds. Website verification is unavailable; review the lead using the remaining verified information."` In addition, verified that when website reachability fails, the external checks card informs the user that the pipeline safely continued using verified synthetic account facts without blocking the workflow.

Before:
- Error message varied between 3.0s and 8.0s in documentation, and socket errors could appear without an operational SDR instruction.

After:
- Exactly 5.0s bounded timeout enforced and clearly reported with actionable operational instructions for non-technical SDRs.

Verification:
Verified via deliberate failure test `FC-02` and automated test `test_day4_website_timeout_bounded_latency`. The test confirms `reachable=False`, error code `TIMEOUT`, bounded latency under 5000ms, and the presence of clear actionable guidance.
