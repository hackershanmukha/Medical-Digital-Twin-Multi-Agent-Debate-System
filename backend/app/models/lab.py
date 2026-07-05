import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class LabReport(Base):
    __tablename__ = "lab_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    panel_name: Mapped[str] = mapped_column(String(200), nullable=False)  # e.g., "Lipid Panel", "CBC"
    test_name: Mapped[str] = mapped_column(String(200), nullable=False)   # e.g., "LDL Cholesterol"
    loinc_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    
    ref_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ref_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    flag: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # "L" (Low), "H" (High), "N" (Normal)
    
    collected_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    patient = relationship("Patient", back_populates="lab_reports")
