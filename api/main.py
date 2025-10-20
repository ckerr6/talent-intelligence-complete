# ABOUTME: FastAPI main application entry point
# ABOUTME: Configures app, middleware, routes, and startup/shutdown events

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.config import settings
from api.routers import people, companies, stats
from api.models.common import HealthResponse
from config import Config


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)


# Include routers
app.include_router(people.router, prefix="/api")
app.include_router(companies.router, prefix="/api")
app.include_router(stats.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Initialize connection pool and resources on startup"""
    print("="*80)
    print("🚀 Starting Talent Intelligence API")
    print("="*80)
    
    try:
        # Initialize connection pool
        Config.get_connection_pool()
        print("✅ Connection pool initialized")
    except Exception as e:
        print(f"⚠️  Warning: Connection pool initialization failed: {e}")
        print("   API will use direct connections")
    
    print(f"📍 API available at: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 Docs available at: http://{settings.HOST}:{settings.PORT}/docs")
    print("="*80)


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    print("\n" + "="*80)
    print("🛑 Shutting down Talent Intelligence API")
    print("="*80)
    
    try:
        Config.close_connection_pool()
        print("✅ Connection pool closed")
    except Exception as e:
        print(f"⚠️  Warning: Error closing connection pool: {e}")
    
    print("👋 Goodbye!")
    print("="*80)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Talent Intelligence API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint"""
    pool_health = Config.check_pool_health()
    
    return {
        "status": "healthy",
        "database": Config.PG_DATABASE,
        "timestamp": datetime.now(),
        "pool_health": pool_health
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Not found",
            "detail": f"The endpoint {request.url.path} does not exist"
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later."
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )

