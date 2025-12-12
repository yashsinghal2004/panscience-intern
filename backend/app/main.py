"""FastAPI main application."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.analytics_routes import router as analytics_router
from app.api.business_routes import router as business_router
from app.middleware.performance import PerformanceMiddleware
from app.core.config import settings, get_cors_origins
from app.core.logging_config import setup_logging
from app.models.database import init_db

# Setup logging
setup_logging(log_level="INFO" if not settings.DEBUG else "DEBUG")
logger = logging.getLogger(__name__)

# Initialize database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.warning(f"Database initialization warning: {e}")

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Production-ready RAG Document Q&A API with Analytics",
)

# Performance tracking middleware
app.add_middleware(PerformanceMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["RAG"])
app.include_router(analytics_router, prefix="/api/v1", tags=["Analytics"])
app.include_router(business_router, prefix="/api/v1/business", tags=["Business Analysis"])

# Include diagnostic router for debugging
from app.api.diagnostic_routes import router as diagnostic_router
app.include_router(diagnostic_router, prefix="/api/v1/diagnostic", tags=["Diagnostics"])

# Include migration router for index fixes
from app.api.migration_routes import router as migration_router
app.include_router(migration_router, prefix="/api/v1", tags=["Migration"])

# Include fix router for data consistency
from app.api.fix_routes import router as fix_router
app.include_router(fix_router, prefix="/api/v1/fix", tags=["Data Fixes"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RAG Document Q&A API",
        "version": settings.API_VERSION,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )


