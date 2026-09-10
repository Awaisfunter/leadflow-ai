"""
LeadFlow AI — Pydantic v2 Data Contracts
All schemas used across the end-to-end pipeline.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class IcpTier(str, Enum):
    TIER_1 = "Tier 1"
    TIER_2 = "Tier 2"
    TIER_3 = "Tier 3"
    DISQUALIFIED = "Disqualified"
    QUARANTINED = "Quarantined"

class RiskFlag(str, Enum):
    COMPETITOR_RISK = "COMPETITOR_RISK"
    PROMPT_INJECTION = "PROMPT_INJECTION_DETECTED"
    FREE_MAIL_DOMAIN = "FREE_MAIL_DOMAIN"
    ACADEMIC_DOMAIN = "ACADEMIC_DOMAIN"
    SPARSE_INPUT = "SPARSE_INPUT_WARNING"
    ENRICHMENT_UNAVAILABLE = "ENRICHMENT_UNAVAILABLE"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"

class ApprovalStatus(str, Enum):
    DRAFTED = "DRAFTED"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    EDITED = "EDITED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"

class NextAction(str, Enum):
    ROUTE_ENTERPRISE_AE = "ROUTE_ENTERPRISE_AE"
    ROUTE_COMMERCIAL_AE = "ROUTE_COMMERCIAL_AE"
    ROUTE_EXPRESS_ONBOARDING = "ROUTE_EXPRESS_ONBOARDING"
    ROUTE_SELF_SERVE = "ROUTE_SELF_SERVE"
    ROUTE_EMEA_ENTERPRISE = "ROUTE_EMEA_ENTERPRISE"
    ROUTE_MIGRATION_SPECIALIST = "ROUTE_MIGRATION_SPECIALIST"   # TC-04: competitive migration
    ROUTE_ENTERPRISE_DISCOVERY = "ROUTE_ENTERPRISE_DISCOVERY"   # TC-06: sparse enterprise input
    REQUIRE_CORPORATE_EMAIL = "REQUIRE_CORPORATE_EMAIL"
    QUARANTINE_COMPETITOR = "QUARANTINE_COMPETITOR"
    QUARANTINE_INJECTION = "QUARANTINE_INJECTION"
    QUARANTINE_ACADEMIC = "QUARANTINE_ACADEMIC"
    NEEDS_MANUAL_REVIEW = "NEEDS_MANUAL_REVIEW"
    VALIDATION_ERROR = "VALIDATION_ERROR"

class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    COMPETITOR_FLAGGED = "COMPETITOR_FLAGGED"
    ACADEMIC_DOMAIN = "ACADEMIC_DOMAIN"
    FLAGGED_INJECTION_RISK = "FLAGGED_INJECTION_RISK"
    NOT_FOUND = "NOT_FOUND"
    UNVERIFIED = "UNVERIFIED"

class EventType(str, Enum):
    LEAD_RECEIVED = "LEAD_RECEIVED"
    VALIDATION_PASSED = "VALIDATION_PASSED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    RISK_DETECTED = "RISK_DETECTED"
    DOMAIN_CHECK_COMPLETED = "DOMAIN_CHECK_COMPLETED"
    WEBSITE_CHECK_COMPLETED = "WEBSITE_CHECK_COMPLETED"
    ENRICHMENT_COMPLETED = "ENRICHMENT_COMPLETED"
    ENRICHMENT_FAILED = "ENRICHMENT_FAILED"
    ICP_SCORED = "ICP_SCORED"
    DRAFT_GENERATED = "DRAFT_GENERATED"
    DRAFT_FALLBACK = "DRAFT_FALLBACK"
    CLAIM_VALIDATED = "CLAIM_VALIDATED"
    CLAIM_BLOCKED = "CLAIM_BLOCKED"
    APPROVAL_STATE_CHANGED = "APPROVAL_STATE_CHANGED"
    CRM_PAYLOAD_GENERATED = "CRM_PAYLOAD_GENERATED"
    PIPELINE_ERROR = "PIPELINE_ERROR"
    # Day 4 Hardening & Reliability Event Types
    INTEGRATION_FAILED = "INTEGRATION_FAILED"
    RETRY_ATTEMPTED = "RETRY_ATTEMPTED"
    FALLBACK_ACTIVATED = "FALLBACK_ACTIVATED"
    VALIDATION_BLOCKED = "VALIDATION_BLOCKED"
    APPROVAL_BLOCKED = "APPROVAL_BLOCKED"
    QUARANTINE_APPLIED = "QUARANTINE_APPLIED"
    HARDENING_REGRESSION_PASSED = "HARDENING_REGRESSION_PASSED"


# ─────────────────────────────────────────────────────────────────────────────
# 1. LeadInput — raw inbound form payload (UNTRUSTED)
# ─────────────────────────────────────────────────────────────────────────────

class LeadInput(BaseModel):
    """Raw inbound lead from web form. Treat ALL fields as untrusted customer input."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    company: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., min_length=1, max_length=200)
    team_size: str = Field(..., min_length=1, max_length=50,
                           description="Self-reported team size range, e.g. '500-1000'")
    notes: Optional[str] = Field(default="", max_length=2000,
                                  description="Free-text notes — untrusted customer content")

    @field_validator("notes", mode="before")
    @classmethod
    def sanitize_notes_whitespace(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip()

    def input_hash(self) -> str:
        """SHA-256 fingerprint of the raw payload for audit logging."""
        raw = f"{self.first_name}{self.last_name}{self.email}{self.company}{self.notes}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ─────────────────────────────────────────────────────────────────────────────
# 2. LeadIdentity — parsed domain + identity signals
# ─────────────────────────────────────────────────────────────────────────────

class LeadIdentity(BaseModel):
    lead_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    domain: str
    is_corporate_domain: bool
    is_disposable_webmail: bool
    is_competitor_domain: bool
    is_academic_domain: bool
    inferred_company_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────────────────
# 3a. DomainVerificationResult — real DNS-over-HTTPS check result (Day 3)
# ─────────────────────────────────────────────────────────────────────────────

class DomainVerificationResult(BaseModel):
    """
    Result of a real DNS-over-HTTPS lookup against Cloudflare public resolver.
    source is always 'public_dns' — never synthetic.
    """
    domain: str
    valid_syntax: bool
    dns_resolves: bool
    ip_addresses: list[str] = Field(default_factory=list)
    record_type: str = Field(default="A")
    status: str  # VERIFIED | UNRESOLVED | INVALID_SYNTAX | ERROR
    source: str = Field(default="public_dns")
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: Optional[int] = None


# ─────────────────────────────────────────────────────────────────────────────
# 3b. WebsiteMetadataResult — real public HTTP metadata check (Day 3)
# ─────────────────────────────────────────────────────────────────────────────

class WebsiteMetadataResult(BaseModel):
    """
    Result of a real HTTP HEAD/GET request to the company's public website.
    Only safe, bounded metadata is extracted. Page content is UNTRUSTED and discarded.
    source is always 'public_website' — never synthetic.
    """
    url: str
    reachable: bool
    status_code: Optional[int] = None
    https: bool = False
    final_url: Optional[str] = None
    title: Optional[str] = None
    response_time_ms: Optional[int] = None
    content_type: Optional[str] = None
    source: str = Field(default="public_website")
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────────────────
# 3. EnrichedAccount — verified company data from synthetic enrichment
# ─────────────────────────────────────────────────────────────────────────────

class EnrichedAccount(BaseModel):
    """
    Company data from the synthetic enrichment adapter.
    source MUST always identify the data origin (never claim 'LinkedIn' or 'Crunchbase').
    """
    domain: str
    company_name: str
    employee_count: int = Field(ge=0)
    employee_range: str
    industry: str
    funding_stage: str
    headquarters: str
    technology_signals: list[str] = Field(default_factory=list)
    verification_status: VerificationStatus
    source: str = Field(description="Always 'synthetic_internal_dataset' for v0.")
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    enrichment_available: bool = True
    notes: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# 4. LeadRiskFlags — pre-flight and post-enrichment risk signals
# ─────────────────────────────────────────────────────────────────────────────

class LeadRiskFlags(BaseModel):
    flags: list[RiskFlag] = Field(default_factory=list)
    prompt_injection_detected: bool = False
    injection_signatures_found: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    requires_quarantine: bool = False
    confidence_note: Optional[str] = None

    def add_flag(self, flag: RiskFlag) -> None:
        if flag not in self.flags:
            self.flags.append(flag)


# ─────────────────────────────────────────────────────────────────────────────
# 5. QualificationResult — deterministic ICP scoring output
# ─────────────────────────────────────────────────────────────────────────────

class ScoringBreakdown(BaseModel):
    firmographic_points: int = Field(ge=0, le=40)
    role_points: int = Field(ge=0, le=25)
    intent_points: int = Field(ge=0, le=20)
    urgency_points: int = Field(ge=0, le=15)
    risk_penalty: int = Field(le=0)
    raw_score: int
    final_score: int = Field(ge=0, le=100)

class QualificationResult(BaseModel):
    tier: IcpTier
    scoring_breakdown: ScoringBreakdown
    reasoning: list[str] = Field(description="Human-readable explanation of each scoring decision")
    next_action: NextAction
    sla_hours: Optional[int] = None
    scored_by: str = Field(default="deterministic_icp_engine_v1",
                           description="Always a deterministic engine, never an LLM.")
    scored_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────────────────
# 6. DraftContext — bounded context passed to LLM (no raw system data)
# ─────────────────────────────────────────────────────────────────────────────

class DraftContext(BaseModel):
    """
    Strictly bounded context given to the LLM.
    Only verified facts and approved value propositions are included.
    Raw lead notes are included as UNTRUSTED CUSTOMER CONTENT with explicit labelling.
    """
    lead_first_name: str
    lead_role: str
    company_name: str
    industry: str
    employee_range: str
    funding_stage: str
    icp_tier: str
    key_pain_points: list[str] = Field(description="Extracted from notes by the system, not fabricated.")
    approved_value_propositions: list[str]
    untrusted_customer_notes: str = Field(
        description="Raw customer notes — the LLM must treat this as untrusted content only."
    )
    language_hint: str = Field(default="en", description="ISO 639-1 language code detected from notes.")
    prohibited_claims: list[str] = Field(
        default_factory=lambda: [
            "Do not invent pricing or discounts.",
            "Do not promise custom SLA not listed in approved propositions.",
            "Do not invent certifications (e.g. ISO 27001, SOC 2 Type II).",
            "Do not invent customer logos or references.",
            "Do not promise implementation timelines not agreed.",
            "Do not make contractual commitments.",
            "Only use facts from the verified company context above.",
        ]
    )


# ─────────────────────────────────────────────────────────────────────────────
# 7. EmailDraft — structured LLM or fallback template output
# ─────────────────────────────────────────────────────────────────────────────

class EmailDraft(BaseModel):
    subject: str = Field(min_length=5, max_length=200)
    body: str = Field(min_length=50, max_length=3000)
    generated_by: str = Field(description="'gemini-1.5-flash', 'deterministic_fallback', etc.")
    is_fallback: bool = Field(default=False)
    language: str = Field(default="en")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────────────────
# 8. ClaimValidationResult — deterministic post-generation validation
# ─────────────────────────────────────────────────────────────────────────────

class ClaimValidationResult(BaseModel):
    passed: bool
    warnings: list[str] = Field(default_factory=list)
    blocked_claims: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    validator_version: str = "claim_validator_v1"


# ─────────────────────────────────────────────────────────────────────────────
# 9. ApprovalState — human-in-the-loop gate record
# ─────────────────────────────────────────────────────────────────────────────

class ApprovalStateRecord(BaseModel):
    lead_id: str
    status: ApprovalStatus = ApprovalStatus.PENDING_REVIEW
    reviewer_id: Optional[str] = None
    previous_status: Optional[ApprovalStatus] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None
    edited_body: Optional[str] = Field(default=None,
                                        description="If reviewer edited the draft before approval.")


# ─────────────────────────────────────────────────────────────────────────────
# 10. CRMDispatchPayload — validated CRM-ready JSON (no live CRM in v0)
# ─────────────────────────────────────────────────────────────────────────────

class CRMAccount(BaseModel):
    name: str
    domain: str
    industry: str
    employee_count: int
    employee_range: str
    funding_stage: str
    headquarters: str
    technology_signals: list[str]

class CRMContact(BaseModel):
    first_name: str
    last_name: str
    email: str
    role: str
    lead_source: str = "inbound_web_form"

class CRMQualification(BaseModel):
    icp_tier: str
    final_score: int
    scoring_breakdown: dict[str, Any]
    reasoning: list[str]
    next_action: str
    sla_hours: Optional[int]
    risk_flags: list[str]

class CRMOutreach(BaseModel):
    subject: str
    body: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    generated_by: str

class CRMMetadata(BaseModel):
    lead_id: str
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    system_version: str = "leadflow-ai-v0-day3"
    data_source: str = "synthetic_internal_dataset"
    crm_status: str = "PREVIEW_ONLY"
    dispatch_authorized: bool = False
    disclaimer: str = (
        "Synthetic CRM-ready payload preview — no live CRM connection in v0. "
        "Dispatch authorization withheld pending human SDR approval."
    )

class CRMDispatchPayload(BaseModel):
    account: CRMAccount
    contact: CRMContact
    qualification: CRMQualification
    outreach: CRMOutreach
    metadata: CRMMetadata


# ─────────────────────────────────────────────────────────────────────────────
# 11. AuditEvent — append-only audit trail entry
# ─────────────────────────────────────────────────────────────────────────────

class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    component: str
    status: str
    input_hash: Optional[str] = None
    output_summary: Optional[str] = None
    risk_flags: list[str] = Field(default_factory=list)
    approval_state: Optional[str] = None
    error: Optional[str] = None
    latency_ms: Optional[int] = None


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline Response — full pipeline result returned by the API
# ─────────────────────────────────────────────────────────────────────────────

class PipelineResponse(BaseModel):
    lead_id: str
    identity: LeadIdentity
    enrichment: Optional[EnrichedAccount]
    domain_verification: Optional[DomainVerificationResult] = None
    website_metadata: Optional[WebsiteMetadataResult] = None
    risk_flags: LeadRiskFlags
    qualification: Optional[QualificationResult]
    draft: Optional[EmailDraft]
    claim_validation: Optional[ClaimValidationResult]
    approval_state: ApprovalStateRecord
    crm_payload: Optional[CRMDispatchPayload] = None
    pipeline_status: str
    processing_time_ms: int
    audit_events: list[str] = Field(description="List of event_ids logged.")
