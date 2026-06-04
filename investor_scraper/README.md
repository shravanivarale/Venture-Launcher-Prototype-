# 🚀 Production-Grade Investor Scraping Pipeline

A robust, fault-tolerant data scraping and aggregation system that collects early-stage startup investors in India.

## 📋 Overview

This system automatically scrapes investor data from multiple sources, cleans and deduplicates records, and exports structured datasets in CSV and Excel formats. Designed for production-scale use with proper error handling, rate limiting, and circuit breaker patterns.

### Key Features

✅ **Multi-source scraping** — AngelList, Crunchbase, Tracxn, LetsVenture, Google Search  
✅ **Fault tolerance** — Circuit breakers, retry logic, error isolation  
✅ **Deduplication** — Fuzzy matching with intelligent record merging  
✅ **Rate limiting** — Per-domain throttling to avoid blocks  
✅ **LinkedIn-safe** — Uses Google SERP instead of direct scraping  
✅ **Data validation** — Comprehensive cleaning and normalization  
✅ **Structured output** — CSV and Excel with proper formatting  
✅ **Comprehensive logging** — Full audit trail of operations  

---

## 📦 Project Structure

```
investor_scraper/
├── main.py                 # Entry point
├── config.py               # Configuration
├── requirements.txt        # Dependencies
├── README.md               # This file
│
├── core/
│   ├── engine.py           # Main orchestration engine
│   ├── schemas.py          # Pydantic data models
│   └── exceptions.py       # Custom exceptions
│
├── scrapers/
│   ├── base_scraper.py     # Base scraper class
│   ├── angellist.py        # AngelList scraper
│   ├── crunchbase.py       # Crunchbase scraper
│   ├── tracxn.py           # Tracxn scraper
│   ├── letsventure.py      # LetsVenture scraper
│   └── google_fallback.py  # Google Search fallback
│
├── pipeline/
│   ├── extractor.py        # Data extraction utilities
│   ├── cleaner.py          # Data cleaning & normalization
│   ├── deduplicator.py     # Fuzzy matching deduplication
│   └── exporter.py         # CSV/Excel export
│
├── utils/
│   ├── logger.py           # Logging system
│   ├── retry.py            # Retry & circuit breaker
│   ├── rate_limiter.py     # Rate limiting
│   ├── validators.py       # Data validators
│   └── linkedin_safe.py    # LinkedIn extraction (safe method)
│
├── logs/                   # Log files
└── output/                 # Output files (CSV, Excel, logs)
```

---

## ⚙️ Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

1. **Clone/navigate to project:**
   ```bash
   cd investor_scraper
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Usage

### Quick Start

Run the full pipeline:
```bash
python main.py
```

### With Options

```bash
# Limit to 50 records per scraper
python main.py --limit 50

# Export only to CSV
python main.py --output csv

# Run specific scrapers
python main.py --scrapers angellist crunchbase

# Skip deduplication
python main.py --no-deduplicate

# Generate sample output (no actual scraping)
python main.py --sample

# Verbose logging
python main.py --verbose
```

### Full Command-Line Help

```bash
python main.py --help
```

---

## 📊 Output

After execution, find output files in the `output/` directory:

- **investors.csv** — Comma-separated values
- **investors.xlsx** — Excel spreadsheet with formatting
- **logs/investor_scraper.log** — Full execution logs
- **logs/pipeline_summary.json** — Execution summary

### Output Fields

| Field | Description |
|-------|-------------|
| Investor Name | Name of the investor/fund |
| Investor Type | VC / Angel / Seed Fund / Corporate / Individual |
| Website URL | Official website or profile URL |
| Investment Stage | Pre-seed / Seed / Series A / Series B / Series C+ / Growth |
| Sectors of Interest | AI/ML, SaaS, Fintech, Healthtech, etc. (semicolon-separated) |
| Portfolio Companies | Known portfolio companies (semicolon-separated) |
| LinkedIn Profile | LinkedIn profile URL |
| Data Source | Source scraper name |
| Data Quality Score | Confidence score (0-100%) |
| Data Collected | Timestamp of collection |

---

## 🔧 Architecture

### Pipeline Flow

```
Scraping Phase
     ↓
