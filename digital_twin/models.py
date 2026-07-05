"""
Digital Twin Pydantic Models for Patient Data
Comprehensive clinical data models with validation.
"""
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class Gender(str, Enum):
    """Patient gender."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class BloodType(str, Enum):
    """ABO blood type with Rh factor."""
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"
    UNKNOWN = "unknown"


class ActivityLevel(str, Enum):
    """Physical activity level."""
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class SmokingStatus(str, Enum):
    """Smoking status."""
    NEVER = "never"
    FORMER = "former"
    CURRENT = "current"
    UNKNOWN = "unknown"


class AlcoholConsumption(str, Enum):
    """Alcohol consumption level."""
    NONE = "none"
    OCCASIONAL = "occasional"
    MODERATE = "moderate"
    HEAVY = "heavy"
    UNKNOWN = "unknown"


class MedicationFrequency(str, Enum):
    """Medication dosing frequency."""
    ONCE_DAILY = "once_daily"
    TWICE_DAILY = "twice_daily"
    THREE_TIMES_DAILY = "three_times_daily"
    FOUR_TIMES_DAILY = "four_times_daily"
    EVERY_12_HOURS = "every_12_hours"
    EVERY_8_HOURS = "every_8_hours"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    AS_NEEDED = "as_needed"
    CUSTOM = "custom"


class MedicationRoute(str, Enum):
    """Medication administration route."""
    ORAL = "oral"
    SUBCUTANEOUS = "subcutaneous"
    INTRAVENOUS = "intravenous"
    INTRAMUSCULAR = "intramuscular"
    TOPICAL = "topical"
    INHALATION = "inhalation"
    SUBLINGUAL = "sublingual"
    TRANSDERMAL = "transdermal"
    RECTAL = "rectal"
    OTHER = "other"


class LabTestCategory(str, Enum):
    """Categories of lab tests."""
    CHEMISTRY = "chemistry"
    HEMATOLOGY = "hematology"
    LIPID_PANEL = "lipid_panel"
    DIABETES = "diabetes"
    CARDIAC = "cardiac"
    LIVER = "liver"
    KIDNEY = "kidney"
    THYROID = "thyroid"
    INFLAMMATION = "inflammation"
    COAGULATION = "coagulation"
    URINALYSIS = "urinalysis"
    OTHER = "other"


class Severity(str, Enum):
    """Clinical severity levels."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class AdherenceLevel(str, Enum):
    """Medication adherence levels."""
    EXCELLENT = "excellent"  # >95%
    GOOD = "good"  # 80-95%
    FAIR = "fair"  # 60-80%
    POOR = "poor"  # <60%
    UNKNOWN = "unknown"


# ============================================================================
# Core Data Models
# ============================================================================

class Demographics(BaseModel):
    """Patient demographic information."""
    patient_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: Gender
    blood_type: BloodType = BloodType.UNKNOWN
    ethnicity: Optional[str] = Field(None, max_length=100)
    preferred_language: str = "en"
    phone: Optional[str] = Field(None, pattern=r"^\+?[\d\s\-\(\)]{10,}$")
    email: Optional[str] = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @property
    def age(self) -> int:
        """Calculate current age."""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def full_name(self) -> str:
        """Full name for display."""
        return f"{self.first_name} {self.last_name}"


