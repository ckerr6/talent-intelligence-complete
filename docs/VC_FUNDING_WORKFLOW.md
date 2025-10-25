# VC Funding Data Workflow

**Status:** ✅ Complete and ready to use  
**Created:** October 25, 2025  
**Branch:** `github-native-intelligence`

## Overview

This workflow scrapes VC funding data from cryptorank.io and stores it in our PostgreSQL database. It captures:

- **Funding rounds**: Amount, stage, date, valuation
- **Investors**: VC firms, angels, corporate investors with their portfolios
- **Company data**: Social links (Twitter, GitHub, LinkedIn), website, metadata
- **Cap tables**: Full investor participation per round

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  cryptorank.io                                       │
│  - Funding list (50 companies/page)                 │
│  - Company detail pages (funding rounds + investors)│
│  - Overview pages (social links, metadata)          │
└────────────────┬────────────────────────────────────┘
                 │
                 │ Playwright Scraper
                 ▼
┌─────────────────────────────────────────────────────┐
│  Scraped Data (JSON)                                │
│  scripts/market_intelligence/scraped_data/          │
└────────────────┬────────────────────────────────────┘
                 │
                 │ Ingestion Module
                 ▼
┌─────────────────────────────────────────────────────┐
│  PostgreSQL 'talent' Database                       │
│  - investor (VC funds, angels)                      │
│  - company_funding_round (raises, cap tables)       │
│  - company (enhanced with social links)             │
└─────────────────────────────────────────────────────┘
```

## Components

### 1. Database Schema (`migration_scripts/11_funding_and_investor_schema.sql`)

**New Tables:**
- `investor`: VC funds, angels, corporate investors
  - Fields: name, type, website, LinkedIn, Twitter, cryptorank_slug
  - Seeded with 10 major crypto VCs (a16z, Paradigm, etc.)

**Enhanced Tables:**
- `company_funding_round`: Added valuation, stage, investors JSONB, source
- `company`: Added Twitter, GitHub, Telegram, Discord, cryptorank_slug

**Views:**
- `recent_funding`: Recent funding activity with company details
- `investor_portfolio_summary`: Investor activity and metrics

### 2. Playwright Scraper (`scripts/market_intelligence/cryptorank_scraper.py`)

**Features:**
- Async/await for performance
- Login support (required for full data access)
- Headless or visible browser mode
- Screenshot capture for debugging
- Robust error handling and retries

**Key Methods:**
- `scrape_funding_list(pages)`: Scrape funding rounds list
- `scrape_company_detail(slug)`: Deep dive on specific company
- `_extract_funding_rounds()`: Parse funding round details
- `_extract_social_links()`: Extract social media URLs

**Usage:**
```bash
# Scrape funding list (first 5 pages = 250 companies)
python scripts/market_intelligence/cryptorank_scraper.py --pages 5 --output data.json

# Scrape specific company
python scripts/market_intelligence/cryptorank_scraper.py --company echodotxyz --output company.json

# With authentication
python scripts/market_intelligence/cryptorank_scraper.py \
  --email user@example.com \
  --password secret \
  --pages 10
```

### 3. Data Ingestion (`scripts/market_intelligence/funding_ingestion.py`)

**Features:**
- Idempotent: Safe to run multiple times
- Company matching: Links to existing companies by name or cryptorank_slug
- Investor deduplication: Merges investors by name/slug
- JSONB storage: Investors stored as structured JSON in funding rounds

**Key Methods:**
- `store_funding_list(funding_list)`: Batch process funding rounds
- `store_funding_round(funding_data)`: Store single round with all details
- `_get_or_create_company()`: Find or create company record
- `_get_or_create_investor()`: Find or create investor record

**Usage:**
```bash
# Ingest scraped data
python scripts/market_intelligence/funding_ingestion.py data.json
```

### 4. Continuous Sync Orchestrator (`scripts/market_intelligence/continuous_funding_sync.py`)

**Features:**
- One-time or continuous mode
- Automatic scraping + ingestion
- Saves raw JSON (audit trail)
- Statistics and logging
- Configurable sync intervals

**Modes:**

1. **One-time sync** (scrape + ingest immediately):
```bash
python scripts/market_intelligence/continuous_funding_sync.py --pages 5
```

2. **Specific company**:
```bash
python scripts/market_intelligence/continuous_funding_sync.py --company echodotxyz
```

3. **Continuous mode** (daily updates):
```bash
python scripts/market_intelligence/continuous_funding_sync.py \
  --continuous \
  --pages 10 \
  --interval 86400  # 24 hours
