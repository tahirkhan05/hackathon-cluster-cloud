"""ClusterCloud API - Main Entry Point"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings
from database import engine, Base
from init_db import init_database

from domains.jobs.router import router as jobs_router
from domains.nodes.router import router as nodes_router
from domains.tasks.router import router as tasks_router
from domains.workloads.router import router as workloads_router
from domains.incidents.router import router as incidents_router
from domains.reliability.router import router as reliability_router
from domains.ledger.router import router as ledger_router
from domains.websocket.router import router as websocket_router
from domains.scheduling.router import router as scheduling_router


logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    logger.info("🚀 Starting ClusterCloud API...")
    
    # Initialize database
    try:
        Base.metadata.create_all(bind=engine)
        init_database()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"Database init: {e}")
    
    yield
    
    logger.info("Shutting down...")


app = FastAPI(
    title="ClusterCloud API",
    description="Community cloud computing marketplace",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "clustercloud-api"}


@app.get("/")
async def root():
    return {
        "service": "ClusterCloud",
        "version": "0.1.0",
        "docs": "/docs"
    }


app.include_router(workloads_router, prefix="/api/workloads", tags=["workloads"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["tasks"])
app.include_router(nodes_router, prefix="/api/nodes", tags=["nodes"])
app.include_router(incidents_router, prefix="/api/incidents", tags=["incidents"])
app.include_router(reliability_router, prefix="/api/reliability", tags=["reliability"])
app.include_router(ledger_router, prefix="/api/ledger", tags=["ledger"])
app.include_router(websocket_router, prefix="/ws", tags=["websocket"])
app.include_router(scheduling_router, prefix="/api/scheduling", tags=["scheduling"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
