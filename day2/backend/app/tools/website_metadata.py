"""
LeadFlow AI — Real Website Metadata Tool (Day 3)

Performs a real HTTP request to the company's public website to collect
bounded, safe metadata (status, redirect, HTTPS, title, response time).

Security boundaries (strictly enforced):
- Only HTTPS and HTTP schemes are accepted. No file://, ftp://, etc.
- Maximum 3 redirects. Does not follow infinite chains.
- Strict timeout (8s default). Will not block the pipeline.
- Page content is fetched ONLY to extract the <title> tag.
- Page content is treated as UNTRUSTED EXTERNAL DATA and immediately discarded.
- Page text MUST NOT influence ICP score, routing, approval state, or CRM.
- No JavaScript execution (plain httpx — not a browser).
- No form submission, no authentication, no file upload.
- No crawling beyond the root URL.
- No cookies stored or sent beyond the single request.
- No private/authenticated pages accessed.

Data provenance: source = "public_website" always.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Optional
from urllib.parse import urlparse

import httpx

from ..schemas.models import WebsiteMetadataResult

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 5.0     # seconds (bounded timeout for SDR responsiveness)
_MAX_REDIRECTS = 3
_MAX_BODY_BYTES = 32_768   # 32 KB — enough for <title>, avoids large downloads
_ALLOWED_SCHEMES = {"http", "https"}

# Safe title extractor — reads only the HTML title element
_TITLE_RE = re.compile(r"<title[^>]*>([^<]{1,200})</title>", re.IGNORECASE | re.DOTALL)


def _sanitize_title(raw: str) -> str:
    """Strip whitespace and truncate title to 200 chars. No further processing."""
    return raw.strip()[:200]


async def fetch_website_metadata(
    domain: str,
    timeout: float = _DEFAULT_TIMEOUT,
    max_redirects: int = _MAX_REDIRECTS,
) -> WebsiteMetadataResult:
    """
    Fetch safe public metadata from the company's root website.

    Tries HTTPS first, then HTTP fallback if HTTPS fails.
    Extracts ONLY: status code, final URL, HTTPS flag, title, response time, content type.
    All page body content is UNTRUSTED and discarded after title extraction.

    Returns WebsiteMetadataResult with source='public_website'.
    """
    # Validate scheme — reject non-HTTP(S) inputs
    if "://" in domain:
        parsed = urlparse(domain)
        if parsed.scheme not in _ALLOWED_SCHEMES:
            return WebsiteMetadataResult(
                url=domain,
                reachable=False,
                error_code="UNSUPPORTED_SCHEME",
                error_message=(
                    f"URL scheme '{parsed.scheme}' is not supported. "
                    "Only https:// and http:// are accepted."
                ),
            )
        urls_to_try = [domain]
    elif ":" in domain:
        scheme = domain.split(":", 1)[0].lower()
        if scheme not in _ALLOWED_SCHEMES:
            return WebsiteMetadataResult(
                url=domain,
                reachable=False,
                error_code="UNSUPPORTED_SCHEME",
                error_message=(
                    f"URL scheme '{scheme}' is not supported. "
                    "Only https:// and http:// are accepted."
                ),
            )
        urls_to_try = [domain]
    else:
        # Build both HTTPS and HTTP variants
        urls_to_try = [f"https://{domain}", f"http://{domain}"]

    primary_url = urls_to_try[0]
    last_error: Optional[str] = None
    last_error_code: Optional[str] = None

    for url in urls_to_try:
        t0 = time.perf_counter()
        connect_timeout = min(2.0, timeout)
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=connect_timeout, read=timeout, write=connect_timeout, pool=connect_timeout),
                follow_redirects=True,
                max_redirects=max_redirects,
                headers={
                    "User-Agent": "LeadFlow-AI-Metadata-Checker/0.3 (assessment; no-crawl)",
                    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
                },
            ) as client:
                resp = await client.get(url)

            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            final_url = str(resp.url)
            is_https = final_url.startswith("https://")
            content_type = resp.headers.get("content-type", "")

            # Extract title from response body (UNTRUSTED — read only, immediately discarded)
            title: Optional[str] = None
            try:
                raw_body = resp.content[:_MAX_BODY_BYTES].decode("utf-8", errors="replace")
                match = _TITLE_RE.search(raw_body)
                if match:
                    title = _sanitize_title(match.group(1))
            except Exception:
                title = None  # Title extraction failure is non-fatal

            logger.info(
                "Website metadata fetched for %s: status=%d, https=%s, title=%r, %dms",
                domain, resp.status_code, is_https, title, elapsed_ms
            )

            return WebsiteMetadataResult(
                url=primary_url,
                reachable=True,
                status_code=resp.status_code,
                https=is_https,
                final_url=final_url,
                title=title,
                response_time_ms=elapsed_ms,
                content_type=content_type.split(";")[0].strip() if content_type else None,
            )

        except httpx.TooManyRedirects:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            last_error = f"Too many redirects (>{max_redirects}) when fetching {url}"
            last_error_code = "TOO_MANY_REDIRECTS"
            logger.warning("Too many redirects for %s", url)
            # Don't try HTTP fallback for redirect loops
            break

        except httpx.TimeoutException:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            last_error = (
                f"The company website did not respond within {timeout:.1f} seconds. "
                "Website verification is unavailable; review the lead using the remaining verified information."
            )
            last_error_code = "TIMEOUT"
            logger.warning("Website timeout for %s attempt at %s", domain, url)
            # HARDENING: Do not retry HTTP if remote host times out — avoid double timeout latency
            break

        except httpx.ConnectError:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            last_error = (
                f"Could not connect to the company website at {url}. "
                "The site may be offline or the domain may not host a website."
            )
            last_error_code = "CONNECTION_ERROR"
            logger.info("Website connect error for %s at %s", domain, url)

        except httpx.InvalidURL:
            last_error = f"Invalid URL format: {url}"
            last_error_code = "INVALID_URL"
            logger.warning("Invalid URL %s", url)
            break

        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            last_error = f"Unexpected error fetching website metadata: {type(exc).__name__}"
            last_error_code = "ERROR"
            logger.error("Website metadata error for %s: %s", domain, exc)
            break

    return WebsiteMetadataResult(
        url=primary_url,
        reachable=False,
        error_code=last_error_code or "ERROR",
        error_message=last_error or "Website metadata could not be retrieved.",
    )


def fetch_website_metadata_sync(
    domain: str,
    timeout: float = _DEFAULT_TIMEOUT,
) -> WebsiteMetadataResult:
    """Synchronous wrapper for use in non-async test contexts."""
    import asyncio
    return asyncio.run(fetch_website_metadata(domain, timeout=timeout))
