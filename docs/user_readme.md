# LeadFlow AI User Guide
*For Sales Development Representatives (SDRs)*

## Getting Started

### How to Start LeadFlow AI

1. **Windows:** Double-click `start_leadflow.bat` in the main project folder
2. **Any Platform:** Open terminal, go to `day2` folder, run:
   ```
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Open your web browser** and go to: `http://localhost:8000`

You should see the LeadFlow AI dashboard with a dropdown menu and a "Process Inbound Lead" button.

## Processing Your First Lead

### Step 1: Select a Test Lead

Click the dropdown menu at the top of the page. You'll see options like:
- **TC-01: Enterprise Buyer** - Large company executive 
- **TC-02: Normal Mid-Market Lead** - Medium-sized company contact
- **TC-08: Small Business** - Small company inquiry
- **TC-09: Competitor Intelligence** - Suspicious competitor request

**For your first try, select "TC-01: Enterprise Buyer"**

### Step 2: Click "Process Inbound Lead"

The system will start working automatically. You'll see several sections fill in with information:

## Understanding the Results

### Domain Verification Section
**What it shows:** Whether the company's website domain exists and is reachable

**What you'll see:**
- ✅ **VERIFIED** - Domain exists and resolves properly
- ⚠️ **UNRESOLVED** - Domain doesn't exist or has DNS issues
- ❌ **TIMEOUT** - Domain took too long to check

**What DNS verification means:** We check if the company domain (like "acmecorp.com") actually exists on the internet by looking it up in public DNS records. This helps confirm the company is real.

**When DNS fails:** The lead can still be processed, but you should be extra careful about legitimacy.

### Website Verification Section  
**What it shows:** Whether we can reach the company website and get basic information

**What you'll see:**
- ✅ **REACHABLE** - Website loads and we got the page title
- ⚠️ **UNREACHABLE** - Website doesn't respond or times out  
- 🕒 **TIMEOUT** - Website took longer than 5 seconds to respond

**What website verification means:** We try to visit the company's actual website to get the page title and confirm it's a real business website. This adds another layer of legitimacy checking.

**When website fails:** This is normal - many company websites are slow or have technical issues. The lead can still be qualified.

### Synthetic Enrichment Section
**What it shows:** Additional company information from our internal database

**What you'll see:**
- Company headcount (e.g., "850 employees")
- Industry (e.g., "Enterprise Software")  
- Funding stage (e.g., "Public", "Series B")
- Technology used (e.g., "Salesforce", "AWS")

**What synthetic enrichment means:** We look up the company in our internal database of company information. This data is labeled "synthetic" because it's from our test database, not live external APIs.

**When enrichment is missing:** Shows "ENRICHMENT_UNAVAILABLE" - we don't have this company in our database, so scoring is based only on the lead form information.

### ICP Score Breakdown
**What it shows:** How well this lead matches our Ideal Customer Profile (0-100 points)

**What the score means:**
- **80-100 points:** Tier 1 (Enterprise) - High-value prospect  
- **30-79 points:** Tier 2 (Commercial) - Good fit prospect
- **0-29 points:** Tier 3 (Self-serve) - Low-priority prospect

**Score categories:**
- **Firmographic Points (0-40):** Company size, funding, industry fit
- **Role Points (0-25):** How senior/relevant the contact's job title is
- **Intent Points (0-20):** How clearly they described their problem/need
- **Urgency Points (0-15):** How soon they need a solution
- **Risk Penalty (0-100):** Deductions for red flags

**What Tier means:**
- **Tier 1:** Route to Enterprise Account Executive (highest priority)
- **Tier 2:** Route to Commercial Account Executive (standard priority)
- **Tier 3:** Route to self-serve resources (lowest priority)

### Routing Recommendation
**What it shows:** What sales action to take next

**Common routing actions:**
- **ROUTE_ENTERPRISE_AE:** Assign to Enterprise Account Executive
- **ROUTE_COMMERCIAL_AE:** Assign to Commercial Account Executive  
- **ROUTE_EXPRESS_ONBOARDING:** Fast-track to product demo
- **REQUIRE_CORPORATE_EMAIL:** Ask for business email instead of personal
- **QUARANTINE_COMPETITOR:** Block - this is a competitor trying to spy
- **QUARANTINE_INJECTION:** Block - suspicious/malicious content detected

### Email Draft Section
**What it shows:** A personalized email ready to send to the prospect

**Draft source indicators:**
- **LLM-Generated:** AI wrote a custom email using the lead details
- **Deterministic Fallback:** System used a template because AI was unavailable

**What LLM-generated vs deterministic fallback means:**
- **LLM-Generated:** The AI (Large Language Model) created a personalized email based on all the lead information and company details
- **Deterministic Fallback:** When the AI system isn't available, we use pre-written templates filled in with the lead details. The content is still personalized but follows a standard structure.

Both approaches create professional, personalized outreach - the fallback ensures you can always process leads even if AI services are down.

### Claim Validation Results
**What it shows:** Whether the email draft contains any unauthorized promises

**What you'll see:**
- ✅ **CLAIM_VALIDATION_PASSED** - Email is safe to send
- ❌ **BLOCKED_CLAIMS_DETECTED** - Email contains problematic promises

**Why claim validation exists:** The system checks that generated emails don't make promises we can't keep, like:
- Unauthorized discounts ("50% off")
- Compliance claims we haven't verified ("HIPAA compliant") 
- Impossible guarantees ("100% uptime", "zero downtime")
- Specific SLA promises we don't offer

**When claims are blocked:** You must edit the email to remove the problematic language before you can approve it.

