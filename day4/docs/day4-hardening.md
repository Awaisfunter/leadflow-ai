# Day 4 — System Hardening Specifications
## LeadFlow AI Engineering Architecture & Safeguards
**Author:** Awais Saeed | Applied AI Engineer Candidate  
**Date:** 2026-09-08  
**Scope:** Hardening Mechanisms, Safeguards, and Invariant Verification  

---

## 1. Timeout Architecture & Bounded Latency

### Mechanism
- **Authoritative Value:** `5.0 seconds` strict timeout across the entire system.
- **Components Hardened:**
  - `day2/backend/app/config.py`: `website_timeout_seconds: float = 5.0`
  - `day2/backend/app/tools/website_metadata.py`: `_DEFAULT_TIMEOUT = 5.0`
  - `day4/break_tests/run_break_tests.py`: `test_fc02_website_timeout(timeout=5.0)`
- **Guardrail Implementation:**
  - Connect timeout is capped at `min(2.0, timeout)` to fail fast if host is unreachable.
  - If HTTPS times out, the client does NOT attempt an HTTP fallback, eliminating double-timeout latency loops.
  - Returns structured `WebsiteMetadataResult(reachable=False, error_code="TIMEOUT", ...)` with non-developer actionable guidance.
- **Regression Verification:** `test_day4_website_timeout_bounded_latency`.

---

## 2. External Integration Fallback Safeguards

### DNS Failure Fallback
- If DNS-over-HTTPS (DoH via Cloudflare `1.1.1.1`) returns `NXDOMAIN` or fails to resolve:
  1. The pipeline does not throw an unhandled exception.
  2. The lead's domain verification is marked `status="UNRESOLVED"`, `dns_resolves=False`.
  3. A `NEEDS_VERIFICATION` risk flag is appended to the lead.
  4. An `INTEGRATION_FAILED` audit event is recorded.
  5. The pipeline falls back to synthetic account records if present or computes scoring from self-reported form fields.

### Synthetic Enrichment Fallback
- If a domain is not present in `synthetic_companies.json`:
  1. Invokes `make_unavailable_enrichment()`.
  2. Sets `enrichment_available=False` and `verification_status=VerificationStatus.NOT_FOUND`.
  3. Scorer deterministically evaluates the lead using only verified self-reported inputs (team size, role seniority, intent notes).
  4. Logs `ENRICHMENT_FAILED` and `FALLBACK_ACTIVATED` audit events.

### Remote LLM Outage Fallback
- If remote OpenRouter or Gemini API calls fail or timeout:
  1. Fallback template generator `generate_deterministic_fallback_draft()` creates a bounded first-touch email based strictly on verified company facts.
  2. Emits `FALLBACK_ACTIVATED` audit event with template provenance.
  3. Runs deterministic claim validation over the fallback draft.

---

## 3. Commercial Policy Enforcement (Claim Validator)

### Patterns Blocked
- **Unauthorized Discounts:** `(?i)\b(100%|50%|40%|30%|25%|20%|free)\s+discount\b`
- **Absolute SLA Guarantees:** `(?i)\b(100%|99\.999%|zero)\s+(uptime|downtime)\b`
- **Regulatory Commitments:** `(?i)\b(HIPAA|SOC\s*2|GDPR|ISO\s*27001)\s+(certified|certification|compliant|guaranteed)\b`
- **Contractual Guarantees:** `(?i)\bguarantee(d)?\s+to\b`

### Two-Stage Enforcement
1. **Initial Draft Generation:** Evaluated immediately after LLM or fallback draft creation.
2. **Approval Action (Re-validation):** Evaluated in `handle_approval_action` against `final_body`. Any unapproved modifications cause the approval to be rejected, raising `ValueError` and recording `APPROVAL_BLOCKED` and `VALIDATION_BLOCKED` audit events.

---

## 4. Human Approval Gate & Security State Machine

### Authoritative State Machine
- **Lifecycle Transitions:**
  - **Ingestion:** `status = PENDING_REVIEW`, `dispatch_authorized = False`, `crm_status = "PREVIEW_ONLY"`
  - **Approval:** `status = APPROVED`, `dispatch_authorized = True`, `crm_status = "APPROVED_FOR_DISPATCH"`
  - **Quarantine:** `status = QUARANTINED`, `dispatch_authorized = False`, `crm_status = "PREVIEW_ONLY"`
  - **Rejection:** `status = REJECTED`, `dispatch_authorized = False`, `crm_status = "STATUS_REJECTED"`

### Hard Security Invariants
1. **Quarantine Lock:** A lead with `QUARANTINED` status cannot transition to `APPROVED` via SDR action. Attempting to approve raises a `SecurityViolation` and logs `APPROVAL_BLOCKED`.
2. **Rejection Lock:** A lead with `REJECTED` status cannot be approved without administrative reset.
3. **Mandatory Final Text Re-validation:** Approval fails if `final_body` contains prohibited claims.

---

## 5. Append-Only Audit Logging

All pipeline operations, security detections, fallback activations, and human approval events are recorded in the append-only SQLite audit database (`logs/audit.db`).
- `VALIDATION_PASSED` / `VALIDATION_BLOCKED`
- `RISK_DETECTED` / `SECURITY_VIOLATION`
- `DOMAIN_CHECK_COMPLETED` / `WEBSITE_CHECK_COMPLETED`
- `INTEGRATION_FAILED` / `FALLBACK_ACTIVATED`
- `ICP_SCORED`
- `APPROVAL_STATE_CHANGED` / `APPROVAL_BLOCKED`
- `CRM_PAYLOAD_GENERATED`
