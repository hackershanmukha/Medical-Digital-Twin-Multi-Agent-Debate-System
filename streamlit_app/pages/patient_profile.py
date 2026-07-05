"""
Patient Profile Page — Build and view the Patient Digital Twin.
"""
import streamlit as st
from datetime import date, datetime, timezone


def render():
    st.markdown("# 👤 Patient Profile")
    st.markdown("*Build a comprehensive patient digital twin*")

    twin = st.session_state.get("patient_twin")

    tab1, tab2 = st.tabs(["📝 Enter / Edit Patient", "🔍 View Digital Twin"])

    with tab1:
        _render_input_form()

    with tab2:
        if twin:
            _render_twin_view(twin)
        else:
            st.info("No patient loaded. Fill in the form or load the demo patient from the Home page.")


def _render_input_form():
    from digital_twin.models import (
        PatientDigitalTwin, Demographics, Vitals, MedicalHistory,
        MedicalCondition, Allergy, FamilyHistory, Lifestyle, Medication,
        Gender, BloodType, SmokingStatus, ActivityLevel, AlcoholConsumption,
        MedicationRoute, MedicationFrequency, Severity,
    )

    with st.form("patient_form", clear_on_submit=False):
        # ── Demographics ─────────────────────────────────────────────────
        st.markdown("### 📋 Demographics")
        c1, c2, c3 = st.columns(3)
        with c1:
            first_name = st.text_input("First Name", value="Jane")
            dob = st.date_input("Date of Birth", value=date(1965, 7, 20),
                                min_value=date(1900, 1, 1), max_value=date.today())
        with c2:
            last_name = st.text_input("Last Name", value="Doe")
            gender = st.selectbox("Gender", ["male", "female", "other"])
        with c3:
            blood_type = st.selectbox("Blood Type", [bt.value for bt in BloodType])

        # ── Vitals ───────────────────────────────────────────────────────
        st.markdown("### 💓 Vital Signs")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            sbp = st.number_input("Systolic BP (mmHg)", 80, 250, 135)
            dbp = st.number_input("Diastolic BP (mmHg)", 40, 150, 85)
        with c2:
            hr = st.number_input("Heart Rate (bpm)", 30, 220, 78)
            spo2 = st.number_input("O₂ Saturation (%)", 50, 100, 97)
        with c3:
            height = st.number_input("Height (cm)", 100, 250, 165)
            weight = st.number_input("Weight (kg)", 30, 300, 75)
        with c4:
            wc = st.number_input("Waist Circumference (cm)", 40, 200, 88)
            temp = st.number_input("Temperature (°C)", 34.0, 42.0, 36.8)

        # ── Labs ─────────────────────────────────────────────────────────
        st.markdown("### 🔬 Laboratory Results")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            glucose = st.number_input("Fasting Glucose (mg/dL)", 50, 500, 108)
            hba1c = st.number_input("HbA1c (%)", 4.0, 15.0, 6.1)
        with c2:
            total_chol = st.number_input("Total Cholesterol (mg/dL)", 80, 400, 205)
            ldl = st.number_input("LDL Cholesterol (mg/dL)", 30, 300, 120)
        with c3:
            hdl = st.number_input("HDL Cholesterol (mg/dL)", 15, 120, 45)
            trig = st.number_input("Triglycerides (mg/dL)", 30, 600, 155)
        with c4:
            egfr = st.number_input("eGFR (mL/min/1.73m²)", 5, 140, 78)
            creat = st.number_input("Creatinine (mg/dL)", 0.3, 15.0, 1.0)

        # ── Lifestyle ────────────────────────────────────────────────────
        st.markdown("### 🏃 Lifestyle")
        c1, c2, c3 = st.columns(3)
        with c1:
            activity = st.selectbox("Activity Level",
                ["sedentary", "light", "moderate", "active", "very_active"])
            smoking = st.selectbox("Smoking Status", ["never", "former", "current"])
            pack_years = st.number_input("Pack-Years", 0.0, 100.0, 0.0)
        with c2:
            alcohol = st.selectbox("Alcohol Consumption", ["none", "occasional", "moderate", "heavy"])
            sleep_h = st.number_input("Sleep Hours/Night", 2.0, 12.0, 7.0)
            stress = st.selectbox("Stress Level", ["low", "moderate", "high"])
        with c3:
            fruit_serv = st.number_input("Fruit Servings/Day", 0, 10, 2)
            veg_serv = st.number_input("Veg Servings/Day", 0, 10, 3)
            lives_alone = st.checkbox("Lives Alone")

        # ── Conditions ───────────────────────────────────────────────────
        st.markdown("### 🩺 Medical Conditions")
        conditions_text = st.text_area(
            "Active Conditions (one per line: Name|ICD10|Severity|Status)",
            value="Essential Hypertension|I10|moderate|chronic\nType 2 Diabetes|E11.9|moderate|chronic",
            height=100,
        )

        # ── Family History ────────────────────────────────────────────────
        st.markdown("### 👨‍👩‍👧 Family History")
        fh_text = st.text_area(
            "Family History (one per line: Relation|Condition)",
            value="father|Coronary Artery Disease\nmother|Type 2 Diabetes",
            height=80,
        )

        # ── Medications ──────────────────────────────────────────────────
        st.markdown("### 💊 Medications")
        meds_text = st.text_area(
            "Medications (one per line: Name|Strength|Frequency|Indication)",
            value="Metformin|1000mg|twice_daily|Type 2 Diabetes\nAmlodipine|5mg|once_daily|Hypertension",
            height=80,
        )

        submitted = st.form_submit_button("💾 Build Digital Twin", type="primary", use_container_width=True)

    if submitted:
        twin = _build_twin_from_form(
            first_name, last_name, dob, gender, blood_type,
            sbp, dbp, hr, spo2, height, weight, wc, temp,
            glucose, hba1c, total_chol, ldl, hdl, trig, egfr, creat,
            activity, smoking, pack_years, alcohol, sleep_h, stress,
            fruit_serv, veg_serv, lives_alone,
            conditions_text, fh_text, meds_text,
        )
        st.session_state.patient_twin = twin
        st.session_state.risk_results = None
        st.session_state.debate_result = None
        st.success(f"✅ Digital Twin created for {first_name} {last_name}!")
        st.balloons()


