# LeadFlow AI — Troubleshooting Guide

This guide helps diagnose and resolve common issues when operating LeadFlow AI.

## Application Startup Issues

### Symptom: Application does not start or port already in use

**Cause:** 
- Another process is listening on port 8000
- Python dependencies are not installed
- Environment variables are misconfigured

**Action:**
1. Check if port 8000 is in use: `netstat -ano | findstr :8000`
2. Kill the process if needed: `taskkill /PID <PID> /F`
3. Verify dependencies: `pip list | grep fastapi`
4. Reinstall if needed: `pip install -r requirements.txt`
5. Start the application: `python day2/backend/app/main.py`

---

## Dependency Issues

### Symptom: Import errors or missing modules

**Cause:**
- Requirements not installed in current environment
- Incompatible Python version
- Virtual environment not activated

**Action:**
1. Verify Python version: `python --version` (should be 3.10+)
2. Reinstall all dependencies: `pip install -r day2/requirements.txt --force-reinstall`
3. Verify installation: `pip show fastapi pydantic httpx`
4. Clear cache: `pip cache purge`
5. Retry application startup

---

## DNS Resolution Failure

### Symptom: "DNS Status: UNRESOLVED" appears for valid domains

**Cause:**
- Network connectivity issue
- DNS server unreachable
- Domain doesn't exist or is not publicly resolvable

**Action:**
1. Test system DNS: `nslookup google.com` (should return IP)
2. Check network connection: `ping 8.8.8.8`
3. Verify domain spelling in lead form
4. If domain is internal/private, it cannot be resolved publicly
5. System will fall back to synthetic enrichment data automatically

---

## Website Timeout

### Symptom: "Website: Unreachable" message when company website should be accessible

**Cause:**
- Website not responding within 5.0-second timeout
- Server is down or experiencing issues
- Network connectivity problem
- Website blocks automated requests

**Action:**
1. Verify website is accessible: Open in browser manually
2. Check website status: Use uptime monitoring service
3. Test connectivity: `ping <company-domain>`
4. Website timeout is intentional for SDR responsiveness
5. System automatically falls back to internal enrichment data
6. No action needed — this is expected behavior

---

## LLM Unavailable / Fallback Activated

### Symptom: "No candidate models returned" or fallback template used

**Cause:**
- LLM API key missing or invalid (GEMINI_API_KEY)
- LLM provider is unavailable
- Rate limit or quota exceeded
- Network connectivity to LLM provider

**Action:**
1. Check if LLM key is configured: `echo $GEMINI_API_KEY`
2. Verify key is valid in Gemini console
3. Check network connectivity to API
4. System is designed to work without LLM — fallback is normal
5. Generated draft will use deterministic template
6. No action required for basic operation

---

## Enrichment Data Missing

### Symptom: "Enrichment: no match found for domain" in logs

**Cause:**
- Company domain not in synthetic enrichment database
- Domain format is unusual or internal

**Action:**
1. Review synthetic data: `day2/data/synthetic_companies.json`
2. Add new company if needed (development only):
   ```json
   {
     "domain": "new-domain.com",
     "company_name": "New Company",
     "size": "1000-5000",
     "industry": "Technology",
     "founding_year": 2015
   }
   ```
3. Restart application after changes
4. System continues processing — enrichment is optional

---

## Claim Blocked Before Approval

### Symptom: "Claim Check: BLOCKED ⚠" message in UI

**Cause:**
- Generated draft contains unapproved claims:
  - Discount percentages ("50% off")
  - SLA guarantees ("99.99% uptime")
  - Compliance certification ("HIPAA certified")
  - Custom commitments

**Action:**
1. Click **✎ Edit Draft** in the UI
2. Remove the prohibited phrase
3. Resubmit the draft
4. Claim validator runs automatically
5. If still blocked, review policy rules in `day2/data/business_rules.json`

---

## Quarantine

### Symptom: "Tier: QUARANTINED" with red warning badge

**Cause:**
- Competitor domain detected (TC-09, TC-10, TC-11)
- Prompt injection signature detected (TC-10)
- Academic/research domain (TC-11)
- Direct approval attempt on quarantined lead

**Action:**
1. **DO NOT APPROVE** — this is a security protection
2. Review the quarantine reason in the interface
3. Contact RevOps if false positive suspected
4. Review security events in audit trail
5. System logs quarantine decision with full context

---

## Approval State Issues

### Symptom: Cannot approve lead or approval option not available

**Cause:**
- Lead is in QUARANTINED state (no approval possible)
- Draft contains blocked claims
- Edited draft contains invalid claims
- Pre-approval state not yet reached

**Action:**
1. Check current lead status in interface
2. If QUARANTINED: Contact RevOps (security decision)
3. If BLOCKED: Edit and remove prohibited claims
4. If PREVIEW_ONLY: Ensure draft passes all validations
5. Click **Approve** when interface enables it
6. After approval, status changes to APPROVED_FOR_DISPATCH

---

## Audit Issues

### Symptom: Audit trail incomplete or events missing

**Cause:**
- SQLite database not initialized
- Logging configuration disabled
- Disk space full
- Database file corrupted

**Action:**
1. Check audit database exists: `ls day2/logs/audit.db`
2. Verify permissions: File should be readable/writable
3. Restart application (recreates database if needed)
4. Check logs: `tail -f day2/logs/leadflow.log`
5. If corrupted, delete and restart (application recreates)

---

## Port Conflict

### Symptom: "Address already in use" error on startup

**Cause:**
- Another application using port 8000
- Previous instance of LeadFlow not fully stopped

**Action:**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F

# Restart application
python day2/backend/app/main.py
```

---

## Performance Issues

### Symptom: Total processing time is unexpectedly high

**Cause:**
- External integrations (DNS, website) taking longer than expected
- System resource constraints
- Network latency or timeouts
- LLM latency (if configured)

**Action:**
1. Expected latency: 2-5 seconds typical for end-to-end pipeline
2. Each external integration can add latency:
   - DNS resolution: 0-5000ms (bounded by DNS_TIMEOUT_SECONDS)
   - Website fetch: 0-5000ms (bounded by WEBSITE_TIMEOUT_SECONDS=5.0)
3. Monitor the audit trail for specific step timings
4. Check system resources: CPU, memory, disk
5. Check network connectivity and responsiveness
6. Review audit trail for TIMEOUT or INTEGRATION_FAILED events
7. This is normal for assessment environment with external verifications

---

## Clean Reset

To completely reset LeadFlow AI:

```powershell
# Stop application (Ctrl+C in terminal)

# Remove runtime database
Remove-Item day2/logs/audit.db

# Clear Python cache
Remove-Item -Recurse day2/backend/__pycache__
Remove-Item -Recurse day2/.pytest_cache

# Reinstall dependencies
pip install -r day2/requirements.txt --force-reinstall

# Restart application
python day2/backend/app/main.py
```

---

## Getting Help

For issues not covered here:
1. Check application logs: `day2/logs/leadflow.log`
2. Review audit trail for the specific lead
3. Check environment variables: `.env` file
4. Verify all dependencies installed: `pip list`
5. Consult architecture documentation: `day2/docs/architecture.md`
