#!/bin/bash
# Continuous GitHub Stats Enrichment
# Runs in background, enriching profiles gradually to respect rate limits

echo "🚀 Starting continuous GitHub enrichment service..."
echo "   This will enrich 50 profiles every hour"
echo "   Press Ctrl+C to stop"
echo ""

cd "$(dirname "$0")/.."

# Check if GITHUB_TOKEN is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  WARNING: No GITHUB_TOKEN set!"
    echo "   Set it in .env or export GITHUB_TOKEN=your_token"
    echo "   Without a token, rate limits are very restrictive (60/hour vs 5000/hour)"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

BATCH_SIZE=50
SLEEP_TIME=3600  # 1 hour

iteration=1

while true; do
    echo "═══════════════════════════════════════════════════════════"
    echo "🔄 Iteration #$iteration - $(date)"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    
    # Run enrichment
    python enrichment_scripts/enrich_github_enhanced_stats.py --limit $BATCH_SIZE
    
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo ""
        echo "✅ Batch complete!"
    else
        echo ""
        echo "❌ Batch failed with exit code $exit_code"
    fi
    
    echo ""
    echo "⏳ Waiting $((SLEEP_TIME / 60)) minutes before next batch..."
    echo "   Next batch at: $(date -v +${SLEEP_TIME}S '+%H:%M:%S' 2>/dev/null || date -d "+${SLEEP_TIME} seconds" '+%H:%M:%S' 2>/dev/null)"
    echo ""
    
    sleep $SLEEP_TIME
    iteration=$((iteration + 1))
done

