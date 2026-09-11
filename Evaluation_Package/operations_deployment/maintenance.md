# LeadFlow AI — Operator Maintenance Guide

This guide explains how to safely maintain and modify LeadFlow AI operational configuration without breaking the system.

---

## Business Rules Configuration

### What: Modify ICP scoring weights, tier thresholds, routing rules

**Where:** `day2/data/business_rules.json`

**How to Modify:**

```json
{
  "icp_tiers": {
    "tier_1": {
      "min_score": 80,
      "max_score": 100,
      "characteristics": "Enterprise: 500+ employees, strong product-market fit"
    },
    "tier_2": {
      "min_score": 60,
      "max_score": 79,
      "characteristics": "Mid-market: 100-500 employees"
    }
  },
  "firmographic_scoring": {
    "company_size": {
      "1000+": 40,
      "100-1000": 20,
      "10-100": 10,
      "1-10": 0
    }
  }
}
```

**Risks:**
- Changing tier thresholds may alter lead routing unexpectedly
- Lowering thresholds may increase false positives
- Scoring changes are not retroactive to already-processed leads
- Must test after changes

**Tests to Run:**
```bash
# Run benchmark to verify scoring still matches expectations
python day3/benchmark/run_12_case_benchmark.py

# Run full test suite
pytest day2/backend/tests/test_pipeline.py -k "scoring or tier" -v

# Manually verify 2-3 test cases
```

---

## Competitor Domain List

### What: Add/remove competitor domains for automatic quarantine

**Where:** `day2/data/business_rules.json` → `competitor_domains`

**How to Modify:**

```json
"competitor_domains": [
  "competitor-a.com",
  "competitor-b.io",
  "new-competitor.com"  # Add here
]
```

**Risks:**
- Removed competitors will no longer be quarantined
- Typos may inadvertently quarantine wrong companies
- Case-sensitive matching — use lowercase
- Changes apply immediately to new leads

**Tests to Run:**
```bash
# Run security tests
pytest day2/backend/tests/test_pipeline.py -k "quarantine" -v

# Manual test: Submit a lead from added competitor domain
# Expected: Immediate quarantine, tier=QUARANTINED, no draft
```

---

## Claim Validator Rules

### What: Add/modify forbidden claim patterns

**Where:** `day2/backend/app/services/claim_validator.py`

**Patterns Currently Blocked:**
- Discount/pricing commitments
- SLA guarantees (uptime %)
- Compliance certification promises
- Custom promises not in whitelist

**How to Add New Pattern:**

```python
def _check_commercial_claims(self, draft: str) -> ClaimValidationResult:
    # ... existing code ...
    
    # Add new pattern
    forbidden_patterns = [
        # Existing patterns...
        (r"guarantee\s+(?:free|no-charge)", "Guarantee of free service without limit"),
    ]
    
    # ... rest of code ...
```

**Risks:**
- Overly broad patterns will block legitimate claims
- Regex errors will cause crashes
- Patterns are case-insensitive but may miss variants
- Changes require code restart

**Tests to Run:**
```bash
# Run claim validation tests
pytest day2/backend/tests/test_pipeline.py::test_claim_validator_blocks_multiple_patterns -v

# Manual test: Submit draft with new forbidden phrase
# Expected: BLOCKED status with clear error message
```

---

## Synthetic Enrichment Database

### What: Modify synthetic company data used for enrichment

**Where:** `day2/data/synthetic_companies.json`

**How to Modify:**

```json
{
  "domain": "acme-corp.com",
  "company_name": "ACME Corporation",
  "size": "1000-5000",           # Change size tier
  "industry": "Manufacturing",   # Change industry
  "founding_year": 1995,         # Change founding year
  "location": "USA"              # Add new fields
}
```

**Risks:**
- Changes affect scoring for matching domains
- No historical changes — affects all retroactive queries
- Incorrect data degrades ICP accuracy
- Test case expectations may fail with changed data

**Tests to Run:**
```bash
# Run benchmark to verify scoring unchanged for test cases
python day3/benchmark/run_12_case_benchmark.py

# Check specific test case (TC-01 through TC-12)
# Verify tier and score still match expected values
```

---

