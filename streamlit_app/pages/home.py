"""
Home page — Project overview and quick-start.
"""
import streamlit as st


def render():
    # Hero section
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        border-radius: 20px;
        padding: 3rem 2.5rem;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(102,126,234,0.3);
    ">
        <h1 style="color:white; font-size:2.8rem; font-weight:700; margin:0;">
            🧬 MedTwin AI
        </h1>
        <p style="color:rgba(255,255,255,0.9); font-size:1.2rem; margin-top:0.75rem;">
            Multi-Agent Clinical Decision Support System
        </p>
        <p style="color:rgba(255,255,255,0.75); font-size:0.95rem; max-width:600px; margin:1rem auto 0;">
            Combining XGBoost risk prediction with a multi-specialist AI debate to 
            generate evidence-based clinical recommendations for your patients.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    cols = st.columns(3)
    features = [
        ("📊", "ML Risk Prediction", "XGBoost models trained on clinically-validated synthetic data. Cardiovascular, diabetes, and composite risk scoring with SHAP explanations.", "#667eea"),
        ("🗣️", "Multi-Agent Debate", "3 AI specialist agents (Cardiologist, Endocrinologist, GP) powered by Gemini 2.5 Pro debate risk factors over 3 structured rounds.", "#764ba2"),
        ("📋", "MDT Consensus", "AI Moderator synthesises debate transcript into a prioritised clinical action plan with monitoring protocols.", "#f093fb"),
    ]

    for col, (icon, title, desc, color) in zip(cols, features):
        with col:
            st.markdown(f"""
            <div style="
                background: white;
                border-radius: 16px;
                padding: 1.75rem;
                height: 100%;
                box-shadow: 0 4px 20px rgba(0,0,0,0.06);
                border-top: 4px solid {color};
                text-align: center;
            ">
                <div style="font-size:2.5rem;">{icon}</div>
                <h3 style="color:#1e293b; margin:0.5rem 0;">{title}</h3>
                <p style="color:#64748b; font-size:0.9rem; line-height:1.6;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # System architecture
    st.markdown("## 🏗️ System Architecture")
    st.markdown("""
    ```
    ┌─────────────────────────────────────────────────────────────────┐
    │                        MedTwin AI Pipeline                      │
    │                                                                 │
    │  1. Patient Digital Twin  →  2. ML Risk Engine  →  3. Agents   │
    │     (Demographics,            (XGBoost CVD,          (Gemini   │
    │      Vitals, Meds,             Diabetes, Risk)        Powered)  │
    │      Labs, History)            + SHAP Explanations             │
    │                                       ↓                         │
    │                          4. Multi-Agent Debate                  │
    │                    ❤️ Cardiologist ←→ 🧬 Endocrinologist        │
    │                              ↕             ↕                    │
    │                         👨‍⚕️ General Practitioner                │
    │                                       ↓                         │
    │                     5. ⚖️ Moderator Consensus                   │
    │                    (MDT Report + Priority Actions)              │
    └─────────────────────────────────────────────────────────────────┘
    ```
    """)

    # Quick start
    st.markdown("## 🚀 Quick Start")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(
            "**Step 1:** Enter patient data in the **👤 Patient Profile** page  \n"
            "**Step 2:** Review ML risk scores in **📊 Risk Analysis**  \n"
            "**Step 3:** Launch the AI debate in **🗣️ Clinical Debate**  \n"
            "**Step 4:** View the MDT consensus in **📋 Consensus Report**"
        )
    with col2:
        if st.button("▶️ Load Demo Patient", use_container_width=True, type="primary"):
            _load_demo_patient()
            st.session_state.page = "patient"
            st.rerun()

    # Stats
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("ML Models", "3", "Heart, Diabetes, Composite")
    with c2:
        st.metric("AI Specialists", "4", "3 agents + moderator")
    with c3:
        st.metric("Debate Rounds", "3", "Open → Rebut → Close")
    with c4:
        st.metric("Powered by", "Gemini 2.5", "Google AI")


def _load_demo_patient():
    """Load a demo patient into session state."""
    from datetime import date
    from digital_twin.models import (
        PatientDigitalTwin, Demographics, Vitals, MedicalHistory,
        MedicalCondition, Allergy, FamilyHistory, FamilyHistoryEntry,
        Lifestyle, Medication, LabPanel, LabReport,
        Gender, BloodType, SmokingStatus, ActivityLevel,
        AlcoholConsumption, MedicationRoute, MedicationFrequency,
        LabTestCategory, Severity,
    )
    from datetime import datetime, timezone

    demographics = Demographics(
        first_name="Robert",
        last_name="Johnson",
        date_of_birth=date(1962, 3, 15),
        gender=Gender.MALE,
        blood_type=BloodType.O_POS,
    )

    vitals = Vitals(
        systolic_bp=148.0,
        diastolic_bp=92.0,
        heart_rate=82.0,
        height_cm=176.0,
        weight_kg=94.0,
        waist_circumference_cm=102.0,
        oxygen_saturation=97.0,
    )

    conditions = [
        MedicalCondition(name="Type 2 Diabetes Mellitus", icd10_code="E11.9",
                         severity=Severity.MODERATE, status="chronic", is_primary=True),
        MedicalCondition(name="Essential Hypertension", icd10_code="I10",
                         severity=Severity.MODERATE, status="chronic"),
        MedicalCondition(name="Hyperlipidaemia", icd10_code="E78.5",
                         severity=Severity.MILD, status="active"),
    ]

    allergies = [
        Allergy(allergen="Penicillin", allergen_type="drug",
                reaction="Urticaria", severity=Severity.MODERATE, verified=True),
    ]

    history = MedicalHistory(conditions=conditions, allergies=allergies)

    fh = FamilyHistory(entries=[
        FamilyHistoryEntry(relation="father", condition="Coronary Artery Disease",
                           age_at_diagnosis=58, deceased=True, age_at_death=67),
        FamilyHistoryEntry(relation="mother", condition="Type 2 Diabetes Mellitus",
                           age_at_diagnosis=62),
        FamilyHistoryEntry(relation="brother", condition="Hypertension", age_at_diagnosis=50),
    ])

    lifestyle = Lifestyle(
        activity_level=ActivityLevel.SEDENTARY,
        exercise_minutes_per_week=30,
        smoking_status=SmokingStatus.FORMER,
        pack_years=15.0,
        quit_date=date(2018, 6, 1),
        alcohol_consumption=AlcoholConsumption.MODERATE,
        drinks_per_week=8,
        sleep_hours_per_night=6.0,
        stress_level="high",
        fruit_servings_per_day=1,
        vegetable_servings_per_day=2,
        lives_alone=False,
        occupation="Accountant",
    )

    medications = [
        Medication(
            name="Metformin", generic_name="metformin", strength="1000mg",
            route=MedicationRoute.ORAL, frequency=MedicationFrequency.TWICE_DAILY,
            indication="Type 2 Diabetes Mellitus", is_active=True,
            start_date=date(2019, 1, 10),
        ),
        Medication(
            name="Amlodipine", generic_name="amlodipine", strength="10mg",
            route=MedicationRoute.ORAL, frequency=MedicationFrequency.ONCE_DAILY,
            indication="Essential Hypertension", is_active=True,
            start_date=date(2020, 3, 5),
        ),
        Medication(
            name="Atorvastatin", generic_name="atorvastatin", strength="40mg",
            route=MedicationRoute.ORAL, frequency=MedicationFrequency.ONCE_DAILY,
            indication="Hyperlipidaemia", is_active=True,
            start_date=date(2020, 3, 5),
        ),
    ]

    labs = [
        LabPanel(
            panel_name="Comprehensive Metabolic Panel",
            collected_at=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc),
            tests=[
                LabReport(test_name="Fasting Glucose", category=LabTestCategory.DIABETES,
                          value=148.0, unit="mg/dL",
                          reference_range_low=70.0, reference_range_high=100.0,
                          flag="H", collected_at=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)),
                LabReport(test_name="HbA1c", category=LabTestCategory.DIABETES,
                          value=8.2, unit="%",
                          reference_range_low=4.0, reference_range_high=5.7,
                          flag="H", collected_at=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)),
                LabReport(test_name="Total Cholesterol", category=LabTestCategory.LIPID_PANEL,
                          value=218.0, unit="mg/dL",
                          reference_range_high=200.0,
                          flag="H", collected_at=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)),
                LabReport(test_name="HDL Cholesterol", category=LabTestCategory.LIPID_PANEL,
                          value=38.0, unit="mg/dL",
                          reference_range_low=40.0,
                          flag="L", collected_at=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)),
                LabReport(test_name="LDL Cholesterol", category=LabTestCategory.LIPID_PANEL,
                          value=142.0, unit="mg/dL",
                          reference_range_high=100.0,
                          flag="H", collected_at=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)),
                LabReport(test_name="Triglycerides", category=LabTestCategory.LIPID_PANEL,
                          value=190.0, unit="mg/dL",
                          reference_range_high=150.0,
                          flag="H", collected_at=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)),
                LabReport(test_name="eGFR", category=LabTestCategory.KIDNEY,
                          value=72.0, unit="mL/min/1.73m²",
                          reference_range_low=60.0,
                          collected_at=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)),
                LabReport(test_name="Creatinine", category=LabTestCategory.KIDNEY,
                          value=1.1, unit="mg/dL",
                          reference_range_high=1.2,
                          collected_at=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)),
            ],
        )
    ]

    twin = PatientDigitalTwin(
        demographics=demographics,
        vitals=vitals,
        medical_history=history,
        family_history=fh,
        lifestyle=lifestyle,
        medications=medications,
        lab_reports=labs,
    )

    st.session_state.patient_twin = twin
    st.session_state.risk_results = None
    st.session_state.debate_result = None
    st.success("✅ Demo patient 'Robert Johnson' loaded successfully!")
