# LeadFlow AI User Runbook
**Target User**: Inbound Sales Development Representative (SDR)  
**Skill Level**: Non-Developer  
**Environment**: Windows/Mac with web browser  

---

## Quick Start (5 Minutes)

### Step 1: Start the System
1. **Double-click** `start_leadflow.bat` in the main folder
2. **Wait** for the message "Application startup complete"
3. **Open your browser** to `http://localhost:8000`

> If you see an error, make sure Python 3.11+ is installed

### Step 2: Process Your First Lead
1. **Click** the "TC-01: Enterprise Buyer" button (blue preset chip)
2. **Click** "⚡ Process Inbound Lead" 
3. **Watch** the real-time progress bar
4. **Review** the results in each section
5. **Click** "✓ Approve & Dispatch" when ready

### Step 3: Understanding What Happened
- **External Verification**: System checked if the company domain exists and website is reachable
- **Enrichment**: Found company details (headcount, industry, tech stack)  
- **ICP Score**: Calculated qualification score (0-100) with point breakdown
- **Draft**: Generated personalized first-touch email
- **Human Approval**: Waited for your approval before authorizing CRM dispatch

---

## Understanding the Interface

### Section A: Lead Input Form
**What you see**: Name, Email, Company, Role, Team Size, Notes fields  
**What to do**: Either fill manually or click a preset button (TC-01, TC-02, etc.)  
**Tips**: Presets load different scenarios for testing

### Section B: Process Button  
**What you see**: "⚡ Process Inbound Lead" button  
**What it does**: Starts the automated qualification pipeline  
**When to click**: After loading lead information

### Section C: Progress Status
**What you see**: Step-by-step progress indicators  
**What it means**: Shows which part of the pipeline is currently running  
**Colors**: Gray (pending), Blue (processing), Green (completed)

### Section D: External Verification 
**DNS Status**: Shows if company domain exists on the internet
- ✅ **VERIFIED**: Domain resolves normally  
- ❌ **UNRESOLVED**: Domain doesn't exist or has issues
- ⏱️ **TIMEOUT**: DNS check took too long

**Website Status**: Shows if company website is reachable
- ✅ **REACHABLE**: Website loads normally with HTTPS security
- ❌ **UNREACHABLE**: Website down or not responding  
- ⏱️ **TIMEOUT**: Website took too long to respond

### Section E: Company Enrichment
**What you see**: Employee count, industry, funding stage, tech stack  
**Data source**: Internal company database  
**If missing**: Shows "ENRICHMENT_UNAVAILABLE" - still processable

### Section F: ICP Qualification  
**Score**: Number from 0-100 (higher = better fit)
**Tier**: Classification level
- **Tier 1**: Enterprise (80-100 points) - High priority
- **Tier 2**: Mid-Market (60-79 points) - Standard priority  
- **Tier 3**: SMB (30-59 points) - Self-serve
- **Disqualified**: <30 points or security risk

**Point Breakdown**: Shows exactly how the score was calculated

### Section G: Safety Checks
**Risk Flags**: Shows any detected issues
- **CLEAN**: No issues found
- **NEEDS_VERIFICATION**: Requires manual review  
- **QUARANTINED**: Security risk detected - cannot approve

**Claim Validation**: Checks outreach draft for policy violations
- **PASSED**: Draft is safe to send
- **FAILED**: Contains unauthorized promises or discounts

### Section H: First-Touch Draft
**Subject Line**: Proposed email subject  
**Email Body**: Personalized outreach message  
**Generation Source**: Shows if written by AI or template fallback

### Section I: Human Approval Actions
**Pre-Approval State**: "AWAITING REVIEW" + "Dispatch Locked 🔒"
- CRM payload shows `PREVIEW_ONLY`
- No outreach will be sent yet

**Your Options**:
1. **✓ Approve & Dispatch**: Authorizes CRM dispatch and outreach
2. **✎ Edit Draft**: Modify the email before approving  
3. **⚠ Quarantine**: Block the lead from processing

**Post-Approval State**: "DISPATCH AUTHORIZED" + "Approved ✓"
- CRM payload changes to `APPROVED_FOR_DISPATCH`
- System ready for outreach execution

---

## How to Handle Different Scenarios

