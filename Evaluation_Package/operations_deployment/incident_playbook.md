# LeadFlow AI — Incident Response Playbook

This guide provides step-by-step procedures for responding to operational incidents.

---

## Incident 1: LLM Outage

**Symptoms:**
- "No candidate models returned 200" in logs
- Draft generation takes >10 seconds then times out
- All leads show fallback template without attempts at LLM generation

**Root Cause Detection:**
1. Check logs: `tail -50 day2/logs/leadflow.log | grep -i llm`
2. Verify API key: `echo $GEMINI_API_KEY`
3. Test connectivity: `curl https://generativelanguage.googleapis.com/` (if VPN required)
4. Check API status page: https://status.cloud.google.com

**Response Steps:**

| Priority | Action | Timeline |
|----------|--------|----------|
| **Immediate** | Notify SDR team that system is in fallback mode | < 1 min |
| **Immediate** | Continue processing leads with deterministic template | < 1 min |
| **5 min** | Verify API key is valid and non-expired | < 5 min |
| **5 min** | Check LLM provider status page for outages | < 5 min |
| **15 min** | If API key issue: update `.env` with new key, restart | < 15 min |
| **30 min** | If provider outage: monitor status page, update team | Ongoing |

**Verification:**
```bash
# After fix, check logs
tail -f day2/logs/leadflow.log

# Process a test lead
# Expected: Draft generated with attempted LLM content (not just template)
# Verify in audit trail: No FALLBACK_ACTIVATED event
```

**Escalation:**
- If unresolved > 1 hour: Contact LLM provider support
- Switch to alternative LLM provider if available

---

## Incident 2: DNS Resolution Outage

**Symptoms:**
- All leads show "DNS Status: UNRESOLVED"
- Logs show "DNS query timed out" repeatedly
- Network connectivity otherwise normal

**Root Cause Detection:**
1. Test system DNS: `nslookup google.com`
2. Test alternate DNS: `nslookup google.com 8.8.8.8`
3. Check network connectivity: `ping 8.8.8.8`
4. Verify DNS configuration: `ipconfig /all` (check DNS servers)

**Response Steps:**

| Priority | Action | Timeline |
|----------|--------|----------|
| **Immediate** | Notify SDR team that enrichment is unavailable | < 1 min |
| **Immediate** | Continue processing leads with synthetic data only | < 1 min |
| **5 min** | Test manual DNS query: `nslookup <domain>` | < 5 min |
| **10 min** | Check network connectivity and DNS server | < 10 min |
| **15 min** | If DNS server down: switch to alternate (8.8.8.8 or 1.1.1.1) | < 15 min |
| **30 min** | If ISP issue: contact network team | Ongoing |

**Verification:**
```bash
# After DNS restored
# Process a test lead with publicly resolvable domain
# Expected: "DNS Status: RESOLVED" with latency in logs
```

**Escalation:**
- If network team cannot resolve: escalate to ISP
- May need to configure alternate DNS servers in system

---

## Incident 3: Website Verification Service Outage

**Symptoms:**
- "Website: Unreachable" for all company domains (including reachable sites)
- Website timeout errors in logs even for fast-loading sites
- All leads stuck on website verification step

**Root Cause Detection:**
1. Manual test: Open websites in browser (should load normally)
2. Check logs for pattern: `tail -50 day2/logs/leadflow.log | grep -i website`
3. Test connectivity to a known site: `curl -I https://google.com`
4. Check firewall rules: May be blocking outbound HTTPS

**Response Steps:**

| Priority | Action | Timeline |
|----------|--------|----------|
| **Immediate** | Notify SDR team that website verification is unavailable | < 1 min |
| **Immediate** | Continue processing with fallback to synthetic data | < 1 min |
| **5 min** | Verify websites are publicly accessible (manual browser test) | < 5 min |
| **10 min** | Check outbound network connectivity and firewall | < 10 min |
| **15 min** | If firewall blocking: Request IT to allow HTTPS to public sites | < 15 min |
| **30 min** | If persistent: Investigate HTTP client configuration | Ongoing |

