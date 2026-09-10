"""
LeadFlow AI — Real Domain Verification Tool (Day 3)

Performs an actual DNS-over-HTTPS (DoH) lookup via Cloudflare's public resolver
(https://cloudflare-dns.com/dns-query) to verify whether a company domain resolves.

Security boundaries:
- No proprietary credentials required.
- Only A-record resolution is checked — no recursive crawling.
- Returns structured DomainVerificationResult. Never trusts DNS text content.
- Website page content is NOT fetched here — that is the website_metadata tool's job.
- Failures produce structured fallback results, never crash the pipeline.

Data provenance: source = "public_dns" always.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Optional

import httpx

from ..schemas.models import DomainVerificationResult

logger = logging.getLogger(__name__)

# Cloudflare DNS-over-HTTPS endpoint (public, no auth required)
_DOH_ENDPOINT = "https://cloudflare-dns.com/dns-query"
_DEFAULT_TIMEOUT = 5.0   # seconds
_MAX_RETRIES = 2

# Simple domain syntax regex (does not guarantee registrability, just basic validity)
_DOMAIN_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)


def _is_valid_domain_syntax(domain: str) -> bool:
    """Check basic domain syntax without making any network call."""
    if not domain or len(domain) > 253:
        return False
    return bool(_DOMAIN_RE.match(domain))


async def verify_domain(
    domain: str,
    timeout: float = _DEFAULT_TIMEOUT,
    max_retries: int = _MAX_RETRIES,
) -> DomainVerificationResult:
    """
    Perform a real DNS-over-HTTPS A-record lookup for the given domain.

    Returns a DomainVerificationResult with:
      - status: VERIFIED | UNRESOLVED | INVALID_SYNTAX | ERROR
      - dns_resolves: True only if Cloudflare DoH confirms at least one A record
      - ip_addresses: list of resolved IPs (empty on failure)
      - source: always "public_dns"
      - latency_ms: actual measured roundtrip
    """
    # Step 1: syntax check (no network needed)
    if not _is_valid_domain_syntax(domain):
        logger.info("Domain syntax invalid, skipping DNS lookup: %s", domain)
        return DomainVerificationResult(
            domain=domain,
            valid_syntax=False,
            dns_resolves=False,
            status="INVALID_SYNTAX",
            error_code="INVALID_SYNTAX",
            error_message=(
                f"The domain '{domain}' does not have valid DNS name syntax. "
                "Please verify the company domain before approving this lead."
            ),
        )

    # Step 2: real DoH lookup with retry
    last_error: Optional[str] = None
    last_error_code: Optional[str] = None

    for attempt in range(1, max_retries + 2):
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=3.0, read=timeout, write=3.0, pool=3.0),
                follow_redirects=False,
            ) as client:
                resp = await client.get(
                    _DOH_ENDPOINT,
                    params={"name": domain, "type": "A"},
                    headers={"Accept": "application/dns-json"},
                )
            elapsed_ms = int((time.perf_counter() - t0) * 1000)

            if resp.status_code != 200:
                last_error = f"DoH resolver returned HTTP {resp.status_code}"
                last_error_code = f"DOH_HTTP_{resp.status_code}"
                logger.warning("DoH HTTP error for %s: %s", domain, resp.status_code)
                continue

            data = resp.json()
            # RFC 8484 / Cloudflare DoH: NOERROR=0, NXDOMAIN=3
            rcode = data.get("Status", -1)
            answers = data.get("Answer", [])
            a_records = [
                a["data"] for a in answers if a.get("type") == 1  # type 1 = A record
            ]

            if rcode == 0 and a_records:
                logger.info(
                    "DNS VERIFIED for %s: %s IPs in %dms", domain, a_records, elapsed_ms
                )
                return DomainVerificationResult(
                    domain=domain,
                    valid_syntax=True,
                    dns_resolves=True,
                    ip_addresses=a_records,
                    record_type="A",
                    status="VERIFIED",
                    latency_ms=elapsed_ms,
                )
            elif rcode == 3:  # NXDOMAIN
                logger.info("DNS NXDOMAIN for %s in %dms", domain, elapsed_ms)
                return DomainVerificationResult(
                    domain=domain,
                    valid_syntax=True,
                    dns_resolves=False,
                    status="UNRESOLVED",
                    error_code="DNS_NXDOMAIN",
                    error_message=(
                        f"The company domain '{domain}' did not resolve through the public "
                        "DNS check (NXDOMAIN). This may indicate a non-existent or mistyped "
                        "domain. The lead can still be reviewed using available synthetic data."
                    ),
                    latency_ms=elapsed_ms,
                )
            else:
                # Resolved but no A records (e.g. only MX, or empty answer)
                logger.info("DNS no A-record for %s rcode=%s in %dms", domain, rcode, elapsed_ms)
                return DomainVerificationResult(
                    domain=domain,
                    valid_syntax=True,
                    dns_resolves=False,
                    status="UNRESOLVED",
                    error_code="DNS_NO_A_RECORD",
                    error_message=(
                        f"The domain '{domain}' resolved but returned no A records "
                        f"(rcode={rcode}). It may use different DNS record types."
                    ),
                    latency_ms=elapsed_ms,
                )

        except httpx.TimeoutException:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            last_error = f"DNS lookup timed out after {timeout}s (attempt {attempt})"
            last_error_code = "DNS_TIMEOUT"
            logger.warning("DoH timeout for %s attempt %d", domain, attempt)
        except httpx.ConnectError as exc:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            last_error = f"Could not connect to DNS resolver: {exc}"
            last_error_code = "DNS_CONNECT_ERROR"
            logger.warning("DoH connect error for %s: %s", domain, exc)
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            last_error = f"Unexpected error during DNS lookup: {type(exc).__name__}"
            last_error_code = "DNS_UNEXPECTED_ERROR"
            logger.error("DoH unexpected error for %s: %s", domain, exc)
            break  # Don't retry unexpected errors

    # All attempts exhausted
    return DomainVerificationResult(
        domain=domain,
        valid_syntax=True,
        dns_resolves=False,
        status="ERROR",
        error_code=last_error_code or "DNS_UNKNOWN_ERROR",
        error_message=(
            f"The domain check could not be completed after {max_retries + 1} attempts. "
            f"Detail: {last_error}. "
            "The lead can still be reviewed using the available synthetic account data."
        ),
    )


def verify_domain_sync(
    domain: str,
    timeout: float = _DEFAULT_TIMEOUT,
) -> DomainVerificationResult:
    """Synchronous wrapper for use in non-async test contexts."""
    import asyncio
    return asyncio.run(verify_domain(domain, timeout=timeout, max_retries=1))
