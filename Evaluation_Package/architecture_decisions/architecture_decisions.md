# Architecture Decisions Record

## Decision Log

### 1. FastAPI as Web Framework
**Decision**: Use FastAPI for the backend API  
**Reason**: Automatic OpenAPI/Swagger documentation, built-in Pydantic validation, async support  
**Trade-off**: Python ecosystem vs Node.js; chose Python for data science libraries and validation  
**Alternative considered**: Flask, Django REST Framework  
**Why chosen**: Type safety, automatic validation, self-documenting API endpoints  

### 2. Pydantic for Data Validation  
**Decision**: Use Pydantic v2 for all data contracts and validation  
**Reason**: Strong typing, automatic validation, JSON schema generation  
**Trade-off**: Learning curve vs manual validation; chose type safety over simplicity  
**Alternative considered**: Manual JSON validation, marshmallow  
**Why chosen**: Prevents runtime errors, enforces data contracts at API boundaries  

### 3. SQLite for Audit Database  
**Decision**: Use append-only SQLite database for audit trail  
**Reason**: Zero-configuration, embedded, transaction guarantees, SQL queries for analysis  
**Trade-off**: Single-file limitation vs PostgreSQL scalability; chose simplicity for v0  
**Alternative considered**: PostgreSQL, JSON files, cloud databases  
**Why chosen**: Embeddable, no external dependencies, supports concurrent reads  

### 4. Deterministic Scoring Engine  
**Decision**: ICP scores calculated by deterministic arithmetic, not LLM  
**Reason**: Consistent, auditable, explainable business logic; prevents drift  
**Trade-off**: Manual rule updates vs dynamic learning; chose predictability  
**Alternative considered**: LLM-based scoring, ML models  
**Why chosen**: Business rules must be transparent and consistent across reps  

### 5. LLM Fallback Architecture  
**Decision**: Deterministic template fallback when LLM unavailable  
**Reason**: System must function without external dependencies; offline reliability  
**Trade-off**: Template quality vs AI personalization; chose reliability over perfection  
**Alternative considered**: Queue and retry, fail fast  
**Why chosen**: SDR workflow cannot be blocked by external API outages  

### 6. DNS-over-HTTPS Integration  
**Decision**: Use Cloudflare public DoH for domain verification  
**Reason**: No credentials required, bypasses corporate DNS policies, JSON API  
**Trade-off**: External dependency vs local DNS; chose authoritative resolution  
**Alternative considered**: Local DNS resolution, third-party APIs  
**Why chosen**: Public service, high availability, structured responses  

### 7. Public Website Metadata Only  
**Decision**: Fetch only root URL metadata, no crawling or scraping  
**Reason**: Security boundary, minimize attack surface, respect robots.txt  
**Trade-off**: Limited data vs comprehensive scraping; chose safety  
**Alternative considered**: Full website crawling, paid scraping APIs  
**Why chosen**: Avoids legal issues, reduces processing time, bounds security risk  

### 8. Human Approval Gate  
**Decision**: Mandatory human approval before CRM dispatch  
**Reason**: Legal liability for commercial claims, maintains human oversight  
**Trade-off**: Automation speed vs governance; chose liability protection  
**Alternative considered**: Fully automated dispatch, approval by exception  
**Why chosen**: Commercial commitments require human sign-off for legal protection  

### 9. Synthetic Enrichment Database  
**Decision**: Use curated synthetic company data for enrichment  
**Reason**: No API costs, privacy compliance, predictable test results  
**Trade-off**: Data freshness vs live APIs; chose cost control for v0  
**Alternative considered**: Clearbit, Apollo, ZoomInfo APIs  
**Why chosen**: Evaluation environment requires reproducible results without costs  

### 10. Bounded LLM Context  
**Decision**: Limit LLM to draft generation with verified facts only  
**Reason**: Prevent hallucination of company details, pricing, or capabilities  
**Trade-off**: Creative flexibility vs accuracy; chose factual accuracy  
**Alternative considered**: Open-ended LLM generation, fact-checking post-processing  
**Why chosen**: Commercial communications cannot contain unsupported claims  

### 11. Single-Page Web Interface  
**Decision**: One-page HTML dashboard with JavaScript, no separate frontend framework  
**Reason**: Simplicity for non-developer users, zero build process  
**Trade-off**: UI sophistication vs complexity; chose simplicity  
**Alternative considered**: React SPA, Vue.js, multiple pages  
**Why chosen**: Non-developer SDRs need simple, intuitive interface  

### 12. Windows Batch Startup Scripts  
**Decision**: Provide .bat files for one-click startup  
**Reason**: Target users likely on Windows, eliminates command-line complexity  
**Trade-off**: Platform specificity vs universality; chose target user optimization  
**Alternative considered**: Docker containers, shell scripts only  
**Why chosen**: Reduces barrier to entry for business users on Windows  

## Implementation Principles

1. **Deterministic Business Logic**: All scoring, routing, and classification uses explicit rules, not ML/LLM
2. **Bounded External Dependencies**: External APIs have timeouts, fallbacks, and graceful degradation  
3. **Human-in-the-Loop**: Commercial decisions require human approval; automation assists, doesn't replace
4. **Audit Everything**: Every decision and state change is logged for compliance and debugging
5. **Security by Default**: Untrusted data is isolated; prompts and scores cannot be manipulated
6. **Non-Developer UX**: Interface designed for sales reps, not engineers
7. **Offline Capable**: Core functionality works without external API keys