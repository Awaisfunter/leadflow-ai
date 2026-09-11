# LeadFlow AI — Day 3 External Integrations Specification

> **System Milestone:** Day 3 — Build the Working Core  
> **Author:** Awais Saeed | Applied AI Engineer Candidate  
> **Classification:** Integration Contracts & Security Boundaries

---

## 1. Executive Summary

Day 3 establishes **two real, verifiable external integrations** to augment inbound lead qualification with live public network signals. Both integrations operate without proprietary customer credentials or private API keys, execute with bounded timeouts, fail gracefully into structured models, and strictly isolate external data from business logic and generative models.

```
+-------------------------------------------------------------------------------+
|                       DATA PROVENANCE & ISOLATION MODEL                       |
+------------------------------------+------------------------------------------+
|  Real External Public Signal #1    |  Real External Public Signal #2          |
|  Cloudflare DNS-over-HTTPS (DoH)   |  Public Website HTTP Metadata Inspector  |
|  [source: public_dns]              |  [source: public_website]                |
+------------------------------------+------------------------------------------+
|                                    |                                          |
|  * A-Record Resolution             |  * HTTP Status Code (200, 301, etc.)     |
|  * Network Roundtrip Latency (ms)  |  * HTTPS / TLS Enforcement               |
|  * Syntax Verification             |  * Response Latency (ms)                 |
|  * Graceful Fallback on NXDOMAIN   |  * Safe HTML <title> Extraction (<=200c) |
|                                    |  * Body content discarded immediately    |
+------------------------------------+------------------------------------------+
                                     |
                                     v
                 [ STRICT UNTRUSTED EXTERNAL BOUNDARY ]
                                     |
                                     v
+-------------------------------------------------------------------------------+
|                      AUTHORITATIVE BUSINESS LOGIC CORE                        |
|                                                                               |
|  * Deterministic ICP Scoring (0-100 arithmetic via business_rules.json)       |
|  * Internal Synthetic Company Database [source: synthetic_internal_dataset]   |
|  * Bounded Context Generative Outreach [source: llm or deterministic_fallback]|
|  * Commercial Claim Validation (Blocks unapproved discounts, SLA, logos)      |
|  * Mandatory Human SDR Approval Gate                                          |
|  * Append-Only SQLite Audit Persistence [logs/audit.db]                       |
+-------------------------------------------------------------------------------+
```

---

## 2. Integration #1: Real Public DNS Verification (DNS-over-HTTPS)

### 2.1 Purpose
Verifies whether the submitted corporate domain resolves at the DNS level through a public resolver, detects non-existent or mistyped domains, validates syntax, and captures live DNS roundtrip latency.

### 2.2 Technology & Mechanism
- **Mechanism:** DNS-over-HTTPS (RFC 8484) JSON API.
- **Provider:** Cloudflare Public DNS Resolver (`https://cloudflare-dns.com/dns-query`).
- **Client Library:** `httpx.AsyncClient` with asynchronous connection pooling.
- **Record Type:** `A` (IPv4 Host Address).
- **Endpoint:** `GET https://cloudflare-dns.com/dns-query?name={domain}&type=A`
- **Request Headers:** `Accept: application/dns-json`

### 2.3 Input Schema
```python
domain: str  # Parsed domain, e.g. "acmecorp.com" or "cloudflare.com"
timeout: float = 5.0  # Configurable via Settings.dns_timeout_seconds
max_retries: int = 2
```

### 2.4 Output Schema (`DomainVerificationResult`)
```json
{
  "domain": "cloudflare.com",
  "valid_syntax": true,
  "dns_resolves": true,
  "ip_addresses": ["104.16.132.229", "104.16.133.229"],
  "record_type": "A",
  "status": "VERIFIED",
  "source": "public_dns",
  "error_code": null,
  "error_message": null,
  "checked_at": "2026-09-08T02:36:18.123456Z",
  "latency_ms": 304
}
```

For non-existent domains (`nonexistent-test-domain-123456789.invalid`):
```json
{
  "domain": "nonexistent-test-domain-123456789.invalid",
  "valid_syntax": true,
  "dns_resolves": false,
  "ip_addresses": [],
  "record_type": "A",
  "status": "UNRESOLVED",
  "source": "public_dns",
  "error_code": "DNS_NXDOMAIN",
  "error_message": "The company domain '...' did not resolve through the public DNS check (NXDOMAIN)...",
  "checked_at": "2026-09-08T02:36:18.456789Z",
  "latency_ms": 282
}
```

