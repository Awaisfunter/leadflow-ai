# LeadFlow AI — Day 3 Core Architecture Specification

> **System Milestone: Day 3 — Build the Working Core**  
> **Author:** Awais Saeed | Applied AI Engineer Candidate  
> **Target Audience:** Inbound Sales Development Representatives (Primary), RevOps Managers (Secondary)  
> **Classification:** Technical Architecture & Security Boundary Contract

---

## 1. Architectural Overview & Philosophy

LeadFlow AI is a bounded AI operating system engineered to eliminate the manual 16-minute triage interval between inbound lead submission and approved sales outreach. It operates under a strict principle of **Zero-Trust for External and Generative Data**:

1. **Untrusted External Data**: Inbound form submissions, website HTML, and public DNS records are treated as strictly untrusted external context.
2. **Authoritative Deterministic Core**: Commercial qualification, numerical ICP scoring (0–100), risk penalties, claim validations, and CRM dispatch authorization are governed exclusively by deterministic Python algorithms—never by an unconstrained LLM.
3. **Bounded Generative Drafting**: Generative models (Gemini / OpenRouter adapters) receive sanitized, fact-bounded context. If generative facilities are offline, the system seamlessly uses deterministic fallback templates.
4. **Mandatory Human Governance**: No sales email or CRM payload can be dispatched autonomously. Human SDR approval is an inviolable gate that validates all claims before authorization.

---

## 2. End-to-End Pipeline Architecture (Mermaid)

The updated Day 3 pipeline incorporates two real public external integrations alongside controlled synthetic enrichment, deterministic ICP qualification, claim guardrails, and append-only audit persistence.

```mermaid
flowchart TD
    subgraph INTAKE ["1. Intake & Identity (Untrusted Inputs)"]
        UI["Web Form / Inbound API"] -->|Raw Untrusted LeadInput| PYD["Pydantic v2 Schema Validator"]
        PYD -->|Hash & Parse| IDP["Identity Parser & Corporate Domain Classifier"]
    end

    subgraph RISK ["2. Pre-Flight Risk Engine (Deterministic)"]
        IDP --> RDK["Pre-Flight Risk Detector"]
        RDK -.->|Regex / Signatures| INJ["Injection & Competitor Guard"]
    end

    subgraph INTEGRATIONS ["3. External & Internal Data Enrichment"]
        direction TB
        RDK -->|Domain| DOH["Real Integration #1: Cloudflare DNS-over-HTTPS<br/><i>[source: public_dns]</i>"]
        RDK -->|Domain| WEB["Real Integration #2: Public HTTP Website Metadata<br/><i>[source: public_website]</i>"]
        RDK -->|Domain + Company| ENR["Synthetic Account Lookup<br/><i>[source: synthetic_internal_dataset]</i>"]
    end

    subgraph SCORING ["4. Deterministic ICP Qualification"]
        DOH --> ICP["Deterministic Scoring Engine<br/><i>[source: deterministic_rule]</i>"]
        WEB --> ICP
        ENR --> ICP
        ICP -->|Firmographic (40) + Role (25) + Intent (20) + Urgency (15) - Penalties| QUAL["Tier Classification & Next Action"]
    end

    subgraph DRAFTING ["5. Bounded Sales Outreach"]
        QUAL -->|Bounded Context Only| LLM["LLM Provider Adapter / Offline Fallback<br/><i>[source: llm or deterministic_fallback]</i>"]
        LLM --> DRAFT["First-Touch Email Draft"]
        DRAFT --> CLM["Post-Generation Claim Validator<br/><i>(Blocks unauthorized pricing, SLA, logos)</i>"]
    end

    subgraph GOVERNANCE ["6. Human-In-The-Loop Governance"]
        CLM --> HITL["SDR Review Dashboard<br/><i>(Approve / Edit / Quarantine)</i>"]
        HITL -->|Approve / Edit| APPR["Dispatch Authorized"]
        HITL -->|Quarantine| QUAR["Security Lockout"]
    end

    subgraph DISPATCH ["7. CRM-Ready Structured Dispatch"]
        APPR --> CRM["CRMDispatchPayload<br/><i>status: APPROVED_FOR_DISPATCH</i>"]
        QUAR --> REJ["CRMDispatchPayload<br/><i>status: PREVIEW_ONLY (Locked)</i>"]
    end

    subgraph AUDIT ["8. Append-Only Audit Trail"]
        PYD -.-> AUD[("SQLite Append-Only Audit Log<br/>logs/audit.db")]
        RDK -.-> AUD
        DOH -.-> AUD
        WEB -.-> AUD
        ENR -.-> AUD
        ICP -.-> AUD
        LLM -.-> AUD
        CLM -.-> AUD
        HITL -.-> AUD
        CRM -.-> AUD
    end

    classDef untrusted fill:#451a1a,stroke:#f87171,stroke-width:2px,color:#fff;
    classDef deterministic fill:#143224,stroke:#34d399,stroke-width:2px,color:#fff;
    classDef external fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#fff;
    classDef llm fill:#2e1065,stroke:#a855f7,stroke-width:2px,color:#fff;
    classDef governance fill:#451a03,stroke:#fbbf24,stroke-width:2px,color:#fff;
    classDef audit fill:#0f172a,stroke:#64748b,stroke-width:2px,color:#fff;

    class UI,INJ untrusted;
    class PYD,IDP,RDK,ICP,QUAL,CLM,CRM,REJ deterministic;
    class DOH,WEB,ENR external;
    class LLM,DRAFT llm;
    class HITL,APPR,QUAR governance;
    class AUD audit;
```

