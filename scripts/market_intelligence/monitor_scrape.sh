#!/bin/bash
# ABOUTME: Monitor the progress of a long-running scrape
# ABOUTME: Shows statistics and latest activity from the log file

LOG_FILE=${1:-scrape_100_pages.log}

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo "Usage: ./monitor_scrape.sh [logfile]"
    exit 1
fi

clear
echo "========================================================================"
echo "CryptoRank Scrape Monitor"
echo "========================================================================"
echo "Log file: $LOG_FILE"
echo ""

# Count progress
PAGES_SCRAPED=$(grep -c "Scraping page" "$LOG_FILE" || echo "0")
COMPANIES_DETAILED=$(grep -c "Scraping.*\[" "$LOG_FILE" || echo "0")
COMPANIES_STORED=$(grep "companies_stored" "$LOG_FILE" | tail -1 | grep -o "'companies_stored': [0-9]*" | grep -o "[0-9]*" || echo "0")
ROUNDS_CREATED=$(grep "rounds_created" "$LOG_FILE" | tail -1 | grep -o "'rounds_created': [0-9]*" | grep -o "[0-9]*" || echo "0")
INVESTORS_CREATED=$(grep "investors_created" "$LOG_FILE" | tail -1 | grep -o "'investors_created': [0-9]*" | grep -o "[0-9]*" || echo "0")
ERRORS=$(grep -c "ERROR" "$LOG_FILE" || echo "0")

echo "📊 Progress:"
echo "  Pages scraped:       $PAGES_SCRAPED"
echo "  Companies detailed:  $COMPANIES_DETAILED"
echo "  Companies stored:    $COMPANIES_STORED"
echo "  Rounds created:      $ROUNDS_CREATED"
echo "  Investors created:   $INVESTORS_CREATED"
echo "  Errors:              $ERRORS"
echo ""

# Show latest activity
echo "📝 Latest Activity (last 20 lines):"
echo "------------------------------------------------------------------------"
tail -20 "$LOG_FILE"
echo "------------------------------------------------------------------------"
echo ""

# Check if still running
if ps aux | grep -q "[p]ython3.*continuous_funding_sync.py"; then
    echo "✅ Scrape is still running"
else
    echo "❌ Scrape has stopped"
    
    # Check if completed successfully
    if grep -q "✅ Sync complete" "$LOG_FILE"; then
        echo "✅ Completed successfully!"
    else
        echo "⚠️  May have exited with errors"
    fi
fi

echo ""
echo "Commands:"
echo "  Watch live: tail -f $LOG_FILE"
echo "  Monitor:    ./monitor_scrape.sh $LOG_FILE"
echo "  Stop:       pkill -f continuous_funding_sync.py"
echo "========================================================================"