### 2.5 Timeouts, Retries & Failure Handling
- **Connect Timeout:** 3.0 seconds.
- **Read Timeout:** 5.0 seconds.
- **Retries:** Up to 2 retries with exponential backoff on transient network faults.
- **Pre-Flight Syntax Check:** Invalid names (e.g. `invalid..domain`) fail fast as `INVALID_SYNTAX` without making network requests.
- **Failure Resilience:** NXDOMAIN or connection errors return structured objects with `dns_resolves: false` and set `RiskFlag.NEEDS_VERIFICATION`. Never raises unhandled exceptions.

### 2.6 Security Boundaries & Data Provenance
- **Data Provenance:** Always tagged `source: "public_dns"`.
- **Zero Credentials:** Operates without API keys or accounts.
- **No Crawler Behavior:** Only requests DNS A-records; does not query zone transfers, PTR records, or execute arbitrary requests.
- **Untrusted Signal:** DNS resolution status does not directly assign ICP points.

---

## 3. Integration #2: Real Public Website HTTP Metadata Inspector

### 3.1 Purpose
Performs an HTTP inspection of the company's root website to confirm web presence, detect HTTPS/TLS security, measure server response time, follow redirects up to a safe limit, and extract bounded page metadata.

### 3.2 Technology & Mechanism
- **Client Library:** `httpx.AsyncClient`.
- **Protocol:** HTTP/1.1 and HTTP/2 over TLS.
- **URL Resolution:** Attempts `https://{domain}` first; falls back to `http://{domain}` if HTTPS handshake fails.
- **Redirect Policy:** Follows redirects with a hard ceiling of `max_redirects = 3`.
- **User Agent:** Bounded descriptive header `LeadFlow-AI-Metadata-Checker/0.3 (assessment; no-crawl)`.

### 3.3 Input Schema
```python
domain: str  # Domain or root URL, e.g. "example.com"
timeout: float = 8.0  # Configurable via Settings.website_timeout_seconds
max_redirects: int = 3
```

### 3.4 Output Schema (`WebsiteMetadataResult`)
```json
{
  "url": "https://example.com",
  "reachable": true,
  "status_code": 200,
  "https": true,
  "final_url": "https://example.com/",
  "title": "Example Domain",
  "response_time_ms": 309,
  "content_type": "text/html",
  "source": "public_website",
  "error_code": null,
  "error_message": null,
  "checked_at": "2026-09-08T02:36:19.123456Z"
}
```

For unreachable or non-routable targets (`192.0.2.1`):
```json
{
  "url": "https://192.0.2.1",
  "reachable": false,
  "status_code": null,
  "https": false,
  "final_url": null,
  "title": null,
  "response_time_ms": null,
  "content_type": null,
  "source": "public_website",
  "error_code": "TIMEOUT",
  "error_message": "Company website could not be reached within 2.0 seconds...",
  "checked_at": "2026-09-08T02:36:21.123456Z"
}
```

### 3.5 Security Boundaries (Strictly Enforced)
1. **Forbidden Schemes:** Rejects all schemes other than `http` and `https` (`ftp://`, `file://`, `javascript:`, `gopher://`).
2. **Buffer Limits:** Reads at most 32 KB (`_MAX_BODY_BYTES = 32_768`) to locate `<title>`.
3. **No DOM / JavaScript Execution:** Plain HTTP client; no Chromium, headless browser, or V8 engine.
4. **Immediate Discard:** Full response body is immediately deallocated after title extraction.
5. **No Form Submissions or Authentication:** Never sends POST/PUT requests, cookies, or authorization tokens.
6. **No Crawling:** Never follows internal links, sitemaps, or subdirectory paths.
7. **Prompt Injection Defense:** External page titles are treated as untrusted text strings (truncated to 200 chars). They are never interpolated into system prompt instructions.

---

## 4. Integration Verification & Evidence

Both integrations are covered by dedicated automated test scenarios in `day2/backend/tests/test_pipeline.py`:
- `test_day3_domain_verification_valid_public_domain`: Validates Cloudflare DoH resolution on `cloudflare.com`.
- `test_day3_domain_verification_invalid_syntax`: Rejects invalid domain names with `INVALID_SYNTAX`.
- `test_day3_domain_verification_unresolved_domain`: Verifies NXDOMAIN response handling without crash.
- `test_day3_website_metadata_reachable`: Verifies HTTP 200, HTTPS flag, and title extraction on `example.com`.
- `test_day3_website_metadata_unreachable_handled_gracefully`: Verifies timeout handling on `192.0.2.1`.
- `test_day3_website_metadata_unsupported_schemes_rejected`: Verifies immediate rejection of `ftp://` and `javascript:`.
- `test_day3_untrusted_external_content_isolation`: Proves that injection text in external input cannot alter ICP scoring.

Live empirical execution evidence is recorded in:
- `day3/evidence/integration_verification_evidence.json`
- `day3/evidence/test_execution_evidence.txt`
- `day3/benchmark/day3_execution_results.csv`
