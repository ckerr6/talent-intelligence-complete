#!/bin/bash
# Run test enrichment with PhantomBuster MCP
# Usage: ./run_test_enrichment.sh [batch_size]

BATCH_SIZE=${1:-15}

echo "========================================"
echo "PhantomBuster Test Enrichment"
echo "========================================"
echo "Batch size: $BATCH_SIZE"
echo ""

# Check if API key is set
if [ -z "$PHANTOMBUSTER_API_KEY" ]; then
    echo "⚠️  WARNING: PHANTOMBUSTER_API_KEY not set in environment"
    echo "   Make sure it's in your .env file"
    echo ""
fi

# Validate batch first
echo "Step 1: Validating test batch..."
python3 validate_test_batch.py
echo ""

read -p "Proceed with enrichment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Run enrichment
echo ""
echo "Step 2: Running enrichment..."
python3 phantombuster_linkedin_enrichment.py --test --batch-size $BATCH_SIZE

# Show results
echo ""
echo "Step 3: Showing results..."
python3 monitor_enrichment_progress.py

echo ""
echo "✅ Test enrichment complete!"
echo "   Check logs: tail -f ../logs/phantombuster_enrichment.log"

