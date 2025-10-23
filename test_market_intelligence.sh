#!/bin/bash

# Test script for Market Intelligence API
# Usage: ./test_market_intelligence.sh [company_name]

COMPANY_NAME=${1:-"Uniswap"}
API_URL="http://localhost:8000"

echo "========================================"
echo "Testing Market Intelligence API"
echo "Company: $COMPANY_NAME"
echo "========================================"
echo ""

echo "1. Searching for company..."
echo "----------------------------------------"
curl -s "$API_URL/api/market/companies/search?query=$COMPANY_NAME&limit=5" | python3 -m json.tool
echo ""
echo ""

echo "2. Getting hiring patterns (last 24 months)..."
echo "----------------------------------------"
curl -s "$API_URL/api/market/hiring-patterns?company_name=$COMPANY_NAME&time_period_months=24" | python3 -m json.tool
echo ""
echo ""

echo "3. Analyzing talent flow (inbound and outbound)..."
echo "----------------------------------------"
curl -s "$API_URL/api/market/talent-flow?company_name=$COMPANY_NAME&direction=both" | python3 -m json.tool
echo ""
echo ""

echo "4. Getting technology distribution..."
echo "----------------------------------------"
curl -s "$API_URL/api/market/technology-distribution?company_name=$COMPANY_NAME&limit=10" | python3 -m json.tool
echo ""
echo ""

echo "5. Asking AI about hiring trends..."
echo "----------------------------------------"
curl -s -X POST "$API_URL/api/market/ask" \
  -H "Content-Type: application/json" \
  -d "{
    \"question\": \"What are the hiring trends at $COMPANY_NAME? What roles are they focusing on?\",
    \"company_name\": \"$COMPANY_NAME\",
    \"provider\": \"openai\"
  }" | python3 -m json.tool
echo ""
echo ""

echo "6. Asking AI about talent flow..."
echo "----------------------------------------"
curl -s -X POST "$API_URL/api/market/ask" \
  -H "Content-Type: application/json" \
  -d "{
    \"question\": \"Where does $COMPANY_NAME recruit most of their talent from? What companies are their top feeders?\",
    \"company_name\": \"$COMPANY_NAME\",
    \"provider\": \"openai\"
  }" | python3 -m json.tool
echo ""

echo "========================================"
echo "Test Complete!"
echo "========================================"

