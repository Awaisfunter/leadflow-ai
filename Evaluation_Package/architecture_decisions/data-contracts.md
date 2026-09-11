# LeadFlow AI — Data Contracts & Schema Specification (Day 2 v0)

All data moving across system boundaries in LeadFlow AI is strictly governed by **Pydantic v2 data models**. This document specifies each contract, its fields, producers, consumers, and validation semantics.

---

## 1. `LeadInput`
- **Purpose**: Represents the untrusted raw inbound payload from a web form.
- **Producer**: Inbound Webhook / User Web Form UI.
- **Consumer**: FastAPI route `/api/leads/process`, Pre-flight Risk Detector.
- **Failure Behavior**: HTTP 422 with exact field validation failure details.

| Field | Type | Required | Constraints / Validation | Description |
|---|---|---|---|---|
| `first_name` | `str` | Yes | `min_length=1`, `max_length=100` | Lead first name |
| `last_name` | `str` | Yes | `min_length=1`, `max_length=100` | Lead last name |
| `email` | `EmailStr` | Yes | RFC 5322 compliant email format | Work or contact email |
| `company` | `str` | Yes | `min_length=1`, `max_length=200` | Self-reported company name |
| `role` | `str` | Yes | `min_length=1`, `max_length=200` | Self-reported job role |
| `team_size` | `str` | Yes | `min_length=1`, `max_length=50` | Self-reported team size bracket |
| `notes` | `Optional[str]`| No | `max_length=2000`, whitespace stripped | Raw free-text customer notes |

---

## 2. `LeadIdentity`
- **Purpose**: Normalized identity metadata extracted from the lead.
- **Producer**: `pipeline.py` (Identity Extraction phase).
- **Consumer**: Enrichment tool, ICP Scorer, CRM payload builder.

| Field | Type | Description |
|---|---|---|
| `lead_id` | `str` (UUIDv4) | Unique identifier for the pipeline execution session |
| `email` | `str` | Normalized lowercase email address |
| `domain` | `str` | Extracted email domain |
| `is_corporate_domain`| `bool` | `False` if free webmail (gmail, yahoo, etc.), else `True` |
| `is_disposable_webmail`| `bool`| `True` if webmail domain |
| `is_competitor_domain`| `bool` | `True` if matched against competitor registry |
| `is_academic_domain` | `bool` | `True` if `.edu` or academic domain |
| `inferred_company_name`| `Optional[str]` | Derived from company name input |
| `created_at` | `datetime` (UTC) | Pipeline inception timestamp |

---

## 3. `EnrichedAccount`
- **Purpose**: Verified company data retrieved from synthetic internal dataset.
- **Producer**: `SyntheticEnrichment` adapter (`lookup_company`).
- **Consumer**: ICP Scorer, Draft Context Assembler, CRM Dispatcher.
- **Important Constraint**: The `source` field MUST strictly state `"synthetic_internal_dataset"`.

| Field | Type | Description |
|---|---|---|
| `domain` | `str` | Verified corporate domain |
| `company_name` | `str` | Official entity name |
| `employee_count` | `int` (`ge=0`) | Numerical verified headcount |
| `employee_range` | `str` | Headcount bracket (e.g. "500-1000") |
| `industry` | `str` | Verified industry vertical |
| `funding_stage` | `str` | Seed, Series A, Series B, Public, etc. |
| `headquarters` | `str` | City, State, Country |
| `technology_signals` | `list[str]` | Detected tech stack (Salesforce, SAP, etc.) |
| `verification_status` | `VerificationStatus`| `VERIFIED`, `COMPETITOR_FLAGGED`, `NOT_FOUND` |
| `source` | `str` | Always `"synthetic_internal_dataset"` |
| `enrichment_available`| `bool` | `False` if fallback record generated |

---

## 4. `LeadRiskFlags`
- **Purpose**: Pre-flight security, competitor, and quality risk signals.
- **Producer**: `RiskDetector` service.
- **Consumer**: ICP Scorer, Approval State machine, Audit Logger.

| Field | Type | Description |
|---|---|---|
| `flags` | `list[RiskFlag]` | Array of detected flags (`COMPETITOR_RISK`, `PROMPT_INJECTION`, etc.) |
| `prompt_injection_detected` | `bool` | `True` if adversarial prompt override signatures found |
| `injection_signatures_found` | `list[str]` | Specific matched regex patterns |
| `requires_human_review` | `bool` | Elevated to human review if any flag is raised |
| `requires_quarantine` | `bool` | Auto-quarantines submission (competitor or injection) |

---

## 5. `QualificationResult`
- **Purpose**: Explainable output of the deterministic ICP scoring calculation.
- **Producer**: `icp_scorer.py` (`score_lead`).
- **Consumer**: Draft Context Assembler, CRM Dispatcher, SDR Dashboard.

| Field | Type | Description |
|---|---|---|
| `tier` | `IcpTier` | `Tier 1`, `Tier 2`, `Tier 3`, `Disqualified`, `Quarantined` |
| `scoring_breakdown` | `ScoringBreakdown`| Firmographics (0–40), Role (0–25), Intent (0–20), Urgency (0–15), Penalty (≤0) |
| `reasoning` | `list[str]` | Bullet-point justification for each awarded point |
| `next_action` | `NextAction` | E.g. `ROUTE_ENTERPRISE_AE`, `ROUTE_COMMERCIAL_AE` |
| `sla_hours` | `Optional[int]` | E.g. 1 hour (Tier 1), 4 hours (Tier 2) |
| `scored_by` | `str` | Always `"deterministic_icp_engine_v1"` |

