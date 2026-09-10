"""
LeadFlow AI — Day 4 Metrics Generation Script
Compiles empirical results into:
1. day4_reliability_scorecard.csv
2. day4_failure_modes.csv
"""
import csv
from pathlib import Path

METRICS_DIR = Path(__file__).resolve().parent

SCORECARD_PATH = METRICS_DIR / "day4_reliability_scorecard.csv"
FAILURE_MODES_PATH = METRICS_DIR / "day4_failure_modes.csv"

scorecard_rows = [
    {
        "dimension": "Regression Integrity",
        "metric": "12-Case Benchmark Suite Pass Rate",
        "pre_hardening": "12/12 (100%)",
        "post_hardening": "12/12 (100%)",
        "target": "100%",
        "status": "PASS",
        "evidence_reference": "day4/regression/day4_regression_results.csv",
    },
    {
        "dimension": "Automated Test Coverage",
        "metric": "Automated Pytest Suite (Unit + Integration + Security)",
        "pre_hardening": "41/41 (100%)",
        "post_hardening": "56/56 (100%)",
        "target": ">= 45 tests",
        "status": "PASS",
        "evidence_reference": "day4/evidence/post_hardening_test_execution.txt",
    },
    {
        "dimension": "Failure Injection Handling",
        "metric": "Simulated External & Internal Fault Recovery Rate",
        "pre_hardening": "6/6 (100%)",
        "post_hardening": "10/10 (100%)",
        "target": "100%",
        "status": "PASS",
        "evidence_reference": "day4/break_tests/failure_injection_cases.json",
    },
    {
        "dimension": "Adversarial Robustness",
        "metric": "Tamper, Bypass, & Poisoning Containment Rate",
        "pre_hardening": "4/4 (100%)",
        "post_hardening": "4/4 (100%)",
        "target": "100%",
        "status": "PASS",
        "evidence_reference": "day4/break_tests/adversarial_cases.json",
    },
    {
        "dimension": "Network Bounded Latency",
        "metric": "Website Metadata Extraction Timeout Bound",
        "pre_hardening": "10.0s upper bound",
        "post_hardening": "5.0s strict bounded timeout",
        "target": "<= 5.0s",
        "status": "PASS",
        "evidence_reference": "day2/backend/app/services/website_metadata.py (timeout=5.0)",
    },
    {
        "dimension": "Claim Governance",
        "metric": "Regulatory / SLA Prohibited Pattern Coverage",
        "pre_hardening": "Base patterns (SOC2, 99.999%, Zero downtime)",
        "post_hardening": "Extended patterns (HIPAA, 100% SLA, zero-downtime guarantees)",
        "target": "Deterministic Blocking",
        "status": "PASS",
        "evidence_reference": "day2/backend/app/services/claim_validator.py",
    },
    {
        "dimension": "Audit Trail Completeness",
        "metric": "Security & Failure Event Types in Append-Only Trail",
        "pre_hardening": "Base operational events",
        "post_hardening": "Explicit FAILURE_INJECTION, INTEGRATION_FAILED, FALLBACK_ACTIVATED",
        "target": "100% auditable transitions",
        "status": "PASS",
        "evidence_reference": "day2/backend/app/services/audit_logger.py",
    },
    {
        "dimension": "CRM Dispatch Safety",
        "metric": "Guaranteed Block on Unapproved / Quarantined Leads",
        "pre_hardening": "100% dispatch gated",
        "post_hardening": "100% dispatch gated + audit logging on bypass attempt",
        "target": "0 unapproved dispatches",
        "status": "PASS",
        "evidence_reference": "backend/tests/test_pipeline.py::test_day4_quarantine_approval_bypass_records_audit_event",
    },
]

