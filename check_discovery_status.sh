#!/bin/bash

echo "=========================================="
echo "📊 DISCOVERY STATUS SNAPSHOT"
echo "=========================================="
echo ""

# Check if process is running
if [ -f logs/discovery_pid.txt ]; then
    PID=$(cat logs/discovery_pid.txt)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Discovery process is RUNNING"
        echo "   PID: $PID"
        ELAPSED=$(ps -p $PID -o etime= | tr -d ' ')
        echo "   Running for: $ELAPSED"
        CPU=$(ps -p $PID -o %cpu= | tr -d ' ')
        MEM=$(ps -p $PID -o %mem= | tr -d ' ')
        echo "   CPU: ${CPU}%  |  Memory: ${MEM}%"
    else
        echo "❌ Discovery process has STOPPED"
        echo "   Last PID: $PID"
    fi
else
    echo "⚠️  No discovery process found"
fi

echo ""
echo "=========================================="
echo "📁 LOG FILE STATUS"
echo "=========================================="

# Get the latest log file
LOG_FILE=$(ls -t logs/overnight_discovery_*.log 2>/dev/null | head -1)

if [ -z "$LOG_FILE" ]; then
    echo "❌ No discovery log file found!"
    exit 1
fi

echo "📁 Latest log: $LOG_FILE"
echo "📏 Size: $(du -h "$LOG_FILE" | cut -f1)"
echo "🕐 Modified: $(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$LOG_FILE")"

echo ""
echo "=========================================="
echo "🔄 CURRENT ACTIVITY (Last 20 lines)"
echo "=========================================="

tail -20 "$LOG_FILE" | grep -E "(Processing:|Found|contributors|\[.*\]|Completed|ERROR)" | tail -15

echo ""
echo "=========================================="
echo "📈 PROGRESS SUMMARY"
echo "=========================================="

# Count repos processed
REPOS_COMPLETED=$(grep -c "✅ Completed" "$LOG_FILE" 2>/dev/null || echo "0")
echo "✅ Repositories completed: $REPOS_COMPLETED"

# Count contributors discovered
CONTRIBUTORS=$(grep -c "\[.*/.*/.*\]" "$LOG_FILE" 2>/dev/null || echo "0")
echo "👤 Contributors processed: $CONTRIBUTORS"

# Check for errors
ERRORS=$(grep -c "ERROR" "$LOG_FILE" 2>/dev/null || echo "0")
if [ "$ERRORS" -gt "0" ]; then
    echo "❌ Errors encountered: $ERRORS"
else
    echo "✅ No errors detected"
fi

echo ""
echo "=========================================="
echo "💡 QUICK COMMANDS"
echo "=========================================="
echo ""
echo "  Watch live:          ./watch_discovery_live.sh"
echo "  Check morning stats: ./check_overnight_results.sh"
echo "  View full log:       tail -100 $LOG_FILE"
echo ""

