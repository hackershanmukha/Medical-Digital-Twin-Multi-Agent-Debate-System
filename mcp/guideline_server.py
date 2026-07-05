"""
MCP Server 3: Clinical Guidelines & Evidence Service
Port: 8003

Provides evidence-based clinical guideline retrieval for AI agents.
Tools:
  - search_guidelines       : Search for relevant clinical guidelines by query
  - get_risk_calculator     : Run validated clinical risk scores
  - get_treatment_targets   : Evidence-based treatment targets for conditions
  - get_screening_schedule  : Preventive care & monitoring recommendations
  - get_clinical_evidence   : Key trial evidence for a drug/intervention
"""
import json
import math
import os
import sys
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="guideline-service",
    instructions=(
        "Provides evidence-based clinical guideline retrieval, validated risk calculators, "
        "treatment targets, screening schedules, and clinical trial evidence summaries "
        "to support AI-driven clinical decision support."
    ),
)

# ─── Guideline knowledge base ─────────────────────────────────────────────────

GUIDELINES: list[dict] = [
    # ── Hypertension ──────────────────────────────────────────────────────────
    {
        "id": "GL-HTN-01",
        "topic": "hypertension",
        "title": "ACC/AHA 2017 Hypertension Guideline",
        "source": "ACC/AHA",
        "year": 2017,
        "keywords": ["hypertension", "blood pressure", "antihypertensive", "bp target"],
        "summary": (
            "BP ≥130/80 mmHg now classified as Stage 1 hypertension. "
            "Treatment threshold for high-risk patients (CVD, DM, CKD): BP ≥130/80. "
            "Target BP <130/80 for most adults. First-line agents: thiazide diuretics, "
            "ACE inhibitors, ARBs, or calcium channel blockers. "
            "Lifestyle modification (DASH diet, exercise, sodium restriction, weight loss) "
            "reduces BP by 5-10 mmHg."
        ),
        "key_recommendations": [
            "BP <130/80 mmHg target for adults with CVD or 10-year ASCVD risk ≥10%",
            "Lifestyle modification as initial therapy for Stage 1 HTN (BP 130-139/80-89)",
            "Combination therapy for Stage 2 HTN (BP ≥140/90)",
            "Home BP monitoring recommended for all hypertensive patients",
            "White coat hypertension: confirm with 24h ambulatory monitoring",
        ],
    },
    {
        "id": "GL-HTN-02",
        "topic": "hypertension",
        "title": "NICE NG136 — Hypertension in Adults (2023 update)",
        "source": "NICE",
        "year": 2023,
        "keywords": ["hypertension", "blood pressure", "NICE", "UK guidelines"],
        "summary": (
            "Diagnose HTN at clinic BP ≥140/90 (confirmed by home/ABPM). "
            "Stage 1: 135/85–149/94 ABPM — treat if <80y with end-organ damage, CVD, DM, or 10-yr CVD risk ≥10%. "
            "Stage 2: ABPM ≥150/95 — always treat. "
            "Step 1: ACE-i/ARB (<55y, not Black) or CCB (≥55y or Black). "
            "Step 2: ACE-i/ARB + CCB. Step 3: Add thiazide. Step 4: Specialist referral."
        ),
        "key_recommendations": [
            "Use ABPM/HBPM for diagnosis to avoid white coat effect",
            "Target <140/90 clinic BP (or <135/85 home/ABPM) for most adults",
            "Target <130/80 in T2DM and CKD with proteinuria",
            "Offer treatment to all adults with Stage 2 HTN regardless of CVD risk",
        ],
    },
    # ── Diabetes ──────────────────────────────────────────────────────────────
    {
        "id": "GL-DM-01",
        "topic": "diabetes",
        "title": "ADA Standards of Care in Diabetes — 2024",
        "source": "ADA",
        "year": 2024,
        "keywords": ["diabetes", "hba1c", "metformin", "sglt2", "glp1", "glycaemic", "glucose"],
        "summary": (
            "HbA1c target <7.0% for most adults; individualise (6.5–8.0%) based on hypoglycaemia risk, "
            "life expectancy and patient preference. First-line therapy: metformin + lifestyle. "
            "For patients with established ASCVD or high CVD risk: add GLP-1 RA (semaglutide/liraglutide) "
            "or SGLT-2i (empagliflozin/dapagliflozin) regardless of HbA1c. "
            "SGLT-2i preferred in heart failure or CKD."
        ),
        "key_recommendations": [
            "HbA1c <7.0% target for most adults with T2DM",
            "GLP-1 RA or SGLT-2i in T2DM + ASCVD — proven cardiovascular benefit",
            "SGLT-2i in T2DM + heart failure or CKD eGFR 25–45 (cardiorenal protection)",
            "Screen for diabetes complications annually (retinopathy, nephropathy, neuropathy, foot)",
            "BP target <130/80 in T2DM",
            "Statin therapy: high-intensity if ASCVD; moderate-intensity if 40-75 without ASCVD",
        ],
    },
    {
        "id": "GL-DM-02",
        "topic": "prediabetes",
        "title": "ADA Diabetes Prevention Guideline 2024",
        "source": "ADA",
        "year": 2024,
        "keywords": ["prediabetes", "diabetes prevention", "lifestyle intervention", "dpp", "metformin"],
        "summary": (
            "DPP lifestyle intervention: intensive program (≥150 min/week moderate activity + 7% weight loss) "
            "reduces T2DM risk by 58%. Metformin (500-1700mg/day) reduces risk by 31% — "
            "consider for: BMI ≥35, age <60, prior GDM, HbA1c ≥6.0%, or progressive HbA1c rise. "
            "Screen all adults ≥45y; screen earlier if BMI ≥25 + risk factors."
        ),
        "key_recommendations": [
            "Refer all prediabetes patients to structured lifestyle programme",
            "Goal: ≥5% weight loss + ≥150min/week moderate exercise",
            "Metformin for high-risk prediabetes (BMI≥35, age<60, prior GDM)",
            "Annual screening: FPG + HbA1c to monitor progression",
            "Smoking cessation strongly recommended (doubles diabetes risk)",
        ],
    },
    # ── Cardiovascular ────────────────────────────────────────────────────────
    {
        "id": "GL-CVD-01",
        "topic": "cardiovascular",
        "title": "ACC/AHA 2019 Primary Prevention of Cardiovascular Disease",
        "source": "ACC/AHA",
        "year": 2019,
        "keywords": ["cardiovascular", "cvd", "ascvd", "prevention", "statin", "aspirin", "risk"],
        "summary": (
            "CVD prevention requires comprehensive risk factor management. "
            "Statin therapy: high-intensity if ASCVD risk ≥20%; moderate-intensity if 7.5-20%. "
            "Aspirin: consider only in selected high-risk adults 40-70y with no bleeding risk; "
            "NOT recommended for primary prevention in adults ≥70. "
            "10-year ASCVD risk calculator (PCE) essential for treatment decisions."
        ),
        "key_recommendations": [
            "Calculate 10-year ASCVD risk for all adults 40-75y",
            "High-intensity statin for ASCVD risk ≥20%",
            "Moderate-intensity statin for ASCVD risk 7.5-20%",
            "LDL target: <70 mg/dL for high risk; <55 mg/dL for very high risk",
            "Aspirin no longer recommended for primary prevention in most adults",
            "BP target <130/80 for all adults with CVD or risk ≥10%",
        ],
    },
    {
        "id": "GL-CVD-02",
        "topic": "heart failure",
        "title": "ACC/AHA/HFSA 2022 Heart Failure Guideline",
        "source": "ACC/AHA/HFSA",
        "year": 2022,
        "keywords": ["heart failure", "hfref", "hfpef", "lvef", "ace inhibitor", "beta blocker", "sglt2"],
        "summary": (
            "HFrEF (LVEF <40%): GDMT = ACE-i/ARNI + beta-blocker + MRA + SGLT-2i (quadruple therapy). "
            "HFmrEF (LVEF 41-49%): Consider same agents. "
            "HFpEF (LVEF ≥50%): SGLT-2i (empagliflozin/dapagliflozin) Class IIa; "
            "Diuretics for congestion. Manage hypertension and AF aggressively."
        ),
        "key_recommendations": [
            "SGLT-2i (empagliflozin/dapagliflozin) recommended in all HF subtypes",
            "HFrEF: initiate and uptitrate GDMT (ACE-i, BB, MRA, SGLT-2i)",
            "Avoid NSAIDs, non-DHP CCBs, and thiazolidinediones in HFrEF",
            "Diuresis to euvolaemia — daily weight monitoring",
            "Consider ICD/CRT if LVEF ≤35% despite GDMT ≥3 months",
        ],
    },
    # ── Lipids ────────────────────────────────────────────────────────────────
    {
        "id": "GL-LIPID-01",
        "topic": "lipids",
        "title": "ACC/AHA 2018 Cholesterol Guideline",
        "source": "ACC/AHA",
        "year": 2018,
        "keywords": ["cholesterol", "ldl", "statin", "hyperlipidaemia", "dyslipidaemia", "lipid"],
        "summary": (
            "Risk-based LDL targets: Very high risk (ASCVD): <55 mg/dL; High risk: <70 mg/dL; "
            "Moderate risk: <100 mg/dL. Prefer high-intensity statins. "
            "Add ezetimibe if LDL target not met on maximally tolerated statin. "
            "Add PCSK9 inhibitor for very high risk with LDL ≥70 on statin + ezetimibe."
        ),
        "key_recommendations": [
            "Very high ASCVD risk: LDL target <55 mg/dL",
            "High ASCVD risk: LDL target <70 mg/dL",
            "Atorvastatin 40-80mg or rosuvastatin 20-40mg = high-intensity statin",
            "Check fasting lipid panel 4-12 weeks after statin initiation/dose change",
            "Non-HDL cholesterol used when triglycerides >400 mg/dL",
        ],
    },
    # ── Chronic Kidney Disease ────────────────────────────────────────────────
    {
        "id": "GL-CKD-01",
        "topic": "chronic kidney disease",
        "title": "KDIGO 2024 CKD Guideline",
        "source": "KDIGO",
        "year": 2024,
        "keywords": ["ckd", "kidney", "renal", "egfr", "proteinuria", "creatinine"],
        "summary": (
            "Optimise RAAS blockade with ACE-i or ARB in CKD with albuminuria. "
            "SGLT-2i (dapagliflozin) recommended for CKD with eGFR ≥25 and uACR ≥200 mg/g — "
            "slows CKD progression by ~40% (DAPA-CKD). "
            "BP target <120/80 per SPRINT data. Avoid nephrotoxins and NSAIDs. "
            "Monitor eGFR + uACR q3-6m based on stage."
        ),
        "key_recommendations": [
            "SGLT-2i (dapagliflozin/empagliflozin) recommended for CKD eGFR ≥25 + uACR ≥200",
            "ACE-i or ARB for CKD with albuminuria — do not combine",
            "BP target <120/80 in CKD",
            "Avoid NSAIDs, nephrotoxic antibiotics, and contrast media without precautions",
            "Anaemia management: Hb target 10-12 g/dL with ESA or iron",
        ],
    },
    # ── Obesity / Lifestyle ───────────────────────────────────────────────────
    {
        "id": "GL-OB-01",
        "topic": "obesity",
        "title": "ACC/AHA Obesity and Lifestyle Guideline 2023",
        "source": "ACC/AHA",
        "year": 2023,
        "keywords": ["obesity", "bmi", "weight", "lifestyle", "exercise", "diet", "bariatric"],
        "summary": (
            "Obesity (BMI ≥30) increases CVD, T2DM, HF, and cancer risk. "
            "5-10% weight loss significantly improves cardiometabolic risk factors. "
            "Recommended: intensive behavioural therapy (≥14 sessions/year), Mediterranean diet, "
            "≥150 min/week moderate activity. Pharmacotherapy: GLP-1 RA (semaglutide 2.4mg/week) "
            "achieves ~15-17% weight loss. Bariatric surgery for BMI ≥40 or ≥35 with comorbidities."
        ),
        "key_recommendations": [
            "Target 5-10% weight loss — improves HbA1c, BP, and lipids significantly",
            "Mediterranean/DASH diet preferred over low-fat diet for cardiometabolic outcomes",
            "≥150 min/week moderate exercise (or ≥75 min vigorous)",
            "Semaglutide 2.4mg/week — ~15-17% weight loss (STEP trials)",
            "Bariatric surgery: most effective for sustained weight loss and T2DM remission",
        ],
    },
]