def _build_twin_from_form(
    first_name, last_name, dob, gender, blood_type,
    sbp, dbp, hr, spo2, height, weight, wc, temp,
    glucose, hba1c, total_chol, ldl, hdl, trig, egfr, creat,
    activity, smoking, pack_years, alcohol, sleep_h, stress,
    fruit_serv, veg_serv, lives_alone,
    conditions_text, fh_text, meds_text,
):
    from digital_twin.models import (
        PatientDigitalTwin, Demographics, Vitals, MedicalHistory,
        MedicalCondition, Allergy, FamilyHistory, FamilyHistoryEntry,
        Lifestyle, Medication, LabPanel, LabReport,
        Gender, BloodType, SmokingStatus, ActivityLevel, AlcoholConsumption,
        MedicationRoute, MedicationFrequency, Severity, LabTestCategory,
    )

    # Demographics
    try:
        bt = BloodType(blood_type)
    except Exception:
        bt = BloodType.UNKNOWN

    demographics = Demographics(
        first_name=first_name, last_name=last_name,
        date_of_birth=dob, gender=Gender(gender), blood_type=bt,
    )

    # Vitals
    vitals = Vitals(
        systolic_bp=float(sbp), diastolic_bp=float(dbp),
        heart_rate=float(hr), oxygen_saturation=float(spo2),
        height_cm=float(height), weight_kg=float(weight),
        waist_circumference_cm=float(wc), temperature_c=float(temp),
    )

    # Conditions
    conditions = []
    for line in conditions_text.strip().splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 1 and parts[0]:
            conditions.append(MedicalCondition(
                name=parts[0],
                icd10_code=parts[1] if len(parts) > 1 else None,
                severity=Severity(parts[2]) if len(parts) > 2 else Severity.MILD,
                status=parts[3] if len(parts) > 3 else "active",
            ))

    history = MedicalHistory(conditions=conditions)

    # Family history
    fh_entries = []
    for line in fh_text.strip().splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2:
            fh_entries.append(FamilyHistoryEntry(relation=parts[0], condition=parts[1]))
    fh = FamilyHistory(entries=fh_entries)

    # Lifestyle
    lifestyle = Lifestyle(
        activity_level=ActivityLevel(activity),
        smoking_status=SmokingStatus(smoking),
        pack_years=float(pack_years),
        alcohol_consumption=AlcoholConsumption(alcohol),
        sleep_hours_per_night=float(sleep_h),
        stress_level=stress,
        fruit_servings_per_day=int(fruit_serv),
        vegetable_servings_per_day=int(veg_serv),
        lives_alone=lives_alone,
    )

    # Medications
    meds = []
    for line in meds_text.strip().splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 1 and parts[0]:
            try:
                freq = MedicationFrequency(parts[2]) if len(parts) > 2 else MedicationFrequency.ONCE_DAILY
            except Exception:
                freq = MedicationFrequency.ONCE_DAILY
            meds.append(Medication(
                name=parts[0],
                strength=parts[1] if len(parts) > 1 else "unknown",
                frequency=freq,
                indication=parts[3] if len(parts) > 3 else None,
                is_active=True,
                start_date=date.today(),
            ))

    # Labs
    now = datetime.now(timezone.utc)
    labs = [LabPanel(
        panel_name="Recent Labs",
        collected_at=now,
        tests=[
            LabReport(test_name="Fasting Glucose", category=LabTestCategory.DIABETES,
                      value=float(glucose), unit="mg/dL",
                      reference_range_low=70.0, reference_range_high=100.0,
                      flag="H" if glucose > 100 else "N", collected_at=now),
            LabReport(test_name="HbA1c", category=LabTestCategory.DIABETES,
                      value=float(hba1c), unit="%",
                      reference_range_high=5.7,
                      flag="H" if hba1c > 5.7 else "N", collected_at=now),
            LabReport(test_name="Total Cholesterol", category=LabTestCategory.LIPID_PANEL,
                      value=float(total_chol), unit="mg/dL",
                      reference_range_high=200.0,
                      flag="H" if total_chol > 200 else "N", collected_at=now),
            LabReport(test_name="LDL Cholesterol", category=LabTestCategory.LIPID_PANEL,
                      value=float(ldl), unit="mg/dL",
                      reference_range_high=100.0,
                      flag="H" if ldl > 100 else "N", collected_at=now),
            LabReport(test_name="HDL Cholesterol", category=LabTestCategory.LIPID_PANEL,
                      value=float(hdl), unit="mg/dL",
                      reference_range_low=40.0,
                      flag="L" if hdl < 40 else "N", collected_at=now),
            LabReport(test_name="Triglycerides", category=LabTestCategory.LIPID_PANEL,
                      value=float(trig), unit="mg/dL",
                      reference_range_high=150.0,
                      flag="H" if trig > 150 else "N", collected_at=now),
            LabReport(test_name="eGFR", category=LabTestCategory.KIDNEY,
                      value=float(egfr), unit="mL/min/1.73m²",
                      reference_range_low=60.0,
                      flag="L" if egfr < 60 else "N", collected_at=now),
            LabReport(test_name="Creatinine", category=LabTestCategory.KIDNEY,
                      value=float(creat), unit="mg/dL",
                      reference_range_high=1.2,
                      flag="H" if creat > 1.2 else "N", collected_at=now),
        ],
    )]

    return PatientDigitalTwin(
        demographics=demographics, vitals=vitals, medical_history=history,
        family_history=fh, lifestyle=lifestyle, medications=meds, lab_reports=labs,
    )