class Vitals(BaseModel):
    """Patient vital signs with clinical ranges."""
    # Cardiovascular
    systolic_bp: Optional[float] = Field(None, ge=50, le=300, description="Systolic BP mmHg")
    diastolic_bp: Optional[float] = Field(None, ge=30, le=200, description="Diastolic BP mmHg")
    heart_rate: Optional[float] = Field(None, ge=30, le=250, description="Heart rate bpm")

    # Respiratory
    respiratory_rate: Optional[float] = Field(None, ge=5, le=60, description="Respiratory rate/min")
    oxygen_saturation: Optional[float] = Field(None, ge=50, le=100, description="SpO2 %")

    # Temperature
    temperature_c: Optional[float] = Field(None, ge=30, le=45, description="Temperature Celsius")
    temperature_f: Optional[float] = Field(None, ge=86, le=113, description="Temperature Fahrenheit")

    # Anthropometric
    height_cm: Optional[float] = Field(None, ge=30, le=250, description="Height in cm")
    weight_kg: Optional[float] = Field(None, ge=1, le=300, description="Weight in kg")
    bmi: Optional[float] = Field(None, ge=10, le=70, description="Body Mass Index")
    waist_circumference_cm: Optional[float] = Field(None, ge=30, le=200, description="Waist circumference cm")

    # Metadata
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    measured_by: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def compute_bmi(self) -> "Vitals":
        """Auto-compute BMI if height and weight available."""
        if self.height_cm and self.weight_kg and not self.bmi:
            height_m = self.height_cm / 100
            self.bmi = round(self.weight_kg / (height_m ** 2), 1)
        return self

    @model_validator(mode="after")
    def sync_temperature(self) -> "Vitals":
        """Sync Celsius and Fahrenheit."""
        if self.temperature_c and not self.temperature_f:
            self.temperature_f = round(self.temperature_c * 9/5 + 32, 1)
        elif self.temperature_f and not self.temperature_c:
            self.temperature_c = round((self.temperature_f - 32) * 5/9, 1)
        return self

    @property
    def bp_category(self) -> Optional[str]:
        """Categorize blood pressure per ACC/AHA guidelines."""
        if self.systolic_bp is None or self.diastolic_bp is None:
            return None
        if self.systolic_bp < 120 and self.diastolic_bp < 80:
            return "normal"
        elif 120 <= self.systolic_bp < 130 and self.diastolic_bp < 80:
            return "elevated"
        elif 130 <= self.systolic_bp < 140 or 80 <= self.diastolic_bp < 90:
            return "stage_1_hypertension"
        elif self.systolic_bp >= 140 or self.diastolic_bp >= 90:
            return "stage_2_hypertension"
        return None


class MedicalCondition(BaseModel):
    """Individual medical condition/diagnosis."""
    condition_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str = Field(..., min_length=1, max_length=200)
    icd10_code: Optional[str] = Field(None, pattern=r"^[A-Z]\d{2}(\.\d+)?$")
    diagnosed_date: Optional[date] = None
    severity: Severity = Severity.MILD
    status: str = "active"  # active, resolved, chronic, in_remission
    treating_physician: Optional[str] = None
    notes: Optional[str] = None
    is_primary: bool = False


class Allergy(BaseModel):
    """Patient allergy/adverse reaction."""
    allergy_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    allergen: str = Field(..., min_length=1, max_length=200)
    allergen_type: str = "drug"  # drug, food, environmental, latex, other
    reaction: str = Field(..., min_length=1, max_length=500)
    severity: Severity = Severity.MILD
    onset_date: Optional[date] = None
    verified: bool = False
    notes: Optional[str] = None


class FamilyHistoryEntry(BaseModel):
    """Family medical history entry."""
    relation: str = Field(..., description="e.g., mother, father, sibling, maternal_grandmother")
    condition: str = Field(..., min_length=1, max_length=200)
    icd10_code: Optional[str] = None
    age_at_diagnosis: Optional[int] = Field(None, ge=0, le=120)
    deceased: bool = False
    age_at_death: Optional[int] = Field(None, ge=0, le=120)
    notes: Optional[str] = None


class FamilyHistory(BaseModel):
    """Complete family history."""
    entries: list[FamilyHistoryEntry] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def get_conditions_for_relation(self, relation: str) -> list[str]:
        """Get all conditions for a specific relation."""
        return [e.condition for e in self.entries if e.relation.lower() == relation.lower()]

    def has_condition(self, condition: str) -> bool:
        """Check if any family member has a condition (case-insensitive)."""
        condition_lower = condition.lower()
        return any(condition_lower in e.condition.lower() for e in self.entries)


