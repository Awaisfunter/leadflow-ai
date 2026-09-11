# LeadFlow AI — Privacy & Permission Boundaries (Day 2 v0)

## 1. Governance & Data Privacy Policy (v0 Synthetic Stage)
LeadFlow AI v0 operates entirely under **controlled synthetic conditions**:
1. **Synthetic Data Only**: All company firmographics, contact names, and benchmark scenarios use synthetic datasets. No production customer data or live Salesforce/HubSpot instances are utilized in this sprint.
2. **Zero Credentials in Source Code**: All API keys and environment configurations are loaded strictly via `.env` using `pydantic-settings`. `.env` is explicitly ignored by version control.
3. **Untrusted Input Isolation**: User-submitted form notes are treated as hostile, untrusted strings. They are segregated from system prompts to prevent prompt injection and remote instruction execution.
4. **Audit Log Data Minimization**: Audit logs record cryptographic SHA-256 fingerprints of raw inputs rather than unbounded sensitive data blobs. Secret keys and credentials are never written to the audit database.

---

## 2. Role-Based Permission Matrix

```
┌──────────────────────────────┬──────────────┬──────────────┬──────────────┐
│ Action / Capability          │ Inbound SDR  │ RevOps Lead  │ System (AI)  │
├──────────────────────────────┼──────────────┼──────────────┼──────────────┤
│ Submit & Process Inbound Lead│      ✓       │      ✓       │  Automated   │
│ View Enrichment & Score      │      ✓       │      ✓       │  Automated   │
│ Edit AI First-Touch Draft    │      ✓       │      ✓       │  Prohibited  │
│ Approve Standard First-Touch │      ✓       │      ✓       │  Prohibited  │
│ Release Quarantined Lead     │  Prohibited  │      ✓       │  Prohibited  │
│ View Full SQLite Audit Trail │      ✓       │      ✓       │  Write Only  │
│ Modify ICP Weighting Rules   │  Prohibited  │      ✓       │  Prohibited  │
│ Disregard Blocked Claims     │  Prohibited  │  Prohibited  │  Prohibited  │
│ Auto-Dispatch Without Review │  Prohibited  │  Prohibited  │  Prohibited  │
└──────────────────────────────┴──────────────┴──────────────┴──────────────┘
```

---

## 3. Boundary Definitions by Actor

### Inbound Sales Development Representative (SDR)
- **Granted Permissions**:
  - May trigger lead processing via the web dashboard.
  - May inspect the firmographic enrichment, score breakdown, and security flags.
  - May review and edit the generated first-touch email draft.
  - May authorize dispatch for leads with status `PENDING_REVIEW` when claim checks pass.
  - May reject or manually quarantine leads.
- **Prohibited Actions**:
  - Cannot bypass blocked commercial claims (must edit out violations first).
  - Cannot approve leads flagged under active `QUARANTINED` status without RevOps escalation.
  - Cannot alter deterministic scoring weights.

### Revenue Operations Manager (RevOps)
- **Granted Permissions**:
  - May view complete append-only SQLite audit trails across all processed leads.
  - May inspect system latency, token usage, and claim block rates.
  - May review and release quarantined leads following manual security inspection.
  - May configure business rules, competitor domain blacklists, and ICP scoring thresholds in `business_rules.json`.
- **Prohibited Actions**:
  - Cannot authorize unilateral pricing concessions without human sales leadership sign-off.

### System / AI Engine
- **Granted Permissions**:
  - May validate schemas, parse domains, and look up company facts in the synthetic dataset.
  - May calculate numerical ICP scores and assign tiers according to explicit deterministic rules.
  - May draft email text within the boundaries of verified facts.
  - May log append-only audit records into SQLite.
- **Prohibited Actions**:
  - STRICTLY PROHIBITED from acting as the source of truth for qualification or tiering.
  - STRICTLY PROHIBITED from auto-dispatching outreach without human confirmation.
  - STRICTLY PROHIBITED from modifying CRM records autonomously.
  - STRICTLY PROHIBITED from inventing features, pricing, or certifications.

---

## 4. Path to Production Compliance
Before migrating from synthetic v0 to enterprise production:
1. **GDPR / CCPA Right-to-be-Forgotten**: Implement an automated deletion worker that cascades lead deletion requests through SQLite audit storage and CRM sync queues.
2. **Role-Based Access Control (RBAC)**: Replace local `demo_user` sessions with OAuth2 / SAML SSO integration (Okta, Azure AD).
3. **Secret Rotation**: Enforce automated key rotation via AWS Secrets Manager or HashiCorp Vault.
