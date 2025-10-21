# Talent Intelligence Dashboard

A simple, clean dashboard to visualize and explore the talent intelligence database.

## Features

### ✅ Implemented
- **Real-time Statistics**: Live data from PostgreSQL database
  - Total people (35,262)
  - Companies (91,722)
  - Employment records (203,076)
  - Email addresses (3,627)
  - GitHub profiles (17,534)
  
- **Data Completeness Charts**: Visual representation of data coverage
  - LinkedIn, Email, GitHub, Location, Headline percentages
  - Interactive Chart.js visualizations

- **Company Search**: Search for people by company name
  - Returns up to 10 results with full details
  - Shows name, headline, location, LinkedIn followers

- **API Health Monitoring**: Real-time API connection status

### 🚧 Deferred
- **Co-Employment Network Graph**: Postponed until we optimize the graph data
  - Current approach would generate 65M+ edges
  - Need smarter filtering/sampling strategy

## Running the Dashboard

### Prerequisites
- FastAPI server running on port 8000
- Python 3 for serving static files

### Start the Services

```bash
# Terminal 1: Start the API
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete
python3 -m uvicorn api.main:app --reload --port 8000

# Terminal 2: Start the Dashboard
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete/dashboard
python3 -m http.server 8080
```

### Access
- **Dashboard**: http://localhost:8080
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

## API Endpoints Available

### Stats
- `GET /api/stats/overview` - Database totals
- `GET /api/stats/quality` - Data completeness metrics
- `GET /api/stats/coverage` - Coverage percentages

### People
- `GET /api/people` - List people with filters
- `GET /api/people/{id}` - Get person details
- `GET /api/people/search/company` - Search by company
- `GET /api/people/search/location` - Search by location

### Companies
- `GET /api/companies` - List companies
- `GET /api/companies/{id}` - Get company details
- `GET /api/companies/{id}/employees` - Get company employees
- `GET /api/companies/{id}/timeline` - Hiring timeline
- `GET /api/companies/{id}/github/contributors` - External GitHub contributors

### Graph (Ready but no data yet)
- `GET /api/graph/coworkers/{person_id}` - Get co-workers
- `GET /api/graph/company/{company_id}/network` - Company network
- `GET /api/graph/stats` - Graph statistics
- `GET /api/graph/top-connected` - Most connected people

### Query
- `GET /api/query/search` - Complex multi-criteria search
  - Filters: company, location, has_email, has_github, headline_keyword, date range

## Technology Stack

### Frontend
- Vanilla JavaScript (no framework needed for this simple dashboard)
- Chart.js for data visualization
- D3.js (included for future network graph)
- Modern CSS with gradients and animations

### Backend
- FastAPI (Python)
- PostgreSQL database
- psycopg2 for database connections
- Pydantic for data validation

## Next Steps

1. **Optimize Graph Generation**
   - Implement sampling strategy for large companies
   - Add company size filters
   - Create on-demand graph generation instead of pre-computing all edges

2. **Add More Visualizations**
   - Timeline of hiring trends
   - University representation charts
   - Skills distribution
   - Location heatmap

3. **Enhanced Search**
   - Autocomplete for company names
   - Advanced filters UI
   - Export results to CSV

4. **Authentication**
   - Add API key authentication
   - User management
   - Rate limiting

## File Structure

```
dashboard/
├── index.html      # Main HTML structure
├── style.css       # Styling and layout
├── app.js          # JavaScript for API calls and charts
└── README.md       # This file
```

## Notes

- The dashboard uses CORS-enabled API calls
- All data is fetched dynamically from the live database
- Charts update automatically on page load
- Search results are limited to 10 for performance

