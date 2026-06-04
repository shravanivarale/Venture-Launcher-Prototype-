# Quick Start Guide

Get the investor scraper running in 5 minutes.

## 🚀 Installation (2 min)

### 1. Setup Environment

```bash
# Navigate to project
cd investor_scraper

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

That's it! ✅

---

## 🎯 First Run (3 min)

### Generate Sample Output (No Real Scraping)

```bash
python main.py --sample
```

**Output:**
```
✅ Sample output generated successfully!
  - CSV: output/investors.csv
  - Excel: output/investors.xlsx
```

### Check Generated Files

```bash
ls output/
# investors.csv
# investors.xlsx
```

Open `output/investors.xlsx` in Excel to see formatted data!

---

## 🔍 Real Scraping

### Run Full Pipeline

```bash
python main.py
```

This will:
1. ✅ Scrape from all sources
2. ✅ Clean & validate data
3. ✅ Remove duplicates
4. ✅ Export to CSV/Excel

**Typical duration**: 2-5 minutes for ~200 records

### Monitor Progress

Watch the logs in real-time:
```bash
tail -f logs/investor_scraper.log
```

---

## 🎛️ Common Commands

```bash
# Limit to 10 records per scraper (faster test)
python main.py --limit 10

# Only run 2 scrapers
python main.py --scrapers angellist crunchbase

# Export only CSV (skip Excel)
python main.py --output csv

# Verbose logging
python main.py --verbose

# Skip deduplication
python main.py --no-deduplicate

# See all options
python main.py --help
```

---

## 📊 View Results

### CSV File
```bash
cat output/investors.csv
```

### Excel File
```bash
# On Windows: just double-click
# On macOS: open output/investors.xlsx
# On Linux: libreoffice output/investors.xlsx
```

### Execution Summary
```bash
cat logs/pipeline_summary.json | python -m json.tool
```

---

## ⚡ Tips

### Faster Testing
```bash
# Quick test with limit
python main.py --limit 5 --scrapers angellist

# Should complete in < 30 seconds
```

### Troubleshooting
```bash
# Enable verbose output
python main.py --verbose

# Check logs
tail -100 logs/investor_scraper.log

# Look for errors
grep ERROR logs/investor_scraper.log
```

### Rate Limiting Issues
```bash
# If getting blocked/rate limited:
# 1. Increase delay in config.py: rate_limit_delay = 5
# 2. Reduce scrapers: python main.py --scrapers angellist
# 3. Reduce limit: python main.py --limit 10
```

---

## 🔄 Typical Workflow

```
1. Test with sample output
   └─ python main.py --sample

2. Quick test with one scraper
   └─ python main.py --scrapers angellist --limit 10

3. Full run
   └─ python main.py

4. Export analysis
   └─ Open output/investors.xlsx
```

---

## ✅ Success Indicators

After running, you should see:

```
✅ CSV exported successfully
✅ Excel exported successfully
✅ PIPELINE COMPLETED SUCCESSFULLY
```

And files:
- `output/investors.csv` (~100+ KB for ~100 records)
- `output/investors.xlsx` (~50+ KB for ~100 records)
- `logs/investor_scraper.log` (shows all operations)

---

## ❌ Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `ConnectionError` | Check internet, try later |
| `Rate limited` | Increase `rate_limit_delay` in config.py |
| `No records found` | Try sample mode first: `--sample` |
| `Excel won't open` | Check Excel is installed, check file size > 1KB |

---

## 📈 Next Steps

1. **Review output**: Open `investors.xlsx`
2. **Check quality**: Look at "Data Quality Score" column
3. **Analyze data**: Use Excel filters/pivot tables
4. **Schedule runs**: Add to cron/scheduler for daily updates
5. **Integrate**: Export to database/data warehouse

---

## 🆘 Need Help?

1. **Check logs**: `tail logs/investor_scraper.log`
2. **Read docs**: [README.md](README.md)
3. **Try sample**: `python main.py --sample`
4. **Enable verbose**: `python main.py --verbose`

---

**That's it! You're ready to go. Run `python main.py --help` to see all options.** 🚀
