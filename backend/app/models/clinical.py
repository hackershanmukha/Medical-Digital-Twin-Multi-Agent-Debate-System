import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import String, Date, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class Condition(Base):
    __tablename__ = "conditions"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    icd10_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    diagnosed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    severity: Mapped[str] = mapped_column(String(50), default="mild")
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, chronic, resolved
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    patient = relationship("Patient", back_populates="conditions")


class Allergy(Base):
    __tablename__ = "allergies"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    allergen: Mapped[str] = mapped_column(String(200), nullable=False)
    allergen_type: Mapped[str] = mapped_column(String(50), default="drug")  # drug, food, environmental
    reaction: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="mild")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    patient = relationship("Patient", back_populates="allergies")
