# LeadFlow AI Operator Runbook
*For System Administrators and Operations Staff*

## Daily Operations

### Startup Procedures

#### Automated Startup (Windows)
```bash
# Navigate to project root
cd /path/to/leadflow-ai-final
# Run startup script
start_leadflow.bat
```

#### Manual Startup (Any Platform)
```bash
# Navigate to application directory
cd leadflow-ai-final/day2

# Verify Python environment
python --version
# Should show Python 3.11 or higher

# Install/update dependencies (if needed)
pip install -r requirements.txt

# Start application
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

#### Startup Verification
1. **Service Health Check:**
   ```bash
   curl http://localhost:8000/health
   ```
   Expected: `{"status":"healthy","timestamp":"..."}`

2. **Web Interface Check:**
   Open browser to `http://localhost:8000`
   Expected: LeadFlow AI dashboard with dropdown menu

3. **Database Check:**
   Verify audit database exists: `day2/logs/audit.db`

### Shutdown Procedures

#### Graceful Shutdown
1. Press `Ctrl+C` in the terminal running the application
2. Wait for "Interrupted by user" message
3. Verify no processes remain: `ps aux | grep uvicorn`

#### Force Stop (if needed)
```bash
# Find the process
ps aux | grep uvicorn
# Kill by PID
kill [PID]
# Or kill all uvicorn processes
pkill -f uvicorn
```

## Configuration Management

### Environment Variables

#### Required Configuration (Optional)
Create `day2/.env` file:
```env
# LLM Configuration (optional - system works without)
GEMINI_API_KEY=your_api_key_here
OPENAI_API_KEY=alternative_provider

# Service Configuration
DNS_TIMEOUT_SECONDS=10
WEBSITE_TIMEOUT_SECONDS=5
LOG_LEVEL=INFO

# Database Configuration  
AUDIT_DATABASE_PATH=logs/audit.db
```

#### Business Rules Configuration
**File:** `day2/data/business_rules.json`

**Competitor Domains:** Add/remove competitor domains to monitor
```json
{
  "competitor_domains": [
    "competitorsaas.com",
    "rivalplatform.io",
    "newcompetitor.com"
  ]
}
```

**Scoring Weights:** Adjust ICP scoring parameters
```json
{
  "scoring_weights": {
    "firmographic_max": 40,
    "role_max": 25,
    "intent_max": 20,
    "urgency_max": 15
  }
}
```

**Tier Thresholds:** Modify lead classification ranges
```json
{
  "tier_thresholds": {
    "tier_1_min": 80,
    "tier_2_min": 30
  }
}
```

#### Synthetic Enrichment Data
**File:** `day2/data/synthetic_companies.json`

Add new companies for enrichment:
```json
{
  "newcompany.com": {
    "name": "New Company Inc",
    "headcount": 250,
    "industry": "FinTech",
    "funding": "Series B",
    "tech_stack": ["React", "AWS", "Stripe"]
  }
}
```

### Log Locations

#### Application Logs
- **Console Output:** Terminal running uvicorn
- **Error Logs:** Stderr in terminal
- **Access Logs:** HTTP requests logged to console

#### Audit Database
- **Location:** `day2/logs/audit.db`
- **Type:** SQLite database
- **Schema:** Events table with lead processing history

#### System Logs
- **OS Logs:** Check system logs for process management
- **Python Logs:** Virtual environment and package installation

## Monitoring and Health Checks

### Health Endpoints

#### Basic Health Check
```bash
curl http://localhost:8000/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-09-08T10:30:00Z",
  "version": "v0.1.0"
}
```

#### Processing Statistics
```bash
curl http://localhost:8000/metrics
```
**Response Fields:**
- `total_processed`: Number of leads processed
- `avg_latency_ms`: Average processing time
- `external_integration_rate`: Success rate for DNS/website checks
- `llm_fallback_rate`: Percentage using deterministic templates

### Testing Procedures

#### Automated Test Suite
```bash
cd day2
pytest backend/tests/test_pipeline.py -v
```
**Expected:** 56 tests pass, 0 failures

**Key Tests:**
- Schema validation
- Scoring arithmetic
- Security quarantine
- Approval workflows
- External integrations
- Audit logging

#### Benchmark Suite
```bash
cd leadflow-ai-final
python day3/benchmark/run_12_case_benchmark.py
```
**Expected:** 12/12 cases with perfect tier, score, and routing match

#### Break Test Suite
```bash
cd leadflow-ai-final  
python day4/break_tests/run_break_tests.py
```
**Expected:** 10/10 failure scenarios handled gracefully

