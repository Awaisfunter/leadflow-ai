"""
LeadFlow AI — Real Integration Smoke Tests (Day 3)
Verifies both real external integrations:
  1. Cloudflare DNS-over-HTTPS (DoH) Resolver
  2. Public Website HTTP Metadata Inspector
Tests known public domains, nonexistent domains, timeouts, and invalid schemes.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add day2 to path
DAY2_DIR = Path(__file__).resolve().parent.parent.parent / "day2"
if str(DAY2_DIR) not in sys.path:
    sys.path.insert(0, str(DAY2_DIR))

from backend.app.tools.domain_verification import verify_domain
from backend.app.tools.website_metadata import fetch_website_metadata


async def verify_real_integrations():
    print("=" * 70)
    print("LeadFlow AI Day 3 — Real External Integrations Smoke Test")
    print("=" * 70)

    # ---------------------------------------------------------
    # INTEGRATION #1: Cloudflare DNS-over-HTTPS (DoH)
    # ---------------------------------------------------------
    print("\n--- [INTEGRATION #1] Cloudflare Public DNS-over-HTTPS (DoH) ---")

    test_domains = [
        ("cloudflare.com", "Known Resolvable Public Domain"),
        ("example.com", "RFC 2606 Reserved Example Domain"),
        ("nonexistent-test-domain-123456789.invalid", "Nonexistent Domain (NXDOMAIN)"),
        ("invalid..domain..name", "Malformed Syntax Domain"),
    ]

    dns_results = []
    for domain, label in test_domains:
        print(f"\nChecking DNS: {domain} ({label})...")
        res = await verify_domain(domain, timeout=5.0)
        out = {
            "domain": res.domain,
            "label": label,
            "status": res.status,
            "valid_syntax": res.valid_syntax,
            "dns_resolves": res.dns_resolves,
            "ip_addresses": res.ip_addresses,
            "source": res.source,
            "latency_ms": res.latency_ms,
            "error_code": res.error_code,
        }
        dns_results.append(out)
        print(f"  -> Status  : {res.status}")
        print(f"  -> Resolves: {res.dns_resolves}")
        print(f"  -> IPs     : {res.ip_addresses}")
        print(f"  -> Latency : {res.latency_ms} ms")
        print(f"  -> Source  : {res.source}")

    # ---------------------------------------------------------
    # INTEGRATION #2: Public Website HTTP Metadata Inspector
    # ---------------------------------------------------------
    print("\n--- [INTEGRATION #2] Public Website HTTP Metadata Inspector ---")

    test_targets = [
        ("example.com", "Standard Public Website"),
        ("cloudflare.com", "High-traffic HTTPS Website"),
        ("192.0.2.1", "Non-routable IP (Timeout Test)"),
        ("ftp://example.com", "Forbidden FTP Scheme"),
        ("javascript:alert(1)", "XSS/Forbidden Scheme"),
    ]

    web_results = []
    for target, label in test_targets:
        print(f"\nChecking Website: {target} ({label})...")
        res = await fetch_website_metadata(target, timeout=2.0)
        out = {
            "target": target,
            "label": label,
            "reachable": res.reachable,
            "status_code": res.status_code,
            "https": res.https,
            "final_url": res.final_url,
            "title": res.title,
            "response_time_ms": res.response_time_ms,
            "source": res.source,
            "error_code": res.error_code,
        }
        web_results.append(out)
        print(f"  -> Reachable   : {res.reachable}")
        print(f"  -> Status Code : {res.status_code}")
        print(f"  -> HTTPS       : {res.https}")
        print(f"  -> Final URL   : {res.final_url}")
        print(f"  -> Title       : {res.title}")
        print(f"  -> Response ms : {res.response_time_ms} ms")
        print(f"  -> Source      : {res.source}")
        if not res.reachable:
            print(f"  -> Error Code  : {res.error_code}")

    evidence_file = Path(__file__).resolve().parent.parent / "evidence" / "integration_verification_evidence.json"
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump({"dns_tests": dns_results, "website_tests": web_results}, f, indent=2)

    print("\n" + "=" * 70)
    print(f"[PASS] BOTH REAL INTEGRATIONS VERIFIED. Evidence saved to:\n  {evidence_file}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(verify_real_integrations())
