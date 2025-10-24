#!/bin/bash

echo "=========================================="
echo "🔴 LIVE DISCOVERY MONITORING"
echo "=========================================="
echo ""
echo "Press Ctrl+C to stop watching (discovery will continue)"
echo ""

# Get the latest log file
LOG_FILE=$(ls -t logs/overnight_discovery_*.log 2>/dev/null | head -1)

if [ -z "$LOG_FILE" ]; then
    echo "❌ No discovery log file found!"
    exit 1
fi

# Check if process is running
if [ -f logs/discovery_pid.txt ]; then
    PID=$(cat logs/discovery_pid.txt)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Discovery process is RUNNING (PID: $PID)"
        ELAPSED=$(ps -p $PID -o etime= | tr -d ' ')
        echo "⏱️  Running for: $ELAPSED"
    else
        echo "⚠️  Discovery process has stopped"
    fi
else
    echo "⚠️  No PID file found"
fi

echo ""
echo "📁 Watching: $LOG_FILE"
echo ""
echo "Latest activity:"
echo "=========================================="

# Show last 30 lines and keep updating
tail -f -n 30 "$LOG_FILE" | while read line; do
    # Colorize output based on content
    if [[ $line == *"ERROR"* ]]; then
        echo "❌ $line"
    elif [[ $line == *"Processing:"* ]] || [[ $line == *"📦"* ]]; then
        echo ""
        echo "🔄 $line"
    elif [[ $line == *"✅"* ]] || [[ $line == *"Completed"* ]]; then
        echo "✅ $line"
    elif [[ $line == *"contributors"* ]] || [[ $line == *"Found"* ]]; then
        echo "📊 $line"
    elif [[ $line == *"["*"/"*"]"* ]]; then
        echo "👤 $line"
    else
        echo "$line"
    fi
done

