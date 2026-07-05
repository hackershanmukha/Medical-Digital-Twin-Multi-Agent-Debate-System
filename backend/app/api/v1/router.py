from fastapi import APIRouter
from app.api.v1 import auth, patients, vitals, debate

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(patients.router, prefix="/patients", tags=["Digital Twins"])
api_router.include_router(vitals.router, prefix="/vitals", tags=["Vitals"])
api_router.include_router(debate.router, prefix="/debate", tags=["Debate"])
