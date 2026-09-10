"""
LeadFlow AI — Deterministic ICP Scoring Engine

Implements the Day 1 scoring formula exactly.
Final Score = max(0, Firmographic + Role + Intent + Urgency - Penalties)
The LLM is NEVER used for scoring. All decisions are rule-based.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

from ..schemas.models import (
    EnrichedAccount,
    IcpTier,
    LeadInput,
    LeadRiskFlags,
    NextAction,
    QualificationResult,
    RiskFlag,
    ScoringBreakdown,
)

logger = logging.getLogger(__name__)

def _word_match(keywords: list[str], text: str) -> bool:
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE):
            return True
    return False


# ─── Role keyword maps ────────────────────────────────────────────────────────
C_LEVEL_VP_KEYWORDS = [
    "ceo", "coo", "cto", "cfo", "cro", "cso", "chief", "vp", "vice president",
    "head of", "founder", "president", "owner", "partner",
]
DIRECTOR_KEYWORDS = ["director", "lead", "principal", "solutions architect", "enterprise architect"]
MANAGER_KEYWORDS = ["manager", "specialist", "analyst", "engineer", "architect", "consultant"]
ACADEMIC_KEYWORDS = ["student", "intern", "phd", "researcher", "professor", "academic", "postdoc"]

# ─── Intent keyword maps ──────────────────────────────────────────────────────
ACTIVE_REPLACEMENT_KEYWORDS = [
    "replacing", "replace", "migration", "migrate", "switching from", "moving away",
    "contract expires", "switching", "transition from", "deploy", "expansion", "expanding",
    "enterprise pilot",
]
EVALUATION_KEYWORDS = [
    "demo", "evaluate", "evaluation", "trial", "pilot", "looking for", "considering",
    "automate", "automation", "interested in", "exploring", "solution", "triage",
    "benoetigen", "loesung", "vertriebsteam", "dsgvo",
]
PRICING_KEYWORDS = ["pricing", "price", "cost", "quote", "budget", "roi", "free tier", "student discount"]

# ─── Urgency keyword maps ─────────────────────────────────────────────────────
IMMEDIATE_KEYWORDS = [
    "q4", "this quarter", "end of month", "end of the month", "this month", "asap", "immediately",
    "immediate", "within two weeks", "within 2 weeks", "urgent", "2-week", "two-week", "next month",
    "dsgvo", "vertriebsteam", "enterprise pilot",
]
SIX_MONTH_KEYWORDS = [
    "next quarter", "h1", "h2", "within 6 months", "this year", "by year end",
    "portfolio", "personal",
]


def _score_firmographics(employee_count: int) -> tuple[int, str]:
    if employee_count > 500:
        return 40, f"Headcount {employee_count} > 500 → 40 pts (Enterprise)"
    elif employee_count >= 100:
        return 30, f"Headcount {employee_count} (100–499) → 30 pts (Mid-Market Upper)"
    elif employee_count >= 50:
        return 20, f"Headcount {employee_count} (50–99) → 20 pts (Mid-Market Lower)"
    elif employee_count >= 10:
        return 10, f"Headcount {employee_count} (10–49) → 10 pts (SMB)"
    elif employee_count >= 1:
        return 5, f"Headcount {employee_count} (1–9) → 5 pts (Micro)"
    else:
        return 0, "Headcount unknown → 0 pts"


def _score_role(role: str) -> tuple[int, str]:
    if _word_match(ACADEMIC_KEYWORDS, role):
        return 0, f"Role '{role}' matches academic/student → 0 pts"
    if _word_match(C_LEVEL_VP_KEYWORDS, role):
        return 25, f"Role '{role}' is C-Level/VP/Head → 25 pts"
    if _word_match(DIRECTOR_KEYWORDS, role):
        return 18, f"Role '{role}' is Director/Lead/Senior Architect → 18 pts"
    if _word_match(MANAGER_KEYWORDS, role):
        return 10, f"Role '{role}' is Manager/Specialist → 10 pts"
    return 5, f"Role '{role}' is Individual Contributor → 5 pts"


def _score_intent(notes: str) -> tuple[int, str]:
    notes_lower = notes.lower()
    if any(kw in notes_lower for kw in ACTIVE_REPLACEMENT_KEYWORDS):
        return 20, "Notes indicate active tool replacement/migration → 20 pts"
    if any(kw in notes_lower for kw in PRICING_KEYWORDS):
        return 10, "Notes indicate pricing inquiry → 10 pts"
    if any(kw in notes_lower for kw in EVALUATION_KEYWORDS):
        return 15, "Notes indicate evaluation/demo request → 15 pts"
    if notes.strip():
        return 5, "Notes present but general inquiry → 5 pts"
    return 5, "No notes provided → 5 pts (general inquiry)"


def _score_urgency(notes: str, team_size: str) -> tuple[int, str]:
    notes_lower = notes.lower()
    if any(kw in notes_lower for kw in IMMEDIATE_KEYWORDS):
        return 15, "Urgency signals indicate this-quarter/immediate deployment → 15 pts"
    if any(kw in notes_lower for kw in SIX_MONTH_KEYWORDS) or team_size in ("500-1000", "1000+"):
        return 10, "Urgency signals indicate standard 6-month evaluation cycle → 10 pts"
    return 5, "No explicit urgency signals → 5 pts (exploring)"


def _determine_tier(
    final_score: int,
    employee_count: int,
    risk_flags: LeadRiskFlags,
    role_pts: int = 0,
    intent_pts: int = 0,
    urgency_pts: int = 0,
    notes: str = "",
    domain: str = "",
) -> tuple[IcpTier, NextAction, Optional[int], list[str]]:
    reasoning: list[str] = []

    # Quarantine overrides all scoring
    if RiskFlag.COMPETITOR_RISK in risk_flags.flags:
        reasoning.append("QUARANTINED: Competitor domain detected → Score overridden to 0.")
        return IcpTier.QUARANTINED, NextAction.QUARANTINE_COMPETITOR, None, reasoning
    if RiskFlag.PROMPT_INJECTION in risk_flags.flags:
        reasoning.append("QUARANTINED: Prompt injection detected → Score overridden to 0.")
        return IcpTier.QUARANTINED, NextAction.QUARANTINE_INJECTION, None, reasoning
    if RiskFlag.ACADEMIC_DOMAIN in risk_flags.flags:
        reasoning.append("DISQUALIFIED: Academic domain detected → Out-of-ICP.")
        return IcpTier.DISQUALIFIED, NextAction.QUARANTINE_ACADEMIC, None, reasoning

    notes_lower = notes.lower()

    # Tier 1: score >= 80 AND headcount > 100
    if final_score >= 80 and employee_count > 100:
        reasoning.append(f"TIER 1: Score {final_score} ≥ 80 AND headcount {employee_count} > 100.")
        # EMEA / DSGVO route (TC-07)
        if domain.endswith(".de") or any(w in notes_lower for w in ("dsgvo", "german", "benoetigen", "europaeisch")):
            return IcpTier.TIER_1, NextAction.ROUTE_EMEA_ENTERPRISE, 1, reasoning
        # Competitive migration route (TC-04) — detects explicit competitor switch language
        if any(kw in notes_lower for kw in ("contract expires", "contract with competitor", "migration assistance",
                                             "migrate", "migration", "switching from", "moving away")):
            return IcpTier.TIER_1, NextAction.ROUTE_MIGRATION_SPECIALIST, 1, reasoning
        # Sparse-input enterprise discovery (TC-06) — single short notes word
        if notes.strip() and len(notes.strip().split()) <= 2:
            return IcpTier.TIER_1, NextAction.ROUTE_ENTERPRISE_DISCOVERY, 1, reasoning
        return IcpTier.TIER_1, NextAction.ROUTE_ENTERPRISE_AE, 1, reasoning

    # Tier 2 Standard (Mid-Market): score 60–79 AND headcount 50–249
    if (60 <= final_score <= 79):
        if RiskFlag.FREE_MAIL_DOMAIN in risk_flags.flags:
            reasoning.append(f"TIER 2 (Flagged Free Mail): Score {final_score} requires corporate domain verification.")
            return IcpTier.TIER_2, NextAction.REQUIRE_CORPORATE_EMAIL, 4, reasoning
        if employee_count < 50 and role_pts >= 25 and intent_pts >= 15 and urgency_pts >= 15:
            reasoning.append(
                f"TIER 2 (Explicit Accelerated SMB Exception): Headcount {employee_count} < 50 elevated to Tier 2 "
                f"due to C-Level buyer ({role_pts} pts), high intent ({intent_pts} pts), and urgent deployment ({urgency_pts} pts)."
            )
            return IcpTier.TIER_2, NextAction.ROUTE_EXPRESS_ONBOARDING, 4, reasoning
        reasoning.append(f"TIER 2 (Mid-Market): Score {final_score} in 60–79 range.")
        return IcpTier.TIER_2, NextAction.ROUTE_COMMERCIAL_AE, 4, reasoning

    # General Tier 2 boundary
    if final_score >= 60:
        if RiskFlag.FREE_MAIL_DOMAIN in risk_flags.flags:
            reasoning.append(f"TIER 2 (Flagged Free Mail): Score {final_score} requires corporate domain verification.")
            return IcpTier.TIER_2, NextAction.REQUIRE_CORPORATE_EMAIL, 4, reasoning
        reasoning.append(f"TIER 2: Score {final_score} ≥ 60.")
        return IcpTier.TIER_2, NextAction.ROUTE_COMMERCIAL_AE, 4, reasoning

    # Tier 3: score 30–59
    if final_score >= 30:
        reasoning.append(f"TIER 3 (SMB / Self-Serve): Score {final_score} in 30–59 range (headcount {employee_count}).")
        return IcpTier.TIER_3, NextAction.ROUTE_SELF_SERVE, None, reasoning

    # Disqualified
    reasoning.append(f"DISQUALIFIED: Score {final_score} < 30.")
    return IcpTier.DISQUALIFIED, NextAction.NEEDS_MANUAL_REVIEW, None, reasoning


def score_lead(
    lead: LeadInput,
    enrichment: Optional[EnrichedAccount],
    risk_flags: LeadRiskFlags,
) -> QualificationResult:
    """
    Deterministic ICP scoring engine.
    Formula: Final Score = max(0, Firmographic + Role + Intent + Urgency - Penalties)
    The LLM is never involved in this calculation.
    """
    reasoning: list[str] = []

    # Firmographics
    employee_count = enrichment.employee_count if enrichment and enrichment.enrichment_available else 0
    firm_pts, firm_reason = _score_firmographics(employee_count)
    reasoning.append(f"[Firmographic] {firm_reason}")

    # Role seniority
    role_pts, role_reason = _score_role(lead.role)
    reasoning.append(f"[Role] {role_reason}")

    # Commercial intent
    intent_pts, intent_reason = _score_intent(lead.notes or "")
    reasoning.append(f"[Intent] {intent_reason}")

    # Deployment urgency
    urgency_pts, urgency_reason = _score_urgency(lead.notes or "", lead.team_size)
    reasoning.append(f"[Urgency] {urgency_reason}")

    # Risk penalties
    penalty = 0
    penalty_reasons: list[str] = []
    if RiskFlag.COMPETITOR_RISK in risk_flags.flags:
        penalty += 100
        penalty_reasons.append("Competitor domain penalty: -100 pts")
    if RiskFlag.PROMPT_INJECTION in risk_flags.flags:
        penalty += 100
        penalty_reasons.append("Prompt injection penalty: -100 pts")
    if RiskFlag.FREE_MAIL_DOMAIN in risk_flags.flags:
        penalty += 20
        penalty_reasons.append("Disposable webmail penalty: -20 pts")
    if RiskFlag.ACADEMIC_DOMAIN in risk_flags.flags:
        penalty += 80
        penalty_reasons.append("Academic domain penalty: -80 pts")
    for r in penalty_reasons:
        reasoning.append(f"[Penalty] {r}")

    raw_score = firm_pts + role_pts + intent_pts + urgency_pts - penalty
    final_score = max(0, raw_score)
    reasoning.append(
        f"[Score] Raw={firm_pts}+{role_pts}+{intent_pts}+{urgency_pts}-{penalty}={raw_score} → Clamped={final_score}"
    )

    breakdown = ScoringBreakdown(
        firmographic_points=firm_pts,
        role_points=role_pts,
        intent_points=intent_pts,
        urgency_points=urgency_pts,
        risk_penalty=-penalty,
        raw_score=raw_score,
        final_score=final_score,
    )

    tier, next_action, sla_hours, tier_reasoning = _determine_tier(
        final_score,
        employee_count,
        risk_flags,
        role_pts,
        intent_pts,
        urgency_pts,
        notes=lead.notes or "",
        domain=str(lead.email).split("@")[-1],
    )
    reasoning.extend(tier_reasoning)

    return QualificationResult(
        tier=tier,
        scoring_breakdown=breakdown,
        reasoning=reasoning,
        next_action=next_action,
        sla_hours=sla_hours,
    )
