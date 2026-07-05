from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.vitals import Vitals
from app.models.clinical import Condition, Allergy
from app.models.medication import Medication
from app.models.lab import LabReport
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse, PatientSummary
from app.schemas.vitals import VitalsResponse
from app.schemas.clinical import (
    ConditionCreate, ConditionResponse,
    AllergyCreate, AllergyResponse,
    MedicationCreate, MedicationResponse,
    LabReportCreate, LabReportResponse,
)

router = APIRouter()

# ─── Patient CRUD ────────────────────────────────────────────────────────────

@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_in: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new patient digital twin."""
    db_patient = Patient(**patient_in.model_dump(), created_by=current_user.id)
    db.add(db_patient)
    await db.commit()
    await db.refresh(db_patient)
    return db_patient

@router.get("/", response_model=List[PatientSummary])
async def list_patients(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all patients for the current clinician."""
    stmt = (
        select(Patient)
        .where(Patient.created_by == current_user.id)
        .order_by(Patient.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single patient by ID."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this patient")
    return patient

@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_in: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update patient demographics."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = patient_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
    await db.commit()
    await db.refresh(patient)
    return patient

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a patient and all associated data."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.delete(patient)
    await db.commit()

# ─── Nested Clinical Data ────────────────────────────────────────────────────

@router.post("/{patient_id}/conditions", response_model=ConditionResponse, status_code=201)
async def add_condition(
    patient_id: str,
    condition_in: ConditionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    condition = Condition(**condition_in.model_dump())
    condition.patient_id = patient_id
    db.add(condition)
    await db.commit()
    await db.refresh(condition)
    return condition

@router.get("/{patient_id}/conditions", response_model=List[ConditionResponse])
async def list_conditions(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Condition).where(Condition.patient_id == patient_id))
    return result.scalars().all()

@router.post("/{patient_id}/allergies", response_model=AllergyResponse, status_code=201)
async def add_allergy(
    patient_id: str,
    allergy_in: AllergyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allergy = Allergy(**allergy_in.model_dump())
    allergy.patient_id = patient_id
    db.add(allergy)
    await db.commit()
    await db.refresh(allergy)
    return allergy

@router.get("/{patient_id}/allergies", response_model=List[AllergyResponse])
async def list_allergies(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Allergy).where(Allergy.patient_id == patient_id))
    return result.scalars().all()

@router.post("/{patient_id}/medications", response_model=MedicationResponse, status_code=201)
async def add_medication(
    patient_id: str,
    med_in: MedicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    med = Medication(**med_in.model_dump())
    med.patient_id = patient_id
    db.add(med)
    await db.commit()
    await db.refresh(med)
    return med

@router.get("/{patient_id}/medications", response_model=List[MedicationResponse])
async def list_medications(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Medication).where(Medication.patient_id == patient_id)
    )
    return result.scalars().all()

@router.post("/{patient_id}/labs", response_model=LabReportResponse, status_code=201)
async def add_lab_report(
    patient_id: str,
    lab_in: LabReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lab = LabReport(**lab_in.model_dump())
    lab.patient_id = patient_id
    db.add(lab)
    await db.commit()
    await db.refresh(lab)
    return lab

@router.get("/{patient_id}/labs", response_model=List[LabReportResponse])
async def list_lab_reports(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(LabReport)
        .where(LabReport.patient_id == patient_id)
        .order_by(LabReport.collected_at.desc())
    )
    return result.scalars().all()