**Verification:**
```bash
# After network restored
# Process a test lead with publicly accessible website
# Expected: "Website: Reachable" with latency 100-3400ms
# Verify title extracted correctly
```

**Escalation:**
- If firewall blocks: Escalate to IT/Security team
- May need to request exceptions for specific domains

---

## Incident 4: Enrichment Data Corruption

**Symptoms:**
- Incorrect company information appearing in enrichment
- ICP scores unexpectedly low or high for known companies
- Historical leads now showing different enrichment values

**Root Cause Detection:**
1. Check enrichment database: `day2/data/synthetic_companies.json`
2. Verify file integrity: Compare with backup if available
3. Check file size: Should be ~50-200 KB (not corrupted)
4. Review recent changes: Check if maintenance was performed

**Response Steps:**

| Priority | Action | Timeline |
|----------|--------|----------|
| **Immediate** | Notify RevOps of data issue | < 1 min |
| **5 min** | Stop accepting new leads until resolved | < 5 min |
| **10 min** | Check if backup exists: `ls day2/data.backup.*/` | < 10 min |
| **15 min** | If backup available: Restore from backup | < 15 min |
| **30 min** | If no backup: Manually verify/correct top 20 company records | < 30 min |
| **60 min** | Review what changes caused corruption | Ongoing |

**Verification:**
```bash
# After restore
# Run benchmark to verify data correctness
python day3/benchmark/run_12_case_benchmark.py

# Expected: All 12 cases show correct tier/score matches
# Verify in day3/benchmark/day3_execution_results.csv
```

**Escalation:**
- If corruption widespread: May need data reconstruction
- Review change logs to understand what happened

---

## Incident 5: Approval Gate Security Alert

**Symptoms:**
- Quarantined lead was approved (should be impossible)
- Draft with blocked claims was approved
- audit_events show "SECURITY_BYPASS_DETECTED"

**Root Cause Detection:**
1. Check audit trail for specific lead
2. Review state transitions in database query
3. Check API logs for unusual requests
4. Verify approval credentials

**Response Steps:**

| Priority | Action | Timeline |
|----------|--------|----------|
| **CRITICAL** | Immediately stop any CRM dispatch for affected leads | < 1 min |
| **CRITICAL** | Notify compliance officer of security event | < 1 min |
| **5 min** | Collect evidence: Lead ID, audit trail, API logs | < 5 min |
| **15 min** | Review approval credentials and access logs | < 15 min |
| **30 min** | Determine if system bug or user error | < 30 min |
| **60 min** | If system bug: Deploy fix and revert affected leads | Ongoing |

**Verification:**
```bash
# After fix deployed
# Run security regression tests
pytest day2/backend/tests/test_pipeline.py -k "approval" -v

# Expected: All approval gate tests pass
# Verify no bypass vulnerabilities exist
```

**Escalation:**
- Notify compliance and security teams immediately
- Document incident in security log
- May require external audit of approval mechanism

---

## Incident 6: Prompt Injection Attack

**Symptoms:**
- Lead company name contains injected commands ("ignore previous instructions")
- System generates draft with unauthorized claims
- Quarantine did not trigger as expected

**Root Cause Detection:**
1. Review lead submission data
2. Check claim validator logs
3. Verify quarantine signatures in `business_rules.json`
4. Review draft generation audit events

**Response Steps:**

| Priority | Action | Timeline |
|----------|--------|----------|
| **CRITICAL** | Block approval of suspected lead immediately | < 1 min |
| **Immediate** | Notify security team of attack attempt | < 5 min |
| **5 min** | Verify quarantine fired correctly | < 5 min |
| **15 min** | Review all recent leads for similar patterns | < 15 min |
| **30 min** | Update quarantine signatures if patterns missed | < 30 min |
| **60 min** | Verify fix with security regression tests | Ongoing |

