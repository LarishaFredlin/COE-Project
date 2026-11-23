
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.database import init_database
from backend.routes.investigations import router as investigation_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(
    title="SpareSync API",
    description="Inventory Transaction Reconciliation and Investigation Management API",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
def home():
    return {
        "message": "Welcome to SpareSync API",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "SpareSync"
    }


app.include_router(investigation_router)
