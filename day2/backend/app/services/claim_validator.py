"""
LeadFlow AI — Deterministic Claim Validator (v0)

Post-generation guardrail that validates first-touch email drafts against
prohibited commercial claims, hallucinated certifications, unauthorized discounts,
and unapproved commitments.
"""
from __future__ import annotations

import json
import logging
import os
import re

from ..schemas.models import ClaimValidationResult

logger = logging.getLogger(__name__)

# Default blocked and warning patterns
DEFAULT_BLOCKED_PATTERNS = [
    r"\$\d+[kK]?\s*(?:off|discount|free|credit|rebate)",
    r"\b\d+%\s*discount\b",
    r"(?i)\b(?:guaranteed|guarantee|commit|promise)\b.*\b(?:implementation|deployment)\b",
    r"(?i)\bcertified\b.*\biso\b",
    r"(?i)\biso\s*\d{4,5}\b",
    r"(?i)\bsoc\s*2\s*type\s*ii\b",
    r"(?i)\bg2\s*leader\b",
    r"(?i)\bgartner\s*magic\s*quadrant\b",
    r"(?i)\b100%\s*uptime\s*guarantee\b",
    r"(?i)\b\d+(?:\.\d+)?%\s*(?:uptime|sla)\b",
    r"(?i)\bhipaa\s*(?:certified|certification|compliant|compliance)\b",
    r"(?i)\bunlimited\s*users?\s*free\b",
    r"(?i)\bmoney[- ]back\s*guarantee\b",
    r"(?i)\bguaranteed\s*roi\b",
    r"(?i)\bexclusive\s*\d+%\s*discount\b",
    r"(?i)\b(?:unconditional|guaranteed)\s*\d+%\s*discount\b",
]

DEFAULT_WARNING_PATTERNS = [
    r"(?i)\bbest[- ]in[- ]class\b",
    r"(?i)\bindustry[- ]leading\b",
    r"(?i)\bguaranteed\s*results\b",
    r"(?i)\bproven\s*roi\b",
]

_RULES_LOADED = False
_BLOCKED_PATTERNS = DEFAULT_BLOCKED_PATTERNS
_WARNING_PATTERNS = DEFAULT_WARNING_PATTERNS


def _load_claim_rules(data_path: str = "data") -> None:
    global _RULES_LOADED, _BLOCKED_PATTERNS, _WARNING_PATTERNS
    if _RULES_LOADED:
        return
    try:
        path = os.path.join(data_path, "business_rules.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                rules = json.load(f)
            claim_rules = rules.get("claim_validation", {})
            _BLOCKED_PATTERNS = claim_rules.get("blocked_patterns", DEFAULT_BLOCKED_PATTERNS)
            _WARNING_PATTERNS = claim_rules.get("warning_patterns", DEFAULT_WARNING_PATTERNS)
        _RULES_LOADED = True
    except Exception as e:
        logger.warning(f"Could not load custom claim validation rules: {e}. Using defaults.")
        _RULES_LOADED = True


def validate_draft(
    subject: str,
    body: str,
    data_path: str = "data"
) -> ClaimValidationResult:
    """
    Deterministically scans subject and body for unauthorized commercial claims.
    Returns ClaimValidationResult.
    """
    _load_claim_rules(data_path)
    combined_text = f"{subject}\n{body}"

    blocked_detected: list[str] = []
    warnings_detected: list[str] = []

    # Check blocked patterns
    for pattern in _BLOCKED_PATTERNS:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            blocked_detected.append(
                f"Blocked claim detected: '{match.group(0)}' violates commercial commitment policy."
            )

    # Check warning patterns
    for pattern in _WARNING_PATTERNS:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            warnings_detected.append(
                f"Advisory: '{match.group(0)}' is subjective marketing language. Human review advised."
            )

    is_passed = len(blocked_detected) == 0
    requires_human = len(blocked_detected) > 0 or len(warnings_detected) > 0

    return ClaimValidationResult(
        passed=is_passed,
        warnings=warnings_detected,
        blocked_claims=blocked_detected,
        requires_human_review=requires_human
    )
