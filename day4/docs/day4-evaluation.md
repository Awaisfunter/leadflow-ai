# Day 4 — Evaluation Framework & Methodology
## LeadFlow AI Reliability and Quality Assessment
**Author:** Awais Saeed | Applied AI Engineer Candidate  
**Date:** 2026-09-08  

---

## 1. Evaluation Methodology

LeadFlow AI was evaluated using a four-tier framework to ensure objective, reproducible results:

```
[Level 1: Unit & Schema Validation]
  56 automated pytest and functional regression tests (pytest backend/tests/test_pipeline.py)
        ↓
[Level 2: 12-Case Benchmark Suite]
  Day 1 benchmark cases tested against live operating system (run_12_case_benchmark.py)
        ↓
[Level 3: Deliberate Failure Injection]
  10 break tests targeting edge cases, malicious attacks, and timeouts (run_break_tests.py)
        ↓
[Level 4: Proxy SDR Workflow Evaluation]
  Human-in-the-loop decision testing and state machine audit (run_proxy_sdr_evaluation.py)
```

---

## 2. Evaluation Metrics & Formulas

### Quality Metrics
1. **Benchmark Pass Rate:**
   $$\text{Pass Rate} = \frac{\text{Cases with Tier, Score, and Route Match}}{\text{Total Benchmark Cases}} = \frac{12}{12} = 1.0 \text{ (100.0\%)}$$

2. **Route Accuracy:**
   $$\text{Route Accuracy} = \frac{\text{Correctly Routed Cases}}{\text{Total Benchmark Cases}} = \frac{12}{12} = 1.0 \text{ (100.0\%)}$$

3. **Tier Accuracy:**
   $$\text{Tier Accuracy} = \frac{\text{Correctly Categorized Tier Cases}}{\text{Total Benchmark Cases}} = \frac{12}{12} = 1.0 \text{ (100.0\%)}$$

4. **Claim Safety Rate:**
   $$\text{Claim Safety Rate} = \frac{\text{Drafts Passing Commercial Policy}}{\text{Total Drafts Generated}} = \frac{9}{9} = 1.0 \text{ (100.0\%)}$$

   *Note: Denominator is 9 actual drafts generated (TC-01 through TC-08, plus TC-11), excluding TC-09, TC-10, TC-12 which were quarantined/suppressed before draft generation.*

5. **Controlled Failure Rate:**
   $$\text{Controlled Failure Rate} = \frac{\text{Failure Injections Exhibiting Graceful Degradation}}{\text{Total Injected Failures}} = \frac{10}{10} = 1.0 \text{ (100.0\%)}$$

6. **Pre-Approval Leakage Rate:**
   $$\text{Leakage Rate} = \frac{\text{Pre-Approval Leads with dispatch\_authorized = True}}{\text{Total Ingested Leads}} = \frac{0}{12} = 0.0 \text{ (0.0\%)}$$

---

## 3. Pre-Hardening Baseline vs Post-Hardening State

| Dimension | Pre-Hardening Baseline | Post-Hardening State | Hardening Verification |
|---|---|---|---|
| **Automated Tests** | 41 passed | 56 passed | +15 security, timeout, and approval regression tests |
| **Failure Cases Handled** | 6 evaluated | 10 evaluated (10/10 passed) | Full FC-01 through FC-10 coverage |
| **Website Timeout** | Indeterminate / 8.0s | Bounded 5.0s max | Fast-fail connect, single-attempt on HTTPS timeout |
| **LLM Fallback Audit** | Fallback worked without audit event | `FALLBACK_ACTIVATED` event logged | Full SQLite telemetry tracking |
| **Claim Safety** | Basic discount rules | Full HIPAA + SLA + discount rules | Blocks promises before and during approval |
| **Approval Security** | Implicit dashboard filter | Explicit backend invariant | Direct approval of quarantined leads blocked |
| **CRM Dispatch Gating** | Implicit | Explicit state machine + UI lock | Pre: `PREVIEW_ONLY` / Post: `APPROVED_FOR_DISPATCH` |

---

## 4. Remaining Operational Boundaries

- **External Host Responsiveness:** Website and DNS checks depend on external server performance; timeouts ensure bounded latency (< 5.0s), but network conditions vary.
- **Evaluation Environment Cost Tracking:** Evaluation runs were performed locally without billable API vendor costs (`NOT_MEASURED`).
- **Semantic Evasion:** Advanced semantic prompt injections may require continuous adversarial dictionary updates.
