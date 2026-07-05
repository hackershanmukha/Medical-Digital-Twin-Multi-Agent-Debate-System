from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.vitals import Vitals
from app.schemas.vitals import VitalsCreate, VitalsResponse

router = APIRouter()

@router.post("/", response_model=VitalsResponse, status_code=201)
async def record_vitals(
    vitals_in: VitalsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a new vitals measurement for a patient."""
    vitals = Vitals(**vitals_in.model_dump())
    # Auto-compute BMI if height and weight provided
    if vitals.height_cm and vitals.weight_kg and not vitals.bmi:
        height_m = vitals.height_cm / 100
        vitals.bmi = round(vitals.weight_kg / (height_m ** 2), 1)
    db.add(vitals)
    await db.commit()
    await db.refresh(vitals)
    return vitals

@router.get("/{patient_id}/history", response_model=List[VitalsResponse])
async def get_vitals_history(
    patient_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get vitals history for a patient, most recent first."""
    result = await db.execute(
        select(Vitals)
        .where(Vitals.patient_id == patient_id)
        .order_by(Vitals.measured_at.desc())
        .limit(limit)
    )
    return result.scalars().all()

@router.get("/{patient_id}/latest", response_model=VitalsResponse)
async def get_latest_vitals(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the most recent vitals for a patient."""
    result = await db.execute(
        select(Vitals)
        .where(Vitals.patient_id == patient_id)
        .order_by(Vitals.measured_at.desc())
        .limit(1)
    )
    vitals = result.scalars().first()
    if not vitals:
        raise HTTPException(status_code=404, detail="No vitals found for this patient")
    return vitals
