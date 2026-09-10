"""
LeadFlow AI — Pre-flight Risk Detector

Performs deterministic signature-based risk detection on untrusted lead input.
This is v0 initial detection only — not a complete security solution.
"""
from __future__ import annotations

import json
import logging
import os
import re

from ..schemas.models import LeadInput, LeadRiskFlags, RiskFlag

logger = logging.getLogger(__name__)

# Competitor domains loaded from business_rules.json
_COMPETITOR_DOMAINS: list[str] = []
_ACADEMIC_TLD: list[str] = []
_WEBMAIL_DOMAINS: list[str] = []
_INJECTION_SIGNATURES: list[str] = []
_RULES_LOADED = False


def _load_rules(data_path: str = "data") -> None:
    global _COMPETITOR_DOMAINS, _ACADEMIC_TLD, _WEBMAIL_DOMAINS, _INJECTION_SIGNATURES, _RULES_LOADED
    if _RULES_LOADED:
        return
    try:
        path = os.path.join(data_path, "business_rules.json")
        with open(path, encoding="utf-8") as f:
            rules = json.load(f)
        _COMPETITOR_DOMAINS = rules["competitor_domains"]
        _ACADEMIC_TLD = rules["academic_domains"]
        _WEBMAIL_DOMAINS = rules["disposable_webmail_domains"]
        _INJECTION_SIGNATURES = rules["prompt_injection_signatures"]
        _RULES_LOADED = True
    except Exception as exc:
        logger.error("Failed to load business rules: %s", exc)
        # Fallback minimal rules
        _COMPETITOR_DOMAINS = ["competitorsaas.com"]
        _ACADEMIC_TLD = [".edu"]
        _WEBMAIL_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com"]
        _INJECTION_SIGNATURES = ["ignore previous instructions", "system override"]
        _RULES_LOADED = True


def detect_risks(lead: LeadInput, data_path: str = "data") -> LeadRiskFlags:
    """
    Deterministic pre-flight risk detection.
    Treats all lead fields as untrusted customer input.
    Returns LeadRiskFlags with all detected signals.
    """
    _load_rules(data_path)
    flags = LeadRiskFlags()
    domain = lead.email.split("@")[-1].lower()

    # 1. Competitor domain check
    if domain in _COMPETITOR_DOMAINS:
        flags.add_flag(RiskFlag.COMPETITOR_RISK)
        flags.requires_quarantine = True
        logger.warning("Risk: Competitor domain detected - %s", domain)

    # 2. Academic domain check
    if any(domain.endswith(tld) or tld in domain for tld in _ACADEMIC_TLD):
        flags.add_flag(RiskFlag.ACADEMIC_DOMAIN)
        flags.requires_quarantine = True
        logger.warning("Risk: Academic domain detected - %s", domain)

    # 3. Disposable webmail
    if domain in _WEBMAIL_DOMAINS:
        flags.add_flag(RiskFlag.FREE_MAIL_DOMAIN)
        flags.requires_human_review = True
        logger.info("Risk: Free webmail domain — %s", domain)

    # 4. Prompt injection in notes
    notes_lower = (lead.notes or "").lower()
    detected_sigs: list[str] = []
    for sig in _INJECTION_SIGNATURES:
        try:
            if re.search(sig, notes_lower, re.IGNORECASE):
                detected_sigs.append(sig)
        except re.error:
            if sig.lower() in notes_lower:
                detected_sigs.append(sig)

    if detected_sigs:
        flags.prompt_injection_detected = True
        flags.injection_signatures_found = detected_sigs
        flags.add_flag(RiskFlag.PROMPT_INJECTION)
        flags.requires_quarantine = True
        logger.warning("Risk: Prompt injection signatures detected: %s", detected_sigs)

    # 5. Sparse input check
    total_content = len((lead.notes or "").strip()) + len(lead.role.strip())
    if total_content < 10:
        flags.add_flag(RiskFlag.SPARSE_INPUT)
        flags.confidence_note = "Very sparse input — enrichment-dependent qualification."
        logger.info("Risk: Sparse input detected for lead %s", lead.email)

    # Set human review for all flagged leads
    if flags.flags:
        flags.requires_human_review = True

    return flags


def extract_domain(email: str) -> str:
    """Extract domain from email address."""
    return email.split("@")[-1].lower()


def is_corporate_domain(domain: str, data_path: str = "data") -> bool:
    """Returns True if domain is NOT a webmail provider."""
    _load_rules(data_path)
    return domain not in _WEBMAIL_DOMAINS
