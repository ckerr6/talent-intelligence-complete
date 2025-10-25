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
from api.routers import people, companies, stats, graph, query, analytics, network, recruiter_workflow, ai, market_intelligence, cache, advanced_search, github_ingestion, network_enhanced, market_intelligence_enhanced, profile_enrichment, github, discovery, market_analytics_deep, notifications, github_intelligence
from api.models.common import HealthResponse
from config import Config
from api.services.background_scheduler import start_scheduler, stop_scheduler


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Configure CORS - Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when using wildcard
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"]  # Expose all headers to the client
)


# Include routers
app.include_router(people.router, prefix="/api")
app.include_router(companies.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(network.router)  # Has /api/network prefix in router
app.include_router(recruiter_workflow.router)  # Has /api/workflow prefix in router
app.include_router(ai.router)  # Has /api/ai prefix in router
app.include_router(market_intelligence.router)  # Has /api/market prefix in router
app.include_router(cache.router)  # Has /api/cache prefix in router
app.include_router(advanced_search.router, prefix="/api")  # Advanced multi-criteria search
app.include_router(github_ingestion.router)  # Has /api/github/ingest prefix in router
app.include_router(github.router, prefix="/api")  # GitHub discovery data endpoints
app.include_router(discovery.router, prefix="/api")  # Discovery system endpoints
app.include_router(network_enhanced.router)  # Enhanced network features (multi-node, tech filter)
app.include_router(market_intelligence_enhanced.router)  # Interactive market intel (technologists, 10x engineers)
app.include_router(profile_enrichment.router)  # On-demand GitHub stats enrichment
app.include_router(market_analytics_deep.router, prefix="/api")  # Deep market analytics and company insights
app.include_router(notifications.router, prefix="/api")  # AI-powered notifications and monitoring
app.include_router(github_intelligence.router)  # GitHub-native intelligence endpoints


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
    
    # Start background scheduler for AI monitoring
    try:
        start_scheduler()
        print("✅ Background scheduler started (AI monitoring)")
    except Exception as e:
        print(f"⚠️  Warning: Background scheduler failed to start: {e}")
        print("   AI monitoring will not run automatically")
    
    print(f"📍 API available at: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 Docs available at: http://{settings.HOST}:{settings.PORT}/docs")
    print("="*80)


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    print("\n" + "="*80)
    print("🛑 Shutting down Talent Intelligence API")
    print("="*80)
    
    # Stop background scheduler
    try:
        stop_scheduler()
        print("✅ Background scheduler stopped")
    except Exception as e:
        print(f"⚠️  Warning: Error stopping scheduler: {e}")
    
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

