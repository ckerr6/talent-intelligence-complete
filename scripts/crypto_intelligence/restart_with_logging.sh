#!/bin/bash
# ABOUTME: Restart all Ethereum intelligence processes with DETAILED LOGGING
# ABOUTME: Provides comprehensive visibility into all data ingestion

echo "================================================================================"
echo "🔄 RESTARTING ETHEREUM INTELLIGENCE WITH DETAILED LOGGING"
echo "================================================================================"
echo ""

cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete

# Kill existing processes
echo "🛑 Stopping existing processes..."
pkill -f discover_all_contributors
pkill -f enrich_crypto_developers
sleep 2

# Create logs directory
mkdir -p logs/detailed

# Start discovery with detailed logging
echo "🚀 Starting Discovery Process with Detailed Logging..."
nohup python3 -u scripts/crypto_intelligence/discover_all_contributors.py Ethereum 500 > logs/detailed/discovery_console.log 2>&1 &
DISCOVERY_PID=$!
echo "   ✅ Discovery PID: $DISCOVERY_PID"
echo "   📝 Console log: logs/detailed/discovery_console.log"
echo "   📊 Detailed logs: logs/detailed/ethereum_discovery_*"

sleep 2

# Start enrichment with detailed logging  
echo ""
echo "⚡ Starting Enrichment Process with Detailed Logging..."
nohup python3 -u scripts/crypto_intelligence/enrich_crypto_developers.py Ethereum 25 > logs/detailed/enrichment_console.log 2>&1 &
ENRICHMENT_PID=$!
echo "   ✅ Enrichment PID: $ENRICHMENT_PID"
echo "   📝 Console log: logs/detailed/enrichment_console.log"
echo "   📊 Detailed logs: logs/detailed/ethereum_enrichment_*"

echo ""
echo "================================================================================"
echo "✅ ALL PROCESSES STARTED WITH DETAILED LOGGING"
echo "================================================================================"
echo ""
echo "📊 Monitor in real-time:"
echo ""
echo "   Discovery (live):"
echo "   tail -f logs/detailed/discovery_console.log"
echo ""
echo "   Enrichment (live):"
echo "   tail -f logs/detailed/enrichment_console.log"
echo ""
echo "   All discovery details:"
echo "   tail -f logs/detailed/ethereum_discovery_*_detailed.log"
echo ""
echo "   All enrichment details:"
echo "   tail -f logs/detailed/ethereum_enrichment_*_detailed.log"
echo ""
echo "   Structured JSON logs:"
echo "   tail -f logs/detailed/*_structured.jsonl"
echo ""
echo "   Status dashboard:"
echo "   ./scripts/crypto_intelligence/status_dashboard.sh"
echo ""
echo "================================================================================"

