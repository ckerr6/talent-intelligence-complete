# API Backend - FastAPI Application

## Structure

```
api/
├── routers/        # API endpoints (one file per resource)
├── crud/          # Database operations (pure SQL)
├── services/      # Business logic (AI, enrichment, caching)
├── models/        # Pydantic models for validation
├── dependencies.py # Shared dependencies (DB connection, pagination)
├── config.py      # API-specific configuration
└── main.py        # FastAPI app initialization
```

## Adding a New Endpoint

1. **Create router** in `routers/`
2. **Add CRUD functions** in `crud/`
3. **Define models** in `models/`
4. **Write tests** in `../tests/`

### Example: Adding a new resource "Skills"

**Step 1: Create router** (`api/routers/skills.py`)
```python
from fastapi import APIRouter, Depends
from api.crud import skills as skills_crud
from api.models.skills import SkillResponse
from api.dependencies import get_db

router = APIRouter(prefix="/skills", tags=["skills"])

@router.get("/", response_model=list[SkillResponse])
def list_skills(db=Depends(get_db)):
    return skills_crud.get_all_skills(db)
```

**Step 2: Add CRUD** (`api/crud/skills.py`)
```python
def get_all_skills(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT skill_id, skill_name FROM skills ORDER BY skill_name")
    return cursor.fetchall()
```

**Step 3: Define model** (`api/models/skills.py`)
```python
from pydantic import BaseModel

class SkillResponse(BaseModel):
    skill_id: str
    skill_name: str
```

**Step 4: Register router** in `main.py`:
```python
from api.routers import skills
app.include_router(skills.router, prefix="/api")
```

## Key Services

### AI Service (`services/ai_service.py`)
- Profile summaries (career analysis)
- Code quality analysis
- Interactive Q&A
- Uses OpenAI GPT-4o-mini or Claude Sonnet

### Cache Service (`services/cache_service.py`)
- Redis-backed caching
- 17x performance improvement on searches
- Automatic TTL management

### Background Intelligence (`services/ai_research_assistant.py`)
- Monitors saved searches for new matches
- Detects job changes
- Tracks GitHub activity
- Rising talent identification

## Database Connection Pattern

**Always use connection pooling:**
```python
from config import get_db_context

with get_db_context() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM person WHERE person_id = %s", (person_id,))
    result = cursor.fetchone()
# Connection automatically returned to pool
```

## Common Patterns

### Pagination
```python
from api.dependencies import get_pagination_params, PaginationParams

@router.get("/")
def list_items(pagination: PaginationParams = Depends(get_pagination_params)):
    items = crud.get_items(db, offset=pagination.offset, limit=pagination.limit)
    return {"data": items, "pagination": {...}}
```

### Error Handling
```python
from fastapi import HTTPException

@router.get("/{item_id}")
def get_item(item_id: str):
    item = crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

### UUID Validation
```python
from api.dependencies import validate_uuid

@router.get("/{person_id}")
def get_person(person_id: str):
    try:
        validate_uuid(person_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # ... rest of logic
```

## Testing

Tests in `../tests/test_<router>.py`:

```python
from starlette.testclient import TestClient
from api.main import app

def test_list_endpoint():
    client = TestClient(app)
    response = client.get("/api/items")
    assert response.status_code == 200
    assert "data" in response.json()
```

## API Documentation

When API is running:
- Interactive docs: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- Alternative docs: http://localhost:8000/redoc