class Lifestyle(BaseModel):
    """Patient lifestyle factors."""
    # Physical activity
    activity_level: ActivityLevel = ActivityLevel.SEDENTARY
    exercise_minutes_per_week: int = Field(default=0, ge=0)
    exercise_types: list[str] = Field(default_factory=list)

    # Diet
    diet_type: Optional[str] = None  # mediterranean, keto, vegan, etc.
    daily_calories: Optional[int] = Field(None, ge=500, le=5000)
    fruit_servings_per_day: int = Field(default=0, ge=0)
    vegetable_servings_per_day: int = Field(default=0, ge=0)
    sodium_intake_mg: Optional[int] = Field(None, ge=0, le=10000)
    sugar_intake_g: Optional[int] = Field(None, ge=0, le=500)

    # Substance use
    smoking_status: SmokingStatus = SmokingStatus.NEVER
    pack_years: float = Field(default=0, ge=0)
    cigarettes_per_day: int = Field(default=0, ge=0)
    quit_date: Optional[date] = None

    alcohol_consumption: AlcoholConsumption = AlcoholConsumption.NONE
    drinks_per_week: int = Field(default=0, ge=0)

    substance_use: list[str] = Field(default_factory=list)

    # Sleep
    sleep_hours_per_night: Optional[float] = Field(None, ge=0, le=16)
    sleep_quality: Optional[str] = None  # poor, fair, good, excellent
    sleep_apnea: bool = False

    # Stress & Mental Health
    stress_level: Optional[str] = None  # low, moderate, high
    phq9_score: Optional[int] = Field(None, ge=0, le=27)
    gad7_score: Optional[int] = Field(None, ge=0, le=21)

    # Social
    occupation: Optional[str] = None
    work_hours_per_week: Optional[int] = Field(None, ge=0, le=120)
    shift_work: bool = False
    lives_alone: bool = False
    caregiver_support: bool = False

    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Medication(BaseModel):
    """Patient medication."""
    medication_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str = Field(..., min_length=1, max_length=200)
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    strength: str = Field(..., description="e.g., '10 mg', '500 mg/5 mL'")
    route: MedicationRoute = MedicationRoute.ORAL
    frequency: MedicationFrequency = MedicationFrequency.ONCE_DAILY
    custom_frequency: Optional[str] = None
    dose_amount: Optional[float] = None
    dose_unit: Optional[str] = None

    # Prescribing info
    prescribing_physician: Optional[str] = None
    prescription_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True
    is_prn: bool = False  # As needed

    # Indication & Monitoring
    indication: Optional[str] = None
    target_condition: Optional[str] = None
    monitoring_parameters: list[str] = Field(default_factory=list)

    # Adherence
    adherence: AdherenceLevel = AdherenceLevel.UNKNOWN
    missed_doses_last_month: int = Field(default=0, ge=0)
    last_refill_date: Optional[date] = None
    days_supply: Optional[int] = Field(None, ge=0)

    # Safety
    allergies_checked: bool = False
    interactions_checked: bool = False
    renal_adjustment: bool = False
    hepatic_adjustment: bool = False

    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_chronic(self) -> bool:
        """Determine if medication is for chronic condition."""
        chronic_indications = [
            "hypertension", "diabetes", "hyperlipidemia", "heart failure",
            "atrial fibrillation", "coronary artery disease", "asthma",
            "copd", "depression", "anxiety", "thyroid", "osteoporosis"
        ]
        if self.indication:
            return any(ci in self.indication.lower() for ci in chronic_indications)
        return False


