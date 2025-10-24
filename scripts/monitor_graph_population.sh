#!/bin/bash
# Monitor the coemployment graph population progress

echo "========================================="
echo "Monitoring Coemployment Graph Population"
echo "========================================="
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

last_count=0
start_time=$(date +%s)

while true; do
    clear
    echo "========================================="
    echo "Coemployment Graph Population Monitor"
    echo "========================================="
    echo ""
    
    # Check if process is still running
    if ps aux | grep -v grep | grep "populate_coemployment_graph" > /dev/null; then
        echo "✅ Process Status: RUNNING"
    else
        echo "⚠️  Process Status: NOT RUNNING"
    fi
    echo ""
    
    # Get current edge count
    current_count=$(psql -d talent -t -c "SELECT COUNT(*) FROM edge_coemployment;" 2>/dev/null | tr -d ' ')
    
    if [ ! -z "$current_count" ]; then
        echo "📊 Current Edges: $(printf "%'d" $current_count)"
        
        # Calculate rate
        if [ "$last_count" -ne 0 ]; then
            edges_added=$((current_count - last_count))
            rate=$((edges_added / 5))  # edges per second (we check every 5 seconds)
            echo "📈 Rate: $(printf "%'d" $rate) edges/second"
            
            if [ "$rate" -gt 0 ]; then
                echo "✨ Progress: Adding edges..."
            fi
        fi
        
        last_count=$current_count
    fi
    
    echo ""
    
    # Check active queries
    echo "Active Database Operations:"
    psql -d talent -c "
        SELECT 
            pid,
            LEFT(query, 60) as query,
            EXTRACT(EPOCH FROM (NOW() - query_start))::int as seconds,
            EXTRACT(EPOCH FROM (NOW() - query_start))::int / 60 as minutes
        FROM pg_stat_activity 
        WHERE query LIKE '%edge_coemployment%' 
        AND query NOT LIKE '%pg_stat_activity%'
        AND state = 'active';" 2>/dev/null | head -10
    
    echo ""
    echo "Last updated: $(date)"
    echo ""
    echo "Refreshing in 5 seconds..."
    
    sleep 5
done