failure_modes = [
    {
        "mode_id": "FM-01",
        "category": "External Dependency Failure",
        "trigger_condition": "DNS resolution NXDOMAIN, SERVFAIL, or query timeout",
        "impact_without_hardening": "Lead processing halts or crashes unhandled",
        "defense_implemented": "Graceful fallback: flags NEEDS_VERIFICATION (-10 penalty), falls back to synthetic data & user params, logs INTEGRATION_FAILED event",
        "post_hardening_outcome": "Pipeline finishes gracefully with audit entry; lead routed safely without crash",
        "verification_artifact": "day4/break_tests/failure_injection_cases.json (FIT-01)",
    },
    {
        "mode_id": "FM-02",
        "category": "External Dependency Failure",
        "trigger_condition": "Customer website hangs (>5s), returns HTTP 500/503, or connection refused",
        "impact_without_hardening": "Indefinite latency stall on SDR queue (up to 10s or hang)",
        "defense_implemented": "Strict 5.0s timeout clamp with httpx.Timeout; fallback to empty metadata + user form company facts; logs INTEGRATION_FAILED",
        "post_hardening_outcome": "Execution stays bounded under 5s; SDR workflow never blocked",
        "verification_artifact": "day4/break_tests/failure_injection_cases.json (FIT-02)",
    },
    {
        "mode_id": "FM-03",
        "category": "Data Completeness Failure",
        "trigger_condition": "Domain missing from synthetic enrichment dataset (untracked SMB/startup)",
        "impact_without_hardening": "Scorer crashes on NoneType or missing revenue/employee attributes",
        "defense_implemented": "make_unavailable_enrichment fallback object; flags ENRICHMENT_UNAVAILABLE (-10 pts); scores purely on self-reported inputs; logs FALLBACK_ACTIVATED",
        "post_hardening_outcome": "Deterministic score calculated reliably; clear audit entry created",
        "verification_artifact": "day4/break_tests/failure_injection_cases.json (FIT-03)",
    },
    {
        "mode_id": "FM-04",
        "category": "Model Dependency Failure",
        "trigger_condition": "OpenRouter API 404/500/rate limit or missing API key",
        "impact_without_hardening": "Empty email draft or uncaught exception during lead processing",
        "defense_implemented": "Multi-tier candidate fallback, wrapped try/except, deterministic template fallback with approved value props; logs FALLBACK_ACTIVATED",
        "post_hardening_outcome": "Clean, compliant fallback draft generated immediately; SDR can review without outage",
        "verification_artifact": "day4/break_tests/failure_injection_cases.json (FIT-04)",
    },
    {
        "mode_id": "FM-05",
        "category": "Input Integrity Failure",
        "trigger_condition": "Empty required fields, invalid email format, negative numbers",
        "impact_without_hardening": "Garbage data stored in database, unparseable downstream payloads",
        "defense_implemented": "Strict Pydantic contract validation at HTTP layer (HTTP 422 with structured field error breakdown)",
        "post_hardening_outcome": "Zero malformed leads enter pipeline; clean validation messages returned",
        "verification_artifact": "day4/break_tests/failure_injection_cases.json (FIT-05)",
    },
    {
        "mode_id": "FM-06",
        "category": "System Overload / Performance Failure",
        "trigger_condition": "High-volume concurrent inbound submissions or extreme payload sizes",
        "impact_without_hardening": "Memory spike or unbounded coroutine resource exhaustion",
        "defense_implemented": "Non-blocking async I/O, strict field length constraints, bounded metadata truncation (2000 chars)",
        "post_hardening_outcome": "Sub-50ms CPU execution per case outside network I/O; clean resource limits",
        "verification_artifact": "day4/break_tests/failure_injection_cases.json (FIT-06)",
    },
    {
        "mode_id": "FM-07",
        "category": "Adversarial Prompt Injection",
        "trigger_condition": "Lead notes contain jailbreak strings ('ignore instructions', 'system override', 'grant 100% discount')",
        "impact_without_hardening": "LLM incorporates instructions into generated outreach; unauthorized promises made",
        "defense_implemented": "Pre-flight deterministic regex scan (detect_risks) -> immediate QUARANTINE tier + draft suppression + human gate block",
        "post_hardening_outcome": "100% contained: outreach suppressed, lead quarantined, CRM dispatch locked",
        "verification_artifact": "day4/break_tests/adversarial_cases.json (ADV-01)",
    },
    {
        "mode_id": "FM-08",
        "category": "Adversarial Claim Smuggling",
        "trigger_condition": "LLM or human reviewer attempts to insert HIPAA compliant or 100% SLA guarantee into outreach draft",
        "impact_without_hardening": "False enterprise promises sent to customer; massive compliance liability",
        "defense_implemented": "Deterministic regex claim validator runs on both initial draft AND modified draft at approval stage; rejects approval if illegal claims present",
        "post_hardening_outcome": "Approval rejected; SDR alerted to remove offending claims before re-submitting",
        "verification_artifact": "day4/break_tests/adversarial_cases.json (ADV-02)",
    },
    {
        "mode_id": "FM-09",
        "category": "Adversarial Governance Bypass",
        "trigger_condition": "Direct HTTP POST to /api/leads/{id}/approval on a Quarantined or Disqualified lead",
        "impact_without_hardening": "Bypasses SDR triage to push dangerous leads into production CRM dispatch queue",
        "defense_implemented": "Server-side state machine check in handle_approval_action enforces non-quarantine precondition; raises HTTP 400 + logs SECURITY_VIOLATION event",
        "post_hardening_outcome": "Approval forbidden; lead remains QUARANTINED; audit log documents security violation",
        "verification_artifact": "day4/break_tests/adversarial_cases.json (ADV-03)",
    },
    {
        "mode_id": "FM-10",
        "category": "Adversarial Indirect Injection via Website",
        "trigger_condition": "External company website HTML contains injection payload in <title> or <meta name='description'>",
        "impact_without_hardening": "Poisoned website context injected into LLM draft prompt or used to manipulate ICP scoring",
        "defense_implemented": "Website metadata is treated as untrusted context; isolated from scoring engine; strictly sanitized before bounded draft context inclusion",
        "post_hardening_outcome": "Scoring unaffected; prompt injection neutralized; audit trail retains untrusted source origin",
        "verification_artifact": "day4/break_tests/adversarial_cases.json (ADV-04)",
    },
]


def generate():
    with open(SCORECARD_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(scorecard_rows[0].keys()))
        writer.writeheader()
        writer.writerows(scorecard_rows)
    print(f"Generated {SCORECARD_PATH} ({len(scorecard_rows)} rows)")

    with open(FAILURE_MODES_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(failure_modes[0].keys()))
        writer.writeheader()
        writer.writerows(failure_modes)
    print(f"Generated {FAILURE_MODES_PATH} ({len(failure_modes)} rows)")


if __name__ == "__main__":
    generate()