```

4. **With authentication**:
```bash
export CRYPTORANK_EMAIL="your_email@example.com"
export CRYPTORANK_PASSWORD="your_password"
python scripts/market_intelligence/continuous_funding_sync.py --pages 10
```

## Setup Instructions

### Step 1: Install Dependencies

```bash
# Run setup script (installs Playwright + browsers)
bash scripts/market_intelligence/setup_scraper.sh

# Or manually:
pip install playwright psycopg2-binary
python -m playwright install chromium
```

### Step 2: Run Database Migration

```bash
psql -d talent -f migration_scripts/11_funding_and_investor_schema.sql
```

### Step 3: Configure Credentials (Optional but Recommended)

Create a `.env` file or export environment variables:

```bash
export CRYPTORANK_EMAIL="your_email@example.com"
export CRYPTORANK_PASSWORD="your_password"
```

**Why authentication?** Some funding data (investor lists, detailed rounds) requires login.

### Step 4: Run Your First Sync

```bash
# Scrape first 5 pages (250 companies)
python scripts/market_intelligence/continuous_funding_sync.py --pages 5
```

## Workflow Examples

### Example 1: Daily Funding Updates

Run this as a cron job for daily updates:

```bash
# crontab -e
0 6 * * * cd /path/to/talent-intelligence-complete && \
  export CRYPTORANK_EMAIL="..." && \
  export CRYPTORANK_PASSWORD="..." && \
  python scripts/market_intelligence/continuous_funding_sync.py --pages 10 \
  >> logs/funding_sync.log 2>&1
```

### Example 2: Backfill Historical Data

Scrape many pages one time:

```bash
# Scrape first 50 pages (2,500 companies)
python scripts/market_intelligence/continuous_funding_sync.py --pages 50
```

### Example 3: Enrich Specific Companies

After discovering interesting companies, scrape detailed data:

```bash
# List of companies to enrich
for company in echodotxyz uniswap-labs base-protocol; do
  python scripts/market_intelligence/continuous_funding_sync.py --company $company
  sleep 5  # Rate limiting
done
```

### Example 4: Debug Mode

Run with browser visible and screenshots:

```bash
python scripts/market_intelligence/continuous_funding_sync.py \
  --company echodotxyz \
  --show-browser \
  --screenshots
```

Screenshots saved to: `scripts/market_intelligence/screenshots/`

## Querying Funding Data

### Recent Funding Rounds

```sql
-- Recent raises
SELECT * FROM recent_funding
ORDER BY announced_date DESC
LIMIT 20;

-- Companies by total funding
SELECT 
  c.company_name,
  c.website_url,
  COUNT(cfr.round_id) as total_rounds,
  SUM(cfr.amount_usd) as total_raised_usd
FROM company c
JOIN company_funding_round cfr ON c.company_id = cfr.company_id
WHERE cfr.amount_usd IS NOT NULL
GROUP BY c.company_id
ORDER BY total_raised_usd DESC
LIMIT 50;
```

### Investor Analysis

```sql
-- Most active investors
SELECT * FROM investor_portfolio_summary
ORDER BY portfolio_size DESC
LIMIT 20;

-- Find companies backed by specific VC
SELECT 
  c.company_name,
  cfr.announced_date,
  cfr.amount_usd,
  cfr.round_stage
FROM investor i
JOIN company_funding_round cfr ON cfr.investors @> jsonb_build_array(
  jsonb_build_object('investor_id', i.investor_id::text)
)
JOIN company c ON cfr.company_id = c.company_id
WHERE i.investor_name = 'Paradigm'
ORDER BY cfr.announced_date DESC;
```

### Co-Investment Networks

```sql
-- Find investors who often co-invest together
SELECT 
  i1.investor_name as investor_1,
  i2.investor_name as investor_2,
  COUNT(*) as co_investments
FROM company_funding_round cfr
CROSS JOIN LATERAL jsonb_array_elements(cfr.investors) as inv1
CROSS JOIN LATERAL jsonb_array_elements(cfr.investors) as inv2
JOIN investor i1 ON i1.investor_id::text = (inv1->>'investor_id')
JOIN investor i2 ON i2.investor_id::text = (inv2->>'investor_id')
WHERE i1.investor_id < i2.investor_id  -- Avoid duplicates
GROUP BY i1.investor_id, i2.investor_id, i1.investor_name, i2.investor_name
HAVING COUNT(*) >= 3
ORDER BY co_investments DESC;
```

## Data Quality

### Coverage Metrics

```sql
-- Check data completeness
SELECT 
  COUNT(*) as total_rounds,
  COUNT(amount_usd) as with_amount,
  COUNT(valuation_usd) as with_valuation,
  COUNT(round_stage) as with_stage,
  COUNT(CASE WHEN jsonb_array_length(investors) > 0 THEN 1 END) as with_investors
