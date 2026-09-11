# LeadFlow AI — Day 2 AI Collaboration Record

This document records the human-AI engineering collaboration during Day 2 of the 5-Day Remote AI OS Sprint.

---

## 1. AI Assistance Used
- **Primary AI Pairing Model**: Antigravity Applied AI Assistant (Google DeepMind).
- **Engineering Roles Delegated**:
  - Code scaffolding of Pydantic v2 schemas and FastAPI routing structure.
  - Implementation of deterministic scoring and claim validation logic according to Day 1 rules.
  - Generation of comprehensive pytest suites covering edge and failure scenarios.
  - Creation of architectural documentation and Mermaid diagrams.

---

## 2. Engineering Decisions Retained by the Human Engineer
1. **Strict Separation of Concerns**: Enforced that LLMs are never granted authority over numerical scoring, company headcount, or CRM state machines.
2. **Deterministic Mathematical Clamping**: Mandated the use of `max(0, Raw_Score)` to prevent negative scores under heavy risk penalties.
3. **Synthetic Source Attribution**: Enforced that all mock data explicitly states `"synthetic_internal_dataset"` to prevent fabricated API claims.
4. **Offline Resilience**: Required an automatic deterministic template fallback. The deterministic template fallback allows the core workflow to continue when the LLM provider is unavailable, credentials are not configured, or the system is operating without the external LLM dependency.
5. **Human Approval Gate**: Required that approval and dispatch states cannot be reached autonomously without human confirmation.

---

## 3. What Was Reviewed, Modified, or Rejected
- **Rejected**: Initial proposals to use an unconstrained LLM prompt to "score the lead from 1–100". Replaced with pure Python deterministic calculation.
- **Reviewed & Modified**: Ensured prompt injection detection treats customer notes as passive context rather than executable instructions.
- **Added**: Added explicit claim validation rules blocking unverified enterprise certifications (e.g. ISO 27001) and unauthorized discounts.
