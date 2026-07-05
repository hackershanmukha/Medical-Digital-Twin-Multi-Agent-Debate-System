import sys
import os

# Allow importing modules from the project root directory
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine
from app.db.base_class import Base
# Import all models so they register on Base.metadata
from app.models import User, Patient, Vitals, Condition, Allergy, Medication, LabReport, Debate  # noqa: F401
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Medical Digital Twin & Debate System API",
    description="Production-ready clinical debate and risk analysis API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "medical-twin-debate-api"}


@app.get("/")
def read_root():
    return {"message": "Welcome to the Medical Digital Twin & Multi-Agent Debate API"}
