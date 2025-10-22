# ABOUTME: API-specific configuration settings
# ABOUTME: Separate from main config for API server settings

from pydantic_settings import BaseSettings
from typing import List


class APISettings(BaseSettings):
    """API-specific settings"""
    
    # API metadata
    API_TITLE: str = "Talent Intelligence API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "REST API for talent intelligence database"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True  # Auto-reload for development
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080"
    ]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    # Pagination defaults (reduced for demo performance)
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Rate limiting (placeholder for future implementation)
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Authentication (placeholder for future implementation)
    AUTH_ENABLED: bool = False
    API_KEY_HEADER: str = "X-API-Key"
    
    model_config = {
        "env_prefix": "API_",
        "env_file": ".env",
        "extra": "ignore"  # Allow extra env vars without validation errors
    }


# Global settings instance
settings = APISettings()

