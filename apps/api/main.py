"""
ClusterCloud API - Main Entry Point

FastAPI application serving the ClusterCloud control plane.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings
from database import engine, Base
from domains.jobs.router import router as jobs_router
from domains.nodes.router import router as nodes_router
from domains.tasks.router import router as tasks_router
from domains.workloads.router import router as workloads_router
from domains.incidents.router import router as incidents_router
from domains.reliability.router import router as reliability_router
from domains.ledger.router import router as ledger_router
from domains.websocket.router import router as websocket_router


# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager - startup and shutdown logic."""
    logger.info("Starting ClusterCloud API...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    yield
    
    logger.info("Shutting down ClusterCloud API...")


# Create FastAPI application
app = FastAPI(
    title="ClusterCloud API",
    description="Community-owned cloud computing marketplace",
    version="0.1.0",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "clustercloud-api",
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "ClusterCloud API",
        "version": "0.1.0",
        "description": "Community-owned cloud computing marketplace",
        "docs": "/docs",
        "health": "/health"
    }


# Include domain routers
app.include_router(workloads_router, prefix="/api/workloads", tags=["workloads"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["tasks"])
app.include_router(nodes_router, prefix="/api/nodes", tags=["nodes"])
app.include_router(incidents_router, prefix="/api/incidents", tags=["incidents"])
app.include_router(reliability_router, prefix="/api/reliability", tags=["reliability"])
app.include_router(ledger_router, prefix="/api/ledger", tags=["ledger"])
app.include_router(websocket_router, prefix="/ws", tags=["websocket"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
