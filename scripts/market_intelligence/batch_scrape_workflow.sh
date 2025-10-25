#!/bin/bash
# ABOUTME: Automated workflow to scrape and enrich funding data in batches
# ABOUTME: Handles failures gracefully and provides progress tracking

set -e

WORKSPACE="/Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete"
cd "$WORKSPACE"

echo "=================================================================="
echo "VC Funding Scraper - Automated Batch Workflow"
echo "=================================================================="
echo ""
echo "This will scrape funding data in batches:"
echo "  1. Scrape list data (fast, no detail visits)"
echo "  2. Enrich top funded companies with details"
echo ""

# Configuration
PAGES_PER_BATCH=${1:-10}
TOTAL_BATCHES=${2:-10}
ENRICH_TOP=${3:-20}

echo "Configuration:"
echo "  Pages per batch: $PAGES_PER_BATCH"
echo "  Total batches: $TOTAL_BATCHES"
echo "  Enrich top N companies: $ENRICH_TOP"
echo ""

# Create logs directory
mkdir -p logs/batch_scraping

# Run batches
for batch in $(seq 1 $TOTAL_BATCHES); do
    echo "=================================================================="
    echo "Batch $batch/$TOTAL_BATCHES - $(date)"
    echo "=================================================================="
    
    LOG_FILE="logs/batch_scraping/batch_${batch}.log"
    
    echo "Scraping $PAGES_PER_BATCH pages..."
    
    # Run scrape
    PYTHONPATH=$PWD python3 scripts/market_intelligence/continuous_funding_sync.py \
        --pages $PAGES_PER_BATCH \
        --no-details \
        2>&1 | tee "$LOG_FILE"
    
    # Check if successful
    if [ $? -eq 0 ]; then
        echo "✅ Batch $batch complete"
        
        # Get stats from database
        TOTAL_COMPANIES=$(psql -d talent -t -c "SELECT COUNT(DISTINCT company_id) FROM company WHERE cryptorank_slug IS NOT NULL;" | xargs)
        echo "📊 Total companies in database: $TOTAL_COMPANIES"
    else
        echo "❌ Batch $batch failed, but continuing..."
    fi
    
    # Small delay between batches
    echo "Waiting 5 seconds before next batch..."
    sleep 5
    echo ""
done

echo "=================================================================="
echo "List scraping complete! Now enriching top companies..."
echo "=================================================================="

# Enrich top funded companies
echo "Enriching top $ENRICH_TOP funded companies..."
PYTHONPATH=$PWD python3 scripts/market_intelligence/enrich_companies.py \
    --from-db \
    --min-amount 1000000 \
    --max-count $ENRICH_TOP \
    2>&1 | tee logs/batch_scraping/enrichment.log

echo ""
echo "=================================================================="
echo "✅ Workflow complete!"
echo "=================================================================="
echo ""

# Final statistics
echo "📊 Final Statistics:"
psql -d talent -c "
SELECT 
    COUNT(DISTINCT c.company_id) as total_companies,
    COUNT(DISTINCT cfr.round_id) as total_rounds,
    SUM(cfr.amount_usd) as total_funding_tracked,
    COUNT(DISTINCT CASE WHEN c.website_url IS NOT NULL THEN c.company_id END) as companies_enriched
FROM company c
LEFT JOIN company_funding_round cfr ON c.company_id = cfr.company_id AND cfr.source = 'cryptorank'
WHERE c.cryptorank_slug IS NOT NULL;
"

echo ""
echo "View logs in: logs/batch_scraping/"
echo "=================================================================="

