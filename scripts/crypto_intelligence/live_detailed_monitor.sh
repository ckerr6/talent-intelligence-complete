#!/bin/bash
# ABOUTME: Live monitoring dashboard for detailed logging - shows EXACTLY what's being ingested
# ABOUTME: Real-time view of discovery and enrichment with full data visibility

cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete

clear
echo "================================================================================"
echo "🔥 LIVE DETAILED LOGGING MONITOR - ETHEREUM INTELLIGENCE"
echo "================================================================================"
echo ""
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "================================================================================"
    echo "🔥 LIVE DETAILED LOGGING MONITOR"
    echo "================================================================================"
    date
    echo ""
    
    # Processes
    echo "📊 ACTIVE PROCESSES:"
    echo "--------------------------------------------------------------------------------"
    ps aux | grep -E "(discover_all|enrich_crypto)" | grep -v grep | awk '{printf "   ✅ PID %-7s CPU: %3s%%  Mem: %6sMB  %s\n", $2, $3, $6/1024, $NF}' || echo "   ⚠️  No processes running"
    echo ""
    
    # Discovery - Bot filtering in action
    echo "🤖 BOT FILTERING (Last 10 bots filtered):"
    echo "--------------------------------------------------------------------------------"
    tail -500 logs/detailed/ethereum_discovery_*.log 2>/dev/null | grep "Filtered.*bots" | tail -10 | sed 's/^.*DEBUG.*|/   /' || echo "   No bot filtering data yet"
    echo ""
    
    # Latest enrichment data
    echo "⚡ LATEST ENRICHMENT DATA CAPTURED:"
    echo "--------------------------------------------------------------------------------"
    LATEST_PROFILE=$(grep "profile_data_fetched" logs/detailed/ethereum_enrichment_*_structured.jsonl 2>/dev/null | tail -1)
    if [ -n "$LATEST_PROFILE" ]; then
        echo "$LATEST_PROFILE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"   👤 @{data['username']}\")
    print(f\"      Name: {data['data'].get('name', 'N/A')}\")
    print(f\"      Email: {data['data'].get('email', 'N/A')}\")
    print(f\"      Company: {data['data'].get('company', 'N/A')}\")
    print(f\"      Location: {data['data'].get('location', 'N/A')}\")
    print(f\"      Followers: {data['data'].get('followers', 0)}\")
    print(f\"      Repos: {data['data'].get('public_repos', 0)}\")
    print(f\"      Time: {data['timestamp']}\")
except: pass
" 2>/dev/null
    else
        echo "   No enrichment data yet"
    fi
    echo ""
    
    # Latest skills extracted
    echo "🎯 LATEST SKILLS EXTRACTED:"
    echo "--------------------------------------------------------------------------------"
    LATEST_SKILLS=$(grep "skills_extracted" logs/detailed/ethereum_enrichment_*_structured.jsonl 2>/dev/null | tail -1)
    if [ -n "$LATEST_SKILLS" ]; then
        echo "$LATEST_SKILLS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    skills = data['skills']
    print(f\"   👤 @{data['username']}\")
    if 'languages' in skills:
        langs = ', '.join(list(skills['languages'].keys())[:8])
        print(f\"      Languages: {langs}\")
    if 'frameworks' in skills and skills['frameworks']:
        print(f\"      Frameworks: {len(skills['frameworks'])} detected\")
    if 'domains' in skills and skills['domains']:
        doms = ', '.join(skills['domains'][:5])
        print(f\"      Domains: {doms}\")
except: pass
" 2>/dev/null
    else
        echo "   No skills data yet"
    fi
    echo ""
    
    # Database stats
    echo "💾 DATABASE STATISTICS:"
    echo "--------------------------------------------------------------------------------"
    psql -d talent -t -c "SELECT '   Total Crypto Developers: ' || COUNT(*)::text FROM crypto_developers;" 2>/dev/null
    psql -d talent -t -c "SELECT '   Enriched: ' || COUNT(DISTINCT cd.github_profile_id)::text FROM crypto_developers cd JOIN github_intelligence gi ON cd.github_profile_id = gi.github_profile_id;" 2>/dev/null
    echo ""
    
    # Recent discoveries
    echo "🔍 LATEST CONTRIBUTORS DISCOVERED:"
    echo "--------------------------------------------------------------------------------"
    grep "contributor_discovered" logs/detailed/ethereum_discovery_*_structured.jsonl 2>/dev/null | tail -5 | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        data = json.loads(line)
        print(f\"   👤 @{data['username']} - {data['contributions']} contributions in {data['repo']}\")
    except: pass
" 2>/dev/null || echo "   No recent discoveries"
    echo ""
    
    echo "================================================================================"
    echo "🔄 Refreshing every 5 seconds... (Ctrl+C to stop)"
    echo "================================================================================"
    
    sleep 5
done

