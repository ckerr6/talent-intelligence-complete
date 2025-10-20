# Talent Intelligence API

REST API for the Talent Intelligence database. Provides CRUD operations and search functionality for people, companies, and related data.

## Features

- **People Management**: Create, read, update, delete person records
- **Company Management**: Manage company information and employees
- **Search & Filtering**: Advanced search across multiple criteria
- **Statistics**: Database overview and quality metrics
- **Pagination**: Efficient pagination for large datasets
- **Connection Pooling**: PostgreSQL connection pooling for performance
- **Auto-generated Documentation**: OpenAPI/Swagger docs

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements-dev.txt
```

### Running the API

**Development Mode (with auto-reload):**
```bash
python3 run_api.py --reload
```

**Production Mode:**
```bash
python3 run_api.py --no-reload --workers 4
```

**Custom Host/Port:**
```bash
python3 run_api.py --host 0.0.0.0 --port 8080
```

### Accessing the API

- **API Base URL**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### People

- `GET /api/people` - List people with filters
- `GET /api/people/{person_id}` - Get person details
- `POST /api/people` - Create new person
- `PUT /api/people/{person_id}` - Update person
- `DELETE /api/people/{person_id}` - Delete person
- `GET /api/people/search/company` - Search by company
- `GET /api/people/search/location` - Search by location

### Companies

- `GET /api/companies` - List companies with filters
- `GET /api/companies/{company_id}` - Get company details
- `POST /api/companies` - Create new company
- `PUT /api/companies/{company_id}` - Update company
- `DELETE /api/companies/{company_id}` - Delete company
- `GET /api/companies/{company_id}/employees` - Get company employees

### Statistics

- `GET /api/stats/overview` - Database overview
- `GET /api/stats/quality` - Data quality metrics
- `GET /api/stats/coverage` - Coverage statistics

## Example API Calls

### List People

```bash
curl http://localhost:8000/api/people?limit=10&offset=0
```

### Search by Company

```bash
curl "http://localhost:8000/api/people/search/company?company_name=Acme&limit=20"
```

### Get Person Details

```bash
curl http://localhost:8000/api/people/{person-id}
```

### Create Person

```bash
curl -X POST http://localhost:8000/api/people \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Smith",
    "linkedin_url": "https://linkedin.com/in/johnsmith",
    "location": "San Francisco, CA",
    "emails": [
      {"email": "john@example.com", "is_primary": true}
    ]
  }'
```

### Update Person

```bash
curl -X PUT http://localhost:8000/api/people/{person-id} \
  -H "Content-Type: application/json" \
  -d '{
    "headline": "Software Engineer at Acme Corp"
  }'
```

### Get Statistics

```bash
curl http://localhost:8000/api/stats/overview
```

## Pagination

All list endpoints support pagination:

```bash
GET /api/people?limit=50&offset=100
```

Parameters:
- `limit`: Number of results per page (default: 50, max: 1000)
- `offset`: Number of results to skip

Response includes pagination metadata:
```json
{
  "data": [...],
  "pagination": {
    "offset": 100,
    "limit": 50,
    "total": 32515
  }
}
```

## Filtering

### People Filters

```bash
GET /api/people?company=Acme&location=San%20Francisco&has_email=true
```

Available filters:
- `company`: Filter by company name (partial match)
- `location`: Filter by location (partial match)
- `headline`: Filter by headline/title (partial match)
- `has_email`: Filter by email presence (true/false)
- `has_github`: Filter by GitHub profile presence (true/false)

### Company Filters

```bash
GET /api/companies?industry=Technology&min_employees=100
```

Available filters:
- `industry`: Filter by industry (partial match)
- `has_website`: Filter by website presence (true/false)
- `min_employees`: Minimum employee count

## Authentication

**Current Status**: Authentication is not enabled by default.

Authentication skeleton is in place at `api/auth.py`. To enable:

1. Set `AUTH_ENABLED=true` in `api/config.py`
2. Implement authentication logic in `api/auth.py`
3. Add authentication dependency to protected routes

### Future Authentication Options

**API Key Authentication:**
```python
@router.get("/protected", dependencies=[Depends(require_auth)])
def protected_route():
    ...
```

**JWT Token Authentication:**
- Generate tokens on login
- Include token in Authorization header
- Validate token on each request

## Configuration

Configuration is managed in `api/config.py`:

```python
# Environment variables (optional)
API_HOST=0.0.0.0
API_PORT=8000
API_DEFAULT_PAGE_SIZE=50
API_MAX_PAGE_SIZE=1000
```

## Error Handling

The API returns standardized error responses:

```json
{
  "success": false,
  "error": "Not found",
  "detail": "Person with ID xyz not found"
}
```

Common status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

## Connection Pooling

The API uses PostgreSQL connection pooling for performance:

- Min connections: 1
- Max connections: 10
- Automatic connection recycling
- Health checks

Configure in `.env`:
```
PG_POOL_MIN=1
PG_POOL_MAX=10
```

## Development

### Running Tests

```bash
pytest tests/test_api.py -v
```

### Code Structure

```
api/
├── main.py              # FastAPI app
├── config.py            # API configuration
├── dependencies.py      # Dependency injection
├── auth.py              # Authentication (skeleton)
├── models/              # Pydantic models
│   ├── person.py
│   ├── company.py
│   └── common.py
├── crud/                # Database operations
│   ├── person.py
│   └── company.py
└── routers/             # API routes
    ├── people.py
    ├── companies.py
    └── stats.py
```

### Adding New Endpoints

1. Create Pydantic models in `api/models/`
2. Create CRUD operations in `api/crud/`
3. Create router in `api/routers/`
4. Register router in `api/main.py`

## Performance

- Connection pooling reduces overhead
- Pagination prevents large result sets
- Indexed queries for fast lookups
- Efficient PostgreSQL queries

## Security Considerations

**Current Implementation:**
- No authentication (suitable for internal use)
- CORS enabled for specified origins
- SQL injection prevention via parameterized queries
- Input validation via Pydantic models

**For Production:**
- Enable authentication
- Configure CORS for production domains
- Use HTTPS
- Implement rate limiting
- Add request logging
- Set up monitoring

## Troubleshooting

**Connection errors:**
```bash
# Check database connection
psql -d talent

# Verify config
python3 config.py
```

**Port already in use:**
```bash
# Use different port
python3 run_api.py --port 8080
```

**Import errors:**
```bash
# Install dependencies
pip install -r requirements-dev.txt
```

## Support

For issues or questions, check:
1. Interactive docs at `/docs`
2. Health endpoint at `/health`
3. Database connection with `python3 config.py`

