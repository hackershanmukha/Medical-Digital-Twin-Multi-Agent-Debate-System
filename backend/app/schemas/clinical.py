from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field

# --- Conditions ---
class ConditionCreate(BaseModel):
    patient_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=200)
    icd10_code: Optional[str] = None
    diagnosed_date: Optional[date] = None
    severity: str = "mild"
    status: str = "active"
    is_primary: bool = False

class ConditionResponse(ConditionCreate):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

# --- Allergies ---
class AllergyCreate(BaseModel):
    patient_id: Optional[str] = None
    allergen: str = Field(..., min_length=1, max_length=200)
    allergen_type: str = "drug"
    reaction: str = Field(..., min_length=1, max_length=500)
    severity: str = "mild"
    verified: bool = False

class AllergyResponse(AllergyCreate):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

# --- Medications ---
class MedicationCreate(BaseModel):
    patient_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=200)
    generic_name: Optional[str] = None
    strength: str
    route: str = "oral"
    frequency: str = "once_daily"
    dose_amount: Optional[float] = None
    dose_unit: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    is_active: bool = True
    indication: Optional[str] = None

class MedicationResponse(MedicationCreate):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

# --- Lab Reports ---
class LabReportCreate(BaseModel):
    patient_id: Optional[str] = None
    panel_name: str
    test_name: str
    loinc_code: Optional[str] = None
    value: float
    unit: str
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    flag: Optional[str] = None
    collected_at: datetime

class LabReportResponse(LabReportCreate):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