## Making Your Decision

After reviewing all the information, you have three choices:

### ✅ Approve & Dispatch
**When to use:** The lead looks legitimate and the email draft is appropriate

**What happens:**
- Status changes from `PENDING_REVIEW` to `APPROVED`
- Dispatch authorization changes from `False` to `True`  
- CRM status changes from `PREVIEW_ONLY` to `APPROVED_FOR_DISPATCH`
- A structured CRM payload is generated (ready for your CRM system)

**What PREVIEW_ONLY means:** The lead is processed and ready for review, but cannot be sent to your CRM or trigger any sales outreach until you approve it.

**What APPROVED_FOR_DISPATCH means:** You have reviewed and approved this lead. In a production system, this would trigger automatic entry into your CRM and enable sales outreach.

### ✎ Edit Draft  
**When to use:** The lead is good but the email needs changes

**How to edit:**
1. Click in the email text area
2. Make your changes to the subject line or body
3. The system automatically re-checks your edited version for policy violations
4. If clean, you can then approve it
5. If it still has policy violations, you'll see warnings to fix

**Important:** When you edit an email and then approve it, the system re-validates your final text to make sure you didn't accidentally add any unauthorized claims.

### 🚫 Quarantine
**When to use:** The lead is suspicious, inappropriate, or from a competitor

**What happens:**
- Lead is marked as `QUARANTINED`
- No sales outreach will ever be sent
- The decision is logged for security review
- CRM dispatch remains permanently blocked

**When to quarantine:**
- Competitor trying to gather intelligence about your company
- Suspicious content that might be spam or malicious
- Academic research requests (if not serving academic customers)
- Leads with personal attacks or inappropriate language

## Understanding System Status

### Pre-Approval State
When you first process a lead, you'll see:
- **Status:** `PENDING_REVIEW`
- **Dispatch Authorized:** `False`  
- **CRM Status:** `PREVIEW_ONLY`
- **Action Required:** Review and approve/edit/quarantine

**Important:** The system will NEVER send anything to your CRM or trigger sales outreach while in this state. Human approval is always required.

### Post-Approval State  
After you approve a lead, you'll see:
- **Status:** `APPROVED`
- **Dispatch Authorized:** `True`
- **CRM Status:** `APPROVED_FOR_DISPATCH`  
- **Action Completed:** Ready for CRM integration

## What To Do When Things Go Wrong

### DNS or Website Verification Fails
**This is normal!** Many legitimate companies have:
- Slow websites that timeout
- DNS configuration issues
- Temporary connectivity problems

**What to do:** Review the other information (company details, role, intent) and make your decision. The lead can still be qualified without perfect external verification.

### Enrichment is Unavailable
**What this means:** We don't have this company in our database

**What to do:** This is common for newer companies or those outside our database coverage. Review the information from the lead form and proceed with qualification.

### LLM Draft Generation Falls Back to Template
**What this means:** The AI service was unavailable, so we used a pre-written template

**What to do:** Review the template email - it's still personalized with the lead's information. You can edit it if needed, then approve as normal.

### Claim Validation Blocks the Email
**What this means:** The generated email contains promises we shouldn't make

**What to do:**
1. Read the specific blocked claims listed
2. Click "Edit Draft"  
3. Remove or rephrase the problematic language
4. Try to approve again

**Common blocked claims to watch for:**
- Percentage discounts
- Compliance certifications  
- Uptime guarantees
- Specific SLA promises

### Application Becomes Unresponsive
**If the page stops working:**
1. Check that the application is still running (terminal window should be active)
2. Try refreshing the web page
3. If still broken, restart the application and try again

### "This site can't be reached" Error
**This means the application stopped running:**
1. Go back to your terminal/command prompt
2. Restart the application: `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload`
3. Wait for "Uvicorn running" message
4. Refresh your browser

## Tips for Effective Use

### Best Practices
1. **Always review all sections** before making a decision - don't just look at the score
2. **Pay attention to risk flags** - they're there for your protection
3. **Read the generated email carefully** - make sure it sounds professional and appropriate
4. **When in doubt, quarantine** - it's better to be safe than sorry
5. **Use editing when the lead is good but the email needs work** - don't quarantine good leads just because of email issues

### Red Flags to Watch For
- **Competitor domains:** Usually end in names similar to your company
- **Prompt injection attempts:** Weird instructions mixed into the lead notes
- **Too-good-to-be-true scenarios:** Unrealistically perfect leads might be spam
- **Vague or template-like inquiries:** May indicate low-quality lead generation
- **Personal email addresses from large companies:** May indicate the person doesn't actually work there

### Quality Indicators
- **Corporate email domains:** Match the company name
- **Specific problem descriptions:** Show genuine interest
- **Appropriate contact roles:** Match your typical customer profiles  
- **Reasonable company information:** Headcount and funding make sense together
- **Professional inquiry tone:** Sounds like a real business person

## Getting Help

### If You Need Technical Support
- Check `docs/troubleshooting.md` for common issues
- Review `operations/operator_runbook.md` for system operations
- Check the terminal window for error messages

### If You Need Help Understanding Results
- Review this guide for explanations of all fields and statuses
- Check `docs/architecture.md` for technical details
- Look at `case_study/leadflow_case_study.md` for examples

### If You Find a Problem
- Check the audit log at `day2/logs/audit.db` for decision history
- Report issues to your system administrator
- Document what you were trying to do when the problem occurred

---

**Remember:** LeadFlow AI is designed to help you work faster and more consistently, but your human judgment is still the most important part of the process. The system provides information and suggestions, but you make the final decisions about every lead.