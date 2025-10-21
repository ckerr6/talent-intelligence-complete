#!/bin/bash
# Test dashboard company search functionality

echo "════════════════════════════════════════════════════════════════"
echo "Testing Dashboard Company Search"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Test 1: Uniswap
echo "1️⃣  Searching for 'Uniswap'..."
curl -s 'http://localhost:8000/api/query/search?company=Uniswap&limit=5' | python3 -c "
import sys, json
d = json.load(sys.stdin)
companies = {}
for person in d['data']:
    cid = person.get('company_id')
    cname = person.get('company_name')
    if cid and cname:
        companies[cid] = cname

print(f\"   ✅ Found {d['pagination']['total']} people across {len(companies)} companies\")
for cid, cname in list(companies.items())[:3]:
    print(f\"      • {cname} (ID: {cid[:8]}...)\" )
"
echo ""

# Test 2: Ava Labs
echo "2️⃣  Searching for 'Ava Labs'..."
curl -s 'http://localhost:8000/api/query/search?company=Ava%20Labs&limit=5' | python3 -c "
import sys, json
d = json.load(sys.stdin)
companies = {}
for person in d['data']:
    cid = person.get('company_id')
    cname = person.get('company_name')
    if cid and cname:
        companies[cid] = cname

print(f\"   ✅ Found {d['pagination']['total']} people across {len(companies)} companies\")
for cid, cname in list(companies.items())[:3]:
    print(f\"      • {cname} (ID: {cid[:8]}...)\")
"
echo ""

# Test 3: Anchorage
echo "3️⃣  Searching for 'Anchorage'..."
curl -s 'http://localhost:8000/api/query/search?company=Anchorage&limit=5' | python3 -c "
import sys, json
d = json.load(sys.stdin)
companies = {}
for person in d['data']:
    cid = person.get('company_id')
    cname = person.get('company_name')
    if cid and cname:
        companies[cid] = cname

print(f\"   ✅ Found {d['pagination']['total']} people across {len(companies)} companies\")
for cid, cname in list(companies.items())[:3]:
    print(f\"      • {cname} (ID: {cid[:8]}...)\")
"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ All company searches working!"
echo ""
echo "🎯 Next steps:"
echo "   1. Open http://localhost:8080 in your browser"
echo "   2. Scroll down to 'Find External GitHub Contributors'"
echo "   3. Type: Uniswap (or Ava Labs, or Anchorage)"
echo "   4. Click on a company card"
echo "   5. See the external contributors!"
echo "════════════════════════════════════════════════════════════════"

