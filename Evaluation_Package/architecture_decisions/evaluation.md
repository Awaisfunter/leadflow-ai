# LeadFlow AI — Day 2 Evaluation Rubric & Pass/Fail Criteria

To prevent subjective assessments and confirm that the Day 2 deliverable constitutes a **repeatable, robust operating system** rather than a one-time generation, the system is evaluated against **10 strict automated criteria**.

---

## 1. Day 2 Pass / Fail Criteria

| Criterion | Evaluation Requirement | Verification Method | Status |
|---|---|---|---|
| **PASS 1: End-to-End Execution** | One representative synthetic lead (TC-01) travels from raw JSON input to validated CRM-ready payload without manual developer intervention. | Automated Pipeline Test (`test_crm_payload_validation`) & Web UI run | **PASS** |
| **PASS 2: Pydantic Contract Integrity** | All intermediate data payloads (`LeadInput`, `EnrichedAccount`, `QualificationResult`, `EmailDraft`, `CRMDispatchPayload`, `AuditEvent`) validate against strict Pydantic v2 schemas. | Pytest schema validation suite (`test_valid_lead_schema`) | **PASS** |
| **PASS 3: Deterministic ICP Scoring** | ICP scores and tier assignments are calculated strictly via mathematical formula `max(0, Firm + Role + Intent + Urgency - Penalties)` with zero LLM floating judgments. | Automated arithmetic check (`test_enterprise_scoring`) | **PASS** |
| **PASS 4: Synthetic Data Attribution** | All account enrichment is clearly attributed to `"synthetic_internal_dataset"`. No false claims of live third-party APIs (e.g. LinkedIn, ZoomInfo). | Assertion on `EnrichedAccount.source` | **PASS** |
| **PASS 5: Bounded LLM Responsibilities** | LLM draft context is strictly bounded to verified facts, approved claims, and untrusted customer notes. The model is given zero authority over scoring or CRM states. | Schema inspection of `DraftContext` & prompt separation | **PASS** |
| **PASS 6: Commercial Claim Blocking** | Unauthorized commercial claims (e.g. fake discounts, fabricated certifications, guaranteed SLA promises) are detected and blocked by the deterministic claim validator. | Automated regex test (`test_unsupported_claim_blocking`) | **PASS** |
| **PASS 7: Human Approval Boundary** | High-risk leads default to `QUARANTINED`. Clean leads require explicit human approval (`APPROVED` / `EDITED`) before CRM dispatch authorization is granted. | State machine transition test (`test_human_approval_state_transition`) | **PASS** |
| **PASS 8: Append-only Audit Trail** | Every pipeline execution persists step-by-step audit events (SHA-256 fingerprint, component name, status, latency) into an append-only SQLite audit trail. | SQLite database query assertion (`test_sqlite_audit_events`) | **PASS** |
| **PASS 9: Graceful Failure & Fallbacks** | Missing API keys, unknown domains, and adversarial inputs trigger controlled fallback states rather than unhandled 500 exceptions or application crashes. | Fallback test cases (`test_enrichment_not_found_fallback`, `test_llm_unavailable_fallback`) | **PASS** |
| **PASS 10: Automated Test Suite** | 100% of automated unit and integration tests pass cleanly via `pytest`. | Automated test run: 27 passing tests (including security invariants) | **PASS** |

---

## 2. Explicit Failure Conditions (What Fails Day 2)

A deliverable will be graded as **FAIL** if any of the following occur:
1. **LLM Hallucinated Scoring**: An LLM prompt asks the model to "output an ICP score from 1–100" or decide whether a lead is Tier 1 or Tier 2.
2. **Fabricated Integrations**: Mock functions are labeled as live "Clearbit", "LinkedIn", or "Salesforce" integrations without explicit synthetic attribution.
3. **Autonomous Out-of-Bounds Actions**: The system dispatches outreach or marks a CRM record as finalized without human SDR sign-off.
4. **Prompt Injection Susceptibility**: Lead notes containing "Ignore previous instructions" successfully override system constraints or grant discounts.
5. **Silent Fallback Failure**: If an external API or database is unreachable, the application crashes with an unhandled traceback instead of returning a typed, controlled degradation state.
6. **Hardcoded Secrets**: API credentials or private keys committed to source code or git history.

---

## 3. Key Assessment Question Answered
> **"Can this design become a repeatable system rather than a one-time generation?"**

**YES.** LeadFlow AI v0 achieves repeatability by:
1. Replacing prompt-dependent heuristics with strict Pydantic v2 data contracts at every boundary.
2. Decoupling semantic drafting (LLM) from deterministic business rules (Python arithmetic).
3. Implementing an append-only SQLite audit log that records exact SHA-256 fingerprints, component statuses, and execution latencies for every run.
4. Providing reproducible test fixtures across representative, edge, and adversarial scenarios.