FROM company_funding_round;

-- Companies with social links
SELECT 
  COUNT(*) as total_companies,
  COUNT(twitter_url) as with_twitter,
  COUNT(github_url) as with_github,
  COUNT(linkedin_url) as with_linkedin,
  COUNT(website_url) as with_website
FROM company
WHERE cryptorank_slug IS NOT NULL;
```

### Validation

```sql
-- Find funding rounds without company match
SELECT * FROM company_funding_round
WHERE company_id IS NULL;

-- Find investors without portfolio
SELECT i.* FROM investor i
LEFT JOIN company_funding_round cfr ON cfr.investors @> jsonb_build_array(
  jsonb_build_object('investor_id', i.investor_id::text)
)
WHERE cfr.round_id IS NULL;
```

## Troubleshooting

### Issue: Login fails

**Solution:** Ensure credentials are correct. Try logging in manually to verify account works.

```bash
# Test login
python scripts/market_intelligence/cryptorank_scraper.py \
  --email your@email.com \
  --password secret \
  --show-browser \
  --screenshots
```

### Issue: Playwright not installed

**Solution:** Install Playwright browsers:

```bash
python -m playwright install chromium
```

### Issue: Selectors not finding elements

**Solution:** CryptoRank's HTML may have changed. Run with `--show-browser` and `--screenshots` to debug:

```bash
python scripts/market_intelligence/continuous_funding_sync.py \
  --company echodotxyz \
  --show-browser \
  --screenshots
```

Check screenshots in `scripts/market_intelligence/screenshots/` to see what the scraper saw.

### Issue: Rate limiting

**Solution:** Add delays between requests or reduce pages per sync:

```python
# In continuous_funding_sync.py, add delay after each company:
await asyncio.sleep(5)  # 5 second delay
```

### Issue: Database connection errors

**Solution:** Verify PostgreSQL is running and credentials are correct:

```bash
python config.py  # Check database status
```

## Performance Considerations

### Scraping Speed

- **Per page (50 companies):** ~30-60 seconds (list view only)
- **Per company detail:** ~10-15 seconds (2 pages: funding + overview)
- **Full detail scrape (250 companies):** ~40-60 minutes

### Database Performance

- Indexes on all foreign keys and lookup fields
- JSONB GIN indexes for investor queries
- Connection pooling (5-50 connections)

### Recommendations

1. **Start small:** Test with 1-5 pages before scaling
2. **Use authentication:** Gets more complete data
3. **Run off-peak:** Less likely to hit rate limits
4. **Monitor logs:** Check `logs/` directory for errors
5. **Save raw JSON:** Allows re-ingestion if schema changes

## Future Enhancements

### Potential Additions

1. **More data sources:** CrunchBase, PitchBook, Messari
2. **Investor enrichment:** Scrape investor detail pages
3. **Historical tracking:** Track valuation changes over time
4. **Smart matching:** ML-based company matching
5. **API integration:** If CryptoRank offers API access
6. **Alerting:** Notify on new funding rounds for tracked companies
7. **Portfolio analysis:** Find companies in investor portfolios

### API Endpoints

Consider adding FastAPI endpoints:

```python
# api/routers/funding.py

@router.get("/funding/recent")
async def get_recent_funding(limit: int = 50):
    """Get recent funding rounds"""
    
@router.get("/funding/company/{company_id}")
async def get_company_funding(company_id: UUID):
    """Get all funding rounds for a company"""
    
@router.get("/investors/{investor_id}/portfolio")
async def get_investor_portfolio(investor_id: UUID):
    """Get investor's portfolio companies"""
```

## Files Reference

```
scripts/market_intelligence/
├── cryptorank_scraper.py          # Playwright scraper
├── funding_ingestion.py           # Database storage
├── continuous_funding_sync.py     # Orchestrator
├── setup_scraper.sh               # Setup script
├── scraped_data/                  # Raw JSON output
└── screenshots/                   # Debug screenshots

migration_scripts/
└── 11_funding_and_investor_schema.sql  # Database schema

Database Tables:
├── investor                       # VC funds, angels
├── company_funding_round          # Funding rounds
└── company (enhanced)             # Social links added
```

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Run with `--show-browser --screenshots` for debugging
3. Review this documentation
4. Check database with `python config.py`

---

**Last Updated:** October 25, 2025  
**Author:** Charlie + Cursor  
**Status:** ✅ Production ready

