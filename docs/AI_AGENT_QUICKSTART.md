# AI Agent Quickstart - 2 Minute Orientation

## What is this project?
Recruiting intelligence platform. Find developers. 155K profiles. GitHub contributions tracked. AI explains technical work to recruiters.

## What database?
PostgreSQL 'talent' @ localhost:5432. Use `config.py` for connections.

## Main code locations:
- API endpoints: `api/routers/`
- Business logic: `api/services/`
- Database queries: `api/crud/`
- Scripts users run: `scripts/`
- GitHub enrichment: `github_automation/`
- Frontend: `frontend/src/`
- Tests: `tests/`

## Don't touch:
- `archived_implementations/` - old code
- `archived_databases/` - old databases
- `talent_intelligence.db` - old SQLite file

## Adding a feature?
1. API endpoint → `api/routers/<resource>.py`
2. Database query → `api/crud/<resource>.py`
3. Business logic → `api/services/<feature>.py`
4. Test → `tests/test_<feature>.py`
5. Frontend → `frontend/src/components/<area>/`

## Key patterns:
- Use Pydantic models for API requests/responses
- Use connection pooling: `from config import get_db_context`
- Type hints required
- Async for I/O
- Tests with pytest

## Running things:
```bash
python run_api.py              # Start API (port 8000)
cd frontend && npm run dev     # Start frontend (port 3000)
pytest                         # Run tests
python config.py               # Check database connection
```

## Questions?
Read `.cursorrules` in project root for comprehensive guide.


