from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class VitalsCreate(BaseModel):
    patient_id: str
    systolic_bp: Optional[float] = Field(None, ge=50, le=300)
    diastolic_bp: Optional[float] = Field(None, ge=30, le=200)
    heart_rate: Optional[float] = Field(None, ge=30, le=250)
    respiratory_rate: Optional[float] = Field(None, ge=5, le=60)
    oxygen_saturation: Optional[float] = Field(None, ge=50, le=100)
    temperature_c: Optional[float] = Field(None, ge=30, le=45)
    height_cm: Optional[float] = Field(None, ge=30, le=250)
    weight_kg: Optional[float] = Field(None, ge=1, le=300)
    bmi: Optional[float] = Field(None, ge=10, le=70)

class VitalsResponse(VitalsCreate):
    id: int
    measured_at: datetime

    class Config:
        from_attributes = True
