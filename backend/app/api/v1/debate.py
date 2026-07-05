"""
Debate API endpoints — wired to the real DebateEngine.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.debate import Debate
from app.schemas.debate import DebateRequest, DebateResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_twin_from_patient(patient: Patient):
    """
    Build a PatientDigitalTwin from the DB Patient model and its loaded relationships.
    """
    import re
    from collections import defaultdict
    from datetime import date
    from digital_twin.models import (
        PatientDigitalTwin, Demographics, Vitals,
        Gender, BloodType, Lifestyle, MedicalHistory, FamilyHistory,
        MedicalCondition, Allergy as TwinAllergy, Severity,
        Medication as TwinMedication, MedicationRoute, MedicationFrequency,
        LabPanel, LabReport as TwinLabReport, LabTestCategory
    )

    dob = patient.date_of_birth if patient.date_of_birth else date(1970, 1, 1)

    try:
        gender = Gender(patient.gender.lower() if patient.gender else "other")
    except ValueError:
        gender = Gender.OTHER

    try:
        blood_type = BloodType(patient.blood_type)
    except ValueError:
        blood_type = BloodType.UNKNOWN

    # Validate phone and email formats to prevent Pydantic validation failures
    email_val = patient.email if patient.email and re.match(r"^[^@]+@[^@]+\.[^@]+$", patient.email) else None
    phone_val = patient.phone if patient.phone and re.match(r"^\+?[\d\s\-\(\)]{10,}$", patient.phone) else None

    demographics = Demographics(
        patient_id=str(patient.id),
        first_name=patient.first_name or "Unknown",
        last_name=patient.last_name or "Patient",
        date_of_birth=dob,
        gender=gender,
        blood_type=blood_type,
        ethnicity=patient.ethnicity,
        preferred_language=patient.preferred_language or "en",
        phone=phone_val,
        email=email_val,
        address=patient.address,
    )

    # 1. Map Vitals (latest record, as patient.vitals is sorted by measured_at.desc())
    latest_v = patient.vitals[0] if getattr(patient, "vitals", None) else None
    vitals = Vitals(
        systolic_bp=latest_v.systolic_bp if latest_v else None,
        diastolic_bp=latest_v.diastolic_bp if latest_v else None,
        heart_rate=latest_v.heart_rate if latest_v else None,
        respiratory_rate=latest_v.respiratory_rate if latest_v else None,
        oxygen_saturation=latest_v.oxygen_saturation if latest_v else None,
        temperature_c=latest_v.temperature_c if latest_v else None,
        height_cm=latest_v.height_cm if latest_v else None,
        weight_kg=latest_v.weight_kg if latest_v else None,
    )

    # 2. Map Medical History (Conditions and Allergies)
    twin_conditions = []
    for c in getattr(patient, "conditions", []):
        try:
            sev = Severity(c.severity.lower())
        except ValueError:
            sev = Severity.MILD
        twin_conditions.append(
            MedicalCondition(
                condition_id=str(c.id),
                name=c.name,
                icd10_code=c.icd10_code,
                diagnosed_date=c.diagnosed_date,
                severity=sev,
                status=c.status,
                is_primary=c.is_primary,
            )
        )

    twin_allergies = []
    for a in getattr(patient, "allergies", []):
        try:
            sev = Severity(a.severity.lower())
        except ValueError:
            sev = Severity.MILD
        twin_allergies.append(
            TwinAllergy(
                allergy_id=str(a.id),
                allergen=a.allergen,
                allergen_type=a.allergen_type,
                reaction=a.reaction,
                severity=sev,
                verified=a.verified,
            )
        )

    medical_history = MedicalHistory(
        conditions=twin_conditions,
        allergies=twin_allergies,
    )

    # 3. Map Medications
    twin_medications = []
    for m in getattr(patient, "medications", []):
        try:
            route_val = MedicationRoute(m.route.lower())
        except ValueError:
            route_val = MedicationRoute.ORAL

        try:
            freq_val = MedicationFrequency(m.frequency.lower())
        except ValueError:
            freq_val = MedicationFrequency.ONCE_DAILY

        twin_medications.append(
            TwinMedication(
                medication_id=str(m.id),
                name=m.name,
                generic_name=m.generic_name,
                strength=m.strength,
                route=route_val,
                frequency=freq_val,
                dose_amount=m.dose_amount,
                dose_unit=m.dose_unit,
                start_date=m.start_date,
                end_date=m.end_date,
                is_active=m.is_active,
                indication=m.indication,
            )
        )

    # 4. Map Lab Reports (Grouped into LabPanels by (panel_name, collected_at))
    panels_map = defaultdict(list)
    for l in getattr(patient, "lab_reports", []):
        panels_map[(l.panel_name, l.collected_at)].append(l)

    twin_lab_panels = []
    for (panel_name, collected_at), db_reports in panels_map.items():
        twin_reports = []
        for r in db_reports:
            cat = LabTestCategory.OTHER
            name_lower = r.test_name.lower()
            p_lower = r.panel_name.lower()
            if "cholesterol" in name_lower or "lipid" in p_lower or "ldl" in name_lower or "hdl" in name_lower or "triglyceride" in name_lower:
                cat = LabTestCategory.LIPID_PANEL
            elif "glucose" in name_lower or "hba1c" in name_lower or "a1c" in name_lower:
                cat = LabTestCategory.DIABETES
            elif "creatinine" in name_lower or "egfr" in name_lower or "urea" in name_lower or "bun" in name_lower:
                cat = LabTestCategory.KIDNEY
            elif "troponin" in name_lower or "bnp" in name_lower:
                cat = LabTestCategory.CARDIAC
            elif "sodium" in name_lower or "potassium" in name_lower or "chloride" in name_lower or "chemistry" in p_lower:
                cat = LabTestCategory.CHEMISTRY

            twin_reports.append(
                TwinLabReport(
                    lab_id=str(r.id),
                    test_name=r.test_name,
                    test_code=r.loinc_code,
                    category=cat,
                    value=r.value,
                    unit=r.unit,
                    reference_range_low=r.ref_low,
                    reference_range_high=r.ref_high,
                    flag=r.flag,
                    collected_at=r.collected_at,
                    resulted_at=r.collected_at,
                )
            )
        twin_lab_panels.append(
            LabPanel(
                panel_name=panel_name,
                tests=twin_reports,
                collected_at=collected_at,
                resulted_at=collected_at,
            )
        )

    twin = PatientDigitalTwin(
        patient_id=str(patient.id),
        demographics=demographics,
        vitals=vitals,
        medical_history=medical_history,
        lifestyle=Lifestyle(),
        medications=twin_medications,
        lab_reports=twin_lab_panels,
        family_history=FamilyHistory(),
    )
    return twin


@router.post("/run", status_code=200)
async def run_debate(
    request: DebateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger a multi-agent clinical debate for a patient.

    Steps:
    1. Load patient from DB
    2. Build PatientDigitalTwin
    3. Run ML risk prediction
    4. Run multi-agent debate
    5. Persist debate result
    6. Return full transcript + consensus report
    """
    # 1. Load patient with eager relationships
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Patient)
        .options(
            selectinload(Patient.vitals),
            selectinload(Patient.conditions),
            selectinload(Patient.allergies),
            selectinload(Patient.medications),
            selectinload(Patient.lab_reports),
        )
        .where(Patient.id == request.patient_id)
    )
    patient = result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 2. Build digital twin
    twin = _build_twin_from_patient(patient)

    # 3. Run ML risk prediction
    try:
        from ml.inference import predict_all_risks
        risk_results = predict_all_risks(twin)
    except Exception as e:
        logger.error(f"ML inference failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Risk prediction failed: {str(e)}"
        )

    # 4. Run debate engine
    try:
        from debate.engine import DebateEngine
        engine = DebateEngine()
        debate_result = engine.run(
            twin,
            risk_results,
            max_rounds=request.max_rounds or 3,
        )
    except Exception as e:
        logger.error(f"Debate engine failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Debate engine failed: {str(e)}"
        )

    # 5. Persist to DB
    try:
        debate_record = Debate(
            patient_id=str(patient.id),
            initiated_by=str(current_user.id),
            predicted_risk=debate_result["predicted_risk"],
            explanation_attributions=debate_result["explanation_attributions"],
            debate_transcript=debate_result["debate_transcript"],
            final_consensus_report=debate_result["final_consensus_report"],
        )
        db.add(debate_record)
        await db.commit()
        await db.refresh(debate_record)
        debate_result["debate_db_id"] = str(debate_record.id)
    except Exception as e:
        logger.warning(f"Failed to persist debate record: {e}")

    return debate_result


@router.get("/patient/{patient_id}", status_code=200)
async def list_patient_debates(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all debates for a patient."""
    result = await db.execute(
        select(Debate)
        .where(Debate.patient_id == patient_id)
        .order_by(Debate.created_at.desc())
    )
    debates = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "patient_id": d.patient_id,
            "predicted_risk": d.predicted_risk,
            "created_at": d.created_at.isoformat(),
            "consensus_preview": (d.final_consensus_report or "")[:200] + "...",
        }
        for d in debates
    ]