## Benchmark Test Cases

### What: Modify Day 1 baseline test cases for evaluation

**Where:** `day1/test_cases.json`

**Structure:**
```json
{
  "test_id": "TC-01",
  "email": "john@enterprise-corp.com",
  "expected_tier": "Tier 1",
  "expected_score_range": [80, 100],
  "expected_route": "DISPATCH_APPROVED"
}
```

**Risks:**
- Changes to test cases alter assessment baseline
- May invalidate historical evaluation results
- Should only modify with RevOps approval
- Breaking changes make results non-comparable

**Tests to Run:**
```bash
# After modification, run full benchmark
python day3/benchmark/run_12_case_benchmark.py

# Verify tier_match, score_match, route_match all PASS
# Review results in day3/benchmark/day3_execution_results.csv
```

---

## External Integration Settings

### What: Configure DNS timeout, website timeout, external API endpoints

**Where:** `day2/.env` file

**Current Settings:**
```
DNS_TIMEOUT_SECONDS=5.0
WEBSITE_TIMEOUT_SECONDS=5.0
WEBSITE_MAX_REDIRECTS=3
```

**How to Modify:**

```bash
# Example: Adjust DNS timeout only if operational requirements change
DNS_TIMEOUT_SECONDS=5.0

# Example: Adjust website timeout only if operational requirements change
WEBSITE_TIMEOUT_SECONDS=5.0
```

**Important:** Changing timeouts affects system behavior significantly. After modifying:
- Restart the application
- Run the benchmark suite to verify system behavior
- Test with several leads to confirm latencies are acceptable
- Revert if performance degrades

**Risks:**
- Increasing timeout delays SDR workflow
- Decreasing timeout may cause false failures
- Changes apply immediately on application restart
- Audit trail will show different latencies

---

## LLM Configuration

### What: Change LLM provider, model, or API key

**Where:** `day2/.env` file

**Current Setting:**
```
GEMINI_API_KEY=<your-key-here>
```

**How to Modify:**

```bash
# Add your Gemini API key
GEMINI_API_KEY=your_actual_key_here

# Or remove for deterministic fallback only
GEMINI_API_KEY=
```

**Risks:**
- Invalid key causes LLM outages (system falls back to deterministic template)
- Rate limits may apply with high volume
- Different LLM may produce different draft quality
- Model changes affect draft tone/format

**Tests to Run:**
```bash
# Test LLM connectivity
python -c "from day2.backend.app.services.llm_draft import generate_llm_draft; print('LLM connection OK')"

# Submit 3 test leads and verify drafts
# Check audit trail for FALLBACK_ACTIVATED events
# Verify draft quality is acceptable
```

---

## Version Control & Backups

### Backup Before Changes

```powershell
# Create backup of current state
Copy-Item -Recurse day2/data day2/data.backup.$(Get-Date -Format 'yyyy-MM-dd')

# Verify backup
ls day2/data.backup.*/
```

### Restore After Issues

```powershell
# Stop application (Ctrl+C)

# Restore from backup
Copy-Item day2/data day2/data.old
Copy-Item day2/data.backup.yyyy-mm-dd/* day2/data -Recurse -Force

# Restart
python day2/backend/app/main.py
```

---

## Safety Checklist

Before deploying any operational change:

- [ ] Backup current configuration
- [ ] Understand what will change
- [ ] Review impact on scoring/routing
- [ ] Run affected test suite
- [ ] Verify benchmark results unchanged (if expected)
- [ ] Test with 1-2 sample leads
- [ ] Monitor audit trail for errors
- [ ] Have rollback plan ready

---

## Change Log

Track all operational changes:

```
Date: 2026-09-15
Change: Increased WEBSITE_TIMEOUT_SECONDS from 5.0 to 8.0
Reason: Website checks timing out for slow regional sites
Impact: Added 3s to average processing time
Tests: Passed benchmark with 8s timeout, no tier/score changes
```

---

## Contact & Escalation

For questions about operational changes:
- Review architecture documentation: `day2/docs/architecture.md`
- Check data contracts: `day2/docs/data-contracts.md`
- Review business rules documentation: `day2/docs/business_rules.json`
- Escalate to engineering for code changes
