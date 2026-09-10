# Day 2 — Design the System and Ship v0
**Author**: Awais Saeed | Applied AI Engineer Candidate  
**Sprint**: 5-Day Remote AI OS Sprint — Applied AI Engineer Assessment  
**Project**: LeadFlow AI  
**Status**: Day 2 Completed & Verified  

---

## 1. Objective
The Day 2 sprint objective is to transition from Day 1 discovery and empirical baseline modeling into a **working, repeatable v0 operating system**:
- Design end-to-end data flow and system architecture.
- Enforce strict input/output Pydantic v2 data contracts.
- Implement deterministic account enrichment, risk detection, and mathematical ICP scoring.
- Establish bounded LLM first-touch drafting with post-generation claim validation.
- Enforce a mandatory human approval state gate.
- Build an append-only SQLite audit trail and a simple non-developer SDR web interface.
- Move **one representative synthetic lead (TC-01)** completely through the end-to-end flow from raw input to CRM-ready payload.

---

## 2. What Was Built
1. **Backend Service (`backend/app/`)**:
   - `schemas/models.py`: 11 Pydantic v2 data contracts governing all system boundaries.
   - `tools/enrichment.py`: Deterministic synthetic enrichment adapter with fallback handling.
   - `services/icp_scorer.py`: Pure Python scoring engine implementing Day 1 formula and explicit accelerated SMB exceptions.
   - `services/risk_detector.py`: Pre-flight regex detector for prompt injection, competitor domains, and disposable webmail.
   - `services/claim_validator.py`: Post-generation commercial claim guardrail.
   - `services/llm_draft.py`: Configurable LLM provider adapter (current provider: Google Gemini) with a deterministic template fallback when the provider is unavailable.
   - `services/audit_logger.py`: Thread-safe append-only SQLite audit trail logger.
   - `services/pipeline.py`: Master orchestrator coordinating all pipeline steps, security invariants, and human approval transitions.
   - `api/routes.py` & `main.py`: FastAPI application serving REST endpoints and the web dashboard.
2. **Synthetic Data Engine (`data/`)**:
   - `synthetic_companies.json`: Controlled local firmographic dataset (explicitly labeled `synthetic_internal_dataset`).
   - `business_rules.json`: Centralized scoring weights, competitor domains, and blocked claim signatures.
   - `synthetic_leads.json`: Benchmark presets for 1-click evaluation.
3. **Non-Developer SDR Dashboard (`frontend/index.html`)**:
   - Interactive web interface displaying Lead Summary, Enrichment, ICP Scoring Breakdown, Safety Checks, Bounded First-Touch Draft with inline editor, Human Approval Actions, and Synthetic CRM JSON Preview.
4. **Automated Test Suite (`backend/tests/test_pipeline.py`)**:
   - 27 comprehensive pytest scenarios covering schemas, arithmetic, tier thresholds, security quarantines, claim blocking, approval bypass defense, and append-only audit persistence.
5. **Architectural Documentation (`docs/`)**:
   - Architecture specification with Mermaid diagrams, data contracts, tool boundaries, privacy boundaries, evaluation rubrics, and AI collaboration records.

---

## 3. Architecture & Data Flow
The system follows a strict **hybrid architecture**:
```
Raw Inbound Lead (Web Form)
  │
  ▼
[FastAPI /api/leads/process] ──► Pydantic v2 Validation (LeadInput)
  │
  ▼
[Pre-Flight Risk Detector] ────► Scans prompt injection, competitor domains, disposable webmail
  │
  ▼
[Synthetic Enrichment] ────────► Lookups verified company firmographics (synthetic_internal_dataset)
  │
  ▼
[Deterministic ICP Scorer] ────► max(0, Firm + Role + Intent + Urgency - Penalties) ──► Tier 1/2/3
  │
  ▼
[Bounded Context Assembler] ───► Packages verified facts & approved claims (DraftContext)
  │
  ▼
[Generative LLM / Fallback] ——► Configurable LLM Provider (current: Google Gemini) / Deterministic Template (EmailDraft)
  │
  ▼
[Claim Validator] ─────────────► Deterministically blocks unauthorized discounts & fake certifications
  │
  ▼
[Human Approval Gate] ─────────► SDR Dashboard: PENDING_REVIEW ──► APPROVE / EDIT / QUARANTINE
  │
  ▼
[CRM Dispatch Payload] ────────► Validated CRM-ready JSON object (Preview Mode, no live CRM in v0)
  │
  ▼
[SQLite Audit Logger] ─────────► Append-only SQLite audit trail

 (logs/audit.db)
```

