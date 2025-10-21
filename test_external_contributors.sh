#!/bin/bash
# Test script for External GitHub Contributors API

echo "════════════════════════════════════════════════════════════════"
echo "Testing External GitHub Contributors Endpoint"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Uniswap Labs
echo "🦄 Uniswap Labs"
echo "─────────────────────────────────────────────────────────────"
curl -s 'http://localhost:8000/api/companies/802bc649-4246-5100-897d-641f8e2c4653/github/contributors?limit=3' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"Company: {d['company_name']}\")
print(f\"Total External Contributors: {d['pagination']['total']}\")
print(f\"\\nTop 3 Contributors:\")
for c in d['data']:
    print(f\"  • {c['github_username']}: {c['total_contributions']} contributions, {c['followers']} followers\")
    if c['bio']:
        print(f\"    Bio: {c['bio']}\")
"
echo ""

# Ava Labs  
echo "🔺 Ava Labs"
echo "─────────────────────────────────────────────────────────────"
curl -s 'http://localhost:8000/api/companies/b1d82e57-a7f1-9b62-4b11-70a91fe1fd1e/github/contributors?limit=3' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"Company: {d['company_name']}\")
print(f\"Total External Contributors: {d['pagination']['total']}\")
print(f\"\\nTop 3 Contributors:\")
for c in d['data']:
    print(f\"  • {c['github_username']}: {c['total_contributions']} contributions, {c['followers']} followers\")
    if c['location']:
        print(f\"    Location: {c['location']}\")
"
echo ""

# Anchorage Digital
echo "⚓ Anchorage Digital"
echo "─────────────────────────────────────────────────────────────"
curl -s 'http://localhost:8000/api/companies/106d7302-137d-38f5-7a37-ab981a171d82/github/contributors?limit=3' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"Company: {d['company_name']}\")
print(f\"Total External Contributors: {d['pagination']['total']}\")
print(f\"\\nTop 3 Contributors:\")
for c in d['data']:
    print(f\"  • {c['github_username']}: {c['total_contributions']} contributions, {c['public_repos']} public repos\")
    if c['github_email']:
        print(f\"    Email: {c['github_email']}\")
"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ All tests complete!"
echo ""
echo "💡 These are developers who:"
echo "   • Contribute to the company's GitHub repositories"
echo "   • Are NOT employees in our database"
echo "   • Are potential recruitment targets!"
echo "════════════════════════════════════════════════════════════════"

