from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field

class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: str = Field(..., max_length=50)
    blood_type: str = "unknown"
    ethnicity: Optional[str] = None
    preferred_language: str = "en"
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    ethnicity: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class PatientResponse(PatientBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PatientSummary(BaseModel):
    """Lightweight patient listing."""
    id: str
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date
    created_at: datetime

    class Config:
        from_attributes = True