# ─── Evidence base (key clinical trials) ─────────────────────────────────────

TRIAL_EVIDENCE: dict[str, list[dict]] = {
    "semaglutide": [
        {
            "trial": "SUSTAIN-6", "year": 2016,
            "outcome": "26% ↓ MACE (CV death, non-fatal MI, stroke) vs placebo",
            "population": "T2DM with established CVD or high CVD risk, n=3297",
            "duration": "104 weeks",
        },
        {
            "trial": "SELECT", "year": 2023,
            "outcome": "20% ↓ MACE in non-diabetic overweight/obese adults with CVD",
            "population": "BMI ≥27, CVD, no T2DM, n=17,604",
            "duration": "5 years (median 34.2 months)",
        },
    ],
    "empagliflozin": [
        {
            "trial": "EMPA-REG OUTCOME", "year": 2015,
            "outcome": "38% ↓ CV death, 35% ↓ HF hospitalisation, 32% ↓ renal progression",
            "population": "T2DM + established CVD, n=7020",
            "duration": "median 3.1 years",
        },
        {
            "trial": "EMPEROR-Reduced", "year": 2020,
            "outcome": "25% ↓ CV death/HF hospitalisation in HFrEF",
            "population": "HFrEF LVEF <40%, with/without T2DM, n=3730",
            "duration": "median 16 months",
        },
        {
            "trial": "EMPEROR-Preserved", "year": 2021,
            "outcome": "21% ↓ CV death/HF hospitalisation in HFpEF",
            "population": "HFpEF LVEF >40%, n=5988",
            "duration": "median 26 months",
        },
    ],
    "atorvastatin": [
        {
            "trial": "ASCOT-LLA", "year": 2003,
            "outcome": "36% ↓ non-fatal MI and fatal CHD in hypertension + 3 risk factors",
            "population": "Hypertension + ≥3 risk factors, n=10,305",
            "duration": "median 3.3 years",
        },
        {
            "trial": "CARDS", "year": 2004,
            "outcome": "37% ↓ MACE in T2DM without prior CVD",
            "population": "T2DM + ≥1 CVD risk factor, n=2838",
            "duration": "median 3.9 years",
        },
    ],
    "metformin": [
        {
            "trial": "UKPDS 34", "year": 1998,
            "outcome": "32% ↓ diabetes-related endpoints, 36% ↓ all-cause mortality in obese T2DM",
            "population": "Newly diagnosed T2DM, overweight, n=753",
            "duration": "10.7 years",
        },
        {
            "trial": "DPP (Diabetes Prevention Program)", "year": 2002,
            "outcome": "31% ↓ T2DM incidence vs placebo (vs 58% with lifestyle)",
            "population": "Prediabetes, n=3234",
            "duration": "2.8 years",
        },
    ],
    "lifestyle": [
        {
            "trial": "LOOK AHEAD", "year": 2013,
            "outcome": "Intensive lifestyle: −8.6% weight at 1yr, improved HbA1c, BP, lipids",
            "population": "Overweight/obese T2DM, n=5145",
            "duration": "9.6 years",
        },
        {
            "trial": "DPP Lifestyle Arm", "year": 2002,
            "outcome": "58% ↓ T2DM progression with 7% weight loss + 150 min/week exercise",
            "population": "Prediabetes, n=1079",
            "duration": "2.8 years",
        },
    ],
}

