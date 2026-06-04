# Troubleshooting Guide

Solutions for common issues.

---

## Installation Issues

### `ModuleNotFoundError: No module named 'requests'`

**Cause**: Dependencies not installed

**Solution**:
```bash
pip install -r requirements.txt
```

### `ModuleNotFoundError` after `pip install`

**Cause**: Wrong Python interpreter or venv not activated

**Solution**:
```bash
# Check which Python
which python
python --version

# Activate venv
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Install again
pip install -r requirements.txt
```

### `Permission denied` when installing

**Cause**: Running without proper permissions

**Solution**:
```bash
# Try with --user flag
pip install --user -r requirements.txt

# Or use venv (recommended)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Runtime Issues

### `ConnectionError: Failed to connect to xxx.com`

**Cause**: Network connectivity issue or server down

**Solution**:
```bash
# Check internet
ping google.com

# Try later (server might be down)
sleep 60 && python main.py

# Run single scraper to isolate issue
python main.py --scrapers angellist --verbose

# Check proxy settings if behind corporate firewall
```

### `Timeout error / Request timed out`

**Cause**: Slow network or server slow to respond

**Solution**:
```python
# In config.py, increase timeout
SCRAPER_CONFIG = {
    "timeout": 30,  # Increase from 15
}
```

```bash
# Or run with fewer scrapers
python main.py --scrapers angellist --limit 5
```

### `⚠️ Circuit breaker open`

**Cause**: Too many failures from a source

**Solution**:
```python
# In config.py, increase recovery timeout
CIRCUIT_BREAKER_CONFIG = {
    "recovery_timeout": 600,  # Increase from 300 (5 min)
    "failure_threshold": 10,  # Increase from 5
}
```

```bash
# Or skip failing scraper
python main.py --scrapers angellist crunchbase
```

### Rate limiting / Rapid-fire failures

**Cause**: Making requests too fast

**Solution**:
```python
# In config.py, increase rate limit delay
SCRAPER_CONFIG = {
    "rate_limit_delay": 5,  # Increase from 2
}
```

```bash
# Or reduce records per scraper
python main.py --limit 5
```

---

## Data Issues

### `No records found` / Empty output

**Cause**: 
- Scraper logic error
- Website structure changed
- All sources failed

**Solution**:
```bash
# 1. Test with sample data first
python main.py --sample

# 2. Run single scraper with verbose logging
python main.py --scrapers angellist --verbose

# 3. Check logs for errors
grep ERROR logs/investor_scraper.log
grep FAILED logs/investor_scraper.log

# 4. Check if website is accessible
curl https://www.angel.co

# 5. If website structure changed, update scraper
# Edit: scrapers/angellist.py
```

### `CSV file is empty or corrupted`

**Cause**: 
- No records found
- Export error

**Solution**:
```bash
# Check file size
ls -lh output/investors.csv

# View contents
head output/investors.csv

# Run pipeline again with verbose output
python main.py --verbose

# Check for export errors in logs
grep "export\|Export\|ERROR" logs/investor_scraper.log
```

### `Excel file won't open`

**Cause**: 
- File not fully written
- Corruption during export
- Excel locked/in use

**Solution**:
```bash
# 1. Close Excel
# 2. Delete old file
rm output/investors.xlsx

# 3. Re-run
python main.py --output excel

# 4. Wait for completion
# 5. Check file size is > 10KB

# If still issues, install openpyxl
pip install --upgrade openpyxl
```

### `Duplicate records not removed`

**Cause**: Fuzzy matching threshold too high

**Solution**:
```python
# In config.py, lower threshold (0-100)
CLEANING_CONFIG = {
    "fuzzy_match_threshold": 80,  # Lower from 85
}
```

```bash
# Or skip deduplication to diagnose
python main.py --no-deduplicate

# Check for similar names manually in CSV
```

### `Data quality score too low`

**Cause**: Many records missing fields

**Solution**:
```bash
# Use --verbose to see which fields are missing
python main.py --verbose

# Check logs for specific records
grep "Removed invalid record" logs/investor_scraper.log

# Adjust validation in pipeline/cleaner.py
```

---

## Performance Issues

### `Very slow / Takes too long`

**Cause**: Scraping large number of records, network slow, or rate limiting

**Solution**:
```bash
# Reduce scope for testing
python main.py --limit 10 --scrapers angellist

# Monitor progress in another terminal
tail -f logs/investor_scraper.log

# If consistent slowness, check network
speedtest-cli

# Use fewer scrapers
python main.py --scrapers crunchbase
```

### `Out of memory error`

**Cause**: Too many records in memory

**Solution**:
```bash
# Run with lower limit
python main.py --limit 100

# For very large runs, implement streaming
# (See ARCHITECTURE.md for recommendations)

# Check system memory
free -h  # Linux
memory_stats  # Windows
```

### `Disk full error`

**Cause**: Output files too large

**Solution**:
```bash
# Check disk space
df -h

# Delete old output files
rm output/*.csv output/*.xlsx

# Reduce scope
python main.py --limit 50 --output csv  # Skip Excel
```

---

## Logging Issues

### `No logs being written`

**Cause**: Log directory not created or permission issue

**Solution**:
```bash
# Create logs directory
mkdir -p logs

# Check permissions
ls -ld logs

# Try with sudo if permission denied
sudo python main.py

# Or fix permissions
chmod 755 logs
```

### `Logs too verbose / Not enough detail`

**Cause**: Log level setting

**Solution**:
```python
# In config.py
LOGGING_CONFIG = {
    "level": "DEBUG",  # More verbose
    # OR
    "level": "WARNING",  # Less verbose
}
```

```bash
# Or use CLI
python main.py --verbose
```

---

## LinkedIn Extraction Issues

### `No LinkedIn URLs found`

**Cause**: 
- LinkedIn search failing
- Rate limited by Google
- Names not recognized

**Solution**:
```bash
# Check if LinkedIn extraction is enabled
# In config.py:
LINKEDIN_CONFIG = {
    "use_google_serp": True,  # Should be True
}

# Try manual search
python -c "
from utils.linkedin_safe import extract_linkedin_safe
url = extract_linkedin_safe('Sequoia Capital')
print(url)
"

# If Google is blocking:
# - Increase rate_limit_delay
# - Use VPN/proxy
# - Run at different time
```

### `LinkedIn URLs pointing to wrong profiles`

**Cause**: Google SERP mismatched results

**Solution**:
```bash
# Manual verification
# 1. Open logs/investor_scraper.log
# 2. Look for LinkedIn search results
# 3. Manually verify in output/investors.xlsx

# Adjust search query in utils/linkedin_safe.py
# Or disable LinkedIn extraction:
LINKEDIN_CONFIG = {
    "use_google_serp": False,
}
```

---

## Source-Specific Issues

### `AngelList Scraper not finding investors`

**Cause**: AngelList website structure changed

**Solution**:
```bash
# Test manually
python -c "
from scrapers.angellist import AngelListScraper
scraper = AngelListScraper()
records = scraper.scrape()
print(f'Found {len(records)} records')
"

# If 0 records:
# 1. Check if website is accessible: https://www.angel.co
# 2. Update HTML selectors in scrapers/angellist.py
# 3. Check if AngelList requires JavaScript (we don't support)
```

### `Crunchbase rate limiting`

**Cause**: Crunchbase has strict rate limiting

**Solution**:
```bash
# Skip Crunchbase temporarily
python main.py --scrapers angellist tracxn letsventure

# Or increase delays
python main.py --scrapers crunchbase --limit 5 --verbose

# Crunchbase may require API key for production
# Consider Crunchbase API instead
```

### `Tracxn all records have same data`

**Cause**: Scraper parsing wrong elements

**Solution**:
```bash
# Check Tracxn selector in scrapers/tracxn.py
# Update HTML parser if website changed

# Verify website structure:
curl https://tracxn.com/explore/investors | grep "investor-card"

# If no matches, website structure changed - update selectors
```

---

## Development Issues

### `Circular import errors`

**Cause**: Module importing each other

**Solution**:
```python
# Move import to end of file
# Or restructure modules to avoid cycles

# Example: In core/engine.py, move at bottom:
from core.exceptions import CircuitBreakerOpenError
```

### `Pydantic validation errors`

**Cause**: Data doesn't match schema

**Solution**:
```bash
# Enable verbose logging to see validation errors
python main.py --verbose

# Check what's failing in logs
grep "validation\|Validation\|ValueError" logs/investor_scraper.log

# Debug specific record:
python -c "
from core.schemas import InvestorRecord

# Try creating record manually to see error
try:
    record = InvestorRecord(
        investor_name='X',  # Too short
        investor_type='VC'
    )
except Exception as e:
    print(e)
"
```

---

## System-Specific Issues

### Windows: `venv\Scripts\activate` not found

**Cause**: Wrong venv path or missing Scripts

**Solution**:
```bash
# Recreate venv
rmdir /s venv
python -m venv venv

# Then activate
venv\Scripts\activate
```

### macOS: `python: command not found`

**Cause**: Python not installed or wrong path

**Solution**:
```bash
# Install Python 3
brew install python3

# Use python3 explicitly
python3 -m venv venv
source venv/bin/activate
python3 main.py
```

### Linux: Permission denied on logs

**Cause**: Wrong user/permissions

**Solution**:
```bash
# Change permissions
chmod 755 logs

# Or recreate as current user
rm -rf logs
mkdir logs
python main.py
```

---

## Debugging Mode

### Enable full debug logging

```bash
python main.py --verbose
```

This shows:
- Every HTTP request/response
- Debug-level logging
- Full error traces

### Save debug logs

```bash
python main.py --verbose 2>&1 | tee debug_$(date +%s).log
```

### Inspect records directly

```python
# In Python REPL
from core.engine import ScrapeEngine
engine = ScrapeEngine()
records = engine.all_records
print(records[0])  # View first record
print(records[0].dict())  # View as dict
```

---

## Getting Help

1. **Check logs**: `tail -100 logs/investor_scraper.log`
2. **Enable verbose**: `python main.py --verbose`
3. **Run sample**: `python main.py --sample`
4. **Test single scraper**: `python main.py --scrapers angellist`
5. **Read README**: [README.md](README.md)
6. **Read ARCHITECTURE**: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Report an Issue

Include:
```bash
# 1. Command you ran
python main.py --scrapers angellist --limit 10 --verbose

# 2. Error message
# (copy from terminal or logs)

# 3. Logs
tail -50 logs/investor_scraper.log

# 4. System info
python --version
pip list | grep requests
```

---

**Most issues can be resolved by enabling `--verbose` mode and checking logs.** 📋
