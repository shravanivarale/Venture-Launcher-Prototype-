# Architecture & Design Documentation

## System Design Overview

This document describes the production-grade architecture of the Investor Scraping Pipeline.

---

## 🏗️ Architectural Pattern

### Clean Architecture with Separation of Concerns

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│                    (main.py, CLI args)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Orchestration│  │ Cleaning     │  │ Deduplication   │   │
│  │ Engine       │  │ Pipeline     │  │ Engine          │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└────────────┬───────────────────────────────┬────────────────┘
             │                               │
┌────────────▼───────────────────────────────▼────────────────┐
│                    DATA ACCESS LAYER                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Scraper Framework (Base Scraper)           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │   │
│  │  │AngelList │ │Crunchbase│ │LetsVenture, etc.    │ │   │
│  │  └──────────┘ └──────────┘ └──────────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────┬──────────────────────────────────────────────┘
             │
┌────────────▼──────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │
│  │Retry & CB    │ │Rate Limiter  │ │Data Validation  │  │
│  │Exponential   │ │Per-domain    │ │Schemas (Pydantic)  │
│  │Backoff       │ │Throttling    │ │Normalization    │  │
│  └──────────────┘ └──────────────┘ └──────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  HTTP Requests (requests library, BeautifulSoup)    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Pipeline

### End-to-End Process

```
START
  │
  ├─→ [LOAD CONFIG]
  │     • Load YAML/Python config
  │     • Validate settings
  │
  ├─→ [INITIALIZE SCRAPERS]
  │     • Create scraper instances
  │     • Set up rate limiters
  │     • Initialize circuit breakers
  │
  ├─→ [PHASE 1: SCRAPING] ← Errors isolated here
  │   ├─→ AngelList Scraper
  │   │   ├─ Fetch pages (with retry)
  │   │   ├─ Parse HTML (BeautifulSoup)
  │   │   ├─ Extract investor data
  │   │   └─ Rate limit between requests
  │   │
  │   ├─→ Crunchbase Scraper
  │   ├─→ Tracxn Scraper
  │   ├─→ LetsVenture Scraper
  │   └─→ Google Fallback Scraper
  │
  ├─→ [PHASE 2: AGGREGATION]
  │     • Combine all scraper results
  │     • Total: ~200 raw records
  │
  ├─→ [PHASE 3: EXTRACTION]
  │     • Extract email from text (regex)
  │     • Extract sectors (heuristics)
  │     • Extract portfolio companies
  │
  ├─→ [PHASE 4: CLEANING]
  │     • Validate records
  │     • Normalize types (VC → VC)
  │     • Normalize stages (Seed → Seed)
  │     • Normalize sectors (AI → AI/ML)
  │     • Clean URLs
  │     • Validate LinkedIn URLs
  │
  ├─→ [PHASE 5: LINKEDIN ENRICHMENT]
  │     • Search LinkedIn via Google SERP
  │     • Extract profile URLs (safe method)
  │     • Add missing URLs to records
  │
  ├─→ [PHASE 6: DEDUPLICATION]
  │   ├─ Pass 1: Exact name matching
  │   ├─ Pass 2: Fuzzy matching (85%+ similarity)
  │   ├─ Merge duplicate records
  │   └─ Final: ~167 unique records
  │
  ├─→ [PHASE 7: EXPORT]
  │     • Convert to DataFrame
  │     • Export to CSV
  │     • Export to Excel (formatted)
  │
  ├─→ [PHASE 8: LOGGING]
  │     • Generate summary statistics
  │     • Save execution logs
  │     • Write failed URLs log
  │
  └─→ END (Success or Error)
```

---

## 🛡️ Fault Tolerance Architecture

### Circuit Breaker Pattern

```
CLOSED State (Normal Operation)
  │
  ├─→ Success: Stay CLOSED
  │
  └─→ Failure Count ≥ 5: → OPEN State
                           │
                           ├─→ Wait 5 minutes (recovery_timeout)
                           │
                           └─→ HALF_OPEN: Try 2 more attempts
                               ├─→ Success: → CLOSED (recovered)
                               └─→ Failure: → OPEN (retry again)
```

### Retry with Exponential Backoff

```
Attempt 1: Fail
  ↓ Wait 1^1 = 1 second
Attempt 2: Fail
  ↓ Wait 1.5^2 = 2.25 seconds
Attempt 3: Fail
  ↓ Wait 1.5^3 = 3.375 seconds
Attempt 4: Success! ✅
  ↓
Return result
```

### Error Isolation