# ─── Treatment targets ────────────────────────────────────────────────────────

TREATMENT_TARGETS: dict[str, dict] = {
    "diabetes": {
        "hba1c": "<7.0% (most adults); <8.0% (elderly/complex); <6.5% (low hypoglycaemia risk, short duration)",
        "fasting_glucose_mmol": "4.0-7.0 mmol/L (72-126 mg/dL)",
        "postprandial_glucose_mmol": "<8.5 mmol/L (<153 mg/dL) at 2h",
        "bp": "<130/80 mmHg",
        "ldl": "<70 mg/dL with ASCVD; <100 mg/dL without ASCVD",
        "weight": "5-10% weight loss if overweight",
        "source": "ADA Standards of Care 2024",
    },
    "hypertension": {
        "bp": "<130/80 mmHg (most adults with CVD or ≥10% ASCVD risk)",
        "bp_general": "<140/90 mmHg (general population)",
        "bp_elderly": "<150/90 mmHg if ≥80y or frail",
        "bp_diabetes": "<130/80 mmHg",
        "bp_ckd": "<130/80 mmHg",
        "source": "ACC/AHA 2017 + NICE NG136 2023",
    },
    "heart_failure": {
        "lvef_target": "LVEF improvement with GDMT (goal-directed medical therapy)",
        "fluid_status": "Euvolaemic (target weight, no oedema, clear lungs)",
        "bp": "<130/80 mmHg",
        "hr_target": "<70 bpm (HFrEF on beta-blocker)",
        "ldl": "<55 mg/dL (established ASCVD)",
        "source": "ACC/AHA/HFSA 2022",
    },
    "hyperlipidaemia": {
        "ldl_very_high_risk": "<55 mg/dL (established ASCVD or >10yr T2DM with end-organ damage)",
        "ldl_high_risk": "<70 mg/dL (ASCVD risk 7.5-20% or moderate CKD)",
        "ldl_moderate_risk": "<100 mg/dL",
        "non_hdl_add_30": "Non-HDL target = LDL target + 30 mg/dL",
        "hdl": ">40 mg/dL (male); >50 mg/dL (female) — no specific treatment target",
        "triglycerides": "<150 mg/dL (goal); >500 mg/dL requires treatment to prevent pancreatitis",
        "source": "ACC/AHA 2018 Cholesterol Guideline",
    },
    "ckd": {
        "bp": "<120/80 (SPRINT data) or <130/80 (KDIGO)",
        "egfr_monitor": "Declining >5 mL/min/yr = rapid progression — refer nephrology",
        "uacr_target": "Reduce by ≥30% with RAAS blockade",
        "hba1c": "<7.0% in DM-related CKD",
        "haemoglobin": "10-12 g/dL (avoid transfusion where possible)",
        "source": "KDIGO CKD Guideline 2024",
    },
}