### Normal Enterprise Lead
1. **Look for**: High ICP score (80-100), Tier 1 classification
2. **Check**: DNS verified, website reachable, no risk flags
3. **Review**: Draft mentions relevant company details
4. **Action**: Click "✓ Approve & Dispatch"

### Free Email Lead (e.g., Gmail)  
1. **Look for**: "FREE_MAIL_DOMAIN" flag in risk assessment
2. **Check**: Company details still verified through enrichment
3. **Decision**: May require corporate email verification
4. **Action**: Review manually, approve if company is legitimate

### Sparse Information Lead
1. **Look for**: "SPARSE_INPUT_WARNING" flag
2. **Check**: Score based on available information only
3. **Review**: Draft asks discovery questions instead of assuming needs
4. **Action**: Approve if tier and routing look correct

### Security Risk Lead
1. **Look for**: "QUARANTINED" status, score of 0
2. **Warning**: Red quarantine badge, no approval option
3. **Reason**: Could be competitor intelligence or prompt injection
4. **Action**: No action needed - system blocks automatically

---

## What Different Error Messages Mean

### "DNS Resolution Failed"
**What it means**: Company domain doesn't exist on the internet  
**What to check**: Is the company name spelled correctly?  
**What to do**: Review manually - could be startup without website

### "Website Timeout After 5 Seconds"
**What it means**: Company website is slow or unreachable  
**What to check**: Try visiting the website yourself  
**What to do**: Can still process using other data sources

### "Enrichment Data Not Available"
**What it means**: No company details found in database  
**What to check**: Is this a new/unknown company?  
**What to do**: Score based on form information only

### "Commercial Claim Violation Detected"
**What it means**: Draft contains unauthorized promises (discounts, guarantees)  
**What to check**: Review the draft text carefully  
**What to do**: Edit the draft to remove prohibited content

### "Cannot Approve Quarantined Lead"
**What it means**: Security system detected risk (competitor, injection)  
**What to check**: Review the lead details and notes  
**What to do**: Consult with RevOps team if needed

---

## Editing Draft Messages

### When to Edit
- Draft is too generic for the specific lead
- Want to add personalized details you know
- Need to adjust tone or emphasis
- Remove any concerning language

### How to Edit  
1. **Click** "✎ Edit Draft" 
2. **Modify** the subject or body text
3. **Click** "✓ Approve & Dispatch"
4. **System** re-validates the edited text

### What NOT to Include
- Specific discount percentages (blocked)
- Uptime guarantees like "99.999%" (blocked)  
- HIPAA or compliance certifications (blocked)
- Promises not approved by product team

---

## Understanding CRM Status

### Before Your Approval
- **Status**: `PREVIEW_ONLY`
- **Meaning**: Draft payload only, no dispatch authorized
- **Safety**: Nothing will be sent to customer or CRM

### After Your Approval  
- **Status**: `APPROVED_FOR_DISPATCH`  
- **Meaning**: Authorized for CRM integration and outreach
- **Next Step**: System ready to execute approved action

---

## When to Escalate

### Contact RevOps If:
- Seeing repeated quarantine flags you don't understand
- Competitor leads getting through filters  
- Scoring seems consistently wrong for your market
- System performance issues or crashes

### Contact IT If:
- Application won't start (`start_leadflow.bat` fails)
- Browser shows "connection refused" errors
- Getting Python or server error messages

---

## Troubleshooting Common Issues  

### "Page Not Found" at localhost:8000
**Solution**: Make sure `start_leadflow.bat` is running and shows "startup complete"

### Processing Hangs on DNS Check
**Solution**: Check internet connection; system will timeout after 5 seconds automatically  

### All Scores Show 0
**Solution**: Check if enrichment data is loading; contact support if persistent

### Can't Approve Any Leads
**Solution**: Check for quarantine flags or claim validation failures in Section G

---

## Daily Workflow Tips

1. **Start with presets** to learn the system behavior
2. **Pay attention to risk flags** - they prevent issues
3. **Read the point breakdown** to understand scoring
4. **Edit drafts** when you have specific company knowledge  
5. **Approve thoughtfully** - you're authorizing business communications
6. **Check external verification** before approving enterprise leads

**Remember**: You remain responsible for commercial communications sent on your behalf. The system assists your judgment - it doesn't replace it.