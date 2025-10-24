#!/bin/bash
# Watch live discovery progress

echo "=========================================="
echo "🔴 LIVE DISCOVERY MONITORING"
echo "=========================================="
echo ""
echo "Press Ctrl+C to stop watching (discovery will continue)"
echo ""
echo "Showing last 50 lines, updating every 3 seconds..."
echo ""
echo "=========================================="
echo ""

# Find the latest log file
LOG_FILE=$(ls -t logs/comprehensive_discovery_*.log 2>/dev/null | head -1)

if [ -z "$LOG_FILE" ]; then
    echo "❌ No discovery log found"
    echo "Start discovery with: python3 scripts/github/comprehensive_discovery.py"
    exit 1
fi

echo "📁 Watching: $LOG_FILE"
echo ""

# Watch the log file
tail -f "$LOG_FILE"