---

## 6. `DraftContext`
- **Purpose**: Bounded context passed to the generative LLM. No raw system configurations or instructions are included.
- **Producer**: `pipeline.py`.
- **Consumer**: `llm_draft.py` (`generate_draft`).

| Field | Type | Description |
|---|---|---|
| `lead_first_name` | `str` | First name of lead |
| `lead_role` | `str` | Title of lead |
| `company_name` | `str` | Verified company name |
| `industry` | `str` | Verified industry |
| `employee_range` | `str` | Headcount bracket |
| `icp_tier` | `str` | Tier label |
| `key_pain_points` | `list[str]` | Extracted pain points (e.g. "legacy replacement") |
| `approved_value_propositions` | `list[str]` | Explicit list of approved marketing facts |
| `untrusted_customer_notes` | `str` | Raw customer text labeled strictly as untrusted content |
| `prohibited_claims` | `list[str]` | Negative guardrail instructions |

---

## 7. `EmailDraft`
- **Purpose**: Structured output representing the generated first-touch outreach message.
- **Producer**: LLM adapter (`gemini-1.5-flash`) or Deterministic Fallback Template.
- **Consumer**: Claim Validator, SDR Dashboard, CRM Dispatcher.

| Field | Type | Description |
|---|---|---|
| `subject` | `str` | Email subject line (`min_length=5`) |
| `body` | `str` | Email body copy (`min_length=50`) |
| `generated_by` | `str` | Model identifier or `"deterministic_fallback_v1"` |
| `is_fallback` | `bool` | `True` if rule-based template generated the draft |
| `language` | `str` | ISO language code |

---

## 8. `ClaimValidationResult`
- **Purpose**: Post-generation guardrail evaluation.
- **Producer**: `claim_validator.py`.
- **Consumer**: Approval Gate, SDR Dashboard.

| Field | Type | Description |
|---|---|---|
| `passed` | `bool` | `True` if zero blocked claims detected |
| `warnings` | `list[str]` | Advisory warnings for subjective marketing phrases |
| `blocked_claims` | `list[str]` | Prohibited commercial claims (unauthorized discounts, fake SLAs) |
| `requires_human_review` | `bool` | Requires SDR review before dispatch |

---

## 9. `ApprovalStateRecord`
- **Purpose**: Human-in-the-loop governance record.
- **Producer**: SDR Dashboard action / State machine.
- **Consumer**: Pipeline orchestrator, CRM Dispatcher, Audit Logger.

| Field | Type | Description |
|---|---|---|
| `lead_id` | `str` | Pipeline lead identifier |
| `status` | `ApprovalStatus`| `PENDING_REVIEW`, `APPROVED`, `EDITED`, `REJECTED`, `QUARANTINED` |
| `reviewer_id` | `Optional[str]` | Identifier of reviewer (e.g. `"demo_user"`) |
| `previous_status` | `Optional[ApprovalStatus]` | Prior state |
| `updated_at` | `datetime` (UTC) | Timestamp of human action |
| `notes` | `Optional[str]` | Reviewer notes |
| `edited_body` | `Optional[str]` | SDR-edited draft text if modified |

---

## 10. `CRMDispatchPayload`
- **Purpose**: Validated CRM-ready JSON object dispatched to downstream revenue tools.
- **Producer**: `pipeline.py` (`build_crm_payload`).
- **Consumer**: CRM Webhook or integration adapter (simulated in v0).

| Sub-Object | Key Fields |
|---|---|
| `account` | `name`, `domain`, `industry`, `employee_count`, `funding_stage`, `headquarters` |
| `contact` | `first_name`, `last_name`, `email`, `role`, `lead_source` |
| `qualification` | `icp_tier`, `final_score`, `scoring_breakdown`, `reasoning`, `next_action`, `sla_hours` |
| `outreach` | `subject`, `body`, `approved_by`, `approved_at`, `generated_by` |
| `metadata` | `lead_id`, `processed_at`, `system_version`, `data_source`, `crm_status` |

---

## 11. `AuditEvent`
- **Purpose**: Append-only audit log record persisted in SQLite.
- **Producer**: Every component in the pipeline.
- **Consumer**: SQLite database (`logs/audit.db`), RevOps compliance audit endpoint.

| Field | Type | Description |
|---|---|---|
| `event_id` | `str` (UUIDv4) | Unique event primary key |
| `lead_id` | `str` | Session lead identifier |
| `event_type` | `EventType` | Enum: `LEAD_RECEIVED`, `ICP_SCORED`, `DRAFT_GENERATED`, etc. |
| `timestamp` | `datetime` (UTC) | Ingestion timestamp |
| `component` | `str` | Name of executing component |
| `status` | `str` | `SUCCESS`, `FLAGGED`, `BLOCKED`, `PENDING` |
| `input_hash` | `Optional[str]` | SHA-256 fingerprint of input |
| `output_summary` | `Optional[str]` | Safe sanitised summary |
| `latency_ms` | `Optional[int]` | Step execution duration in milliseconds |