#### Integration Smoke Tests
1. **Process Enterprise Lead (TC-01):**
   - Select "TC-01: Enterprise Buyer" from dropdown
   - Click "Process Inbound Lead"
   - Verify Tier 1, score 100, enterprise routing
   - Approve and verify CRM payload generation

2. **Process Competitor Lead (TC-09):**
   - Select "TC-09: Competitor Intelligence"
   - Verify automatic quarantine
   - Confirm no approval option available

3. **Process Prompt Injection (TC-10):**
   - Select "TC-10: Prompt Injection"
   - Verify quarantine with injection detection message

## Failure Handling

### LLM Provider Unavailable

#### Symptoms
- Console shows "LLM generation failed or unavailable"
- Drafts show "deterministic_fallback_v1" source
- Performance may be slightly faster

#### Expected System Behavior
- Automatic fallback to template generation
- `FALLBACK_ACTIVATED` audit events logged
- Users see professional template-based emails
- All other functionality continues normally

#### Actions Required
- **Immediate:** None - system handles automatically
- **Monitor:** Check fallback rate in metrics
- **Escalate:** If fallback rate >80% for extended period

### DNS Resolution Failures

#### Symptoms
- Domain verification shows "UNRESOLVED"
- Error codes: DNS_NXDOMAIN, DNS_NO_A_RECORD
- Processing continues with NEEDS_VERIFICATION flag

#### Expected System Behavior
- Graceful degradation with clear user messaging
- Lead scoring continues using available data
- External integration failure logged to audit

#### Actions Required
- **Check:** Verify internet connectivity
- **Monitor:** If DNS failure rate >20%, investigate network
- **Escalate:** If persistent DNS provider issues

### Website Metadata Timeout

#### Symptoms
- Website verification shows "UNREACHABLE" or "TIMEOUT"
- Processing time approaches 5-second limit
- Website error messages in results

#### Expected System Behavior
- 5-second timeout strictly enforced
- Clear timeout messaging to user
- Lead processing continues without website data

#### Actions Required
- **Normal:** Website timeouts are common and expected
- **Monitor:** Average processing time staying under 6 seconds
- **Investigate:** If timeout rate >50%, check network performance

### Synthetic Enrichment Miss

#### Symptoms
- Enrichment section shows "ENRICHMENT_UNAVAILABLE"
- Company not found in synthetic dataset
- Scoring based on form data only

#### Expected System Behavior
- Form-only scoring calculation
- Clear messaging about missing enrichment
- NEEDS_VERIFICATION flag added

#### Actions Required
- **Review:** Add commonly requested companies to dataset
- **Update:** `synthetic_companies.json` with new entries
- **Restart:** Application to load new data

### Claim Validation Blocking

#### Symptoms
- "BLOCKED_CLAIMS_DETECTED" in results
- Specific policy violations listed
- Approval button disabled until editing

#### Expected System Behavior
- Draft approval blocked automatically
- Clear violation messages to user
- Re-validation after user edits

#### Actions Required
- **Review:** Policy violations for pattern accuracy
- **Update:** Blocked claim patterns if needed
- **Investigate:** If legitimate content blocked frequently

### Quarantine Detection

#### Symptoms
- Lead automatically quarantined
- Quarantine reason displayed (competitor, injection, etc.)
- No approval options available

#### Expected System Behavior
- Immediate quarantine without human review needed
- Security audit events logged
- Zero risk of unauthorized outreach

#### Actions Required
- **Monitor:** Quarantine rates and patterns
- **Review:** False positive quarantines
- **Update:** Detection patterns if needed

### Database Issues

#### Symptoms
- SQLite error messages
- Missing audit.db file
- Audit logging failures

#### Expected System Behavior
- Automatic database creation if missing
- Error handling for write failures
- Application continues with logging warnings

#### Actions Required
- **Check:** File permissions on logs directory
- **Verify:** Disk space availability
- **Backup:** Audit database regularly

## Backup and Recovery

### Backup Procedures

#### Daily Backup
```bash
# Backup audit database
cp day2/logs/audit.db backups/audit_$(date +%Y%m%d).db

# Backup configuration
cp day2/data/business_rules.json backups/
cp day2/data/synthetic_companies.json backups/
cp day2/.env backups/ 2>/dev/null || true
```

#### Full System Backup
```bash
# Create dated backup directory
mkdir -p backups/full_$(date +%Y%m%d)

# Backup entire application
rsync -av --exclude '__pycache__' \
          --exclude '.pytest_cache' \
          --exclude '*.pyc' \
          leadflow-ai-final/ backups/full_$(date +%Y%m%d)/
```