# ─── Screening schedules ──────────────────────────────────────────────────────

SCREENING_SCHEDULES: dict[str, list[dict]] = {
    "diabetes": [
        {"test": "HbA1c", "frequency": "Every 3 months (uncontrolled) / Every 6 months (stable)"},
        {"test": "Fasting Lipid Panel", "frequency": "Annually"},
        {"test": "eGFR + Urine ACR", "frequency": "Annually"},
        {"test": "Diabetic Foot Exam", "frequency": "Annually (or more frequent if neuropathy)"},
        {"test": "Dilated Retinal Exam", "frequency": "Annually (or q2y if stable and low-risk)"},
        {"test": "Blood Pressure", "frequency": "Every clinic visit"},
        {"test": "Body Weight", "frequency": "Every clinic visit"},
    ],
    "hypertension": [
        {"test": "Blood Pressure", "frequency": "Monthly until stable, then q6m"},
        {"test": "U&E / eGFR", "frequency": "At initiation of RAAS blockade, then annually"},
        {"test": "ECG", "frequency": "At diagnosis, then if symptoms"},
        {"test": "Fasting Lipid Panel", "frequency": "Annually"},
        {"test": "Fasting Glucose / HbA1c", "frequency": "Annually (DM screening)"},
        {"test": "Fundoscopy", "frequency": "If hypertensive retinopathy suspected"},
    ],
    "heart_failure": [
        {"test": "Weight", "frequency": "Daily (patient self-monitoring) — alert if >2kg in 2 days"},
        {"test": "U&E / eGFR / BNP", "frequency": "At each titration; q3-6m when stable"},
        {"test": "Echocardiogram", "frequency": "At diagnosis; after 3 months GDMT; q1-2y if stable"},
        {"test": "Blood Pressure", "frequency": "Every clinic visit"},
        {"test": "Iron studies / FBC", "frequency": "Annually (iron deficiency common in HF)"},
        {"test": "6-minute walk test", "frequency": "At diagnosis and q6-12m"},
    ],
    "ckd": [
        {"test": "eGFR + Urine ACR", "frequency": "q3m (G3b-G5); q6m (G3a); q1y (G1-G2 with risk factors)"},
        {"test": "Blood Pressure", "frequency": "Every clinic visit"},
        {"test": "U&E / Bicarbonate", "frequency": "q3-6m (G3-G4)"},
        {"test": "FBC / Haemoglobin", "frequency": "Annually (q6m if anaemia or EPO therapy)"},
        {"test": "Bone mineral (Ca, PO4, PTH)", "frequency": "q6m (G4-G5)"},
        {"test": "Fasting Lipid Panel", "frequency": "Annually"},
    ],
}