def _render_twin_view(twin):
    """Display the patient digital twin in a structured view."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e3a5f, #0d2137);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        color: white;
        margin-bottom: 1.5rem;
    ">
        <h2 style="margin:0; color:#7dd3fc;">
            {twin.demographics.full_name}
        </h2>
        <p style="color:#94a3b8; margin:0.25rem 0 0;">
            {twin.age} y/o · {twin.demographics.gender.value.title()} · 
            Blood type: {twin.demographics.blood_type.value} · 
            BMI: {f"{twin.bmi:.1f}" if twin.bmi else 'N/A'} kg/m²
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 💓 Vital Signs")
        v = twin.vitals
        data = {
            "Blood Pressure": f"{v.systolic_bp}/{v.diastolic_bp} mmHg" if v.systolic_bp else "N/A",
            "Heart Rate": f"{v.heart_rate:.0f} bpm" if v.heart_rate else "N/A",
            "SpO₂": f"{v.oxygen_saturation:.0f}%" if v.oxygen_saturation else "N/A",
            "BMI": f"{twin.bmi:.1f} kg/m²" if twin.bmi else "N/A",
            "Weight": f"{v.weight_kg:.1f} kg" if v.weight_kg else "N/A",
            "Waist": f"{v.waist_circumference_cm:.0f} cm" if v.waist_circumference_cm else "N/A",
        }
        for k, val in data.items():
            st.markdown(f"**{k}:** {val}")

        st.markdown("#### 🩺 Active Conditions")
        for cond in twin.active_conditions or [{"name": "None recorded"}]:
            if isinstance(cond, str):
                st.markdown(f"- {cond}")
            else:
                status_color = {"active": "🔴", "chronic": "🟡", "resolved": "🟢"}.get(cond.status, "⚪")
                st.markdown(f"- {status_color} **{cond.name}** ({cond.status})")

    with col2:
        st.markdown("#### 🔬 Latest Labs")
        if twin.latest_labs:
            for test in twin.latest_labs.tests[:6]:
                flag_icon = {"H": "🔺", "L": "🔻", "HH": "🚨", "LL": "🚨", "N": "✅"}.get(test.flag, "⚪")
                st.markdown(
                    f"- {flag_icon} **{test.test_name}:** {test.value} {test.unit}"
                )

        st.markdown("#### 💊 Current Medications")
        for med in twin.active_medications[:5] or []:
            st.markdown(f"- **{med.name}** {med.strength} — {med.frequency.value.replace('_', ' ')}")

        st.markdown("#### 🏃 Lifestyle")
        ls = twin.lifestyle
        st.markdown(f"- **Activity:** {ls.activity_level.value}")
        st.markdown(f"- **Smoking:** {ls.smoking_status.value}")
        st.markdown(f"- **Alcohol:** {ls.alcohol_consumption.value}")
        st.markdown(f"- **Sleep:** {ls.sleep_hours_per_night}h/night")

    # Next step button
    st.divider()
    if st.button("📊 Proceed to Risk Analysis →", type="primary", use_container_width=True):
        st.session_state.page = "risk"
        st.rerun()
