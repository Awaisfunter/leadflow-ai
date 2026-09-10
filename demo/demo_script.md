# LeadFlow AI - 5-Minute Demo Script

## Demo Overview
**Total Time:** 5 minutes  
**Audience:** Applied AI Engineer Assessment Evaluators  
**Objective:** Show complete lead qualification workflow with failure handling

## Pre-Demo Setup Checklist
- [ ] Application running at `http://localhost:8000`
- [ ] Browser open to LeadFlow AI dashboard  
- [ ] Terminal visible for any error messages
- [ ] No personal file paths or credentials visible
- [ ] System responsive to clicks

## Demo Flow

### 0:00-0:30 | Problem Introduction
**Script:**
> "LeadFlow AI solves a recurring bottleneck for B2B sales teams: qualifying inbound leads. Our baseline measurement showed SDRs spending 16 minutes and 45 seconds per lead across 7 browser tabs - checking domains, researching companies, calculating fit scores, and drafting personalized outreach. This creates response delays that hurt conversion rates."

**Show:** Dashboard overview, clean interface

### 0:30-1:00 | Architecture Overview  
**Script:**
> "The system uses hybrid architecture - deterministic business logic for scoring and routing, bounded AI for draft generation, with mandatory human approval. External integrations verify domains via DNS-over-HTTPS and extract website metadata. Everything flows through Pydantic schemas for type safety and logs to an audit database for complete traceability."

**Show:** Brief architecture diagram or workflow explanation

### 1:00-2:00 | Process Enterprise Lead
**Action:** Select "TC-01: Enterprise Buyer" from dropdown, click "Process Inbound Lead"

**Script:**
> "Let's process Sarah Chen from Acme Corporation, a VP of Sales Operations at an 850-person enterprise software company. Watch as the system verifies her domain, extracts website metadata, enriches with company data, and calculates ICP scoring."

**Point out during processing:**
- Domain verification in progress
- Website metadata extraction  
- Company enrichment from synthetic dataset
- Real-time status updates

### 2:00-2:45 | Review Results
**Show and explain:**

**DNS Verification:** "Domain verified through Cloudflare DNS-over-HTTPS"

**Website Check:** "Retrieved company website title and metadata"  

**Enrichment:** "Found Acme in our synthetic dataset - 850 employees, enterprise software, funded, using Salesforce and AWS"

**ICP Score:** "Perfect 100/100 score: 40 points firmographic, 25 role, 20 intent, 15 urgency, zero penalties"

**Tier:** "Tier 1 classification routes to Enterprise Account Executive"

**Draft:** "AI generated personalized email referencing their Salesforce integration need"

### 2:45-3:30 | Security and Validation
**Script:**
> "Notice the claim validation passed - the system checks that generated emails don't promise unauthorized discounts, compliance certifications, or SLA guarantees. The approval state shows 'PREVIEW_ONLY' and 'Dispatch Locked' - nothing can reach the CRM without human review."

**Show:**
- Claim validation results
- Pre-approval state: `dispatch_authorized = False`
- CRM status: `PREVIEW_ONLY`
- Human approval required

### 3:30-4:15 | Human Approval Workflow
**Action:** Click "✓ Approve & Dispatch"

**Script:**
> "Human approval triggers the state machine transition. Watch the instant change from PREVIEW_ONLY to APPROVED_FOR_DISPATCH. The system generates a structured CRM payload ready for integration, logs the approval decision with timestamp and reviewer identity to the audit database."

**Show:**
- Status change to `APPROVED`
- `dispatch_authorized` changes to `True`  
- CRM status changes to `APPROVED_FOR_DISPATCH`
- CRM payload structure
- Audit trail confirmation

### 4:15-4:45 | Failure Demonstration
**Action:** Select "TC-02: Normal Mid-Market Lead" or manually trigger website timeout

**Script:**
> "Now let's see controlled failure handling. This lead will demonstrate website timeout - our 5-second bounded timeout prevents UI hangs. Notice the system continues processing with graceful degradation, shows clear timeout messaging, and maintains the approval workflow even when external integrations fail."

**Show:**
- Website timeout error message
- Bounded latency (should be ~5 seconds)
- Processing continues despite failure
- Clear error messaging
- NEEDS_VERIFICATION flag
- Lead still processable

### 4:45-5:00 | Results and Limitations
**Script:**
> "Results: 99.8% processing time reduction from 16 minutes to 2.3 seconds average in the assessment benchmark, 56/56 automated tests passing, 12/12 benchmark cases with perfect accuracy, 10/10 deliberate failure tests with bounded degradation. 

> Limitations: Uses synthetic enrichment dataset, no live CRM dispatch, network-dependent external verification, and always requires human approval. This is assessment-ready v0, not production deployment.

> The system demonstrates that we didn't just build an AI demo - we built and evaluated a governed operational AI system with real integrations, comprehensive testing, and honest limitation acknowledgment."

**Show:** 
- Final dashboard state
- Evidence of testing and evaluation
- Clear scope acknowledgment

## Demo Recovery Procedures

### If Application Crashes
1. Stay calm, acknowledge the issue
2. Check terminal for error message
3. Restart if possible: `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload`
4. Explain this demonstrates the importance of error handling in production

### If External Integration Fails  
1. Point out this is a real failure scenario
2. Show how system handles it gracefully
3. Explain this is why we built fallback mechanisms
4. Continue with the workflow to show resilience

### If Network Issues Occur
1. Acknowledge network dependency
2. Explain this is a known limitation
3. Show cached/fallback behavior if available
4. Discuss production architecture considerations

## Key Messages to Emphasize

### Technical Excellence
- Real external integrations, not mocked
- Comprehensive testing (56 automated, 12 benchmark, 10 failure tests)
- Security by design with human approval gates
- Complete audit logging for governance

### Engineering Judgment
- Honest limitation acknowledgment
- Appropriate scope for 5-day assessment
- Focus on evaluation evidence over feature quantity
- Clear distinction between v0 and production-ready

### Operational Readiness
- Complete documentation for handoff
- Reproducible setup and execution
- Real failure scenarios tested and handled
- User-friendly interface for non-developers

## Post-Demo Questions to Anticipate

**Q: How would this work in production?**
A: The architecture supports production scaling - we'd need CRM integrations, production database, authentication, monitoring. The evaluation v0 proves the core workflow and generates realistic payloads.

**Q: What about data privacy?**
A: Current version uses synthetic data only. Production would need PII handling, data retention policies, and compliance frameworks. The audit trail supports regulatory requirements.

**Q: How accurate is the AI generation?**
A: We measure claim safety (9/9 generated drafts pass policy validation) and provide deterministic fallbacks. Production would need human feedback loops and continuous quality monitoring.

**Q: What's the total cost of ownership?**
A: Current evaluation uses free/public APIs. Production costs include LLM provider fees, external data APIs, infrastructure, and operational support. The 99.8% time reduction in the assessment benchmark provides clear ROI framework.

**Q: How would you handle more complex business rules?**
A: The business rules JSON is configurable, scoring engine is modular, and claim validation patterns are updatable. More complex logic would extend the deterministic scoring components, not replace them with AI.

---

**Demo Version:** Day 5 Final  
**Rehearsal Required:** Yes - practice timing and transitions  
**Backup Plan:** Have screenshots available if live demo fails  
**Success Metric:** Demonstrates working system, security, and engineering maturity in 5 minutes