┌────────────────────────────────────┐
│ Scraper 1 (AngelList)              │
│ Scraper 2 (Crunchbase)             │ ← Runs in parallel with
│ Scraper 3 (Tracxn)                 │   error isolation
│ Scraper 4 (LetsVenture)            │
│ Scraper 5 (Google Fallback)        │
└────────────────────────────────────┘
     ↓
Aggregation Phase
     ↓
┌────────────────────────────────────┐
│ Combine all records                │
│ Remove exact duplicates            │
└────────────────────────────────────┘
     ↓
Cleaning Phase
     ↓
┌────────────────────────────────────┐
│ Validate data                      │
│ Normalize types/stages/sectors     │
│ Clean URLs                         │
│ Standardize names                  │
└────────────────────────────────────┘
     ↓
Deduplication Phase
     ↓
┌────────────────────────────────────┐
│ Fuzzy matching on investor names   │
│ Intelligent record merging         │
│ Remove duplicates across sources   │
└────────────────────────────────────┘
     ↓
Export Phase
     ↓
┌────────────────────────────────────┐
│ Export to CSV                      │
│ Export to Excel (formatted)        │
│ Generate summary statistics        │
└────────────────────────────────────┘
```

### Error Handling

The pipeline implements **production-grade error handling**:

1. **Circuit Breaker Pattern**
   - Disables failing scrapers temporarily
   - Prevents cascading failures
   - Auto-recovery after timeout

2. **Retry with Exponential Backoff**
   - Automatic retry with increasing delays
   - Handles transient failures
   - Configurable retry count

3. **Rate Limiting**
   - Per-domain throttling
   - Respects server resources
   - Avoids IP blocking

4. **Error Isolation**
   - One scraper failure doesn't crash pipeline
   - All errors logged for investigation
   - Pipeline continues with other sources

---

## 🔐 LinkedIn-Safe Strategy

**Why we don't scrape LinkedIn directly:**
- LinkedIn ToS prohibits scraping
- IP bans are common
- Account suspension risk
- Legal liability

**Our approach:**
- Use Google SERP queries: `site:linkedin.com/in "investor name"`
- Extract only publicly visible information
- No login automation
- No JavaScript rendering of LinkedIn pages
- Respects LinkedIn ToS

**Example:**
```python
from utils.linkedin_safe import extract_linkedin_safe

# Returns LinkedIn profile URL or None
profile_url = extract_linkedin_safe("John Doe Venture Capital")
```

---

## 🧹 Data Cleaning & Normalization

### Investor Types
- VC → normalized to "VC"
- Venture Capital → "VC"
- Angel Investor → "Angel"
- Seed Fund → "Seed Fund"

### Investment Stages
- Pre-seed, Preseed → "Pre-seed"
- Seed → "Seed"
- Series A, Series-A → "Series A"
- Series B, Series-B → "Series B"
- Series C, Series C+ → "Series C+"
- Growth → "Growth"

### Sectors
Standardized taxonomy:
- AI/ML
- SaaS
- Fintech
- Healthtech
- Edtech
- E-commerce
- Logistics
- Sustainability
- B2B

### Deduplication
- **Exact match**: Case-insensitive name matching
- **Fuzzy match**: Levenshtein-like similarity (85% threshold)
- **Smart merge**: Keeps best non-null fields, combines lists

---

## 📈 Scalability

The system is designed to scale from 100 to 10,000+ records:

### Current Constraints (Configurable)
- Timeout per request: 15-20 seconds
- Max retries: 3
- Rate limit: 2 seconds between requests per domain
- Circuit breaker: Opens after 5 consecutive failures

### For Larger Scale
1. Implement async scraping (Asyncio/Playwright)
2. Add caching layer (Redis)
3. Use task queue (Celery)
4. Implement batch processing
5. Add database storage (PostgreSQL)

---

## 📝 Configuration

Edit `config.py` to customize:

```python
# Scraper settings
SCRAPER_CONFIG = {
    "timeout": 15,              # Seconds per request
    "max_retries": 3,           # Retry attempts
    "backoff_factor": 1.5,      # Exponential backoff
    "rate_limit_delay": 2,      # Seconds between requests
}

