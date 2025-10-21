#!/bin/bash
# Quick API testing script

API_BASE="http://localhost:8000"

echo "=================================="
echo "🧪 Testing Talent Intelligence API"
echo "=================================="
echo ""

# Test 1: Health check
echo "1️⃣  Testing API Health..."
curl -s "$API_BASE/health" | python3 -m json.tool
echo ""
echo ""

# Test 2: Database stats
echo "2️⃣  Getting Database Statistics..."
curl -s "$API_BASE/api/stats/overview" | python3 -m json.tool
echo ""
echo ""

# Test 3: Data quality
echo "3️⃣  Checking Data Quality..."
curl -s "$API_BASE/api/stats/quality" | python3 -m json.tool | head -30
echo ""
echo ""

# Test 4: Search by company
echo "4️⃣  Searching for people at Coinbase..."
curl -s "$API_BASE/api/query/search?company=coinbase&limit=3" | python3 -m json.tool | head -40
echo ""
echo ""

# Test 5: Search by location
echo "5️⃣  Searching for people in San Francisco..."
curl -s "$API_BASE/api/query/search?location=san%20francisco&limit=3" | python3 -m json.tool | head -40
echo ""
echo ""

# Test 6: People with GitHub
echo "6️⃣  Finding people with GitHub profiles..."
curl -s "$API_BASE/api/query/search?has_github=true&limit=3" | python3 -m json.tool | head -40
echo ""
echo ""

# Test 7: Complex search
echo "7️⃣  Complex search (Google + has email)..."
curl -s "$API_BASE/api/query/search?company=google&has_email=true&limit=3" | python3 -m json.tool | head -40
echo ""
echo ""

echo "=================================="
echo "✅ All tests complete!"
echo "=================================="
echo ""
echo "📚 View full API docs at: $API_BASE/docs"
echo "🎨 View dashboard at: http://localhost:8080"
echo ""