---

## 4. Data Contracts Summary
All data is typed and validated using Pydantic v2:
- `LeadInput`: Untrusted customer form submission.
- `LeadIdentity`: Extracted domain, corporate/webmail classification, and unique `lead_id`.
- `EnrichedAccount`: Verified headcount, industry, funding, and tech stack from `synthetic_internal_dataset`.
- `LeadRiskFlags`: Security and quarantine triggers.
- `QualificationResult`: Explainable ICP scoring breakdown and routing action.
- `DraftContext`: Filtered context passed to LLM (no raw system instructions).
- `EmailDraft`: Structured subject line, body, and language.
- `ClaimValidationResult`: Guardrail pass/blocked flags and warnings.
- `ApprovalStateRecord`: Human reviewer identity, action, and timestamp.
- `CRMDispatchPayload`: CRM-ready JSON payload.
- `AuditEvent`: SQLite event record.

---

## 5. Tools & Operational Boundaries
- **Enrichment**: Read-only local JSON lookup. Unknown domains produce `enrichment_available=False` without fabricating facts.
- **Scoring**: Pure arithmetic function. Generative LLMs are strictly prohibited from calculating or modifying scores.
- **LLM Drafting**: Bounded generation with prompt injection isolation. Customer notes are labeled as untrusted context.
- **Claim Validator**: Regex-based post-generation filter. Blocks approval if unauthorized commercial commitments are present.
- **Audit Logger**: Append-only SQLite logging.

---

## 6. Model & Provider Choice
- **LLM Provider**: Configurable provider adapter.
- **Current Configured Provider**: Gemini (via `google-generativeai` or OpenRouter adapter).
  - *Rationale*: High reasoning speed, low latency, cost efficiency, and strong instruction compliance for bounded context prompts.
- **Offline / Deterministic Fallback**: Rule-based template generator (`generate_deterministic_fallback_draft`).
  - *Rationale*: The deterministic fallback allows the core workflow to continue when the LLM provider is unavailable, credentials are not configured, or the system is operating without the external LLM dependency.

---

## 7. Storage Choice
- **Database**: Append-only SQLite audit database (`logs/audit.db`).
  - *Rationale*: Zero-dependency, file-based, thread-safe, and self-initializing. Ideal for v0 local execution while providing identical SQL schema structures for future migration to PostgreSQL.

---

## 8. Human Approval Boundary
The system enforces human governance before any CRM dispatch:
- Standard leads initialize to `PENDING_REVIEW`.
- Leads flagged for competitor reconnaissance or prompt injection initialize to `QUARANTINED`.
- The SDR must explicitly click **Approve & Dispatch**, **Edit Draft**, or **Quarantine**.
- If a draft contains blocked claims, the system prevents approval until the violation is removed.
- Crucially, when an SDR edits a draft before approval, the claim validator re-scans the **final edited body** before granting approval, preventing approval-bypass attacks.
- All actions record the reviewer identifier (`demo_user`), timestamp, and prior state.

---

## 9. Fallback & Resilience Mechanisms
1. **Missing LLM Key / Outage**: Automatically switches to the deterministic fallback template.
2. **Missing Company in Dataset**: Sets `enrichment_available=False`; scores based on form data and alerts SDR.
3. **Malformed Inbound Data**: Rejects with HTTP 422 and exact field errors.
4. **Adversarial Prompt Injection**: Quarantines submission, deducts -100 points, and suppresses sales drafting.

---

