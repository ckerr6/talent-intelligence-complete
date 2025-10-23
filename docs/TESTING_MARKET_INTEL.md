# Market Intelligence Dashboard - Testing Guide

## ✅ **Issue Fixed!**

**Problem**: Company search returned no results, no data appeared on Market Intel page

**Root Cause**: API endpoint was using tuple indexing instead of dict access, causing 500 errors

**Solution**: Updated `/api/market/companies/search` to use `RealDictCursor` for proper dict result handling

---

## 🧪 **How to Test**

### 1. Navigate to Market Intelligence
```
http://localhost:3000/market
```

**Or click "Market Intel" in the sidebar (📈 icon)**

### 2. Search for a Company

**Try these companies** (known to have good data):

- **Uniswap Labs** (245 employees) ⭐ Best test data!
- **Coinbase** (large dataset)
- **Google** (many connections)
- **Microsoft** (good tech distribution)

**What to expect**:
- Type "uni" → dropdown appears
- Shows "Uniswap Labs - 245 employees in database"
- Click to select

### 3. Verify Charts Load

Once you select a company, you should see:

#### **Hiring Trends Chart**
- Monthly bar chart
- 3 stat cards (Total Hires, Avg/Month, Avg Tenure)
- Top roles list at bottom

**Uniswap Labs Example**:
- Total Hires: 57 (last 24 months)
- Avg Tenure: 733 days (≈2 years)
- Monthly breakdown visible

#### **Talent Flow Chart** (Left)
- **Feeder Companies** (green badges)
- **Destination Companies** (blue badges)
- Horizontal bar chart

**Uniswap Labs Example**:
- From Coinbase: 17 people
- From Microsoft: 13 people
- From Google: 13 people
- From Amazon: 8 people

#### **Technology Distribution Chart** (Right)
- Bar chart (default) or Pie chart (toggle)
- Language breakdown list

**Uniswap Labs Example**:
- TypeScript: 35 developers, 15,422 contributions
- Solidity: 18 developers, 4,174 contributions
- JavaScript: 21 developers, 1,537 contributions
- Go, Python, Rust, etc.

### 4. Try AI Chart Builder

1. Click "AI Chart Builder" tab
2. Try a suggested question or type your own:
   ```
   "What are the hiring trends at Uniswap Labs?"
   ```
3. Wait 5-10 seconds
4. Read the AI-generated strategic insights!

**Expected**: Full analysis with:
- Direct answer
- Key insights
- Strategic implications
- Recommendations

---

## 🔍 **If Something's Not Working**

### Company Search Not Showing Results

**Check**:
```bash
curl "http://localhost:8000/api/market/companies/search?query=uni&limit=5"
```

**Expected**: JSON with list of companies

**If fails**: 
- Is API running on port 8000?
- Check: `curl http://localhost:8000/health`

### Charts Not Loading

**Open Browser Console** (F12):
- Go to Console tab
- Look for red errors
- Share any error messages

**Check Network Tab** (F12):
- Go to Network tab
- Search for a company
- Look for failed requests (red)
- Click on them to see error details

### No Data for a Company

**Some companies may have limited data**. Try these "guaranteed good" companies:
- Uniswap Labs
- Coinbase
- Google
- Microsoft

**Check database directly**:
```bash
psql -d talent -c "SELECT company_name, (SELECT COUNT(*) FROM employment WHERE company_id = c.company_id) as emp_count FROM company c WHERE company_name ILIKE '%uniswap%';"
```

---

## ✅ **What We Fixed**

### Backend Fix
**File**: `api/routers/market_intelligence.py`

**Before** (broken):
```python
cursor = db.cursor()
companies = cursor.fetchall()
return [
    {
        "company_id": str(c[0]),  # ❌ Tuple indexing
        "company_name": c[1],
        "employee_count": c[2]
    }
    for c in companies
]
```

