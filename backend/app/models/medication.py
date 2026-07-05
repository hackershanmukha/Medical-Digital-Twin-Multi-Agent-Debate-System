import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import String, Date, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    generic_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    strength: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "10mg"
    route: Mapped[str] = mapped_column(String(50), default="oral")       # oral, iv, sc
    frequency: Mapped[str] = mapped_column(String(50), default="once_daily")
    dose_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dose_unit: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    indication: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    patient = relationship("Patient", back_populates="medications")
