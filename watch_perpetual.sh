#!/bin/bash

echo "=========================================="
echo "🔴 PERPETUAL DISCOVERY LIVE MONITOR"
echo "=========================================="
echo ""

# Check if process is running
if [ -f logs/perpetual_pid.txt ]; then
    PID=$(cat logs/perpetual_pid.txt)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Discovery engine is RUNNING (PID: $PID)"
        ELAPSED=$(ps -p $PID -o etime= | tr -d ' ')
        echo "⏱️  Running for: $ELAPSED"
    else
        echo "⚠️  Discovery engine has stopped"
    fi
else
    echo "⚠️  No PID file found"
fi

echo ""
echo "Press Ctrl+C to stop watching (discovery will continue)"
echo ""

# Get the latest log file
LOG_FILE=$(ls -t logs/perpetual_discovery_*.log 2>/dev/null | head -1)

if [ -z "$LOG_FILE" ]; then
    echo "❌ No discovery log file found!"
    exit 1
fi

echo "📁 Watching: $LOG_FILE"
echo ""
echo "=========================================="

# Show last 40 lines and keep updating
tail -f -n 40 "$LOG_FILE" | while read line; do
    # Colorize output based on content
    if [[ $line == *"ERROR"* ]]; then
        echo "❌ $line"
    elif [[ $line == *"CYCLE"* ]] || [[ $line == *"🔄"* ]]; then
        echo ""
        echo "🔄 $line"
    elif [[ $line == *"✅"* ]] || [[ $line == *"Completed"* ]]; then
        echo "✅ $line"
    elif [[ $line == *"📦"* ]] || [[ $line == *"Processing:"* ]]; then
        echo ""
        echo "📦 $line"
    elif [[ $line == *"STATS"* ]] || [[ $line == *"📊"* ]]; then
        echo "📊 $line"
    elif [[ $line == *"Contributors"* ]] || [[ $line == *"Repos"* ]]; then
        echo "📈 $line"
    elif [[ $line == *"NEW:"* ]] || [[ $line == *"✨"* ]]; then
        echo "✨ $line"
    elif [[ $line == *"🔍"* ]] || [[ $line == *"Discovering"* ]]; then
        echo "🔍 $line"
    elif [[ $line == *"Found"* ]]; then
        echo "📍 $line"
    else
        echo "$line"
    fi
done

