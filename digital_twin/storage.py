"""
SQLite Storage Layer for Digital Twin
Async SQLAlchemy models and repository pattern for persistence.
"""
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    select,
)
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    selectinload,
)

from config.settings import settings


# ============================================================================
# Database Setup
# ============================================================================

class Base(DeclarativeBase):
    """Base class for all models."""
    pass


# Create async engine
def get_async_engine() -> AsyncEngine:
    """Get or create async engine."""
    return create_async_engine(
        settings.database_url.replace("sqlite://", "sqlite+aiosqlite://"),
        echo=settings.database_echo,
        pool_pre_ping=True,
    )


# Create sync engine for migrations
def get_sync_engine() -> Engine:
    """Get or create sync engine for Alembic."""
    return create_engine(
        settings.database_url.replace("sqlite+aiosqlite://", "sqlite://"),
        echo=settings.database_echo,
    )


# Session factory
async_session_factory = async_sessionmaker(
    get_async_engine(),
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session() -> AsyncSession:
    """Get database session with automatic commit/rollback."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ============================================================================
# SQLAlchemy Models
# ============================================================================

class PatientDB(Base):
    """Patient demographic information."""
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    date_of_birth: Mapped[datetime] = mapped_column(DateTime)
    gender: Mapped[str] = mapped_column(String(20))
    blood_type: Mapped[str] = mapped_column(String(10), default="unknown")
    ethnicity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    vitals: Mapped[list["VitalsDB"]] = relationship(
        "VitalsDB", back_populates="patient", cascade="all, delete-orphan"
    )
    conditions: Mapped[list["MedicalConditionDB"]] = relationship(
        "MedicalConditionDB", back_populates="patient", cascade="all, delete-orphan"
    )
    allergies: Mapped[list["AllergyDB"]] = relationship(
        "AllergyDB", back_populates="patient", cascade="all, delete-orphan"
    )
    medications: Mapped[list["MedicationDB"]] = relationship(
        "MedicationDB", back_populates="patient", cascade="all, delete-orphan"
    )
    lab_panels: Mapped[list["LabPanelDB"]] = relationship(
        "LabPanelDB", back_populates="patient", cascade="all, delete-orphan"
    )
    lifestyle: Mapped[Optional["LifestyleDB"]] = relationship(
        "LifestyleDB", back_populates="patient", cascade="all, delete-orphan", uselist=False
    )
    family_history: Mapped[list["FamilyHistoryDB"]] = relationship(
        "FamilyHistoryDB", back_populates="patient", cascade="all, delete-orphan"
    )
    digital_twin: Mapped[Optional["DigitalTwinDB"]] = relationship(
        "DigitalTwinDB", back_populates="patient", cascade="all, delete-orphan", uselist=False
    )

    __table_args__ = (
        Index("ix_patients_name", "last_name", "first_name"),
        Index("ix_patients_dob", "date_of_birth"),
    )


class VitalsDB(Base):
    """Patient vital signs."""
    __tablename__ = "vitals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"))

    # Cardiovascular
    systolic_bp: Mapped[Optional[float]] = mapped_column(nullable=True)
    diastolic_bp: Mapped[Optional[float]] = mapped_column(nullable=True)
    heart_rate: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Respiratory
    respiratory_rate: Mapped[Optional[float]] = mapped_column(nullable=True)
    oxygen_saturation: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Temperature
    temperature_c: Mapped[Optional[float]] = mapped_column(nullable=True)
    temperature_f: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Anthropometric
    height_cm: Mapped[Optional[float]] = mapped_column(nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(nullable=True)
    bmi: Mapped[Optional[float]] = mapped_column(nullable=True)
    waist_circumference_cm: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Metadata
    measured_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    measured_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    patient: Mapped["PatientDB"] = relationship("PatientDB", back_populates="vitals")


class MedicalConditionDB(Base):
    """Medical conditions/diagnoses."""
    __tablename__ = "medical_conditions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"))

    name: Mapped[str] = mapped_column(String(200))
    icd10_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    diagnosed_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="mild")
    status: Mapped[str] = mapped_column(String(30), default="active")
    treating_physician: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    patient: Mapped["PatientDB"] = relationship("PatientDB", back_populates="conditions")

    __table_args__ = (
        Index("ix_conditions_patient_status", "patient_id", "status"),
        Index("ix_conditions_icd10", "icd10_code"),
    )


class AllergyDB(Base):
    """Patient allergies."""
    __tablename__ = "allergies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"))

    allergen: Mapped[str] = mapped_column(String(200))
    allergen_type: Mapped[str] = mapped_column(String(30), default="drug")
    reaction: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default="mild")
    onset_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    verified: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    patient: Mapped["PatientDB"] = relationship("PatientDB", back_populates="allergies")


class MedicationDB(Base):
    """Patient medications."""
    __tablename__ = "medications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"))

    name: Mapped[str] = mapped_column(String(200))
    generic_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    brand_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    strength: Mapped[str] = mapped_column(String(100))
    route: Mapped[str] = mapped_column(String(30), default="oral")
    frequency: Mapped[str] = mapped_column(String(30), default="once_daily")
    custom_frequency: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dose_amount: Mapped[Optional[float]] = mapped_column(nullable=True)
    dose_unit: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Prescribing info
    prescribing_physician: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    prescription_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_prn: Mapped[bool] = mapped_column(default=False)

    # Indication & Monitoring
    indication: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_condition: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    monitoring_parameters: Mapped[list[str]] = mapped_column(SQLiteJSON, default=list)

    # Adherence
    adherence: Mapped[str] = mapped_column(String(20), default="unknown")
    missed_doses_last_month: Mapped[int] = mapped_column(default=0)
    last_refill_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    days_supply: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Safety
    allergies_checked: Mapped[bool] = mapped_column(default=False)
    interactions_checked: Mapped[bool] = mapped_column(default=False)
    renal_adjustment: Mapped[bool] = mapped_column(default=False)
    hepatic_adjustment: Mapped[bool] = mapped_column(default=False)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    patient: Mapped["PatientDB"] = relationship("PatientDB", back_populates="medications")

    __table_args__ = (
        Index("ix_medications_patient_active", "patient_id", "is_active"),
    )


class LabPanelDB(Base):
    """Lab test panels."""
    __tablename__ = "lab_panels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"))

    panel_name: Mapped[str] = mapped_column(String(200))
    collected_at: Mapped[datetime] = mapped_column(DateTime)
    resulted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ordering_provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="final")

    patient: Mapped["PatientDB"] = relationship("PatientDB", back_populates="lab_panels")
    tests: Mapped[list["LabReportDB"]] = relationship(
        "LabReportDB", back_populates="panel", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_lab_panels_patient_collected", "patient_id", "collected_at"),
    )


class LabReportDB(Base):
    """Individual lab test results."""
    __tablename__ = "lab_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    panel_id: Mapped[str] = mapped_column(String(36), ForeignKey("lab_panels.id", ondelete="CASCADE"))

    test_name: Mapped[str] = mapped_column(String(200))
    test_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    category: Mapped[str] = mapped_column(String(30), default="other")
    value: Mapped[float] = mapped_column()
    unit: Mapped[str] = mapped_column(String(50))
    reference_range_low: Mapped[Optional[float]] = mapped_column(nullable=True)
    reference_range_high: Mapped[Optional[float]] = mapped_column(nullable=True)
    reference_range_text: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    flag: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    interpretation: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    ordering_provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    performing_lab: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="final")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    panel: Mapped["LabPanelDB"] = relationship("LabPanelDB", back_populates="tests")


class LifestyleDB(Base):
    """Patient lifestyle factors."""
    __tablename__ = "lifestyle"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), unique=True
    )

    # Physical activity
    activity_level: Mapped[str] = mapped_column(String(20), default="sedentary")
    exercise_minutes_per_week: Mapped[int] = mapped_column(default=0)
    exercise_types: Mapped[list[str]] = mapped_column(SQLiteJSON, default=list)

    # Diet
    diet_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    daily_calories: Mapped[Optional[int]] = mapped_column(nullable=True)
    fruit_servings_per_day: Mapped[int] = mapped_column(default=0)
    vegetable_servings_per_day: Mapped[int] = mapped_column(default=0)
    sodium_intake_mg: Mapped[Optional[int]] = mapped_column(nullable=True)
    sugar_intake_g: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Substance use
    smoking_status: Mapped[str] = mapped_column(String(20), default="never")
    pack_years: Mapped[float] = mapped_column(default=0)
    cigarettes_per_day: Mapped[int] = mapped_column(default=0)
    quit_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    alcohol_consumption: Mapped[str] = mapped_column(String(20), default="none")
    drinks_per_week: Mapped[int] = mapped_column(default=0)

    substance_use: Mapped[list[str]] = mapped_column(SQLiteJSON, default=list)

    # Sleep
    sleep_hours_per_night: Mapped[Optional[float]] = mapped_column(nullable=True)
    sleep_quality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sleep_apnea: Mapped[bool] = mapped_column(default=False)

    # Stress & Mental Health
    stress_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    phq9_score: Mapped[Optional[int]] = mapped_column(nullable=True)
    gad7_score: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Social
    occupation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    work_hours_per_week: Mapped[Optional[int]] = mapped_column(nullable=True)
    shift_work: Mapped[bool] = mapped_column(default=False)
    lives_alone: Mapped[bool] = mapped_column(default=False)
    caregiver_support: Mapped[bool] = mapped_column(default=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    patient: Mapped["PatientDB"] = relationship("PatientDB", back_populates="lifestyle")


class FamilyHistoryDB(Base):
    """Family medical history."""
    __tablename__ = "family_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"))

    relation: Mapped[str] = mapped_column(String(50))
    condition: Mapped[str] = mapped_column(String(200))
    icd10_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    age_at_diagnosis: Mapped[Optional[int]] = mapped_column(nullable=True)
    deceased: Mapped[bool] = mapped_column(default=False)
    age_at_death: Mapped[Optional[int]] = mapped_column(nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    patient: Mapped["PatientDB"] = relationship("PatientDB", back_populates="family_history")


class DigitalTwinDB(Base):
    """Digital Twin system metadata."""
    __tablename__ = "digital_twins"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), unique=True
    )

    version: Mapped[int] = mapped_column(default=1)
    data_source: Mapped[str] = mapped_column(String(30), default="manual")
    data_quality_score: Mapped[float] = mapped_column(default=1.0)

    consent_for_ai: Mapped[bool] = mapped_column(default=True)
    consent_for_research: Mapped[bool] = mapped_column(default=False)
    phi_masking_enabled: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    patient: Mapped["PatientDB"] = relationship("PatientDB", back_populates="digital_twin")


# ============================================================================
# Repository Pattern
# ============================================================================

class PatientRepository:
    """Repository for patient data operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, patient: PatientDB) -> PatientDB:
        """Create a new patient."""
        self.session.add(patient)
        await self.session.flush()
        return patient

    async def get_by_id(self, patient_id: str) -> Optional[PatientDB]:
        """Get patient by ID with all relationships loaded."""
        stmt = (
            select(PatientDB)
            .where(PatientDB.id == patient_id)
            .options(
                selectinload(PatientDB.vitals),
                selectinload(PatientDB.conditions),
                selectinload(PatientDB.allergies),
                selectinload(PatientDB.medications),
                selectinload(PatientDB.lab_panels).selectinload(LabPanelDB.tests),
                selectinload(PatientDB.lifestyle),
                selectinload(PatientDB.family_history),
                selectinload(PatientDB.digital_twin),
            )
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_id_simple(self, patient_id: str) -> Optional[PatientDB]:
        """Get patient by ID without loading relationships."""
        stmt = select(PatientDB).where(PatientDB.id == patient_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, patient: PatientDB) -> PatientDB:
        """Update patient."""
        patient.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return patient

    async def delete(self, patient_id: str) -> bool:
        """Delete patient (cascades to all related data)."""
        patient = await self.get_by_id_simple(patient_id)
        if patient:
            await self.session.delete(patient)
            await self.session.flush()
            return True
        return False

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[PatientDB]:
        """List all patients with pagination."""
        stmt = select(PatientDB).order_by(PatientDB.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search(self, query: str, limit: int = 20) -> list[PatientDB]:
        """Search patients by name."""
        stmt = (
            select(PatientDB)
            .where(
                (PatientDB.first_name.ilike(f"%{query}%")) |
                (PatientDB.last_name.ilike(f"%{query}%"))
            )
            .order_by(PatientDB.last_name, PatientDB.first_name)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class VitalsRepository:
    """Repository for vitals data."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, vitals: VitalsDB) -> VitalsDB:
        self.session.add(vitals)
        await self.session.flush()
        return vitals

    async def get_latest(self, patient_id: str) -> Optional[VitalsDB]:
        stmt = (
            select(VitalsDB)
            .where(VitalsDB.patient_id == patient_id)
            .order_by(VitalsDB.measured_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_history(self, patient_id: str, limit: int = 50) -> list[VitalsDB]:
        stmt = (
            select(VitalsDB)
            .where(VitalsDB.patient_id == patient_id)
            .order_by(VitalsDB.measured_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class MedicationRepository:
    """Repository for medications."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, medication: MedicationDB) -> MedicationDB:
        self.session.add(medication)
        await self.session.flush()
        return medication

    async def get_active(self, patient_id: str) -> list[MedicationDB]:
        stmt = (
            select(MedicationDB)
            .where(
                MedicationDB.patient_id == patient_id,
                MedicationDB.is_active == True
            )
            .order_by(MedicationDB.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all(self, patient_id: str) -> list[MedicationDB]:
        stmt = (
            select(MedicationDB)
            .where(MedicationDB.patient_id == patient_id)
            .order_by(MedicationDB.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, medication_id: str) -> Optional[MedicationDB]:
        stmt = select(MedicationDB).where(MedicationDB.id == medication_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, medication: MedicationDB) -> MedicationDB:
        medication.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return medication

    async def deactivate(self, medication_id: str) -> bool:
        med = await self.get_by_id(medication_id)
        if med:
            med.is_active = False
            med.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
            return True
        return False


class LabRepository:
    """Repository for lab data."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_panel(self, panel: LabPanelDB) -> LabPanelDB:
        self.session.add(panel)
        await self.session.flush()
        return panel

    async def get_latest_panel(self, patient_id: str) -> Optional[LabPanelDB]:
        stmt = (
            select(LabPanelDB)
            .where(LabPanelDB.patient_id == patient_id)
            .options(selectinload(LabPanelDB.tests))
            .order_by(LabPanelDB.collected_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_panels(self, patient_id: str, limit: int = 20) -> list[LabPanelDB]:
        stmt = (
            select(LabPanelDB)
            .where(LabPanelDB.patient_id == patient_id)
            .options(selectinload(LabPanelDB.tests))
            .order_by(LabPanelDB.collected_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_test_trend(
        self, patient_id: str, test_name: str, months: int = 12
    ) -> list[tuple[datetime, float]]:
        """Get trend of a specific lab test."""
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)
        stmt = (
            select(LabPanelDB.collected_at, LabReportDB.value)
            .join(LabReportDB, LabReportDB.panel_id == LabPanelDB.id)
            .where(
                LabPanelDB.patient_id == patient_id,
                LabPanelDB.collected_at >= cutoff,
                LabReportDB.test_name.ilike(f"%{test_name}%"),
            )
            .order_by(LabPanelDB.collected_at)
        )
        result = await self.session.execute(stmt)
        return list(result.all())


class ConditionRepository:
    """Repository for medical conditions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, condition: MedicalConditionDB) -> MedicalConditionDB:
        self.session.add(condition)
        await self.session.flush()
        return condition

    async def get_active(self, patient_id: str) -> list[MedicalConditionDB]:
        stmt = (
            select(MedicalConditionDB)
            .where(
                MedicalConditionDB.patient_id == patient_id,
                MedicalConditionDB.status == "active"
            )
            .order_by(MedicalConditionDB.diagnosed_date.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all(self, patient_id: str) -> list[MedicalConditionDB]:
        stmt = (
            select(MedicalConditionDB)
            .where(MedicalConditionDB.patient_id == patient_id)
            .order_by(MedicalConditionDB.diagnosed_date.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search(self, patient_id: str, query: str) -> list[MedicalConditionDB]:
        stmt = (
            select(MedicalConditionDB)
            .where(
                MedicalConditionDB.patient_id == patient_id,
                MedicalConditionDB.name.ilike(f"%{query}%")
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


# ============================================================================
# Database Initialization
# ============================================================================

async def init_db() -> None:
    """Initialize database tables."""
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Drop all tables (use with caution!)."""
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ============================================================================
# Utility Functions
# ============================================================================

def patient_to_dict(patient: PatientDB) -> dict[str, Any]:
    """Convert PatientDB to dictionary."""
    return {
        "id": patient.id,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
        "gender": patient.gender,
        "blood_type": patient.blood_type,
        "ethnicity": patient.ethnicity,
        "preferred_language": patient.preferred_language,
        "phone": patient.phone,
        "email": patient.email,
        "address": patient.address,
        "emergency_contact_name": patient.emergency_contact_name,
        "emergency_contact_phone": patient.emergency_contact_phone,
        "created_at": patient.created_at.isoformat() if patient.created_at else None,
        "updated_at": patient.updated_at.isoformat() if patient.updated_at else None,
    }


def dict_to_patient(data: dict[str, Any]) -> PatientDB:
    """Convert dictionary to PatientDB."""
    data = data.copy()
    if "date_of_birth" in data and isinstance(data["date_of_birth"], str):
        data["date_of_birth"] = datetime.fromisoformat(data["date_of_birth"])
    return PatientDB(**data)


# ============================================================================
# Export
# ============================================================================

__all__ = [
    # Database
    "Base", "get_async_engine", "get_sync_engine", "get_session",
    "init_db", "drop_db",
    # Models
    "PatientDB", "VitalsDB", "MedicalConditionDB", "AllergyDB",
    "MedicationDB", "LabPanelDB", "LabReportDB", "LifestyleDB",
    "FamilyHistoryDB", "DigitalTwinDB",
    # Repositories
    "PatientRepository", "VitalsRepository", "MedicationRepository",
    "LabRepository", "ConditionRepository",
    # Utilities
    "patient_to_dict", "dict_to_patient",
]