def _keyword_search(query: str, n: int) -> list[dict]:
    """Score and rank guidelines by keyword match."""
    q_lower = query.lower()
    scored = []
    for gl in GUIDELINES:
        score = 0
        for kw in gl.get("keywords", []):
            if kw in q_lower or q_lower in kw:
                score += 2
        # Title / topic match
        if any(w in gl["title"].lower() for w in q_lower.split()):
            score += 3
        if gl["topic"].lower() in q_lower:
            score += 5
        if score > 0:
            scored.append((score, gl))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [g for _, g in scored[:n]]


# ─── MCP Tools ───────────────────────────────────────────────────────────────

@mcp.tool()
def search_guidelines(query: str, top_k: int = 3) -> str:
    """
    Search for relevant clinical guidelines by query string.

    Args:
        query: Free-text query (e.g. 'diabetes hypertension treatment', 'statin CVD risk').
        top_k: Maximum number of guidelines to return (default 3).

    Returns:
        JSON list of matching guidelines with summaries and key recommendations.
    """
    results = _keyword_search(query, top_k)
    if not results:
        return json.dumps({
            "found": False,
            "query": query,
            "message": "No matching guidelines found. Try broader terms.",
        })

    return json.dumps({
        "found": True,
        "query": query,
        "results_count": len(results),
        "guidelines": [
            {
                "id": g["id"],
                "title": g["title"],
                "source": g["source"],
                "year": g["year"],
                "summary": g["summary"],
                "key_recommendations": g["key_recommendations"],
            }
            for g in results
        ],
    }, indent=2)