# Circuit breaker
CIRCUIT_BREAKER_CONFIG = {
    "failure_threshold": 5,     # Failures to trip circuit
    "recovery_timeout": 300,    # Seconds before retry
}

# Deduplication
CLEANING_CONFIG = {
    "fuzzy_match_threshold": 85, # Similarity score 0-100
}

# Enabled scrapers
SCRAPERS = {
    "angellist": {"enabled": True, "priority": 1},
    "crunchbase": {"enabled": True, "priority": 2},
    # ... etc
}
```

---

## 🧪 Testing

### Generate Sample Output
```bash
python main.py --sample
```

### Run Single Scraper
```bash
python main.py --scrapers angellist --limit 10
```

### Verbose Logging
```bash
python main.py --verbose
```

---

## 📊 Sample Output

### First 5 records (CSV format)

| Investor Name | Investor Type | Website URL | Investment Stage | Sectors | LinkedIn |
|---|---|---|---|---|---|
| Sequoia Capital India | VC | sequoiacap.com | Series A | SaaS, B2B | linkedin.com/company/sequoia |
| Accel Partners | VC | accel.com | Seed | Fintech, E-comm | linkedin.com/company/accel |
| India Quotient | Seed Fund | indiaquotient.com | Pre-seed | B2B, AI/ML | linkedin.com/company/iq |
| Ankur Capital | Seed Fund | ankurcapital.com | Seed | Agri-tech | linkedin.com/company/ankur |
| Lightspeed Venture | VC | lsspvp.com | Series B | SaaS | linkedin.com/company/lightspeed |

---

## 📊 Execution Summary

After each run, check `logs/pipeline_summary.json`:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "duration_seconds": 145.23,
  "total_records": 247,
  "scrapers_run": ["angellist", "crunchbase", "tracxn"],
  "scraper_results": {
    "angellist": {
      "success": true,
      "records": 65,
      "duration": 42.15,
      "error": null
    },
    "crunchbase": {
      "success": true,
      "records": 89,
      "duration": 61.08,
      "error": null
    }
  }
}
```

---

## 🐛 Troubleshooting

### Rate Limiting / IP Blocking

If you see:
```
⚠️  Circuit breaker open: Service recovering
```

**Solution:**
- Increase `rate_limit_delay` in `config.py`
- Reduce `limit_per_scraper`
- Run fewer scrapers simultaneously

### Failed URLs

Check `logs/investor_scraper.log` for details:
```bash
grep "Failed:" logs/investor_scraper.log
```

### Memory Issues (Large Runs)

For 10,000+ records:
1. Process in batches
2. Increase limit gradually
3. Monitor memory usage

---

## 🔄 Integration with Data Warehouse

### Export to Database

```python
from core.schemas import InvestorRecord
import sqlite3

conn = sqlite3.connect("investors.db")
for record in engine.all_records:
    conn.execute(
        "INSERT INTO investors VALUES (?, ?, ...)",
        (record.investor_name, record.investor_type, ...)
    )
conn.commit()
```

### Stream to S3

```python
import boto3

s3 = boto3.client("s3")
s3.upload_file("output/investors.csv", "my-bucket", "investors.csv")
```

---

## 📈 Future Enhancements

- [ ] Async scraping for 10x speedup
- [ ] Redis caching layer
- [ ] Streamlit dashboard
- [ ] Database integration
- [ ] GraphQL API
- [ ] Email notifications
- [ ] Scheduler (APScheduler)
- [ ] Advanced ML-based deduplication

---

## 📄 License

MIT License - Feel free to use for commercial purposes.

---

## 👨‍💻 Developer Notes

### Adding New Scraper

1. Create `scrapers/new_source.py`
2. Inherit from `BaseScraper`
3. Implement `scrape()` method
4. Add to `SCRAPERS` dict in `config.py`
5. Update `core/engine.py` to import

### Extending Validators

Edit `utils/validators.py` to add new validation rules.

### Custom Export Formats

Edit `pipeline/exporter.py` to add formats like JSON, Parquet, etc.

---

## 🆘 Support

- Check logs: `logs/investor_scraper.log`
- Enable verbose: `python main.py --verbose`
- Test scrapers individually: `python main.py --scrapers <name>`

---

**Built for production. Made for scale. Engineered for reliability.** 🚀
