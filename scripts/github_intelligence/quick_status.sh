#!/bin/bash
# Quick status check for GitHub intelligence enrichment

cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete

echo "================================"
echo "🔍 GitHub Intelligence Status"
echo "================================"
echo ""

# Check database
echo "📊 Database Status:"
psql -d talent -t -c "SELECT COUNT(*) FROM github_intelligence;" 2>/dev/null | xargs -I {} echo "   Enriched profiles: {}"
echo ""

# Check if enrichment is running
echo "🚀 Enrichment Process:"
if ps aux | grep -v grep | grep intelligence_orchestrator > /dev/null; then
    echo "   ✅ Running"
    ps aux | grep intelligence_orchestrator | grep -v grep | awk '{print "   PID:", $2}'
else
    echo "   ❌ Not running"
fi
echo ""

# Check API
echo "🌐 API Server:"
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "   ✅ Running on port 8000"
    echo "   📚 Docs: http://localhost:8000/docs"
else
    echo "   ❌ Not running"
fi
echo ""

# Check Frontend
echo "🎨 Frontend:"
if lsof -ti:3001 > /dev/null 2>&1; then
    echo "   ✅ Running on port 3001"
    echo "   🌍 URL: http://localhost:3001/github"
elif lsof -ti:5173 > /dev/null 2>&1; then
    echo "   ✅ Running on port 5173"
    echo "   🌍 URL: http://localhost:5173/github"
else
    echo "   ❌ Not running"
fi
echo ""

# Check logs
echo "📄 Recent Enrichment Activity:"
if [ -f logs/github_enrichment.log ]; then
    tail -5 logs/github_enrichment.log | grep -E "(✅|❌|Enriching)" || echo "   No recent activity"
else
    echo "   No log file found"
fi
echo ""

echo "================================"
echo "💡 Quick Commands:"
echo "   View logs: tail -f logs/github_enrichment.log"
echo "   Check DB:  psql -d talent -c 'SELECT COUNT(*) FROM github_intelligence;'"
echo "   Frontend:  http://localhost:3001/github (or :5173)"
echo "================================"

