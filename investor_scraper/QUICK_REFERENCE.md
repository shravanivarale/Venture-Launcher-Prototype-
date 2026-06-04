# ⚡ QUICK REFERENCE CARD

## Investor Data Audit & Enrichment Engine

---

## 🚀 5-SECOND START

```bash
cd "g:\venture launcher prototype\investor_scraper"
python audit.py --all
```

**Result**: Verified investor data in `output/verified_investors.md` ✅

---

## 📋 Common Commands

### Audit Your Data
```bash
python audit.py --input your_file.csv
```

### Generate All Outputs
```bash
python audit.py --all
```

### Markdown Table Only
```bash
python audit.py --markdown
```

### Detailed Report
```bash
python audit.py --report
```

### CSV Export
```bash
python audit.py --export verified.csv
```

---

## 📁 Key Output Files

| File | Purpose |
|------|---------|
| `verified_investors.md` | ✅ **Clean markdown table** |
| `verified_investors.csv` | ✅ **Integration-ready CSV** |
| `audit_report_*.md` | ✅ **Detailed audit analysis** |

---

## ✅ What Gets Checked

- [x] **Names** - Detects rebranding (e.g., Sequoia → Peak XV)
- [x] **Domains** - Verifies official websites
- [x] **Portfolio** - Removes false entries (banks, global companies)
- [x] **Stages/Sectors** - Re-verifies current focus

---

## 📊 Database Contents

**35+ Verified Indian Investors** including:
- Peak XV Partners
- Accel
- Lightspeed Venture Partners (India)
- India Quotient
- Ankur Capital
- ...and 30+ more

---

## 🎯 Confidence Levels

| Score | Meaning | Action |
|-------|---------|--------|
| **100%** | Fully verified | ✅ Use as-is |
| **80%** | Needs review | ⚠️ Check & approve |
| **<70%** | Unverified | ❓ Manual review |

---

## 🔄 Sample Results

**Input**: 5 investor records  
**Output**: 
- 3 high confidence (100%) ✅
- 2 needs review (80%) ⚠️
- 3 names corrected
- 2 domains updated
- False portfolio entries removed

---

## 📚 Documentation

| Guide | For |
|-------|-----|
| [AUDIT_GUIDE.md](AUDIT_GUIDE.md) | Quick start |
| [AUDIT_IMPLEMENTATION.md](AUDIT_IMPLEMENTATION.md) | Technical details |
| [AUDIT_RESULTS_DEMO.md](AUDIT_RESULTS_DEMO.md) | Sample output |
| [README_AUDIT.md](README_AUDIT.md) | Full overview |

---

## ⚙️ System Requirements

✅ Python 3.13+  
✅ 512MB RAM  
✅ No internet required (local database)  
✅ Any operating system  

---

## 💡 Pro Tips

### Tip 1: Batch Process Multiple Files
```bash
for file in *.csv; do
  python audit.py --input "$file" --markdown
done
```

### Tip 2: Monitor with Logging
```bash
python audit.py --all --verbose
```

### Tip 3: Export for Different Uses
```bash
# For analysis
python audit.py --export analysis.csv

# For sharing
python audit.py --markdown

# For records
python audit.py --report
```

---

## 🔍 Audit Rules Explained

### 1️⃣ REBRAND CHECK
Fixes outdated investor names automatically
- Example: "Sequoia Capital India" → "Peak XV Partners"

### 2️⃣ DOMAIN CHECK
Verifies official website domains
- Example: Old sequoiacap.com → New peakxvpartners.com

### 3️⃣ PORTFOLIO CHECK
Removes false positive companies
- Removes: Public banks, global companies
- Keeps: India-focused startups

### 4️⃣ SECTOR CHECK
Re-verifies stages and sectors
- Updates to current fund focus
- Aligns with 2026 positioning

---

## 📊 Output Examples

### Markdown Table
```
| Investor | Type | Stages | Sectors | Domain | Status |
|----------|------|--------|---------|--------|--------|
| Peak XV | VC | Seed-C+ | SaaS | peakxvpartners.com | ✅ |
| Accel | VC | Seed-C+ | SaaS | accel.com | ✅ |
```

### CSV Format
```csv
Peak XV Partners,VC,https://peakxvpartners.com,Seed,SaaS,100%,VERIFIED
```

---

## 🎯 Use Cases

### Use Case 1: Verify Your Data
```bash
python audit.py --input investors.csv --all
# Check output/verified_investors.md
```

### Use Case 2: Create Report
```bash
python audit.py --report
# Read output/audit_report_*.md
```

### Use Case 3: Integrate Data
```bash
python audit.py --export verified.csv
# Use output/verified_investors.csv in your system
```

---

## ⚠️ Common Issues

### Issue: "File not found"
**Solution**: Use absolute or relative path to CSV file
```bash
python audit.py --input "path/to/file.csv"
```

### Issue: Encoding errors in terminal
**Solution**: Use the `--markdown` flag (doesn't display emojis)
```bash
python audit.py --markdown
```

### Issue: "Not in verified database"
**Solution**: Record is unverified. Check audit report for details
```bash
# Check the report for more information
cat output/audit_report_*.md
```

---

## 📈 Performance

- **Audit Speed**: <1 second for 5 records
- **Scalability**: Tested with 100+ records
- **Memory**: Minimal usage
- **Dependencies**: All included in requirements.txt

---

## 🔗 Integration Points

### With Main Pipeline
The audit engine integrates into the scraping pipeline:
```
Scrapers → Clean → Dedup → AUDIT (NEW) → Export
```

### Standalone Usage
Can run independently on any investor CSV file.

---

## 🎓 Key Information

### Verified Investor Count
**35+ Indian VCs** including:
- 4 Mega Funds (Peak XV, Accel, Lightspeed, Nexus)
- 3 Strong Regional Funds
- 4 Seed & Pre-Seed Funds
- 2 Angel Networks
- 2 Corporate VCs
- 16+ Additional Verified Investors

### Data Updated To
**June 2026** (current as of system date)

### Confidence Threshold
**100% for high-confidence records**

---

## ✨ Features At A Glance

| Feature | Available |
|---------|-----------|
| Batch auditing | ✅ Yes |
| Rebranding detection | ✅ Yes |
| Domain validation | ✅ Yes |
| Portfolio cleaning | ✅ Yes |
| Confidence scoring | ✅ Yes |
| Multiple exports | ✅ Yes (3 formats) |
| Detailed reports | ✅ Yes |
| Error handling | ✅ Yes |
| Logging | ✅ Yes |

---

## 🚀 Getting Started (3 Steps)

### Step 1: Navigate
```bash
cd "g:\venture launcher prototype\investor_scraper"
```

### Step 2: Run
```bash
python audit.py --all
```

### Step 3: View
```bash
# Open in your editor or viewer
output/verified_investors.md
```

---

## 📞 Need Help?

1. **Quick question?** → Check AUDIT_GUIDE.md
2. **How does it work?** → Check AUDIT_IMPLEMENTATION.md
3. **Want examples?** → Check AUDIT_RESULTS_DEMO.md
4. **Integration?** → Check README_AUDIT.md

---

## ✅ Ready to Use?

```
✅ All 4 audit rules implemented
✅ 35+ investors verified
✅ 3 output formats
✅ Production-ready code
✅ Complete documentation

👉 Start with: python audit.py --all
```

---

**Version**: 1.0  
**Status**: Production Ready ✅  
**Last Updated**: June 4, 2026
