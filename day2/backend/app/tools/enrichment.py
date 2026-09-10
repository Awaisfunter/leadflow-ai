"""
LeadFlow AI — Synthetic Enrichment Tool (v0)

Performs deterministic local company lookups against a controlled synthetic dataset.
The source field always identifies data as 'synthetic_internal_dataset'.
This adapter is designed to be replaced with real API adapters in production.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from ..schemas.models import EnrichedAccount, RiskFlag, VerificationStatus

logger = logging.getLogger(__name__)

_COMPANY_CACHE: dict[str, dict] | None = None


def _load_companies(data_path: str) -> dict[str, dict]:
    global _COMPANY_CACHE
    if _COMPANY_CACHE is not None:
        return _COMPANY_CACHE
    path = os.path.join(data_path, "synthetic_companies.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    _COMPANY_CACHE = {c["domain"]: c for c in data["companies"]}
    return _COMPANY_CACHE


def lookup_company(
    domain: str,
    company_name_hint: str = "",
    data_path: str = "data",
) -> Optional[EnrichedAccount]:
    """
    Look up a company by domain in the synthetic dataset.
    Returns None if not found (caller should flag ENRICHMENT_UNAVAILABLE).
    Never fabricates data.
    """
    try:
        companies = _load_companies(data_path)
    except Exception as exc:
        logger.error("Failed to load synthetic company dataset: %s", exc)
        return None

    # Exact domain match
    record = companies.get(domain.lower())

    # Fuzzy name fallback (if domain not found but company name matches)
    if record is None and company_name_hint:
        hint_lower = company_name_hint.lower()
        for d, c in companies.items():
            if hint_lower in c["company_name"].lower() or c["company_name"].lower() in hint_lower:
                record = c
                logger.info("Enrichment: name fallback match '%s' → '%s'", company_name_hint, d)
                break

    if record is None:
        logger.warning("Enrichment: no match found for domain='%s'", domain)
        return None

    return EnrichedAccount(
        domain=record["domain"],
        company_name=record["company_name"],
        employee_count=record["employee_count"],
        employee_range=record["employee_range"],
        industry=record["industry"],
        funding_stage=record["funding_stage"],
        headquarters=record["headquarters"],
        technology_signals=record.get("technology_signals", []),
        verification_status=VerificationStatus(record["verification_status"]),
        source="synthetic_internal_dataset",
        retrieved_at=datetime.now(timezone.utc),
        enrichment_available=True,
        notes=record.get("notes"),
    )


def make_unavailable_enrichment(domain: str, company_name: str) -> EnrichedAccount:
    """
    Returns a placeholder EnrichedAccount when enrichment data is unavailable.
    Never invents company facts — all unknown fields are explicitly marked.
    """
    return EnrichedAccount(
        domain=domain,
        company_name=company_name,
        employee_count=0,
        employee_range="Unknown",
        industry="Unknown",
        funding_stage="Unknown",
        headquarters="Unknown",
        technology_signals=[],
        verification_status=VerificationStatus.NOT_FOUND,
        source="synthetic_internal_dataset",
        retrieved_at=datetime.now(timezone.utc),
        enrichment_available=False,
        notes="Enrichment data not available for this domain. Human verification required.",
    )