### Recovery Procedures

#### Restore Configuration
```bash
# Restore business rules
cp backups/business_rules.json day2/data/

# Restore synthetic data  
cp backups/synthetic_companies.json day2/data/

# Restart application
# (use normal startup procedures)
```

#### Restore Audit Database
```bash
# Stop application first
# Copy backup database
cp backups/audit_YYYYMMDD.db day2/logs/audit.db
# Restart application
```

## Maintenance Tasks

### Weekly Tasks
1. **Review audit logs** for unusual patterns
2. **Check processing statistics** and performance trends
3. **Verify backup success** and storage space
4. **Update synthetic dataset** with new companies if needed

### Monthly Tasks  
1. **Run full test suite** to verify functionality
2. **Review quarantine patterns** and detection accuracy
3. **Analyze processing latencies** and identify optimization needs
4. **Update business rules** based on sales team feedback

### Quarterly Tasks
1. **Full system backup** and restore test
2. **Performance baseline** documentation update
3. **Security review** of audit logs and quarantine patterns
4. **Capacity planning** for growth requirements

## Troubleshooting Guide

### Application Won't Start

#### Check Python Version
```bash
python --version
# Should be 3.11 or higher
```

#### Check Dependencies
```bash
cd day2
pip install -r requirements.txt
```

#### Check Port Availability
```bash
# Linux/Mac
lsof -i :8000
# Windows
netstat -an | findstr :8000
```

#### Permission Issues
```bash
# Check directory permissions
ls -la day2/logs/
# Create logs directory if missing
mkdir -p day2/logs
```

### Web Interface Issues

#### Browser Can't Connect
1. Verify application is running (check terminal)
2. Confirm URL: `http://localhost:8000`
3. Try different browser or incognito mode
4. Check firewall settings

#### Page Loads But Doesn't Work
1. Check browser console for JavaScript errors
2. Verify API endpoints are responding: `/health`, `/metrics`
3. Clear browser cache and cookies
4. Restart application

### Performance Issues

#### Slow Processing
1. **Check external service latency:**
   - DNS resolution times
   - Website response times
   - LLM provider performance

2. **Monitor resource usage:**
   - CPU utilization
   - Memory consumption
   - Disk I/O

3. **Review recent changes:**
   - New companies in synthetic dataset
   - Business rule modifications
   - Network configuration changes

### Data Issues

#### Missing or Incorrect Results
1. **Verify test data:** Use known benchmark cases
2. **Check business rules:** Ensure configuration is correct
3. **Review audit logs:** Look for processing errors
4. **Validate external integrations:** DNS and website checks

## Security Monitoring

### Key Security Metrics
- **Quarantine Rate:** Percentage of leads quarantined
- **Injection Detection Rate:** Prompt injection attempts caught
- **Approval Bypass Attempts:** Security violation events
- **External Source Validation:** DNS/website verification rates

### Security Log Review
```sql
-- Connect to audit database
sqlite3 day2/logs/audit.db

-- Review security events
SELECT * FROM audit_events 
WHERE event_type IN ('QUARANTINED', 'APPROVAL_BLOCKED', 'VALIDATION_BLOCKED')
ORDER BY timestamp DESC LIMIT 50;

-- Check quarantine patterns
SELECT event_details, COUNT(*) as count
FROM audit_events 
WHERE event_type = 'QUARANTINED'
GROUP BY event_details
ORDER BY count DESC;
```

### Security Incident Response
1. **Unusual Quarantine Patterns:** Review for new attack vectors
2. **Repeated Bypass Attempts:** Investigate source and intent
3. **Policy Violations:** Update claim validation patterns
4. **External Integration Anomalies:** Check for manipulation attempts

## Escalation Procedures

### When to Escalate

#### Immediate Escalation
- Application completely unavailable
- Security breach indicators
- Data corruption or loss
- Unauthorized access attempts

#### Planned Escalation  
- Performance degradation >50%
- External service outages >24 hours
- Test suite failures
- Repeated user reports of incorrect results

### Escalation Information

#### System Information to Provide
- Application version and commit ID
- Recent configuration changes
- Current error messages and logs
- Performance metrics and trends

#### Contact Information
- **Technical Issues:** Development team
- **Security Issues:** Security team + management
- **Business Issues:** Sales operations team
- **Infrastructure Issues:** IT operations team

---

**Runbook Version:** Day 5 Final  
**Last Updated:** 2026-09-08  
**Review Schedule:** Monthly during initial deployment, quarterly thereafter