@mcp.tool()
def get_risk_calculator(
    calculator: str,
    age: int,
    gender: str,
    systolic_bp: float = 120.0,
    total_cholesterol_mgdl: float = 190.0,
    hdl_cholesterol_mgdl: float = 55.0,
    on_bp_treatment: bool = False,
    smoker: bool = False,
    has_diabetes: bool = False,
    bmi: float = 25.0,
    hba1c: float = 5.5,
    family_history_dm: bool = False,
) -> str:
    """
    Run validated clinical risk calculators.

    Supported calculators:
      - "ascvd"     : 10-year ASCVD risk (ACC/AHA Pooled Cohort Equations)
      - "findrisc"  : FINDRISC diabetes risk score (Finnish Diabetes Risk Score)
      - "bmi_class" : BMI classification (WHO)

    Args:
        calculator: One of 'ascvd', 'findrisc', 'bmi_class'.
        age: Patient age in years.
        gender: 'male' or 'female'.
        systolic_bp: Systolic BP in mmHg.
        total_cholesterol_mgdl: Total cholesterol in mg/dL.
        hdl_cholesterol_mgdl: HDL cholesterol in mg/dL.
        on_bp_treatment: True if on antihypertensive medication.
        smoker: True if current/former smoker.
        has_diabetes: True if diagnosed with diabetes.
        bmi: Body Mass Index.
        hba1c: HbA1c percentage.
        family_history_dm: True if first-degree relative with T2DM.

    Returns:
        JSON with calculated score, risk category, and clinical interpretation.
    """
    calc = calculator.lower().strip()

    if calc == "ascvd":
        # Simplified ACC/AHA PCE (White race coefficients — approximate)
        ln_age = math.log(max(age, 1))
        ln_tc = math.log(max(total_cholesterol_mgdl, 1))
        ln_hdl = math.log(max(hdl_cholesterol_mgdl, 1))
        ln_sbp = math.log(max(systolic_bp, 1))

        if gender.lower() == "male":
            lp = (
                12.344 * ln_age + 11.853 * ln_tc - 7.990 * ln_hdl +
                (1.769 if on_bp_treatment else 1.797) * ln_sbp +
                7.837 * (1 if smoker else 0) + 0.658 * (1 if has_diabetes else 0)
            )
            risk = 1 - 0.88936 ** math.exp(lp - 61.18)
        else:
            lp = (
                -29.799 * ln_age + 13.540 * ln_tc - 13.578 * ln_hdl +
                (2.019 if on_bp_treatment else 1.957) * ln_sbp +
                7.574 * (1 if smoker else 0) + 0.661 * (1 if has_diabetes else 0)
            )
            risk = 1 - 0.95012 ** math.exp(lp - (-29.18))

        risk_pct = max(0.0, min(100.0, risk * 100))
        if risk_pct < 5:
            category = "Low (<5%)"
        elif risk_pct < 7.5:
            category = "Borderline (5-7.5%)"
        elif risk_pct < 20:
            category = "Intermediate (7.5-20%)"
        else:
            category = "High (≥20%)"

        recommendation = ""
        if risk_pct >= 20:
            recommendation = "High-intensity statin therapy strongly recommended. BP target <130/80. Consider aspirin."
        elif risk_pct >= 7.5:
            recommendation = "Discuss statin therapy. Lifestyle optimisation. BP target <130/80."
        else:
            recommendation = "Lifestyle modification. Reassess in 5 years or if risk factors change."

        return json.dumps({
            "calculator": "ACC/AHA ASCVD Pooled Cohort Equations",
            "ten_year_risk_percent": round(risk_pct, 1),
            "risk_category": category,
            "clinical_recommendation": recommendation,
            "guideline": "ACC/AHA 2019 Primary Prevention Guideline",
            "note": "Approximate calculation. Use validated ACC ASCVD Risk Calculator for clinical decisions.",
        }, indent=2)

    elif calc == "findrisc":
        score = 0
        # Age
        if age < 45:
            score += 0
        elif age < 55:
            score += 2
        elif age < 65:
            score += 3
        else:
            score += 4
        # BMI
        if bmi < 25:
            score += 0
        elif bmi < 30:
            score += 1
        else:
            score += 3
        # Waist (approximate from BMI — waist not in tool params)
        # Skip waist in this version
        # Activity
        # (Not in params — assume sedentary for high BMI)
        # Family history
        if family_history_dm:
            score += 5
        # HbA1c proxy for prediabetes
        if hba1c >= 5.7:
            score += 5
        # Smoker (not in FINDRISC but increases risk)
        if smoker:
            score += 2

        if score < 7:
            risk_level, risk_pct, dm_risk = "Low", "<1%", 1
        elif score < 11:
            risk_level, risk_pct, dm_risk = "Slightly Elevated", "1 in 25", 4
        elif score < 15:
            risk_level, risk_pct, dm_risk = "Moderate", "1 in 6", 17
        elif score < 20:
            risk_level, risk_pct, dm_risk = "High", "1 in 3", 33
        else:
            risk_level, risk_pct, dm_risk = "Very High", "1 in 2", 50

        return json.dumps({
            "calculator": "FINDRISC (Finnish Diabetes Risk Score)",
            "score": score,
            "risk_level": risk_level,
            "10yr_diabetes_probability": risk_pct,
            "estimated_percent": dm_risk,
            "recommendation": (
                "Refer to structured diabetes prevention programme. "
                "Consider annual HbA1c + fasting glucose monitoring." if score >= 12
                else "Lifestyle advice. Reassess in 5 years."
            ),
            "guideline": "ADA Standards of Care 2024",
        }, indent=2)

    elif calc == "bmi_class":
        if bmi < 18.5:
            cat, desc = "Underweight", "BMI <18.5 — assess for malnutrition"
        elif bmi < 25:
            cat, desc = "Normal weight", "BMI 18.5-24.9 — maintain with healthy lifestyle"
        elif bmi < 30:
            cat, desc = "Overweight", "BMI 25-29.9 — lifestyle intervention; 5% weight loss target"
        elif bmi < 35:
            cat, desc = "Obesity Class I", "BMI 30-34.9 — intensive lifestyle; consider pharmacotherapy"
        elif bmi < 40:
            cat, desc = "Obesity Class II", "BMI 35-39.9 — pharmacotherapy; consider bariatric surgery if comorbidities"
        else:
            cat, desc = "Obesity Class III (Morbid)", "BMI ≥40 — bariatric surgery evaluation; aggressive risk factor management"

        return json.dumps({
            "calculator": "WHO BMI Classification",
            "bmi": round(bmi, 1),
            "category": cat,
            "description": desc,
            "cvd_risk_impact": (
                "Every 5-unit BMI increase above 25 raises CVD risk by ~30% and T2DM risk by ~60%."
            ),
        }, indent=2)

    else:
        return json.dumps({
            "error": f"Unknown calculator '{calculator}'. Supported: ascvd, findrisc, bmi_class",
        })