```
Pipeline
  │
  ├─→ Scraper 1 ← Error here doesn't affect others
  │   │ (fails) ✗
  │   └─ Circuit opens, pipeline continues
  │
  ├─→ Scraper 2 ← Runs normally
  │   │ (success) ✓
  │   └─ Adds records
  │
  ├─→ Scraper 3 ← Continues even if #1 failed
  │   │ (success) ✓
  │   └─ Adds records
  │
  └─→ Aggregation: Uses data from #2 and #3
```

---

## 🔐 Data Validation Strategy

### Multi-Layer Validation

```
INPUT DATA (from scrapers)
    ↓
[SCHEMA VALIDATION]
    • Pydantic models
    • Type checking
    • Range validation
    ↓
[BUSINESS LOGIC VALIDATION]
    • Name length: 3-200 chars
    • URL format: valid http/https
    • Email format: regex pattern
    • Type in allowed set
    ↓
[NORMALIZATION]
    • Lowercase names
    • Standardize types
    • Map sectors to taxonomy
    ↓
[QUALITY SCORING]
    • Completeness: 0-1.0
    • Source weight: 0.7-1.0
    • Final score: 0-100%
    ↓
OUTPUT DATA (clean, validated)
```

---

## 🔍 Deduplication Algorithm

### Two-Pass Approach

**Pass 1: Exact Match**
```python
seen = {}
for record in records:
    key = record.name.lower().strip()
    if key in seen:
        # Merge with existing
        seen[key] = merge(seen[key], record)
    else:
        seen[key] = record
```

**Pass 2: Fuzzy Match**
```python
for i, record1 in enumerate(records):
    for j, record2 in enumerate(records[i+1:]):
        similarity = similarity_score(record1.name, record2.name)
        if similarity >= 85%:  # threshold
            # Merge and mark as duplicate
            merged = merge(record1, record2)
```

**Similarity Calculation**
```
"Sequoia Capital" vs "Sequoia Capital Inc"
  ↓ Remove common suffixes (inc, ltd, etc.)
"Sequoia Capital" vs "Sequoia Capital"
  ↓ Use SequenceMatcher (Jaro-like algorithm)
Similarity: 98% ✓ DUPLICATE
```

**Intelligent Merge**
```python
merged = InvestorRecord(
    name = record1.name or record2.name,  # keep non-null
    website = record1.website or record2.website,
    sectors = set(r1.sectors + r2.sectors),  # combine lists
    linkedin = record1.linkedin or record2.linkedin,
    source = f"{record1.source},{record2.source}",  # track all sources
    quality_score = max(r1.score, r2.score),  # keep best
)
```

---

## 🌐 Multi-Source Strategy

### Source Priority & Failover

```
1. AngelList (Priority 1)
   ├─ Success: Use data
   └─ Fail: Circuit opens, skip to next
         │
2. Crunchbase (Priority 2)
   ├─ Success: Use data, merge with AngelList
   └─ Fail: Circuit opens, skip to next
         │
3. Tracxn (Priority 3)
   ├─ Success: Use data, merge with previous
   └─ Fail: Circuit opens, skip to next
         │
4. LetsVenture (Priority 4)
   ├─ Success: Use data, merge
   └─ Fail: Circuit opens, skip to next
         │
5. Google Fallback (Priority 5)
   ├─ Success: Use data (lower quality)
   └─ Fail: Skip, but don't fail pipeline
```

### Record Merging Logic

```
Source 1: name=X, sectors=[AI], website=W1
Source 2: name=X, sectors=[B2B], linkedin=L
    │
    ├─ Same name (normalized)
    │
    └─ Merge: name=X, sectors=[AI,B2B], website=W1, linkedin=L
```

---

## 📊 Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Scraping | O(n) | n = number of pages |
| Extraction | O(n) | Linear scan |
| Exact dedup | O(n) | Hash-based |
| Fuzzy dedup | O(n²) | Pairwise comparison |
| Export | O(n) | Single pass |
| **Total** | **O(n²)** | Dominated by fuzzy dedup |

### Space Complexity

| Component | Space |
|-----------|-------|
| Raw records | O(n) |
| Cleaned records | O(n) |
| Dedup tracking | O(n²) | (pairwise comparisons) |
| **Total** | **O(n²)** |

### Optimization for Scale

For 10,000+ records:
- Implement spatial indexing (LSH)
- Use approximate fuzzy matching
- Stream processing instead of in-memory
- Batch database inserts

---

## 🔌 Extensibility Points

### Adding New Scraper

1. **Create scraper file**: `scrapers/new_source.py`
2. **Inherit from BaseScraper**:
   ```python
   class NewSourceScraper(BaseScraper):
       def scrape(self) -> List[InvestorRecord]:
           # Implementation
   ```
3. **Add to engine**: Register in `_get_scrapers()`
4. **Add config**: Update `SCRAPERS` dict in `config.py`

