# Market Intelligence Scripts

Scripts for gathering market intelligence data from external sources.

## Funding Data Scraper

Scrapes VC funding data from cryptorank.io.

### Quick Start

```bash
# 1. Setup (install Playwright)
bash setup_scraper.sh

# 2. Test the workflow
python test_scraper.py

# 3. Run a sync (requires authentication for full data)
export CRYPTORANK_EMAIL="your@email.com"
export CRYPTORANK_PASSWORD="your_password"
python continuous_funding_sync.py --pages 5
```

### Files

- **`cryptorank_scraper.py`** - Playwright-based scraper
- **`funding_ingestion.py`** - Database storage module  
- **`continuous_funding_sync.py`** - Orchestrator (one-time or scheduled)
- **`test_scraper.py`** - Test workflow without authentication
- **`setup_scraper.sh`** - Install dependencies

### Documentation

See [`docs/VC_FUNDING_WORKFLOW.md`](../../docs/VC_FUNDING_WORKFLOW.md) for complete documentation.

### Database

Creates/uses these tables:
- `investor` - VC funds, angels, corporate investors
- `company_funding_round` - Funding rounds with investor participation
- `company` (enhanced) - Adds social links (Twitter, GitHub, etc.)

Migration: `migration_scripts/11_funding_and_investor_schema.sql`

### Output

- **Scraped JSON**: `scraped_data/` directory
- **Screenshots** (debug mode): `screenshots/` directory
- **Database**: PostgreSQL `talent` database

### Common Tasks

```bash
# Scrape recent funding (1 page = 50 companies)
python continuous_funding_sync.py --pages 1

# Scrape specific company
python continuous_funding_sync.py --company echodotxyz

# Daily updates (continuous mode)
python continuous_funding_sync.py --continuous --interval 86400

# Debug mode (show browser + screenshots)
python continuous_funding_sync.py --company test --show-browser --screenshots
```

### Query Examples

```sql
-- Recent funding rounds
SELECT * FROM recent_funding ORDER BY announced_date DESC LIMIT 20;

-- Investor portfolios
SELECT * FROM investor_portfolio_summary ORDER BY portfolio_size DESC;

-- Companies backed by specific VC
SELECT c.company_name, cfr.amount_usd, cfr.announced_date
FROM investor i
JOIN company_funding_round cfr ON cfr.investors @> 
  jsonb_build_array(jsonb_build_object('investor_id', i.investor_id::text))
JOIN company c ON cfr.company_id = c.company_id
WHERE i.investor_name = 'Paradigm'
ORDER BY cfr.announced_date DESC;
```

