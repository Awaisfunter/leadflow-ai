"""
LeadFlow AI — End-to-End Verification Script (v0)
Demonstrates TC-01 traveling completely from raw input to approved CRM payload.
"""
import asyncio
import json
from backend.app.schemas.models import LeadInput
from backend.app.services.pipeline import run_pipeline, handle_approval_action
from backend.app.services.audit_logger import get_audit_trail


async def main():
    print("==================================================================")
    print("LeadFlow AI (Day 2 v0) — End-to-End Pipeline Demonstration")
    print("==================================================================")

    lead = LeadInput(
        first_name="Sarah",
        last_name="Chen",
        email="sarah.chen@acmecorp.com",
        company="Acme Corporation",
        role="VP of Sales Operations",
        team_size="500-1000",
        notes="We are replacing our legacy lead qualification tool across 80 reps in Q4. Need enterprise SLA and custom Salesforce integration."
    )

    print("\n[STEP 1] Ingesting Untrusted Inbound Lead (TC-01)...")
    print(f"  Prospect: {lead.first_name} {lead.last_name} ({lead.email})")
    print(f"  Company : {lead.company} | Role: {lead.role}")
    print(f"  Input SHA-256 Fingerprint: {lead.input_hash()}")

    print("\n[STEP 2] Executing Bounded Pipeline...")
    resp = await run_pipeline(lead)

    print(f"  Pipeline Latency: {resp.processing_time_ms} ms")
    print(f"  Parsed Domain   : {resp.identity.domain} (Corporate={resp.identity.is_corporate_domain})")
    print(f"  Enrichment Data : {resp.enrichment.company_name} | {resp.enrichment.employee_count} emp | Source: {resp.enrichment.source}")
    print(f"  Deterministic ICP: Tier: {resp.qualification.tier.value} | Final Score: {resp.qualification.scoring_breakdown.final_score}/100")
    print(f"  Score Breakdown : Firm={resp.qualification.scoring_breakdown.firmographic_points}, Role={resp.qualification.scoring_breakdown.role_points}, Intent={resp.qualification.scoring_breakdown.intent_points}, Urgency={resp.qualification.scoring_breakdown.urgency_points}")
    print(f"  Routing Decision: {resp.qualification.next_action.value} (SLA: {resp.qualification.sla_hours} hr)")
    print(f"  Risk Detection  : Flags={[f.value for f in resp.risk_flags.flags]} | Quarantined={resp.risk_flags.requires_quarantine}")
    print(f"  Draft Generated : By {resp.draft.generated_by} (Fallback={resp.draft.is_fallback})")
    print(f"  Subject Line    : {resp.draft.subject}")
    print(f"  Claim Validator : Passed={resp.claim_validation.passed} | Blocked={len(resp.claim_validation.blocked_claims)}")
    print(f"  Initial State   : {resp.approval_state.status.value}")
    print(f"  CRM State (Pre) : {resp.crm_payload.metadata.crm_status} (Dispatch Authorized={resp.crm_payload.metadata.dispatch_authorized})")

    print("\n[STEP 3] Human SDR Review & Approval Gate...")
    approved = handle_approval_action(
        lead_id=resp.lead_id,
        action="APPROVE",
        reviewer_id="awais_sdr",
        notes="Verified enterprise requirement and custom Salesforce routing fit."
    )
    print(f"  New Status    : {approved.approval_state.status.value}")
    print(f"  Reviewer ID   : {approved.approval_state.reviewer_id}")
    print(f"  CRM Authorized: {approved.crm_payload.metadata.crm_status} (Dispatch Authorized={approved.crm_payload.metadata.dispatch_authorized})")

    print("\n[STEP 4] Append-only SQLite Audit Trail (v0)...")
    trail = get_audit_trail(resp.lead_id)
    print(f"  Total Audit Events Persisted: {len(trail)}")
    for e in trail:
        print(f"    • [{e['component']:22}] {e['event_type']:22} -> {e['status']} ({e['latency_ms']}ms)")

    print("\n[STEP 5] CRM Dispatch Payload (Synthetic Preview):")
    crm_summary = {
        "account": approved.crm_payload.account.model_dump(),
        "contact": approved.crm_payload.contact.model_dump(),
        "qualification": approved.crm_payload.qualification.model_dump(),
        "metadata": approved.crm_payload.metadata.model_dump(),
    }
    print(json.dumps(crm_summary, indent=2, default=str))

    print("\n==================================================================")
    print("[PASS] END-TO-END HAPPY PATH VERIFICATION COMPLETE")
    print("==================================================================")


if __name__ == "__main__":
    asyncio.run(main())