**Verification:**
```bash
# Run prompt injection tests
pytest day2/backend/tests/test_pipeline.py::test_prompt_injection_detection -v

# Run full security tests
pytest day2/backend/tests/test_pipeline.py -k "security or quarantine" -v

# Expected: All pass, no drafts generated from injection attempts
```

**Escalation:**
- Log attack in security incident log
- Review and update quarantine rules if needed
- May require investigation into attack vector

---

## Incident 7: Unexpected System Error

**Symptoms:**
- Internal Server Error (500) on lead submission
- No useful error message in UI
- Logs show Python stack trace

**Root Cause Detection:**
1. Check error logs: `tail -100 day2/logs/leadflow.log`
2. Identify error type: KeyError, TypeError, etc.
3. Identify affected operation: scoring, enrichment, draft, etc.
4. Check if recent changes were deployed

**Response Steps:**

| Priority | Action | Timeline |
|----------|--------|----------|
| **Immediate** | Pause lead processing if systematic | < 1 min |
| **5 min** | Collect full error logs and stack trace | < 5 min |
| **10 min** | Identify affected leads (count) | < 10 min |
| **15 min** | Attempt root cause analysis from logs | < 15 min |
| **30 min** | If fixable: Deploy fix or revert recent changes | < 30 min |
| **60 min** | Verify system stable, reprocess affected leads | Ongoing |

**Verification:**
```bash
# After fix
# Reprocess affected leads
# Run full test suite
pytest day2/backend/tests/test_pipeline.py -v

# Expected: All tests pass, affected leads now process successfully
```

**Escalation:**
- If unfixable in <1 hour: Escalate to engineering
- May require rollback to previous deployment

---

## Incident 8: Database Corruption

**Symptoms:**
- Cannot read audit trail
- Error: "database disk image malformed"
- Logs stop being written

**Root Cause Detection:**
1. Check database file: `ls -lh day2/logs/audit.db`
2. Try to query: `sqlite3 day2/logs/audit.db "SELECT COUNT(*) FROM events;"`
3. Check disk space: `df -h`
4. Check file permissions: `ls -l day2/logs/`

**Response Steps:**

| Priority | Action | Timeline |
|----------|--------|----------|
| **Immediate** | Stop application to prevent further corruption | < 1 min |
| **5 min** | Backup corrupted database: `cp day2/logs/audit.db day2/logs/audit.db.corrupt` | < 5 min |
| **10 min** | Delete corrupted database: `rm day2/logs/audit.db` | < 10 min |
| **15 min** | Restart application (creates new database) | < 15 min |
| **30 min** | Verify new database working | < 30 min |

**Verification:**
```bash
# After restart
# Process a test lead
# Verify audit trail written correctly
sqlite3 day2/logs/audit.db "SELECT COUNT(*) FROM events;"

# Expected: 1 lead creates ~10-15 audit events
```

**Escalation:**
- If disk space issue: Free up space, investigate what consumed it
- If permission issue: Correct file permissions

---

## General Incident Response Process

1. **DETECT** — Identify the problem
2. **ALERT** — Notify affected teams immediately
3. **CONTAIN** — Prevent escalation or data loss
4. **DIAGNOSE** — Determine root cause
5. **RESOLVE** — Fix the issue
6. **VERIFY** — Confirm fix works
7. **DOCUMENT** — Record what happened and why

---

## Escalation Contacts

| Type | Contact | Timeframe |
|------|---------|-----------|
| Security Issue | Security Team | Immediate |
| Data Issue | RevOps Manager | < 5 min |
| System Error | Engineering Lead | < 15 min |
| Network Issue | IT/Network Team | < 15 min |
| LLM Provider | Provider Support | < 30 min |
| Critical Outage | Executive Sponsor | Immediate |

---

## Post-Incident Review

After resolving any incident:

1. Document what happened
2. Timeline of detection → resolution
3. Root cause
4. What worked well
5. What could be improved
6. Prevention measures
7. Monitoring improvements

Store all post-incident reviews in `operations/incidents/` directory.