---

## 3. Data Classification & Security Boundaries

To maintain institutional trust, LeadFlow AI enforces five distinct data provenance tiers:

| Data Tier | Origin / Source Label | Trust Level | Permitted Usage | Prohibited Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Untrusted Input** | `untrusted_customer_input` | **Zero** | Syntactic parsing, pre-flight regex scanning. | Never directly injected into LLM system prompts or business logic. |
| **Real Public DNS** | `public_dns` | **External Signal** | Validates domain resolvability, IP records, network latency. | Does not determine ICP points; sets `NEEDS_VERIFICATION` if unresolved. |
| **Real Public Web** | `public_website` | **External Signal** | TLS/HTTPS presence, HTTP response status, safe title extraction. | Body text is discarded; never parsed for instructions or sales claims. |
| **Synthetic Account** | `synthetic_internal_dataset` | **Controlled Internal** | Industry, headcount, funding stage, technology signals. | Must never claim real-time live vendor API provenance (e.g. ZoomInfo). |
| **Deterministic Rules** | `deterministic_rule` | **Authoritative** | ICP score (0–100), Tier 1–3 assignment, SLA routing, claim validation. | Authoritative deterministic rule; external text and LLM output cannot modify the scoring logic. |
| **Generative Outreach** | `llm` / `deterministic_fallback`| **Bounded Semantic** | Personalized subject line and body text strictly referencing verified facts. | Cannot commit to discounts, SLA promises, or customer references. |

---

## 4. Pipeline Execution Sequence

1. **Lead Ingestion**: Pydantic v2 validates types, lengths, and email syntax. Invalid payloads fail fast with structured `422` responses.
2. **Deterministic Risk Pre-Flight**: Scans for known prompt injection signatures, competitor domain lists, and academic domains.
3. **Real Integration #1 (Domain Verification)**: Queries Cloudflare DoH (`https://cloudflare-dns.com/dns-query`) for A-records. Measures roundtrip latency.
4. **Real Integration #2 (Website Metadata)**: Performs an HTTP probe with strict timeouts (8s default, 2s connect) and redirect limits (max 3). Extracts `<title>` (truncated to 200 chars); discards HTML body.
5. **Synthetic Account Enrichment**: Looks up company firmographics from the local dataset. Cross-references competitor or security status.
6. **Deterministic ICP Qualification**: Computes numerical score (Firmographic 0–40, Role 0–25, Intent 0–20, Urgency 0–15, Risk Penalties ≤0). Applies specific business rules (e.g. TC-03 SMB fast-onboarding elevation).
7. **Bounded Outreach Drafting**: LLM provider adapter generates first-touch copy using solely approved value propositions. Suppresses outreach if quarantined. Falls back to offline templates if LLM is unreachable.
8. **Claim Guardrail Validation**: Scans draft body for prohibited commercial claims (unapproved discounts, SLAs, certifications).
9. **Human-in-the-Loop Gate**: SDR reviews the aggregated context in the unified dashboard. Can Approve, Edit (re-running claim checks), or Quarantine.
10. **Structured CRM Payload**: Emits validated `CRMDispatchPayload`. Pre-approval state is strictly `PREVIEW_ONLY` (`dispatch_authorized: false`). Approval authorizes dispatch.
11. **Append-Only Audit Logging**: All lifecycle events, hashes, risk flags, latencies, and state transitions are appended to SQLite.

---

## 5. Failure and Degradation Modes

| Failure Condition | Pipeline Behavior | Non-Developer User Experience |
| :--- | :--- | :--- |
| **Public DNS Unresolved** | Domain marked `UNRESOLVED`; `NEEDS_VERIFICATION` flag added. Continues to synthetic enrichment. | Banner warns that domain did not resolve publicly; SDR can review synthetic records. |
| **Website Timeout (>8s)** | Website marked `UNREACHABLE`; error code `TIMEOUT`. Pipeline proceeds uninterrupted. | SDR sees "Website unreachable"; triage continues without delay. |
| **Invalid URL Scheme** | Schemes like `ftp://`, `javascript:` rejected immediately without network requests. | Displays `UNSUPPORTED_SCHEME` error cleanly. |
| **Synthetic Record Absent** | `ENRICHMENT_UNAVAILABLE` flag added; firmographic points default to self-reported values. | Displays unverified tag; routes to SDR discovery queue. |
| **LLM Provider Unreachable** | Automatic fallback to bounded deterministic template. | Notice displays: "Deterministic fallback draft (bounded)". |
| **Prompt Injection Detected** | Risk penalty (-100 points), ICP tier set to `Quarantined`, draft suppressed. | Red quarantine badge displayed; SDR notified of adversarial input. |
