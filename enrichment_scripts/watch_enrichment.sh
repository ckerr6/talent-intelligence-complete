#!/bin/bash
# Watch enrichment progress in real-time
# Usage: ./watch_enrichment.sh [interval_seconds]

INTERVAL=${1:-10}

echo "Watching enrichment progress every ${INTERVAL}s..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    python3 monitor_enrichment_progress.py
    sleep $INTERVAL
done

