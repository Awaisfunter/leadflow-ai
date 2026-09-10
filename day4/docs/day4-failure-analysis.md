# Day 4 — Failure Analysis & Root Cause Investigation
## LeadFlow AI Break Test Evaluation Suite
**Author:** Awais Saeed | Applied AI Engineer Candidate  
**Date:** 2026-09-08  
**Environment:** Windows 11, Python 3.13, FastAPI Backend  

---

## Overview

During Day 4, LeadFlow AI was subjected to deliberate stress and break tests across 10 distinct failure modes (FC-01 through FC-10). This document provides an in-depth investigation into the failures, root causes, hardening interventions, and verified regression status.

---

## Detailed Root Cause Analysis for Significant Failures

### 1. FC-02: External Website HTTP Timeout & Latency Degradation
- **Failure:** Unresponsive or non-routable company website causes pipeline latency spikes.
- **Reproduction:** Submit an inbound lead whose domain points to a non-routable or dropping IP address (`10.255.255.1`) or a web server dropping SYN packets without FIN/RST.
- **Expected:** Pipeline must enforce a strict, bounded timeout ceiling (<= 5.0 seconds), return a structured `TIMEOUT` result, provide actionable guidance for the non-technical SDR, and never hang the dashboard.
- **Observed:** Prior to hardening, default client configurations allowed timeouts to stretch up to 8–10s, and if retrying on HTTP, could double the delay to 16–20s.
- **Root Cause:** Default httpx configurations without strict separate connect/read timeouts allow unroutable connections to consume full socket retry cycles.
- **Why It Matters:** Inbound SDRs process leads in real time. Latencies exceeding 5 seconds lead to abandoned sessions and SDR confusion.
- **Hardening Change:**
  1. Configured `website_timeout_seconds: float = 5.0` in `config.py`.
  2. In `website_metadata.py`, set connect timeout to `min(2.0, timeout)`.
  3. Added single-attempt guardrail: if HTTPS times out, skip HTTP fallback to avoid doubling latency.
  4. Formatted error message with explicit 5.0s limit and actionable SDR guidance.
- **Post-Hardening Result:** Timed out cleanly in 2383ms, well below the 5.0s threshold, with actionable message.
- **Regression Test:** `test_day4_website_timeout_bounded_latency` in `backend/tests/test_pipeline.py`.

---

### 2. FC-03: Silent Fallback Telemetry Gap on Remote LLM Outage
- **Failure:** When remote LLM APIs fail, deterministic fallback templates engage without emitting an auditable event.
- **Reproduction:** Configure OpenRouter/Gemini endpoints to return HTTP 404/503.
- **Expected:** Pipeline falls back to deterministic outreach templates AND records an explicit `FALLBACK_ACTIVATED` event in the append-only SQLite audit database.
- **Observed:** The fallback draft was generated correctly, but no dedicated `FALLBACK_ACTIVATED` audit event was logged; the audit trail only showed `DRAFT_GENERATED`.
- **Root Cause:** The draft generation step in `pipeline.py` did not invoke `_audit(..., EventType.FALLBACK_ACTIVATED)` when `draft.is_fallback` was True.
- **Why It Matters:** Without auditable fallback telemetry, RevOps managers and engineers cannot detect silent LLM provider degradation or measure fallback rates in production.
- **Hardening Change:** Added `EventType.FALLBACK_ACTIVATED` to `audit_logger.py` and inserted explicit audit emission in `pipeline.py` whenever fallback templates are engaged.
- **Post-Hardening Result:** Audit trail immediately records `FALLBACK_ACTIVATED` with template provenance.
- **Regression Test:** `test_day4_llm_draft_fallback_emits_fallback_activated_audit_event`.

---

