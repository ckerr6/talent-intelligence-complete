# Quick Test Guide - API & Dashboard

## Currently Running Services

✅ **API Server**: http://localhost:8000  
✅ **Dashboard**: http://localhost:8080  
✅ **API Docs**: http://localhost:8000/docs

---

## Quick Tests

### 1. Test API Health
```bash
curl http://localhost:8000/health
```

**Expected**: `{"status":"healthy","database":"talent",...}`

### 2. View API Documentation
Open in browser: http://localhost:8000/docs

Try the interactive endpoints!

### 3. Get Database Stats
```bash
curl http://localhost:8000/api/stats/overview | python3 -m json.tool
```

**Expected**:
```json
{
    "totals": {
        "people": 35262,
        "companies": 91722,
        "employment_records": 203076,
        "emails": 3627,
        "github_profiles": 17534
    }
}
```

### 4. Search for People at a Company
```bash
curl 'http://localhost:8000/api/query/search?company=coinbase&limit=3' | python3 -m json.tool
```

### 5. View the Dashboard
Open in browser: http://localhost:8080

You should see:
- Live stats with numbers
- Two charts (completeness & overview)
- Company search box
- Modern gradient design

### 6. Try Dashboard Search
1. Go to http://localhost:8080
2. Type "Google" or "Coinbase" in the search box
3. Click Search
4. See results appear

---

## Stopping the Services

```bash
# Stop API server
pkill -f "uvicorn api.main:app"

# Stop dashboard server
pkill -f "http.server 8080"
```

## Restarting the Services

```bash
# Start API
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete
python3 -m uvicorn api.main:app --reload --port 8000 &

# Start Dashboard
cd dashboard
python3 -m http.server 8080 &
```

---

## Available Endpoints

### Core Stats
- `GET /api/stats/overview` - Database totals
- `GET /api/stats/quality` - Data quality metrics
- `GET /api/stats/coverage` - Coverage stats

### Search & Query
- `GET /api/query/search` - Multi-criteria search
  - Parameters: `company`, `location`, `has_email`, `has_github`, `headline_keyword`, `start_date`, `end_date`

### People
- `GET /api/people` - List people (paginated)
- `GET /api/people/{id}` - Get person details
- `GET /api/people/search/company?company_name=X`
- `GET /api/people/search/location?location=X`

### Companies
- `GET /api/companies` - List companies (paginated)
- `GET /api/companies/{id}` - Get company details
- `GET /api/companies/{id}/employees` - All employees
- `GET /api/companies/{id}/timeline` - Hiring timeline
- `GET /api/companies/{id}/github/contributors` - External GitHub contributors

### Graph (Ready, but no data yet)
- `GET /api/graph/coworkers/{person_id}`
- `GET /api/graph/company/{company_id}/network`
- `GET /api/graph/stats`
- `GET /api/graph/top-connected`

---

## Example Queries

### Find people in San Francisco with GitHub profiles
```bash
curl 'http://localhost:8000/api/query/search?location=san%20francisco&has_github=true&limit=5'
```

### Find people at Stripe
```bash
curl 'http://localhost:8000/api/query/search?company=stripe&limit=10'
```

### Get data quality breakdown
```bash
curl 'http://localhost:8000/api/stats/quality'
```

---

## What Works ✅

- ✅ Full REST API with 20+ endpoints
- ✅ Interactive Swagger documentation
- ✅ Real-time dashboard with charts
- ✅ Company search functionality
- ✅ Data quality visualization
- ✅ Responsive design
- ✅ API health monitoring

## What's Deferred 🔄

- 🔄 Co-employment network graph (65M+ edges too large)
- 🔄 Need optimization strategy before implementing

## Next Steps

1. **Review the dashboard** - Open http://localhost:8080
2. **Test the API** - Try the curl commands above
3. **Explore Swagger docs** - http://localhost:8000/docs
4. **Decide on graph strategy** - How to handle 65M edges?

---

**Everything is working!** 🎉