**After** (fixed):
```python
from psycopg2.extras import RealDictCursor
cursor = db.cursor(cursor_factory=RealDictCursor)
companies = cursor.fetchall()
return [
    {
        "company_id": str(c['company_id']),  # ✅ Dict access
        "company_name": c['company_name'],
        "employee_count": c['employee_count']
    }
    for c in companies
]
```

### Frontend Fix
**File**: `frontend/src/pages/AnalyticsPage.tsx`

**Changed**: Analytics page now redirects to Market Intel
- No duplication
- Clean navigation

---

## 📊 **Expected Results**

### Uniswap Labs (Best Test Case)

**Hiring Patterns**:
- 57 total hires in 24 months
- Avg 2.4 hires/month
- 733 days avg tenure (2 years)
- Top roles: CM LATAM, Smart Contract Engineer, Growth Lead

**Talent Flow**:
- **Inbound**: Coinbase (17), Microsoft (13), Google (13), Amazon (8)
- **Outbound**: Various destinations

**Technology**:
- TypeScript: 35 devs, 15,422 commits
- Solidity: 18 devs, 4,174 commits
- JavaScript: 21 devs, 1,537 commits
- Go: 3 devs, 2,177 commits

**AI Insights** (sample):
```
### Direct Answer
Uniswap Labs has hired 57 people in the last 24 months, 
with strong focus on TypeScript and Solidity engineering...

### Key Insights
1. Heavy recruiting from Coinbase (17 people)
2. Technology focus: TypeScript (35 devs), Solidity (18 devs)
3. Average tenure of 2 years indicates good retention

### Strategic Implications
- Strong talent pipeline from major tech companies
- Focus on DeFi/Web3 engineering expertise
- Balanced between frontend (TS) and smart contracts (Solidity)

### Recommendations
- Target Coinbase, Microsoft, Google for recruiting
- Focus on TypeScript and Solidity experts
- Leverage existing network for introductions
```

---

## 🎯 **Quick Smoke Test**

Run this to verify everything works:

```bash
# 1. Check servers are running
curl http://localhost:8000/health  # Should return {"status": "healthy"}
curl http://localhost:3000 > /dev/null && echo "Frontend OK"

# 2. Test company search
curl "http://localhost:8000/api/market/companies/search?query=uni&limit=3"

# 3. Test data loading (use a company_id from step 2)
curl "http://localhost:8000/api/market/hiring-patterns?company_id=802bc649-4246-5100-897d-641f8e2c4653"

# 4. Open browser and navigate to:
# http://localhost:3000/market
```

---

## 🚀 **Next Steps**

Now that data is loading:

1. **Test thoroughly** - Try 3-4 different companies
2. **Test AI Builder** - Ask several questions
3. **Take screenshots** - Capture charts for pitch deck
4. **Note any issues** - Empty data, slow loading, etc.

Once you confirm everything works, we can:
- Polish the UI/UX
- Add more features
- Optimize performance
- Prepare for demos

---

## 📝 **Known Limitations**

1. **Some companies have limited data** - that's expected
2. **AI responses take 5-10 seconds** - normal for GPT-4o-mini
3. **Universities appear in search** - they're in the employment table
4. **Empty talent flow** - some companies have no transition data yet

**These are data quality issues, not bugs!**

---

## ✅ **Success Checklist**

- [ ] Can search for companies
- [ ] Dropdown shows results with employee counts
- [ ] Can select a company (e.g., Uniswap Labs)
- [ ] Hiring Trends chart loads with data
- [ ] Talent Flow chart shows feeder companies
- [ ] Technology Distribution shows languages
- [ ] Can toggle pie/bar view on tech chart
- [ ] AI Chart Builder tab works
- [ ] Can ask AI questions
- [ ] AI returns strategic insights
- [ ] Analytics page redirects to Market Intel

**If all checked ✅ - YOU'RE READY TO DEMO!** 🎉

---

**Last Updated**: 2025-10-23  
**Status**: All systems operational ✅