### 3. FC-10: Unauthorized Commercial Claim Smuggling via Post-Generation Edit
- **Failure:** Attacker or rogue SDR circumvents commercial policies by editing a clean draft to include unauthorized commitments prior to approval.
- **Reproduction:** Generate a lead with a clean draft, invoke `handle_approval_action` with `edited_body="We promise a 50% discount and full HIPAA certification"`, and action `APPROVE`.
- **Expected:** The human approval gate must re-validate the FINAL edited text before authorizing CRM dispatch, blocking approval if violations are found.
- **Observed:** Early v0 designs assumed validation only needed to run once during initial pipeline processing.
- **Root Cause:** Approval handlers that trust the in-memory draft without secondary re-validation create a commercial commitment vulnerability.
- **Why It Matters:** Commercial commitments (discounts, uptime SLAs, regulatory certifications) expose the company to legal and contractual liability.
- **Hardening Change:** In `handle_approval_action()`, added mandatory re-validation via `validate_draft()` on `final_body`. If claims fail, approval is rejected with an exception, and `APPROVAL_BLOCKED` and `VALIDATION_BLOCKED` events are recorded.
- **Post-Hardening Result:** Approval attempt was immediately rejected, state remained `PENDING_REVIEW`, and `VALIDATION_BLOCKED` was recorded.
- **Regression Test:** `test_day4_tampered_edit_claim_bypass_records_audit_event` and `test_approval_gate_test_g_unsafe_edited_draft_cannot_be_approved`.

---

### 4. FC-09: Direct Quarantine Approval Bypass Attempt
- **Failure:** Attempt to directly approve a lead that has been flagged as `QUARANTINED` due to prompt injection or adversary detection.
- **Reproduction:** Process an injection lead (`DarkCorp`), obtain lead ID, and call `handle_approval_action(lead_id, action="APPROVE")`.
- **Expected:** Security invariant violation raised, approval blocked, state maintained as `QUARANTINED`, and audit event `APPROVAL_BLOCKED` emitted.
- **Observed:** In Day 2, UI prevented the button click, but the backend API endpoint lacked an explicit hard exception.
- **Root Cause:** Reliance on client-side controls without defense-in-depth backend invariant enforcement.
- **Hardening Change:** Added backend security invariant in `handle_approval_action`:
  ```python
  if prev_status == ApprovalStatus.QUARANTINED and new_status == ApprovalStatus.APPROVED:
      log_audit_event(...)
      raise ValueError("Security Violation: Cannot directly approve a QUARANTINED lead. Security / RevOps clearance is required.")
  ```
- **Post-Hardening Result:** Direct approval attempt raises `ValueError`, logs `APPROVAL_BLOCKED`, and leaves dispatch locked.
- **Regression Test:** `test_approval_gate_test_f_quarantined_lead_cannot_be_approved`.

---

## Complete Failure Matrix Summary

| Failure ID | Category | Primary Cause | Hardening Mechanism | Verified Status |
|---|---|---|---|---|
| **FC-01** | DNS Failure | Unallocated domain (NXDOMAIN) | Fallback to synthetic facts + `INTEGRATION_FAILED` audit | **PASS** |
| **FC-02** | Website Timeout | Unroutable / non-responsive IP | 5.0s bounded timeout + single-attempt guardrail | **PASS** |
| **FC-03** | LLM Outage | Remote API failure / 404 | Deterministic fallback + `FALLBACK_ACTIVATED` audit | **PASS** |
| **FC-04** | Prompt Injection | Malicious instruction in notes | Pre-flight regex detector + quarantine routing | **PASS** |
| **FC-05** | Website Injection | Untrusted title override text | Strict untrusted boundary; isolated from scoring | **PASS** |
| **FC-06** | Unsafe Claims | Discount/SLA commitments in draft | Regex claim validator blocks commitment patterns | **PASS** |
| **FC-07** | Malformed Payload | Missing mandatory schema fields | Pydantic schema validation returns HTTP 422 | **PASS** |
| **FC-08** | Enrichment Miss | Domain not in synthetic dataset | `make_unavailable_enrichment` fallback scoring | **PASS** |
| **FC-09** | Quarantine Bypass | Direct approval of quarantined lead | Server-side security invariant + `APPROVAL_BLOCKED` audit | **PASS** |
| **FC-10** | Unsafe Edit Bypass | Rogue SDR inserts unapproved claim | Mandatory re-validation of edited text upon approval | **PASS** |
