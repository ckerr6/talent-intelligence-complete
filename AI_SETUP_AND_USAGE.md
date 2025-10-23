# AI-Powered Recruiting Assistant - Setup & Usage

## Overview

The AI service provides three powerful features:

1. **Profile Summary** - Generates recruiter-friendly career summaries
2. **Code Analysis** - Analyzes GitHub work and technical depth
3. **Interactive Q&A** - Ask questions about any candidate

## Quick Setup

### 1. Install Dependencies

Already done! OpenAI and Anthropic libraries are installed.

### 2. Set Your API Key

You need to set your OpenAI API key as an environment variable.

**Option A: Set in Terminal (temporary)**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

**Option B: Add to ~/.zshrc (permanent)**
```bash
echo 'export OPENAI_API_KEY="sk-your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

**Option C: Use .env file**
```bash
# Create .env file in project root
echo 'OPENAI_API_KEY=sk-your-key-here' >> .env
```

**Get your OpenAI API key**: https://platform.openai.com/api-keys

**Cost estimate**: 
- GPT-4o-mini: ~$0.15 per 1M input tokens, $0.60 per 1M output tokens
- ~100 candidate analyses = $2-3
- Well within your $100-200/month budget

### 3. Restart API (if needed)

```bash
pkill -f "python3 run_api.py"
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete
python3 run_api.py > logs/api.log 2>&1 &
```

### 4. Verify Setup

```bash
curl http://localhost:8000/api/ai/status | python3 -m json.tool
```

Should show: `"available": true` for OpenAI

---

## API Endpoints

### 1. Generate Profile Summary

**Endpoint**: `POST /api/ai/profile-summary`

**What it does**: Creates a comprehensive, recruiter-friendly summary of a candidate's career and technical work.

**Example**:
```bash
curl -X POST http://localhost:8000/api/ai/profile-summary \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "your-person-id",
    "job_context": "Looking for a senior backend engineer with blockchain experience",
    "provider": "openai"
  }' | python3 -m json.tool
```

**Response**:
```json
{
  "success": true,
  "person_id": "...",
  "summary": {
    "executive_summary": "2-3 sentence professional overview",
    "key_strengths": ["strength 1", "strength 2", "strength 3"],
    "technical_domains": ["blockchain", "backend systems"],
    "ideal_roles": ["Senior Backend Engineer", "Protocol Engineer"],
    "career_trajectory": "Assessment of career progression",
    "standout_projects": ["project 1 with explanation"],
    "recruiter_notes": "What makes them interesting or concerns",
    "generated_at": "2025-10-23T...",
    "model": "gpt-4o-mini"
  }
}
```

---

### 2. Analyze Code Quality

**Endpoint**: `POST /api/ai/code-analysis`

**What it does**: Analyzes GitHub contributions and explains technical work in non-technical terms.

**Example**:
```bash
curl -X POST http://localhost:8000/api/ai/code-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "your-person-id",
    "job_requirements": "Need someone who can build high-performance trading systems",
    "provider": "openai"
  }' | python3 -m json.tool
```

**Response**:
```json
{
  "success": true,
  "person_id": "...",
  "analysis": {
    "code_quality_assessment": "Overall assessment in plain English",
    "technical_depth": "Senior - with justification",
    "engineering_style": "Full-stack generalist with systems focus",
    "standout_contributions": ["contribution with impact"],
    "languages_and_tools": ["Solidity", "TypeScript", "Rust"],
    "work_complexity": "Description of complexity level",
    "collaboration_indicators": "Evidence of teamwork",
    "relevance_to_role": "How they match job requirements",
    "concerns": ["any gaps to note"],
    "analyzed_at": "2025-10-23T...",
    "model": "gpt-4o-mini"
  }
}
```

---

### 3. Ask a Question

**Endpoint**: `POST /api/ai/ask`

**What it does**: Interactive Q&A about any candidate. Ask natural language questions.

**Example Questions**:
- "Would they be good for a senior backend role?"
- "Do they have blockchain experience?"
- "How do they compare to engineers at Coinbase?"
- "What's their management experience?"
- "Are they a team leader or individual contributor?"

**Example**:
```bash
curl -X POST http://localhost:8000/api/ai/ask \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "your-person-id",
    "question": "Would they be good for a senior blockchain engineer role?",
    "provider": "openai"
  }' | python3 -m json.tool
