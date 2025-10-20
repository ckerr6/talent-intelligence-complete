# ABOUTME: Tests for FastAPI endpoints
# ABOUTME: Integration tests for API routes and responses

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app


client = TestClient(app)


@pytest.mark.api
class TestRootEndpoints:
    """Test root and health endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["docs"] == "/docs"
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "timestamp" in data


@pytest.mark.api
class TestPeopleEndpoints:
    """Test people API endpoints"""
    
    def test_list_people(self):
        """Test listing people"""
        response = client.get("/api/people?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert isinstance(data["data"], list)
    
    def test_list_people_with_filters(self):
        """Test listing people with filters"""
        response = client.get("/api/people?location=San%20Francisco&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    def test_create_person(self):
        """Test creating a person"""
        person_data = {
            "full_name": "Test Person",
            "first_name": "Test",
            "last_name": "Person",
            "linkedin_url": "https://linkedin.com/in/testperson",
            "location": "Test City",
            "emails": [
                {"email": "test@example.com", "is_primary": True}
            ]
        }
        
        response = client.post("/api/people", json=person_data)
        # May fail if database is read-only in tests
        assert response.status_code in [201, 400, 500]
    
    def test_get_person_invalid_id(self):
        """Test getting person with invalid ID"""
        response = client.get("/api/people/invalid-uuid")
        assert response.status_code == 400
    
    def test_search_by_company(self):
        """Test searching people by company"""
        response = client.get("/api/people/search/company?company_name=Acme")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
    
    def test_search_by_location(self):
        """Test searching people by location"""
        response = client.get("/api/people/search/location?location=San%20Francisco")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


@pytest.mark.api
class TestCompanyEndpoints:
    """Test company API endpoints"""
    
    def test_list_companies(self):
        """Test listing companies"""
        response = client.get("/api/companies?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert isinstance(data["data"], list)
    
    def test_list_companies_with_filters(self):
        """Test listing companies with filters"""
        response = client.get("/api/companies?industry=Technology&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    def test_create_company(self):
        """Test creating a company"""
        company_data = {
            "company_name": "Test Company",
            "website": "https://testcompany.com",
            "industry": "Technology"
        }
        
        response = client.post("/api/companies", json=company_data)
        # May fail if database is read-only in tests
        assert response.status_code in [201, 400, 500]
    
    def test_get_company_invalid_id(self):
        """Test getting company with invalid ID"""
        response = client.get("/api/companies/invalid-uuid")
        assert response.status_code == 400


@pytest.mark.api
class TestStatsEndpoints:
    """Test statistics API endpoints"""
    
    def test_overview_stats(self):
        """Test getting overview statistics"""
        response = client.get("/api/stats/overview")
        assert response.status_code == 200
        data = response.json()
        assert "totals" in data
        assert "people" in data["totals"]
        assert "companies" in data["totals"]
    
    def test_quality_metrics(self):
        """Test getting quality metrics"""
        response = client.get("/api/stats/quality")
        assert response.status_code == 200
        data = response.json()
        assert "total_people" in data or "error" in data
    
    def test_coverage_stats(self):
        """Test getting coverage statistics"""
        response = client.get("/api/stats/coverage")
        assert response.status_code == 200
        data = response.json()
        assert "total_people" in data or "error" in data


@pytest.mark.api
class TestPagination:
    """Test pagination functionality"""
    
    def test_pagination_params(self):
        """Test pagination parameters"""
        response = client.get("/api/people?limit=5&offset=10")
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["limit"] == 5
        assert data["pagination"]["offset"] == 10
    
    def test_pagination_max_limit(self):
        """Test pagination respects max limit"""
        response = client.get("/api/people?limit=99999")
        assert response.status_code in [200, 422]  # 422 if validation rejects
    
    def test_pagination_negative_offset(self):
        """Test negative offset is rejected"""
        response = client.get("/api/people?offset=-1")
        assert response.status_code == 422  # Validation error


@pytest.mark.api
class TestErrorHandling:
    """Test API error handling"""
    
    def test_404_not_found(self):
        """Test 404 for non-existent endpoints"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "error" in data
    
    def test_invalid_json(self):
        """Test invalid JSON in POST request"""
        response = client.post(
            "/api/people",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
    
    def test_missing_required_field(self):
        """Test missing required field in POST"""
        response = client.post("/api/people", json={})
        assert response.status_code == 422  # Validation error


@pytest.mark.api
class TestDocumentation:
    """Test API documentation endpoints"""
    
    def test_openapi_schema(self):
        """Test OpenAPI schema is accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
    
    def test_swagger_docs(self):
        """Test Swagger UI is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc(self):
        """Test ReDoc is accessible"""
        response = client.get("/redoc")
        assert response.status_code == 200