class LabReport(BaseModel):
    """Individual lab test result."""
    lab_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    test_name: str = Field(..., min_length=1, max_length=200)
    test_code: Optional[str] = None  # LOINC code
    category: LabTestCategory = LabTestCategory.OTHER
    value: float
    unit: str = Field(..., min_length=1, max_length=50)
    reference_range_low: Optional[float] = None
    reference_range_high: Optional[float] = None
    reference_range_text: Optional[str] = None

    # Interpretation
    flag: Optional[str] = None  # L, H, LL, HH, A (abnormal), N (normal)
    interpretation: Optional[str] = None  # low, high, normal, critical

    # Metadata
    collected_at: datetime
    resulted_at: Optional[datetime] = None
    ordering_provider: Optional[str] = None
    performing_lab: Optional[str] = None
    status: str = "final"  # preliminary, final, amended, cancelled
    notes: Optional[str] = None

    @property
    def is_abnormal(self) -> bool:
        """Check if result is outside reference range."""
        if self.flag and self.flag in ("L", "H", "LL", "HH", "A"):
            return True
        if self.reference_range_low is not None and self.value < self.reference_range_low:
            return True
        if self.reference_range_high is not None and self.value > self.reference_range_high:
            return True
        return False

    @property
    def is_critical(self) -> bool:
        """Check if result is critically abnormal."""
        return self.flag in ("LL", "HH") if self.flag else False


class LabPanel(BaseModel):
    """Collection of lab tests from a single draw."""
    panel_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    panel_name: str = Field(..., min_length=1, max_length=200)
    tests: list[LabReport] = Field(default_factory=list)
    collected_at: datetime
    resulted_at: Optional[datetime] = None
    ordering_provider: Optional[str] = None
    status: str = "final"

    def get_test(self, test_name: str) -> Optional[LabReport]:
        """Get a specific test by name (case-insensitive)."""
        test_lower = test_name.lower()
        for test in self.tests:
            if test_lower in test.test_name.lower():
                return test
        return None

    def get_abnormal_tests(self) -> list[LabReport]:
        """Get all abnormal tests in panel."""
        return [t for t in self.tests if t.is_abnormal]


class MedicalHistory(BaseModel):
    """Complete medical history."""
    conditions: list[MedicalCondition] = Field(default_factory=list)
    allergies: list[Allergy] = Field(default_factory=list)
    surgeries: list[dict] = Field(default_factory=list)  # {name, date, surgeon, complications}
    hospitalizations: list[dict] = Field(default_factory=list)  # {reason, date, duration, discharge_summary}
    procedures: list[dict] = Field(default_factory=list)  # {name, date, indication, findings}
    immunizations: list[dict] = Field(default_factory=list)  # {vaccine, date, lot, site}
    social_history: dict = Field(default_factory=dict)

    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def get_active_conditions(self) -> list[MedicalCondition]:
        """Get all active conditions."""
        return [c for c in self.conditions if c.status == "active"]

    def get_chronic_conditions(self) -> list[MedicalCondition]:
        """Get chronic conditions."""
        return [c for c in self.conditions if c.status == "chronic"]

    def has_condition(self, condition_name: str) -> bool:
        """Check if patient has a condition (case-insensitive)."""
        name_lower = condition_name.lower()
        return any(name_lower in c.name.lower() for c in self.conditions)

    def get_allergies_by_type(self, allergen_type: str) -> list[Allergy]:
        """Get allergies filtered by type."""
        return [a for a in self.allergies if a.allergen_type.lower() == allergen_type.lower()]


# ============================================================================
# Main Digital Twin Model
# ============================================================================

