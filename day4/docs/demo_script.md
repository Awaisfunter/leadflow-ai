# LeadFlow AI Demo Script
**Target Audience**: Evaluators, stakeholders, technical reviewers  
**Duration**: 4-5 minutes  
**Environment**: Local development, browser-based demo  

---

## Demo Narrative: From Problem to Solution

### 1. Problem Setup (30 seconds)
**Script**: "In B2B sales, inbound leads require manual research across 7 browser tabs, taking SDRs 16+ minutes per lead. This creates response delays that hurt conversions - speed-to-lead is critical for qualification rates."

**Visual**: Show day1/baseline_measurements.csv - highlight 16m45s manual time, 7 browser tabs

---

### 2. Solution Overview (30 seconds)
**Script**: "LeadFlow AI automates the qualification pipeline using real DNS verification, website checks, deterministic ICP scoring, and bounded AI drafting - all with mandatory human approval before CRM dispatch."

**Visual**: Architecture diagram showing: Raw Input → Verification → Enrichment → Scoring → Drafting → Human Approval → CRM

---

### 3. Live System Demo (3 minutes)

#### 3a. Happy Path - Enterprise Lead (60 seconds)
1. **Open browser to localhost:8000**
2. **Click "TC-01: Enterprise Buyer" preset**
3. **Click "Process Inbound Lead"**
4. **Script**: "Watch the real-time pipeline: DNS resolution, website verification, ICP scoring to 100/100, Tier 1 classification, and personalized draft generation"
5. **Highlight**: External verification (DNS resolved, HTTPS confirmed), deterministic score breakdown, human approval gate
6. **Click "Approve & Dispatch"**
7. **Script**: "Notice the transition from PREVIEW_ONLY to APPROVED_FOR_DISPATCH - no automation can bypass human approval"

#### 3b. Security Demo - Prompt Injection (45 seconds)
1. **Click "TC-10: Prompt Injection" preset**
2. **Process the lead**
3. **Script**: "This lead contains 'ignore previous instructions' and tries to get a discount. Watch our security: immediate quarantine, zero score, no draft generated, dispatch permanently blocked."
4. **Highlight**: Red quarantine badge, score forced to 0, no approval option available

#### 3c. Failure Resilience - DNS Timeout (30 seconds)
1. **Navigate to break tests or mention FC-02**
2. **Script**: "When external services fail, the system degrades gracefully. DNS timeouts don't crash the pipeline - they're logged and the lead continues with available data."
3. **Show**: Bounded 5-second timeout, graceful fallback messaging

---

### 4. Quality Evidence (45 seconds)
**Script**: "Let me show you the evaluation rigor:"

1. **Open day3/benchmark/day3_execution_results.csv**
   - **Highlight**: 12/12 benchmark cases passing
   - **Script**: "Every expected tier, score, and route matches exactly"

2. **Show pytest results or mention 56/56 tests passing**
   - **Script**: "56 automated tests cover validation, security, approval gates, and audit trails"

3. **Show day4/evidence/break_test_execution.txt**  
   - **Script**: "10/10 deliberate failure tests pass with controlled degradation"

---

### 5. Business Value Connection (30 seconds)
**Script**: "Results: Manual 16m45s → LeadFlow AI under 1 minute. 12/12 benchmark accuracy. Zero pre-approval dispatch leakage. Complete audit trail. Ready for non-developer SDR handoff."

**Visual**: Show before/after metrics from day4/regression/before_after_summary.csv

---

## Key Demo Talking Points

### Technical Strengths to Highlight:
- **Real external integrations**: Live DNS and website verification, not mocked
- **Deterministic scoring**: Business rules, not black-box ML
- **Security by design**: Prompt injection detection, competitor quarantine
- **Human governance**: Mandatory approval, no automation bypass
- **Failure resilience**: Bounded timeouts, graceful degradation
- **Complete auditability**: Every decision logged to SQLite

### Business Value to Emphasize:
- **Speed**: 16m45s → <1m processing time
- **Consistency**: Eliminates rep bias in qualification
- **Security**: Blocks adversarial leads automatically  
- **Governance**: Human approval prevents unauthorized commitments
- **Reliability**: Works offline with deterministic fallbacks

### What NOT to Claim:
- ❌ Production deployment ready
- ❌ Revenue impact without evidence  
- ❌ Universal reliability across all networks
- ❌ Cost savings (marked NOT_MEASURED)
- ❌ Live CRM integration (v0 generates payloads only)

## Demo Environment Requirements
- Windows laptop with Python 3.11+
- Browser (Chrome/Edge recommended)
- Local server running on localhost:8000
- Internet connection for DNS/website demos
- Pre-loaded with day1 test cases

## Backup Scenarios
If network issues prevent live DNS demo:
1. Show cached results from day3_execution_results.csv
2. Focus on deterministic scoring and approval gates
3. Emphasize offline fallback capabilities
4. Demonstrate with TC-07 (shows DNS_UNRESOLVED handling)