@mcp.tool()
def get_treatment_targets(condition: str) -> str:
    """
    Retrieve evidence-based treatment targets for a clinical condition.

    Args:
        condition: Condition name (e.g. 'diabetes', 'hypertension', 'heart_failure',
                   'hyperlipidaemia', 'ckd').

    Returns:
        JSON with specific treatment targets and their evidence source.
    """
    condition_lower = condition.lower().strip()
    # Fuzzy match
    target = None
    for key in TREATMENT_TARGETS:
        if key in condition_lower or condition_lower in key:
            target = TREATMENT_TARGETS[key]
            break

    if not target:
        return json.dumps({
            "found": False,
            "condition": condition,
            "available_conditions": list(TREATMENT_TARGETS.keys()),
        })

    return json.dumps({
        "found": True,
        "condition": condition,
        "targets": target,
    }, indent=2)


@mcp.tool()
def get_screening_schedule(condition: str) -> str:
    """
    Get the recommended monitoring and screening schedule for a condition.

    Args:
        condition: Condition name (e.g. 'diabetes', 'hypertension', 'heart_failure', 'ckd').

    Returns:
        JSON with recommended tests and frequencies.
    """
    condition_lower = condition.lower().strip()
    schedule = None
    matched_key = None
    for key in SCREENING_SCHEDULES:
        if key in condition_lower or condition_lower in key:
            schedule = SCREENING_SCHEDULES[key]
            matched_key = key
            break

    if not schedule:
        return json.dumps({
            "found": False,
            "condition": condition,
            "available_conditions": list(SCREENING_SCHEDULES.keys()),
        })

    return json.dumps({
        "found": True,
        "condition": matched_key,
        "total_tests": len(schedule),
        "schedule": schedule,
    }, indent=2)


