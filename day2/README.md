# LeadFlow AI — Bounded AI Operating System (v0)

> **Day 2 Deliverable: System Design & Working v0**  
> *Author: Awais Saeed | Applied AI Engineer Candidate*  
> *Assessment: 5-Day Remote AI OS Sprint for MUST Company*

---

## What is LeadFlow AI?
LeadFlow AI is a **bounded hybrid AI operating system** designed for B2B Revenue Operations. It automates inbound lead triage, company enrichment, deterministic ICP qualification, and personalized first-touch email drafting, while enforcing deterministic safety guardrails, commercial claim validation, and mandatory human approval before CRM dispatch.

### Target Users
- **Primary User**: Non-Developer Inbound Sales Development Representative (SDR).
- **Secondary User**: Revenue Operations Manager (RevOps).

### The Exact Bottleneck Being Solved
> *"The manual qualification and enrichment interval between inbound lead submission and approved first-touch sales action."*

In Day 1 empirical research, the manual swivel-chair workflow consumed **16 minutes 45 seconds** across 7 browser tabs. Unconstrained LLM solutions reduced time but introduced critical security, discount, and hallucination risks. LeadFlow AI delivers a qualified, verified, human-approved first-touch action in **under 1 minute**.

---

## Key Architecture Principles
LeadFlow AI strictly separates semantic tasks from deterministic rules:
- **LLM Provider**: Configurable provider adapter (configured for Gemini via `google-generativeai` or OpenRouter). Summarizes notes, extracts intent, and drafts polite first-touch outreach using *only* verified facts.
- **Deterministic Code**: Enforces Pydantic v2 schemas, looks up synthetic accounts, calculates numerical ICP scores via formula, detects prompt injection attacks, validates commercial claims, and manages the human approval state machine.
- **Offline Reliability**: If no API key is supplied or the LLM is unreachable, the system automatically uses a deterministic fallback template.
- **Security & Approval Governance**: Approvals require human action. The claim validator re-scans the final body upon approval, preventing unsafe edit bypasses.

---

## Quick Start Guide

### Prerequisites
- Python 3.11+
- Git

### 1. Install Dependencies
```bash
cd day2
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
```bash
cp .env.example .env
```
> **Note**: An API key is *optional*. If `GEMINI_API_KEY` is left blank, LeadFlow AI runs in offline mode using the deterministic fallback template. No live external connection is required to evaluate the v0.

### 3. Launch with Single Script (Windows)
Double-click `start.bat` or run:
```cmd
start.bat
```
Or start manually via Python:
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Open the SDR Dashboard
Navigate to:
```
http://localhost:8000
```
- Click the **TC-01: Enterprise Happy Path** preset button.
- Click **⚡ Process Inbound Lead**.
- Review the Lead Summary, Verified Account Enrichment, Deterministic ICP Breakdown (100/100, Tier 1), Safety Checks, and AI-Drafted First-Touch Email.
- Click **✓ Approve & Dispatch** or **✎ Edit Draft**.
- Observe the validated, synthetic CRM-ready JSON payload generated in real time.

---

## Running Automated Tests
Run the complete 27-scenario pytest suite:
```bash
cd day2
pytest backend/tests -v
```
All 27 tests validate data contracts, scoring arithmetic, tier thresholds, prompt injection detection, claim blocking, approval bypass defense, and append-only SQLite audit logging. Runtime is environment-dependent.

---

## System Structure
```
day2/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py           # FastAPI REST endpoints
│   │   ├── schemas/
│   │   │   └── models.py           # 11 Pydantic v2 data contracts
│   │   ├── services/
│   │   │   ├── audit_logger.py     # SQLite append-only audit persistence
│   │   │   ├── claim_validator.py  # Post-generation commercial claim guardrails
│   │   │   ├── icp_scorer.py       # Deterministic scoring engine & TC-03 rule
│   │   │   ├── llm_draft.py        # Configurable provider adapter + fallback
│   │   │   ├── pipeline.py         # End-to-end pipeline orchestrator
│   │   │   └── risk_detector.py    # Pre-flight injection & competitor detector
│   │   ├── tools/
│   │   │   └── enrichment.py       # Local synthetic company lookup adapter
│   │   ├── config.py               # Pydantic-settings configuration
│   │   └── main.py                 # FastAPI application entrypoint & dashboard server
│   └── tests/
│       └── test_pipeline.py        # 27 automated pytest test cases
├── data/
│   ├── business_rules.json         # Scoring points, competitor lists, blocked claims
│   ├── synthetic_companies.json    # Controlled synthetic company database
│   └── synthetic_leads.json        # Benchmark test presets
├── docs/
│   ├── architecture.md             # Full architecture with Mermaid diagrams
│   ├── data-contracts.md           # Schema documentation & failure behaviors
│   ├── tool-boundaries.md          # Tool permissions, timeouts, & prohibitions
│   ├── privacy-and-permissions.md  # Governance, SDR vs. RevOps boundaries
│   ├── evaluation.md               # PASS 1 to PASS 10 criteria
│   ├── day2-report.md              # Comprehensive Day 2 completion report
│   └── day2-ai-collaboration.md    # Engineering AI collaboration log
├── frontend/
│   └── index.html                  # Simple non-developer SDR web interface
├── logs/
│   └── audit.db                    # Append-only SQLite audit database (auto-initialized)
├── .env.example                    # Environment variable template
├── .gitignore                      # Git ignore rules for caches, secrets, & temp files
├── pytest.ini                      # Pytest runner configuration
├── README.md                       # System documentation
├── requirements.txt                # Python dependencies
├── start.bat                       # 1-click Windows startup script
└── verify_v0.py                    # Standalone happy-path verification script
```

---

## What is Simulated in v0 vs. Production
- **Enrichment**: Performed via local controlled dataset (`synthetic_internal_dataset`). No live Clearbit/Apollo API calls.
- **CRM Integration**: Produces a validated, Pydantic-verified CRM JSON payload ready for webhook dispatch. No live Salesforce/HubSpot accounts are touched.
- **Authentication**: SDR reviewer session uses `demo_user` for local evaluation.

---

## Day 2 Known Limitations & Next Steps
1. Inbound form input is evaluated synchronously in v0. Day 3 will introduce batch queue processing.
2. Inbound leads in foreign languages (e.g. German GDPR lead TC-07) receive English outreach by default unless language hints are provided. Multilingual translation will be enhanced in Day 3.
3. Pre-flight injection detection uses deterministic signature scanning. Future milestones will incorporate multi-stage semantic guardrail classifiers.