### Adding New Validator

1. **Edit**: `utils/validators.py`
2. **Add method**: `def is_valid_xxx(value)`
3. **Use in cleaner**: `DataCleaner._clean_record()`

### Adding New Export Format

1. **Edit**: `pipeline/exporter.py`
2. **Add method**: `def to_json()`, `def to_parquet()`, etc.
3. **Update config**: Add format option

---

## 🔄 Data Models (Pydantic)

### InvestorRecord Schema

```python
class InvestorRecord(BaseModel):
    investor_name: str  # Required
    investor_type: str  # VC / Angel / Seed Fund
    website_url: Optional[str]
    investment_stage: Optional[str]
    sectors_of_interest: List[str]
    notable_portfolio_companies: List[str]
    linkedin_profile_url: Optional[str]
    source: str  # Scraper name
    data_collected_at: datetime
    data_quality_score: float  # 0.0 - 1.0
```

**Benefits:**
- Type safety
- Automatic validation
- JSON serialization
- IDE autocomplete

---

## 📋 Configuration Management

### Hierarchy

```
1. Default values in code
2. config.py overrides
3. Environment variables override config.py
4. CLI arguments override everything
```

### Example

```python
# config.py
TIMEOUT = 15

# Environment variable
export SCRAPER_TIMEOUT=20

# CLI argument
python main.py --timeout 25  # Uses 25

# Priority: CLI > ENV > config.py > defaults
```

---

## 🧪 Testing Strategy

### Unit Testing Areas

- **Validators**: Test all normalization functions
- **Deduplicator**: Test fuzzy matching accuracy
- **Extractors**: Test regex and heuristic extraction
- **Cleaners**: Test data transformation

### Integration Testing

- **Full pipeline**: End-to-end with sample data
- **Error scenarios**: Circuit breaker, timeouts
- **Large datasets**: Memory and performance

### Example Test

```python
def test_fuzzy_dedup():
    records = [
        InvestorRecord(name="Sequoia Capital"),
        InvestorRecord(name="Sequoia Capital Inc"),
    ]
    dedup = Deduplicator()
    result = dedup.deduplicate(records)
    assert len(result) == 1  # Should merge
```

---

## 📈 Monitoring & Observability

### Key Metrics

```
• Total records scraped
• Records per source
• Success/failure rate per source
• Average data quality score
• Deduplication reduction %
• Processing time
• Memory usage
```

### Logging Levels

- **DEBUG**: Detailed debug info
- **INFO**: Progress updates
- **WARNING**: Recoverable errors (retry, circuit open)
- **ERROR**: Unrecoverable errors

### Log Output

```
2024-01-15 10:30:45 - InvestorScraper - INFO - 🚀 Starting pipeline
2024-01-15 10:30:50 - InvestorScraper.angellist - INFO - ✅ 45 records
2024-01-15 10:31:10 - InvestorScraper.crunchbase - WARNING - ⚠️ Rate limited, retrying...
2024-01-15 10:32:15 - InvestorScraper.deduplicator - INFO - Fuzzy match: 'Sequoia' ~= 'Sequoia Inc'
```

---

## 🔐 Security Considerations

### Current Implementation

- ✅ User-Agent rotation (avoid bot detection)
- ✅ Rate limiting (respect servers)
- ✅ No login automation
- ✅ LinkedIn ToS compliant
- ✅ Error isolation (no data leaks)

### Recommendations for Production

1. **API Key management**: Use environment variables
2. **HTTPS enforcement**: Validate SSL certificates
3. **Data encryption**: Encrypt sensitive data at rest
4. **Access control**: Limit file permissions
5. **Audit logging**: Track who accesses data

---

## 🚀 Deployment Options

### Local Development

```bash
python main.py --sample
python main.py --verbose
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

```bash
docker build -t investor-scraper .
docker run investor-scraper
```

### Cloud (AWS Lambda, GCP Cloud Functions)

```python
def handler(event, context):
    engine = ScrapeEngine()
    result = engine.run()
    return {"statusCode": 200, "body": result}
```

### Scheduled Jobs (Cron/APScheduler)

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(main, 'cron', hour=0, minute=0)  # Daily at midnight
scheduler.start()
```

---

## 📚 References

- [Pydantic Docs](https://docs.pydantic.dev)
- [BeautifulSoup Docs](https://www.crummy.com/software/BeautifulSoup)
- [Requests Library](https://requests.readthedocs.io)
- [Circuit Breaker Pattern](https://en.wikipedia.org/wiki/Circuit_breaker_pattern)
- [Fuzzy String Matching](https://en.wikipedia.org/wiki/Approximate_string_matching)

---

**Architecture designed for production reliability and scalability.** 🏗️
