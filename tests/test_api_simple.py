# ABOUTME: Simple API tests to verify server works
# ABOUTME: Tests basic endpoints and server health

import pytest
from httpx import Client
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.api
def test_api_imports():
    """Test that API modules can be imported"""
    from api import main, config, dependencies
    from api.models import person, company, common
    from api.crud import person as person_crud
    from api.routers import people, companies, stats
    
    assert main.app is not None
    assert hasattr(main.app, 'title')


@pytest.mark.api  
def test_api_configuration():
    """Test API configuration loads correctly"""
    from api.config import settings
    
    assert settings.API_TITLE is not None
    assert settings.API_VERSION is not None
    assert settings.DEFAULT_PAGE_SIZE > 0
    assert settings.MAX_PAGE_SIZE > settings.DEFAULT_PAGE_SIZE


@pytest.mark.api
def test_pydantic_models():
    """Test Pydantic models can be instantiated"""
    from api.models.person import PersonCreate, PersonResponse
    from api.models.company import CompanyCreate, CompanyResponse
    from api.models.common import SuccessResponse, PaginationMeta
    
    # Test person model
    person = PersonCreate(
        full_name="Test Person",
        first_name="Test",
        last_name="Person"
    )
    assert person.full_name == "Test Person"
    
    # Test company model
    company = CompanyCreate(
        company_name="Test Company"
    )
    assert company.company_name == "Test Company"
    
    # Test pagination
    pagination = PaginationMeta(offset=0, limit=10, total=100)
    assert pagination.offset == 0


@pytest.mark.api
def test_crud_imports():
    """Test CRUD operations modules load"""
    from api.crud import person, company
    
    assert hasattr(person, 'get_person')
    assert hasattr(person, 'create_person')
    assert hasattr(company, 'get_company')
    assert hasattr(company, 'create_company')


@pytest.mark.api  
def test_router_registration():
    """Test routers are registered with app"""
    from api.main import app
    
    routes = [route.path for route in app.routes]
    
    # Check key endpoints exist
    assert "/" in routes
    assert "/health" in routes
    # Routers add their own routes dynamically


@pytest.mark.api
def test_app_metadata():
    """Test app has correct metadata"""
    from api.main import app
    
    assert app.title == "Talent Intelligence API"
    assert app.version == "1.0.0"
    assert app.docs_url == "/docs"
    assert app.redoc_url == "/redoc"