## 10. Privacy & Permissions
- **Data Boundary**: Synthetic data only. No real customer PII or credentials.
- **Secrets Management**: Loaded strictly via `.env` through `pydantic-settings`.
- **Untrusted Content**: Notes are strictly quarantined from executable system prompts.
- **Role Isolation**: SDR reviews drafts; RevOps configures business rules and inspects audit logs.

---

## 11. Evaluation Results (PASS 1 to PASS 10)
All 10 Day 2 criteria have been verified and passed:
- PASS 1 (End-to-End Flow): **PASSED**
- PASS 2 (Pydantic Contracts): **PASSED**
- PASS 3 (Deterministic Scoring): **PASSED**
- PASS 4 (Synthetic Attribution): **PASSED**
- PASS 5 (Bounded LLM Scope): **PASSED**
- PASS 6 (Claim Blocking): **PASSED**
- PASS 7 (Human Approval Gate & Bypass Defense): **PASSED**
- PASS 8 (Append-only SQLite Audit Logging): **PASSED**
- PASS 9 (Graceful Fallbacks): **PASSED**
- PASS 10 (Automated Tests): **PASSED (27/27)**

---

## 12. Happy-Path Demonstration (TC-01: Sarah Chen / Acme Corporation)
```json
{
  "lead": {
    "name": "Sarah Chen",
    "email": "sarah.chen@acmecorp.com",
    "company": "Acme Corporation",
    "role": "VP of Sales Operations",
    "team_size": "500-1000",
    "notes": "We are replacing our legacy lead qualification tool across 80 reps in Q4. Need enterprise SLA and custom Salesforce integration."
  },
  "enrichment": {
    "source": "synthetic_internal_dataset",
    "verified_headcount": 850,
    "industry": "Enterprise Software",
    "funding": "Public",
    "tech_signals": ["Salesforce", "Slack", "AWS", "Outreach"]
  },
  "qualification": {
    "tier": "Tier 1",
    "final_score": 100,
    "breakdown": {
      "firmographic_points": 40,
      "role_points": 25,
      "intent_points": 20,
      "urgency_points": 15,
      "risk_penalty": 0
    },
    "next_action": "ROUTE_ENTERPRISE_AE",
    "sla_hours": 1
  },
  "approval": {
    "status": "APPROVED",
    "reviewer": "awais_sdr",
    "dispatch_authorized": true
  },
  "crm_payload": {
    "crm_status": "APPROVED_FOR_DISPATCH",
    "dispatch_authorized": true,
    "disclaimer": "Synthetic CRM dispatch authorized by human SDR — no live CRM connection in v0."
  }
}
```

---

## 13. Automated Test Results
- Total Tests: **27 passed**
- Duration: **Environment-dependent** (typically 3–9s depending on platform I/O)
- Test Coverage: Schema validation, invalid email, empty fields, arithmetic breakdown, tier thresholds, risk penalty clamping, competitor quarantine, prompt injection detection, draft context bounding, claim blocking, CRM payload validation, human approval state machine, approval bypass defenses (unsafe edits, blocked original, quarantine locks), TC-03 explicit SMB acceleration rule, append-only SQLite audit logging, enrichment fallback, LLM offline fallback, and health endpoint privacy.

---

## 14. Known Limitations in v0
1. **Local Synthetic Data**: The enrichment adapter uses local JSON records; external live APIs (Clearbit/Apollo) are intentionally mocked for testing.
2. **Synthetic CRM Payload**: The CRM dispatcher validates and outputs CRM-ready JSON payloads but does not send HTTP requests to live Salesforce/HubSpot instances.
3. **Deterministic Pre-flight Regex**: Injection detection uses known regex signatures; advanced semantic multi-stage safety models are scheduled for future iterations.

---

## 15. Day 3 Plan
- Implement real-time latency optimization and batch processing.
- Add multi-language drafting support (e.g. TC-07 German GDPR inquiry).
- Enhance the Human-in-the-Loop review experience with diff comparisons between raw and edited drafts.
- Build extended synthetic benchmarking scripts to run all 12 Day 1 benchmark cases in batch mode.