```

**Response**:
```json
{
  "success": true,
  "person_id": "...",
  "question": "Would they be good for a senior blockchain engineer role?",
  "answer": "Based on their experience at Uniswap and contributions to multiple DeFi protocols, they would be an excellent fit for a senior blockchain role. They have 3+ years of Solidity development, have built production smart contracts handling millions in TVL, and demonstrate strong understanding of DeFi primitives..."
}
```

**Follow-up Questions** (with conversation history):
```bash
curl -X POST http://localhost:8000/api/ai/ask \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "your-person-id",
    "question": "What about their management experience?",
    "conversation_history": [
      {"role": "user", "content": "Would they be good for a senior blockchain engineer role?"},
      {"role": "assistant", "content": "Based on their experience..."}
    ],
    "provider": "openai"
  }'
```

---

## Quick Test Script

Save this as `test_ai.sh`:

```bash
#!/bin/bash

# Test script for AI features
# Usage: ./test_ai.sh <person_id>

PERSON_ID=${1:-"679c5f97-d1f8-46a9-bc1b-e8959d4288c2"}  # Default to 0age
API_URL="http://localhost:8000"

echo "================================"
echo "Testing AI Features"
echo "================================"
echo ""

echo "1. Checking AI Status..."
curl -s "$API_URL/api/ai/status" | python3 -m json.tool
echo ""
echo ""

echo "2. Generating Profile Summary..."
curl -X POST "$API_URL/api/ai/profile-summary" \
  -H "Content-Type: application/json" \
  -d "{
    \"person_id\": \"$PERSON_ID\",
    \"provider\": \"openai\"
  }" | python3 -m json.tool
echo ""
echo ""

echo "3. Analyzing Code Quality..."
curl -X POST "$API_URL/api/ai/code-analysis" \
  -H "Content-Type: application/json" \
  -d "{
    \"person_id\": \"$PERSON_ID\",
    \"provider\": \"openai\"
  }" | python3 -m json.tool
echo ""
echo ""

echo "4. Asking a Question..."
curl -X POST "$API_URL/api/ai/ask" \
  -H "Content-Type: application/json" \
  -d "{
    \"person_id\": \"$PERSON_ID\",
    \"question\": \"What kind of engineering work do they do?\",
    \"provider\": \"openai\"
  }" | python3 -m json.tool
echo ""
```

Make it executable:
```bash
chmod +x test_ai.sh
```

Run it:
```bash
# Test with default person (0age)
./test_ai.sh

# Test with specific person ID
./test_ai.sh "your-person-id-here"
```

---

## Multi-Model Support

### Use Anthropic Claude Instead

If you prefer Claude or want to compare results:

1. Get an Anthropic API key: https://console.anthropic.com/
2. Set the key: `export ANTHROPIC_API_KEY="sk-ant-..."`
3. Use `"provider": "anthropic"` in your requests

**Example**:
```bash
curl -X POST http://localhost:8000/api/ai/profile-summary \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "your-person-id",
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022"
  }'
```

---

## Next Steps: Frontend Integration

We'll build React components to show:

1. **AI Summary Card** on profile pages (auto-generated)
2. **"Ask AI" Chat Interface** (interactive Q&A)
3. **Code Analysis Section** in GitHub activity
4. **Quick Actions** - "Get AI Insights" button

---

## Cost Management Tips

1. **Cache results** - Store summaries in `candidate_scores` table
2. **Smart triggering** - Only generate on-demand or for top candidates
3. **Batch processing** - Generate summaries overnight for your target list
4. **Use GPT-4o-mini** - 5-10x cheaper than GPT-4, great quality

---

## Troubleshooting

**Error: "OPENAI_API_KEY not found"**
- Make sure you've exported the key: `echo $OPENAI_API_KEY`
- Restart your terminal/API after setting

**Error: "Failed to parse AI response as JSON"**
- Sometimes the AI returns malformed JSON
- The error handler will return the raw response instead
- Adjust temperature or try again

**Slow responses**
- Profile summaries take ~3-5 seconds
- Code analysis takes ~5-8 seconds
- This is normal for GPT-4o-mini

**High costs**
- Monitor usage at: https://platform.openai.com/usage
- Set spending limits in OpenAI dashboard
- Use caching to avoid re-analyzing same candidates

---

## Questions?

The AI service is designed to be:
- **Flexible**: Works with OpenAI or Anthropic
- **Intelligent**: Understands technical work deeply
- **Recruiter-friendly**: Explains in plain English
- **Interactive**: Supports follow-up questions
- **Cost-effective**: ~$2-3 per 100 analyses

Ready to see AI-powered recruiting in action! 🚀

