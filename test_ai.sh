#!/bin/bash

# Test script for AI features
# Usage: ./test_ai.sh <person_id>

PERSON_ID=${1:-"679c5f97-d1f8-46a9-bc1b-e8959d4288c2"}  # Default to 0age
API_URL="http://localhost:8000"

echo "================================"
echo "Testing AI Features"
echo "Person ID: $PERSON_ID"
echo "================================"
echo ""

echo "1. Checking AI Status..."
echo "--------------------------------"
curl -s "$API_URL/api/ai/status" | python3 -m json.tool
echo ""
echo ""

echo "2. Generating Profile Summary..."
echo "--------------------------------"
curl -s -X POST "$API_URL/api/ai/profile-summary" \
  -H "Content-Type: application/json" \
  -d "{
    \"person_id\": \"$PERSON_ID\",
    \"provider\": \"openai\"
  }" | python3 -m json.tool
echo ""
echo ""

echo "3. Analyzing Code Quality..."
echo "--------------------------------"
curl -s -X POST "$API_URL/api/ai/code-analysis" \
  -H "Content-Type: application/json" \
  -d "{
    \"person_id\": \"$PERSON_ID\",
    \"provider\": \"openai\"
  }" | python3 -m json.tool
echo ""
echo ""

echo "4. Asking a Question..."
echo "--------------------------------"
curl -s -X POST "$API_URL/api/ai/ask" \
  -H "Content-Type: application/json" \
  -d "{
    \"person_id\": \"$PERSON_ID\",
    \"question\": \"What kind of engineering work do they do and what roles would they be best suited for?\",
    \"provider\": \"openai\"
  }" | python3 -m json.tool
echo ""

echo "================================"
echo "Test Complete!"
echo "================================"