class PatientDigitalTwin(BaseModel):
    """
    Complete Patient Digital Twin with all clinical data.
    This is the central model that aggregates all patient information.
    """
    # Identity
    patient_id: str = Field(default_factory=lambda: f"DT-{uuid4().hex[:12].upper()}")
    demographics: Demographics

    # Clinical Data
    vitals: Vitals = Field(default_factory=Vitals)
    medical_history: MedicalHistory = Field(default_factory=MedicalHistory)
    lifestyle: Lifestyle = Field(default_factory=Lifestyle)
    medications: list[Medication] = Field(default_factory=list)
    lab_reports: list[LabPanel] = Field(default_factory=list)
    family_history: FamilyHistory = Field(default_factory=FamilyHistory)

    # System Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1
    data_source: str = "manual"  # manual, ehr_import, device, patient_reported
    data_quality_score: float = Field(default=1.0, ge=0, le=1)

    # Consent & Privacy
    consent_for_ai: bool = True
    consent_for_research: bool = False
    phi_masking_enabled: bool = True

    # -------------------------------------------------------------------------
    # Computed Properties
    # -------------------------------------------------------------------------

    @property
    def age(self) -> int:
        return self.demographics.age

    @property
    def bmi(self) -> Optional[float]:
        return self.vitals.bmi

    @property
    def active_medications(self) -> list[Medication]:
        return [m for m in self.medications if m.is_active]

    @property
    def chronic_medications(self) -> list[Medication]:
        return [m for m in self.active_medications if m.is_chronic]

    @property
    def active_conditions(self) -> list[MedicalCondition]:
        return self.medical_history.get_active_conditions()

    @property
    def drug_allergies(self) -> list[Allergy]:
        return self.medical_history.get_allergies_by_type("drug")

    @property
    def latest_vitals(self) -> Vitals:
        return self.vitals

    @property
    def latest_labs(self) -> Optional[LabPanel]:
        if not self.lab_reports:
            return None
        return max(self.lab_reports, key=lambda p: p.collected_at)

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def get_lab_value(self, test_name: str) -> Optional[float]:
        """Get most recent value for a lab test."""
        panel = self.latest_labs
        if not panel:
            return None
        test = panel.get_test(test_name)
        return test.value if test else None

    def get_lab_trend(self, test_name: str, months: int = 12) -> list[tuple[datetime, float]]:
        """Get trend of a lab test over time."""
        cutoff = datetime.now(timezone.utc)
        # Simplified - in production would use dateutil.relativedelta
        results = []
        for panel in sorted(self.lab_reports, key=lambda p: p.collected_at):
            test = panel.get_test(test_name)
            if test:
                results.append((panel.collected_at, test.value))
        return results

    def get_medication_names(self) -> list[str]:
        """Get list of active medication names (generic preferred)."""
        return [
            m.generic_name or m.name
            for m in self.active_medications
        ]

    def get_conditions_summary(self) -> list[str]:
        """Get summary of active conditions."""
        return [c.name for c in self.active_conditions]

    def to_summary_dict(self) -> dict[str, Any]:
        """Convert to summary dictionary for LLM context."""
        return {
            "patient_id": self.patient_id,
            "age": self.age,
            "gender": self.demographics.gender.value,
            "bmi": self.bmi,
            "blood_type": self.demographics.blood_type.value,
            "active_conditions": self.get_conditions_summary(),
            "active_medications": self.get_medication_names(),
            "allergies": [a.allergen for a in self.drug_allergies],
            "family_history": [
                {"relation": e.relation, "condition": e.condition}
                for e in self.family_history.entries
            ],
            "lifestyle": {
                "activity_level": self.lifestyle.activity_level.value,
                "smoking": self.lifestyle.smoking_status.value,
                "alcohol": self.lifestyle.alcohol_consumption.value,
            },
            "latest_vitals": {
                "bp": f"{self.vitals.systolic_bp}/{self.vitals.diastolic_bp}" if self.vitals.systolic_bp else None,
                "hr": self.vitals.heart_rate,
                "spo2": self.vitals.oxygen_saturation,
                "bmi": self.bmi,
            },
            "latest_labs": {
                test.test_name: f"{test.value} {test.unit}"
                for test in (self.latest_labs.tests if self.latest_labs else [])
            } if self.latest_labs else {},
        }

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization hook."""
        self.updated_at = datetime.now(timezone.utc)


# ============================================================================
# Specialized Models for Specific Use Cases
# ============================================================================

class CardiovascularRiskFactors(BaseModel):
    """Extracted cardiovascular risk factors for risk calculators."""
    age: int
    gender: Gender
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    total_cholesterol: Optional[float] = None
    hdl_cholesterol: Optional[float] = None
    ldl_cholesterol: Optional[float] = None
    triglycerides: Optional[float] = None
    has_diabetes: bool = False
    smoker: bool = False
    on_bp_treatment: bool = False
    family_history_premature_cvd: bool = False

    @classmethod
    def from_digital_twin(cls, twin: PatientDigitalTwin) -> "CardiovascularRiskFactors":
        """Extract risk factors from Digital Twin."""
        latest_labs = twin.latest_labs

        def get_lab(name: str) -> Optional[float]:
            if latest_labs:
                test = latest_labs.get_test(name)
                return test.value if test else None
            return None

        # Check for diabetes
        has_dm = twin.medical_history.has_condition("diabetes")
        if not has_dm:
            # Check HbA1c
            hba1c = get_lab("hba1c") or get_lab("hemoglobin a1c") or get_lab("a1c")
            if hba1c and hba1c >= 6.5:
                has_dm = True

        # Check smoking
        smoker = twin.lifestyle.smoking_status in (SmokingStatus.CURRENT, SmokingStatus.FORMER)

        # Check BP treatment
        on_bp_tx = any(
            "hypertension" in (m.indication or "").lower()
            for m in twin.active_medications
        )

        # Family history
        fh_cvd = twin.family_history.has_condition("coronary") or \
                 twin.family_history.has_condition("heart") or \
                 twin.family_history.has_condition("stroke") or \
                 twin.family_history.has_condition("cardiovascular")

        return cls(
            age=twin.age,
            gender=twin.demographics.gender,
            systolic_bp=twin.vitals.systolic_bp,
            diastolic_bp=twin.vitals.diastolic_bp,
            total_cholesterol=get_lab("total cholesterol") or get_lab("cholesterol"),
            hdl_cholesterol=get_lab("hdl") or get_lab("hdl cholesterol"),
            ldl_cholesterol=get_lab("ldl") or get_lab("ldl cholesterol"),
            triglycerides=get_lab("triglycerides"),
            has_diabetes=has_dm,
            smoker=smoker,
            on_bp_treatment=on_bp_tx,
            family_history_premature_cvd=fh_cvd,
        )


class DiabetesRiskFactors(BaseModel):
    """Extracted diabetes risk factors."""
    age: int
    gender: Gender
    bmi: Optional[float] = None
    fasting_glucose: Optional[float] = None
    hba1c: Optional[float] = None
    systolic_bp: Optional[float] = None
    hdl_cholesterol: Optional[float] = None
    triglycerides: Optional[float] = None
    family_history_diabetes: bool = False
    gestational_diabetes: bool = False
    pcos: bool = False
    activity_level: ActivityLevel = ActivityLevel.SEDENTARY

    @classmethod
    def from_digital_twin(cls, twin: PatientDigitalTwin) -> "DiabetesRiskFactors":
        latest_labs = twin.latest_labs

        def get_lab(name: str) -> Optional[float]:
            if latest_labs:
                test = latest_labs.get_test(name)
                return test.value if test else None
            return None

        return cls(
            age=twin.age,
            gender=twin.demographics.gender,
            bmi=twin.bmi,
            fasting_glucose=get_lab("glucose") or get_lab("fasting glucose"),
            hba1c=get_lab("hba1c") or get_lab("hemoglobin a1c") or get_lab("a1c"),
            systolic_bp=twin.vitals.systolic_bp,
            hdl_cholesterol=get_lab("hdl") or get_lab("hdl cholesterol"),
            triglycerides=get_lab("triglycerides"),
            family_history_diabetes=twin.family_history.has_condition("diabetes"),
            activity_level=twin.lifestyle.activity_level,
        )


# ============================================================================
# Export
# ============================================================================

__all__ = [
    # Enums
    "Gender", "BloodType", "ActivityLevel", "SmokingStatus", "AlcoholConsumption",
    "MedicationFrequency", "MedicationRoute", "LabTestCategory", "Severity", "AdherenceLevel",
    # Core Models
    "Demographics", "Vitals", "MedicalCondition", "Allergy", "FamilyHistoryEntry",
    "FamilyHistory", "Lifestyle", "Medication", "LabReport", "LabPanel", "MedicalHistory",
    # Main Model
    "PatientDigitalTwin",
    # Specialized
    "CardiovascularRiskFactors", "DiabetesRiskFactors",
]