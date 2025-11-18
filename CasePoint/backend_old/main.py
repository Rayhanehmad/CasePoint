"""
KanoonPK SaaS Backend
FastAPI application for legal research platform
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, create_tables
from app.api.routes import auth, search, documents, admin, subscriptions
from app.core.exceptions import setup_exception_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting KanoonPK SaaS Backend...")
    await create_tables()
    print("✅ Database tables created")
    yield
    # Shutdown
    print("👋 Shutting down KanoonPK Backend")

# Create FastAPI application
app = FastAPI(
    title="KanoonPK SaaS API",
    description="Legal Research Platform API with OCR and AI capabilities",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)

# Include API routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["Subscriptions"])

# Add AI routes for legacy OpenAI integration
from app.api.routes import ai
app.include_router(ai.router, prefix="/api/ai", tags=["AI Analysis"])

# Mount static files
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🏛️ KanoonPK SaaS API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/api/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "kanoonpk-backend",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )