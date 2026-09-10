"""
LeadFlow AI — Pipeline Orchestrator (v0)

Coordinates end-to-end execution of a single inbound lead:
Input -> Pre-flight Risk -> Enrichment -> ICP Scoring -> Bounded Context
      -> AI Draft -> Claim Validation -> Human Approval State -> CRM Preview -> Audit Log
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from ..config import get_settings
from ..schemas.models import (
    ApprovalStateRecord,
    ApprovalStatus,
    AuditEvent,
    CRMAccount,
    CRMContact,
    CRMDispatchPayload,
    CRMMetadata,
    CRMOutreach,
    CRMQualification,
    ClaimValidationResult,
    DomainVerificationResult,
    DraftContext,
    EmailDraft,
    EnrichedAccount,
    EventType,
    IcpTier,
    LeadIdentity,
    LeadInput,
    LeadRiskFlags,
    PipelineResponse,
    QualificationResult,
    RiskFlag,
    VerificationStatus,
    WebsiteMetadataResult,
)
from ..tools.enrichment import lookup_company, make_unavailable_enrichment
from ..tools.domain_verification import verify_domain
from ..tools.website_metadata import fetch_website_metadata
from .audit_logger import log_audit_event
from .claim_validator import validate_draft
from .icp_scorer import score_lead
from .llm_draft import generate_draft
from .risk_detector import detect_risks, extract_domain, is_corporate_domain

logger = logging.getLogger(__name__)

# In-memory session store for v0 active pipelines (in addition to SQLite audit log)
_PIPELINE_STORE: dict[str, PipelineResponse] = {}


def build_crm_payload(
    identity: LeadIdentity,
    lead_input: LeadInput,
    enrichment: Optional[EnrichedAccount],
    qualification: QualificationResult,
    draft: EmailDraft,
    approval: ApprovalStateRecord,
) -> CRMDispatchPayload:
    """Builds and validates the CRM-ready JSON payload using Pydantic contracts."""
    company_name = (
        enrichment.company_name
        if enrichment and enrichment.enrichment_available
        else lead_input.company
    )
    domain = identity.domain
    industry = enrichment.industry if enrichment and enrichment.enrichment_available else "Unknown"
    employee_count = (
        enrichment.employee_count if enrichment and enrichment.enrichment_available else 0
    )
    employee_range = (
        enrichment.employee_range if enrichment and enrichment.enrichment_available else lead_input.team_size
    )
    funding_stage = (
        enrichment.funding_stage if enrichment and enrichment.enrichment_available else "Unknown"
    )
    headquarters = (
        enrichment.headquarters if enrichment and enrichment.enrichment_available else "Unknown"
    )
    tech_signals = (
        enrichment.technology_signals if enrichment and enrichment.enrichment_available else []
    )

    account = CRMAccount(
        name=company_name,
        domain=domain,
        industry=industry,
        employee_count=employee_count,
        employee_range=employee_range,
        funding_stage=funding_stage,
        headquarters=headquarters,
        technology_signals=tech_signals,
    )

    contact = CRMContact(
        first_name=lead_input.first_name,
        last_name=lead_input.last_name,
        email=str(lead_input.email),
        role=lead_input.role,
        lead_source="inbound_web_form",
    )

    qual = CRMQualification(
        icp_tier=qualification.tier.value,
        final_score=qualification.scoring_breakdown.final_score,
        scoring_breakdown=qualification.scoring_breakdown.model_dump(),
        reasoning=qualification.reasoning,
        next_action=qualification.next_action.value,
        sla_hours=qualification.sla_hours,
        risk_flags=[],
    )

    # Use edited body if the reviewer made modifications
    is_approved = (approval.status == ApprovalStatus.APPROVED)
    outreach_body = approval.edited_body if approval.edited_body else draft.body
    outreach = CRMOutreach(
        subject=draft.subject,
        body=outreach_body,
        approved_by=approval.reviewer_id if is_approved else None,
        approved_at=approval.updated_at if is_approved else None,
        generated_by=draft.generated_by,
    )

    meta = CRMMetadata(
        lead_id=identity.lead_id,
        processed_at=datetime.now(timezone.utc),
        system_version="leadflow-ai-v0-day3",
        data_source=(
            enrichment.source if enrichment else "synthetic_internal_dataset"
        ),
        crm_status="APPROVED_FOR_DISPATCH" if is_approved else "PREVIEW_ONLY",
        dispatch_authorized=is_approved,
        disclaimer=(
            "Synthetic CRM dispatch authorized by human SDR — no live CRM connection in v0."
            if is_approved else
            "Synthetic CRM-ready payload preview — no live CRM connection in v0. "
            "Dispatch authorization withheld pending human SDR approval."
        ),
    )

    return CRMDispatchPayload(
        account=account,
        contact=contact,
        qualification=qual,
        outreach=outreach,
        metadata=meta,
    )


async def run_pipeline(lead_input: LeadInput) -> PipelineResponse:
    """
    Executes the complete LeadFlow AI v0 pipeline on a single raw inbound lead.
    """
    start_time = time.time()
    input_hash = lead_input.input_hash()
    logged_event_ids: list[str] = []

    def _audit(
        component: str,
        event_type: EventType,
        status: str,
        lead_id: str,
        summary: Optional[str] = None,
        risk_flags: Optional[list[str]] = None,
        approval_state: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        ms = int((time.time() - start_time) * 1000)
        event = AuditEvent(
            lead_id=lead_id,
            event_type=event_type,
            component=component,
            status=status,
            input_hash=input_hash,
            output_summary=summary,
            risk_flags=risk_flags or [],
            approval_state=approval_state,
            error=error,
            latency_ms=ms,
        )
        log_audit_event(event)
        logged_event_ids.append(event.event_id)

    # Step 1: Identity Extraction & Domain Classification
    domain = extract_domain(str(lead_input.email))
    settings = get_settings()
    data_dir = settings.data_dir

    identity = LeadIdentity(
        email=str(lead_input.email),
        domain=domain,
        is_corporate_domain=is_corporate_domain(domain, data_dir),
        is_disposable_webmail=not is_corporate_domain(domain, data_dir),
        is_competitor_domain=False,
        is_academic_domain=domain.endswith(".edu") or ".edu" in domain,
        inferred_company_name=lead_input.company,
    )
    _audit(
        component="IdentityParser",
        event_type=EventType.VALIDATION_PASSED,
        status="SUCCESS",
        lead_id=identity.lead_id,
        summary=f"Parsed domain={domain}, corporate={identity.is_corporate_domain}",
    )

    # Step 2: Pre-flight Deterministic Risk Detection
    risk_flags = detect_risks(lead_input, data_dir)
    if risk_flags.flags:
        _audit(
            component="RiskDetector",
            event_type=EventType.RISK_DETECTED,
            status="FLAGGED",
            lead_id=identity.lead_id,
            summary=f"Flags: {[f.value for f in risk_flags.flags]}",
            risk_flags=[f.value for f in risk_flags.flags],
        )
    else:
        _audit(
            component="RiskDetector",
            event_type=EventType.RISK_DETECTED,
            status="CLEAN",
            lead_id=identity.lead_id,
            summary="Zero risk signatures detected.",
        )

    # Step 3: Real Domain Verification (DNS-over-HTTPS via Cloudflare public resolver)
    domain_verification: Optional[DomainVerificationResult] = None
    try:
        domain_verification = await verify_domain(
            domain, timeout=settings.dns_timeout_seconds
        )
        _audit(
            component="DomainVerification",
            event_type=EventType.DOMAIN_CHECK_COMPLETED,
            status=domain_verification.status,
            lead_id=identity.lead_id,
            summary=(
                f"DNS={domain_verification.status}, "
                f"resolves={domain_verification.dns_resolves}, "
                f"latency={domain_verification.latency_ms}ms, "
                f"source={domain_verification.source}"
            ),
        )
        if not domain_verification.dns_resolves:
            risk_flags.add_flag(RiskFlag.NEEDS_VERIFICATION)
            _audit(
                component="DomainVerification",
                event_type=EventType.INTEGRATION_FAILED,
                status=domain_verification.status,
                lead_id=identity.lead_id,
                summary=f"DNS resolution failed: {domain_verification.error_code} — {domain_verification.error_message}",
                error=domain_verification.error_code,
            )
    except Exception as exc:
        logger.error("DomainVerification step failed unexpectedly: %s", exc)
        domain_verification = DomainVerificationResult(
            domain=domain,
            valid_syntax=True,
            dns_resolves=False,
            status="ERROR",
            error_code="DNS_PIPELINE_ERROR",
            error_message="Domain check could not be completed due to an internal error.",
        )
        _audit(
            component="DomainVerification",
            event_type=EventType.INTEGRATION_FAILED,
            status="ERROR",
            lead_id=identity.lead_id,
            summary="Domain verification failed unexpectedly with internal error",
            error="DNS_PIPELINE_ERROR",
        )

    # Step 4: Real Website Metadata (HTTP public fetch)
    website_metadata: Optional[WebsiteMetadataResult] = None
    try:
        website_metadata = await fetch_website_metadata(
            domain,
            timeout=settings.website_timeout_seconds,
            max_redirects=settings.website_max_redirects,
        )
        _audit(
            component="WebsiteMetadata",
            event_type=EventType.WEBSITE_CHECK_COMPLETED,
            status="REACHABLE" if website_metadata.reachable else "UNREACHABLE",
            lead_id=identity.lead_id,
            summary=(
                f"reachable={website_metadata.reachable}, "
                f"status_code={website_metadata.status_code}, "
                f"https={website_metadata.https}, "
                f"title={website_metadata.title!r}, "
                f"source={website_metadata.source}"
            ),
        )
        if not website_metadata.reachable:
            _audit(
                component="WebsiteMetadata",
                event_type=EventType.INTEGRATION_FAILED,
                status="UNREACHABLE",
                lead_id=identity.lead_id,
                summary=f"Website fetch failed: {website_metadata.error_code} — {website_metadata.error_message}",
                error=website_metadata.error_code,
            )
    except Exception as exc:
        logger.error("WebsiteMetadata step failed unexpectedly: %s", exc)
        website_metadata = WebsiteMetadataResult(
            url=f"https://{domain}",
            reachable=False,
            error_code="WEBSITE_PIPELINE_ERROR",
            error_message="Website metadata check could not be completed.",
        )
        _audit(
            component="WebsiteMetadata",
            event_type=EventType.INTEGRATION_FAILED,
            status="ERROR",
            lead_id=identity.lead_id,
            summary="Website metadata check failed unexpectedly with internal error",
            error="WEBSITE_PIPELINE_ERROR",
        )

    # Step 5: Account Enrichment (Controlled Synthetic Lookup)
    enrichment = lookup_company(domain, lead_input.company, data_dir)
    if enrichment is None:
        enrichment = make_unavailable_enrichment(domain, lead_input.company)
        risk_flags.add_flag(RiskFlag.ENRICHMENT_UNAVAILABLE)
        _audit(
            component="SyntheticEnrichment",
            event_type=EventType.ENRICHMENT_FAILED,
            status="NOT_FOUND",
            lead_id=identity.lead_id,
            summary=f"No record for {domain} in synthetic dataset. Flagged ENRICHMENT_UNAVAILABLE.",
        )
        _audit(
            component="SyntheticEnrichment",
            event_type=EventType.FALLBACK_ACTIVATED,
            status="NOT_FOUND",
            lead_id=identity.lead_id,
            summary="Fallback to user-provided form parameters; synthetic account enrichment unavailable.",
        )
    else:
        # Cross-reference competitor / injection flags from verification status
        if enrichment.verification_status == VerificationStatus.COMPETITOR_FLAGGED:
            risk_flags.add_flag(RiskFlag.COMPETITOR_RISK)
        _audit(
            component="SyntheticEnrichment",
            event_type=EventType.ENRICHMENT_COMPLETED,
            status="SUCCESS",
            lead_id=identity.lead_id,
            summary=f"Enriched: {enrichment.company_name}, {enrichment.employee_count} emp, {enrichment.industry}",
        )

    # Step 4: Deterministic ICP Scoring Engine
    qualification = score_lead(lead_input, enrichment, risk_flags)
    _audit(
        component="DeterministicICPScorer",
        event_type=EventType.ICP_SCORED,
        status="SUCCESS",
        lead_id=identity.lead_id,
        summary=f"Tier={qualification.tier.value}, Score={qualification.scoring_breakdown.final_score}/100",
    )

    # Step 5: Bounded Context Assembly & First-Touch Draft
    # Prohibit generative outreach if quarantined
    draft: Optional[EmailDraft] = None
    claim_validation: Optional[ClaimValidationResult] = None

    if qualification.tier in (IcpTier.QUARANTINED, IcpTier.DISQUALIFIED) and (
        RiskFlag.PROMPT_INJECTION in risk_flags.flags or RiskFlag.COMPETITOR_RISK in risk_flags.flags
    ):
        # Quarantine branch — no sales outreach generated
        draft = EmailDraft(
            subject="[QUARANTINED] Inbound submission flagged for security review",
            body=(
                "AUTOMATED SECURITY NOTICE: This lead submission has been quarantined due to "
                f"risk flags ({[f.value for f in risk_flags.flags]}). Automated sales outreach is suppressed. "
                "Manual review by Security / RevOps is required."
            ),
            generated_by="security_quarantine_guardrail",
            is_fallback=True,
            language="en",
            generated_at=datetime.now(timezone.utc),
        )
        claim_validation = ClaimValidationResult(
            passed=True,
            warnings=["Submission quarantined. Generative drafting disabled."],
            blocked_claims=[],
            requires_human_review=True,
        )
    else:
        # Bounded context assembly
        approved_props = [
            "Deterministic lead qualification and routing in under 1 minute.",
            "Native Salesforce and CRM integration support.",
            "Enterprise-grade SLA and governance controls.",
        ]
        pain_points = []
        if lead_input.notes:
            if "replace" in lead_input.notes.lower() or "legacy" in lead_input.notes.lower():
                pain_points.append("Replacing legacy qualification tooling")
            if "sla" in lead_input.notes.lower():
                pain_points.append("Enterprise SLA requirements")
            if "salesforce" in lead_input.notes.lower():
                pain_points.append("Salesforce CRM integration")

        draft_context = DraftContext(
            lead_first_name=lead_input.first_name,
            lead_role=lead_input.role,
            company_name=enrichment.company_name if enrichment else lead_input.company,
            industry=enrichment.industry if enrichment else "Technology",
            employee_range=enrichment.employee_range if enrichment else lead_input.team_size,
            funding_stage=enrichment.funding_stage if enrichment else "Unknown",
            icp_tier=qualification.tier.value,
            key_pain_points=pain_points,
            approved_value_propositions=approved_props,
            untrusted_customer_notes=lead_input.notes or "",
            language_hint="en",
        )

        draft = await generate_draft(draft_context)
        _audit(
            component="LLMDraftGenerator",
            event_type=EventType.DRAFT_GENERATED if not draft.is_fallback else EventType.DRAFT_FALLBACK,
            status="SUCCESS",
            lead_id=identity.lead_id,
            summary=f"Draft by {draft.generated_by} (fallback={draft.is_fallback})",
        )
        if draft.is_fallback:
            _audit(
                component="LLMDraftGenerator",
                event_type=EventType.FALLBACK_ACTIVATED,
                status="FALLBACK_ENGAGED",
                lead_id=identity.lead_id,
                summary=f"LLM draft generation fallback template engaged ({draft.generated_by}).",
            )

        # Step 6: Deterministic Claim Validator
        claim_validation = validate_draft(draft.subject, draft.body, data_dir)
        _audit(
            component="ClaimValidator",
            event_type=EventType.CLAIM_VALIDATED if claim_validation.passed else EventType.CLAIM_BLOCKED,
            status="PASSED" if claim_validation.passed else "BLOCKED",
            lead_id=identity.lead_id,
            summary=f"Passed={claim_validation.passed}, Blocked={len(claim_validation.blocked_claims)}, Warnings={len(claim_validation.warnings)}",
        )

    # Step 7: Human Approval Gate State Initialization
    if risk_flags.requires_quarantine or qualification.tier == IcpTier.QUARANTINED:
        initial_approval = ApprovalStatus.QUARANTINED
    else:
        initial_approval = ApprovalStatus.PENDING_REVIEW

    approval_record = ApprovalStateRecord(
        lead_id=identity.lead_id,
        status=initial_approval,
        reviewer_id=None,
        previous_status=None,
        notes="Awaiting SDR review in LeadFlow AI dashboard.",
    )
    _audit(
        component="HumanApprovalGate",
        event_type=EventType.APPROVAL_STATE_CHANGED,
        status="PENDING",
        lead_id=identity.lead_id,
        approval_state=initial_approval.value,
        summary=f"Initial state: {initial_approval.value}",
    )

    # Step 8: CRM Payload Preview (Draft status, not yet dispatched)
    crm_payload = build_crm_payload(
        identity=identity,
        lead_input=lead_input,
        enrichment=enrichment,
        qualification=qualification,
        draft=draft,
        approval=approval_record,
    )
    _audit(
        component="CRMDispatcher",
        event_type=EventType.CRM_PAYLOAD_GENERATED,
        status="PREVIEW_READY",
        lead_id=identity.lead_id,
        summary="Synthetic CRM payload generated. Live dispatch withheld pending human approval.",
    )

    total_ms = int((time.time() - start_time) * 1000)

    response = PipelineResponse(
        lead_id=identity.lead_id,
        identity=identity,
        enrichment=enrichment,
        domain_verification=domain_verification,
        website_metadata=website_metadata,
        risk_flags=risk_flags,
        qualification=qualification,
        draft=draft,
        claim_validation=claim_validation,
        approval_state=approval_record,
        crm_payload=crm_payload,
        pipeline_status="PENDING_APPROVAL" if initial_approval != ApprovalStatus.QUARANTINED else "QUARANTINED",
        processing_time_ms=total_ms,
        audit_events=logged_event_ids,
    )

    # Cache in session store
    _PIPELINE_STORE[identity.lead_id] = response
    return response


def handle_approval_action(
    lead_id: str,
    action: str,  # "APPROVE", "REJECT", "QUARANTINE", "EDIT"
    reviewer_id: str = "demo_user",
    notes: Optional[str] = None,
    edited_body: Optional[str] = None,
) -> PipelineResponse:
    """
    Applies an SDR's human decision to a pending lead.
    Enforces the human-in-the-loop gate before CRM dispatch authorization.
    """
    if lead_id not in _PIPELINE_STORE:
        raise KeyError(f"Lead ID {lead_id} not found in active session store.")

    current = _PIPELINE_STORE[lead_id]
    prev_status = current.approval_state.status

    action_map = {
        "APPROVE": ApprovalStatus.APPROVED,
        "REJECT": ApprovalStatus.REJECTED,
        "QUARANTINE": ApprovalStatus.QUARANTINED,
        "EDIT": ApprovalStatus.EDITED,
    }

    new_status = action_map.get(action.upper())
    if not new_status:
        raise ValueError(f"Invalid approval action '{action}'. Must be one of: {list(action_map.keys())}")

    # Determine final body and subject for outreach
    final_body = edited_body if edited_body is not None else (
        current.approval_state.edited_body if current.approval_state.edited_body else (
            current.draft.body if current.draft else ""
        )
    )
    final_subject = current.draft.subject if current.draft else ""

    # Security Invariant 1: Quarantined leads cannot be approved directly
    if prev_status == ApprovalStatus.QUARANTINED and new_status == ApprovalStatus.APPROVED:
        log_audit_event(
            AuditEvent(
                lead_id=lead_id,
                event_type=EventType.APPROVAL_BLOCKED,
                component="HumanApprovalGate",
                status="BLOCKED",
                approval_state=prev_status.value,
                output_summary=f"Security Violation: Prohibited approval attempt on QUARANTINED lead by {reviewer_id}",
                error="Quarantined lead approval requires security clearance",
            )
        )
        raise ValueError(
            "Security Violation: Cannot directly approve a QUARANTINED lead. "
            "Security / RevOps clearance is required."
        )

    # Security Invariant 2: Rejected leads cannot be approved without reset
    if prev_status == ApprovalStatus.REJECTED and new_status == ApprovalStatus.APPROVED:
        log_audit_event(
            AuditEvent(
                lead_id=lead_id,
                event_type=EventType.APPROVAL_BLOCKED,
                component="HumanApprovalGate",
                status="BLOCKED",
                approval_state=prev_status.value,
                output_summary=f"Prohibited approval attempt on REJECTED lead by {reviewer_id}",
                error="Rejected lead cannot be approved without reset",
            )
        )
        raise ValueError("Cannot approve a previously REJECTED lead.")

    # Security Invariant 3: Re-validate FINAL text upon approval
    if new_status == ApprovalStatus.APPROVED:
        revalidation = validate_draft(final_subject, final_body)
        if not revalidation.passed:
            blocked_str = "; ".join(revalidation.blocked_claims)
            log_audit_event(
                AuditEvent(
                    lead_id=lead_id,
                    event_type=EventType.VALIDATION_BLOCKED,
                    component="ClaimValidator",
                    status="BLOCKED",
                    approval_state=prev_status.value,
                    output_summary=f"Commercial policy violation detected in outreach: {blocked_str}",
                    risk_flags=revalidation.blocked_claims,
                    error="Blocked commercial claims detected in final draft",
                )
            )
            log_audit_event(
                AuditEvent(
                    lead_id=lead_id,
                    event_type=EventType.APPROVAL_BLOCKED,
                    component="HumanApprovalGate",
                    status="BLOCKED",
                    approval_state=prev_status.value,
                    output_summary=f"Approval blocked due to claim validation failure by {reviewer_id}: {blocked_str}",
                    error="Approval rejected due to commercial commitment policy violation",
                )
            )
            raise ValueError(
                f"Cannot approve draft: Claim validator detected blocked commercial commitments in final text: {blocked_str}"
            )
        current.claim_validation = revalidation

    # If editing, re-validate the updated draft text
    if new_status == ApprovalStatus.EDITED:
        current.claim_validation = validate_draft(final_subject, final_body)

    # Update approval state
    current.approval_state = ApprovalStateRecord(
        lead_id=lead_id,
        status=new_status,
        reviewer_id=reviewer_id,
        previous_status=prev_status,
        updated_at=datetime.now(timezone.utc),
        notes=notes or f"Action {action} performed by {reviewer_id}",
        edited_body=edited_body,
    )

    # Update CRM payload to reflect final approval state
    if current.crm_payload and current.draft:
        is_appr = (new_status == ApprovalStatus.APPROVED)
        current.crm_payload.outreach.body = final_body
        current.crm_payload.outreach.approved_by = reviewer_id if is_appr else None
        current.crm_payload.outreach.approved_at = current.approval_state.updated_at if is_appr else None
        current.crm_payload.metadata.crm_status = "APPROVED_FOR_DISPATCH" if is_appr else f"STATUS_{new_status.value}"
        current.crm_payload.metadata.dispatch_authorized = is_appr
        current.crm_payload.metadata.disclaimer = (
            "Synthetic CRM dispatch authorized by human SDR — no live CRM connection in v0."
            if is_appr else
            f"Synthetic CRM-ready payload ({new_status.value}) — dispatch not authorized."
        )

    # Log audit event
    log_audit_event(
        AuditEvent(
            lead_id=lead_id,
            event_type=EventType.APPROVAL_STATE_CHANGED,
            component="HumanApprovalGate",
            status="UPDATED",
            approval_state=new_status.value,
            output_summary=f"Reviewer={reviewer_id}, Prev={prev_status.value}, New={new_status.value}",
        )
    )

    current.pipeline_status = new_status.value
    _PIPELINE_STORE[lead_id] = current
    return current


def get_pipeline_result(lead_id: str) -> Optional[PipelineResponse]:
    """Retrieve pipeline result from session cache."""
    return _PIPELINE_STORE.get(lead_id)