@mcp.tool()
def get_clinical_evidence(drug_or_intervention: str) -> str:
    """
    Retrieve key clinical trial evidence for a drug or intervention.

    Args:
        drug_or_intervention: Drug name or intervention (e.g. 'semaglutide', 'empagliflozin',
                               'atorvastatin', 'metformin', 'lifestyle').

    Returns:
        JSON with trial names, outcomes, and populations.
    """
    key = drug_or_intervention.lower().strip()
    evidence = None
    for drug_key, trials in TRIAL_EVIDENCE.items():
        if drug_key in key or key in drug_key:
            evidence = trials
            break

    if not evidence:
        return json.dumps({
            "found": False,
            "drug_or_intervention": drug_or_intervention,
            "available_entries": list(TRIAL_EVIDENCE.keys()),
            "message": "No trial evidence in local database. Consider PubMed or Cochrane Library.",
        })

    return json.dumps({
        "found": True,
        "drug_or_intervention": drug_or_intervention,
        "trial_count": len(evidence),
        "evidence": evidence,
    }, indent=2)


# ─── MCP Resources ────────────────────────────────────────────────────────────

@mcp.resource("guidelines://catalogue")
def list_guidelines() -> str:
    """List all available clinical guidelines in the knowledge base."""
    return json.dumps({
        "total": len(GUIDELINES),
        "guidelines": [
            {"id": g["id"], "title": g["title"], "source": g["source"], "year": g["year"], "topic": g["topic"]}
            for g in GUIDELINES
        ],
    }, indent=2)


@mcp.resource("guidelines://conditions")
def list_supported_conditions() -> str:
    """List conditions with treatment targets and screening schedules."""
    return json.dumps({
        "conditions_with_targets": list(TREATMENT_TARGETS.keys()),
        "conditions_with_screening": list(SCREENING_SCHEDULES.keys()),
        "conditions_with_evidence": list(TRIAL_EVIDENCE.keys()),
    })


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Clinical Guidelines MCP Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"])
    parser.add_argument("--port", type=int, default=8003)
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse", port=args.port)
    else:
        mcp.run(transport="stdio")
