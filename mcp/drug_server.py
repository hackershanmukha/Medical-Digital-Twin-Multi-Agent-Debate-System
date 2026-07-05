"""
MCP Server 1: Drug Information & Interaction Service
Port: 8001

Tools exposed:
  - get_drug_info          : Detailed info on a single drug
  - check_drug_interaction : Check interactions between two or more drugs
  - check_allergy_alert    : Validate a drug against a patient's allergy list
  - get_contraindications  : List contraindications for a drug given clinical context
  - get_dosage_guidance    : Dosage recommendations for a drug (renal/hepatic adjustment)
"""
import json
import sys
import os

# Allow imports from project root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="drug-service",
    instructions=(
        "Provides drug information, interaction checking, allergy alerts, "
        "contraindication lookup, and dosage guidance for clinical decision support."
    ),
)

# ─── Embedded drug knowledge base ────────────────────────────────────────────
# In production this would connect to openFDA / RxNorm / DrugBank APIs.
# For the hackathon demo this is a curated in-memory KB covering common
# cardiovascular and metabolic drugs.

DRUG_DB: dict[str, dict] = {
    "metformin": {
        "name": "Metformin",
        "class": "Biguanide",
        "indications": ["Type 2 Diabetes Mellitus", "Prediabetes (off-label)", "PCOS"],
        "mechanism": "Reduces hepatic glucose production; increases peripheral insulin sensitivity",
        "standard_doses": ["500mg BD", "850mg BD", "1000mg BD", "2000mg max/day"],
        "max_dose_mg_day": 2000,
        "renal_adjustment": True,
        "renal_note": "Contraindicated if eGFR <30; reduce dose if eGFR 30-45",
        "hepatic_adjustment": True,
        "hepatic_note": "Avoid in severe hepatic impairment (lactic acidosis risk)",
        "common_side_effects": ["GI upset", "nausea", "diarrhoea", "metallic taste"],
        "serious_side_effects": ["Lactic acidosis (rare, esp. with renal impairment)"],
        "contraindications": [
            "eGFR <30 mL/min/1.73m²",
            "Active hepatic disease",
            "IV contrast media (hold 48h)",
            "Metabolic acidosis",
        ],
        "monitoring": ["eGFR q6m", "Vitamin B12 annually", "LFTs annually"],
        "drug_class_interactions": ["SGLT2 inhibitors (additive hypoglycaemia risk)", "Alcohol"],
    },
    "atorvastatin": {
        "name": "Atorvastatin",
        "class": "HMG-CoA Reductase Inhibitor (Statin)",
        "indications": ["Hyperlipidaemia", "Primary/secondary CVD prevention", "Familial hypercholesterolaemia"],
        "mechanism": "Inhibits HMG-CoA reductase → reduces hepatic cholesterol synthesis → upregulates LDL receptors",
        "standard_doses": ["10mg OD", "20mg OD", "40mg OD (high-intensity)", "80mg OD (high-intensity)"],
        "max_dose_mg_day": 80,
        "renal_adjustment": False,
        "hepatic_adjustment": True,
        "hepatic_note": "Contraindicated in active liver disease / unexplained elevated transaminases",
        "common_side_effects": ["Myalgia", "Headache", "GI disturbance"],
        "serious_side_effects": ["Rhabdomyolysis", "Hepatotoxicity", "New-onset diabetes (class effect)"],
        "contraindications": [
            "Active hepatic disease",
            "Pregnancy / breastfeeding",
            "Concomitant ciclosporin (relative)",
        ],
        "monitoring": ["LFTs at baseline", "CK if myalgia", "HbA1c (diabetes risk)"],
        "drug_class_interactions": [
            "Fibrates (myopathy risk ↑)", "Macrolides (CYP3A4 inhibition → toxicity)",
            "Azole antifungals", "Amiodarone", "Calcium channel blockers (amlodipine: safe)",
        ],
    },
    "amlodipine": {
        "name": "Amlodipine",
        "class": "Dihydropyridine Calcium Channel Blocker",
        "indications": ["Hypertension", "Angina", "Coronary artery disease"],
        "mechanism": "Blocks L-type calcium channels in vascular smooth muscle → vasodilation",
        "standard_doses": ["2.5mg OD", "5mg OD", "10mg OD"],
        "max_dose_mg_day": 10,
        "renal_adjustment": False,
        "hepatic_adjustment": True,
        "hepatic_note": "Start at 2.5mg in severe hepatic impairment",
        "common_side_effects": ["Peripheral oedema", "Headache", "Flushing", "Palpitations"],
        "serious_side_effects": ["Severe hypotension", "Worsening angina on initiation"],
        "contraindications": ["Cardiogenic shock", "Severe aortic stenosis", "Unstable angina"],
        "monitoring": ["BP", "HR", "Oedema"],
        "drug_class_interactions": ["CYP3A4 inhibitors (itraconazole, ritonavir) → toxicity", "Simvastatin (limit 20mg)"],
    },
    "lisinopril": {
        "name": "Lisinopril",
        "class": "ACE Inhibitor",
        "indications": ["Hypertension", "Heart failure", "Post-MI", "Diabetic nephropathy"],
        "mechanism": "Inhibits ACE → reduces angiotensin II → vasodilation + reduced aldosterone",
        "standard_doses": ["2.5mg OD", "5mg OD", "10mg OD", "20mg OD", "40mg OD"],
        "max_dose_mg_day": 40,
        "renal_adjustment": True,
        "renal_note": "Reduce dose by 50% if eGFR 10-30; avoid if eGFR <10",
        "hepatic_adjustment": False,
        "common_side_effects": ["Dry cough (10-15%)", "Dizziness", "Headache", "Hyperkalaemia"],
        "serious_side_effects": ["Angioedema (rare but life-threatening)", "Renal impairment", "Hyperkalaemia"],
        "contraindications": [
            "Pregnancy (all trimesters — teratogenic)",
            "History of ACE inhibitor-associated angioedema",
            "Bilateral renal artery stenosis",
            "Concurrent aliskiren in diabetics",
        ],
        "monitoring": ["U&E + eGFR at 1-2w after start/dose change", "BP", "K+"],
        "drug_class_interactions": ["NSAIDs (↓ efficacy + renal risk)", "Potassium-sparing diuretics", "ARBs (dual RAAS blockade)"],
    },
    "semaglutide": {
        "name": "Semaglutide",
        "class": "GLP-1 Receptor Agonist",
        "indications": ["Type 2 Diabetes Mellitus", "Obesity/weight management (Wegovy)", "CVD risk reduction in T2DM"],
        "mechanism": "GLP-1 receptor agonist → glucose-dependent insulin secretion, ↓ glucagon, ↓ appetite, ↓ gastric emptying",
        "standard_doses": ["0.5mg SC weekly (T2DM start)", "1mg SC weekly", "2mg SC weekly (max T2DM)", "2.4mg SC weekly (obesity)"],
        "max_dose_mg_day": 2.4,  # mg/week
        "renal_adjustment": False,
        "hepatic_adjustment": False,
        "common_side_effects": ["Nausea", "Vomiting", "Diarrhoea", "Constipation", "Injection site reactions"],
        "serious_side_effects": ["Pancreatitis", "Thyroid C-cell tumours (rodent data)", "Diabetic retinopathy worsening"],
        "contraindications": [
            "Personal/family history of medullary thyroid carcinoma",
            "Multiple Endocrine Neoplasia type 2 (MEN2)",
            "Pregnancy",
        ],
        "monitoring": ["HbA1c q3m", "Weight", "BP", "Thyroid exam if symptomatic"],
        "drug_class_interactions": ["Insulin (hypoglycaemia risk — reduce insulin dose)", "Oral medications (↓ absorption due to delayed gastric emptying)"],
        "cvd_benefit": "SUSTAIN-6: 26% reduction in MACE in T2DM with established CVD",
    },
    "empagliflozin": {
        "name": "Empagliflozin",
        "class": "SGLT-2 Inhibitor",
        "indications": ["Type 2 Diabetes Mellitus", "Heart failure (HFrEF + HFpEF)", "Chronic kidney disease"],
        "mechanism": "Inhibits SGLT-2 in proximal tubule → glycosuria → reduced blood glucose + osmotic diuresis + natriuresis",
        "standard_doses": ["10mg OD", "25mg OD"],
        "max_dose_mg_day": 25,
        "renal_adjustment": True,
        "renal_note": "For T2DM: avoid if eGFR <30. For CKD/HF indication: start at any eGFR but reduced glucose-lowering if <45",
        "hepatic_adjustment": False,
        "common_side_effects": ["Genital mycotic infections", "UTI", "Polyuria", "Hypotension"],
        "serious_side_effects": ["Diabetic ketoacidosis (DKA — even euglycaemic)", "Fournier's gangrene (rare)", "AKI on initiation"],
        "contraindications": [
            "T1DM (↑ DKA risk)",
            "Recurrent UTIs",
            "Severe renal impairment (for glucose-lowering indication)",
        ],
        "monitoring": ["eGFR (can cause initial dip — acceptable)", "Volume status", "Ketones if unwell"],
        "drug_class_interactions": ["Insulin (reduce by 20% to avoid hypoglycaemia)", "Diuretics (additive volume depletion)"],
        "cvd_benefit": "EMPA-REG OUTCOME: 38% reduction in CV death; 35% reduction in HF hospitalisation",
        "ckd_benefit": "EMPEROR-Reduced: significant eGFR preservation vs placebo",
    },
    "aspirin": {
        "name": "Aspirin (Low-dose)",
        "class": "Antiplatelet / NSAID",
        "indications": ["Secondary CVD prevention (post-MI, stroke)", "ACS management", "Primary prevention (selected high-risk)"],
        "mechanism": "Irreversibly inhibits COX-1 → ↓ thromboxane A2 → antiplatelet effect",
        "standard_doses": ["75mg OD", "100mg OD (prevention)", "300mg stat (ACS)"],
        "max_dose_mg_day": 300,
        "renal_adjustment": False,
        "hepatic_adjustment": False,
        "common_side_effects": ["GI irritation", "Dyspepsia"],
        "serious_side_effects": ["GI bleeding/ulceration", "Reye's syndrome in children", "Haemorrhagic stroke"],
        "contraindications": [
            "Active peptic ulcer",
            "Bleeding disorders",
            "Children under 16 (Reye's risk)",
            "Severe renal impairment (avoid high doses)",
        ],
        "monitoring": ["Bleeding symptoms", "Haemoglobin annually"],
        "drug_class_interactions": ["Warfarin (major bleeding risk)", "Other NSAIDs (GI risk)", "SSRIs (bleeding risk ↑)"],
    },
}

# ─── Interaction matrix ───────────────────────────────────────────────────────
INTERACTIONS: list[dict] = [
    {
        "drug_a": "metformin", "drug_b": "empagliflozin",
        "severity": "mild",
        "description": "Additive glucose-lowering effect. Monitor for hypoglycaemia if also on insulin/sulfonylurea.",
        "action": "Generally safe combination. No dose adjustment needed unless on insulin.",
        "evidence": "Recommended combination per ADA Standards of Care 2024.",
    },
    {
        "drug_a": "metformin", "drug_b": "semaglutide",
        "severity": "mild",
        "description": "Additive glucose-lowering. Beneficial combination in T2DM with CVD risk.",
        "action": "Safe. Semaglutide may allow metformin dose reduction over time.",
        "evidence": "SUSTAIN trials include metformin as background therapy.",
    },
    {
        "drug_a": "atorvastatin", "drug_b": "amlodipine",
        "severity": "mild",
        "description": "Amlodipine slightly increases atorvastatin AUC (~18%) via CYP3A4 inhibition.",
        "action": "Generally safe. Maximum atorvastatin 80mg still acceptable. Monitor for myopathy.",
        "evidence": "FDA Drug Interaction Data; ACC/AHA Lipid Guideline 2018.",
    },
    {
        "drug_a": "aspirin", "drug_b": "empagliflozin",
        "severity": "mild",
        "description": "Both have renal effects. Aspirin may blunt the natriuretic benefit of SGLT-2i.",
        "action": "Monitor renal function and BP. Low-dose aspirin generally safe.",
        "evidence": "Pharmacodynamic interaction — clinical significance low at standard doses.",
    },
    {
        "drug_a": "lisinopril", "drug_b": "empagliflozin",
        "severity": "mild",
        "description": "Additive BP-lowering and renal-protective effects. Risk of hypotension.",
        "action": "Monitor BP and volume status. Reduce diuretics if co-prescribed.",
        "evidence": "Beneficial combination in diabetic nephropathy / CKD. EMPEROR trials.",
    },
    {
        "drug_a": "metformin", "drug_b": "lisinopril",
        "severity": "none",
        "description": "No clinically significant interaction. Both are first-line agents in T2DM + hypertension.",
        "action": "Standard combination. Monitor eGFR and K+.",
        "evidence": "Multiple guidelines recommend this combination (ADA, NICE, ACC/AHA).",
    },
]


def _normalise(name: str) -> str:
    return name.lower().strip()


def _find_drug(name: str) -> dict | None:
    key = _normalise(name)
    # Exact match
    if key in DRUG_DB:
        return DRUG_DB[key]
    # Partial match
    for k, v in DRUG_DB.items():
        if key in k or k in key or key in v["name"].lower():
            return v
    return None


def _find_interaction(drug_a: str, drug_b: str) -> dict | None:
    a, b = _normalise(drug_a), _normalise(drug_b)
    for ix in INTERACTIONS:
        da, db = _normalise(ix["drug_a"]), _normalise(ix["drug_b"])
        if (a in da or da in a) and (b in db or db in b):
            return ix
        if (b in da or da in b) and (a in db or db in a):
            return ix
    return None


# ─── MCP Tools ───────────────────────────────────────────────────────────────

@mcp.tool()
def get_drug_info(drug_name: str) -> str:
    """
    Retrieve comprehensive clinical information about a drug.

    Args:
        drug_name: Name of the drug (generic or brand).

    Returns:
        JSON string with drug class, indications, dosing, side effects,
        contraindications, monitoring requirements and interactions.
    """
    drug = _find_drug(drug_name)
    if not drug:
        return json.dumps({
            "found": False,
            "drug_name": drug_name,
            "message": (
                f"Drug '{drug_name}' not found in local knowledge base. "
                "Consider querying openFDA or RxNorm for complete information."
            ),
        })
    return json.dumps({"found": True, **drug}, indent=2)


@mcp.tool()
def check_drug_interaction(drug_a: str, drug_b: str) -> str:
    """
    Check for clinically significant interactions between two drugs.

    Args:
        drug_a: First drug name.
        drug_b: Second drug name.

    Returns:
        JSON string with severity, description, recommended action, and evidence.
    """
    ix = _find_interaction(drug_a, drug_b)
    if not ix:
        info_a = _find_drug(drug_a)
        info_b = _find_drug(drug_b)

        # Check class-level interactions from drug KB
        warnings = []
        if info_a and info_b:
            b_lower = drug_b.lower()
            for class_ix in info_a.get("drug_class_interactions", []):
                if b_lower in class_ix.lower() or drug_b.split()[0].lower() in class_ix.lower():
                    warnings.append(class_ix)

        if warnings:
            return json.dumps({
                "drug_a": drug_a, "drug_b": drug_b,
                "found": True,
                "severity": "moderate",
                "description": f"Class-level interaction noted: {'; '.join(warnings)}",
                "action": "Review and monitor carefully. Consider alternatives if high risk.",
                "evidence": "Drug class interaction — consult BNF or Lexicomp for full detail.",
            }, indent=2)

        return json.dumps({
            "drug_a": drug_a, "drug_b": drug_b,
            "found": False,
            "severity": "unknown",
            "message": (
                "No specific interaction found in local database. "
                "This does not exclude an interaction — verify with BNF, Lexicomp or Micromedex."
            ),
        }, indent=2)

    return json.dumps({
        "drug_a": drug_a, "drug_b": drug_b,
        "found": True,
        **ix,
    }, indent=2)


@mcp.tool()
def check_allergy_alert(
    drug_name: str,
    patient_allergies: list[str],
) -> str:
    """
    Check if a drug is contraindicated given a patient's allergy list.

    Args:
        drug_name: Name of the drug to prescribe.
        patient_allergies: List of allergen names from patient record.

    Returns:
        JSON with alert status, matched allergens, and clinical advice.
    """
    drug_lower = _normalise(drug_name)
    drug_class = ""
    drug = _find_drug(drug_name)
    if drug:
        drug_class = drug.get("class", "").lower()

    alerts = []
    for allergen in patient_allergies:
        allergy_lower = _normalise(allergen)
        # Direct name match
        if allergy_lower in drug_lower or drug_lower in allergy_lower:
            alerts.append({"allergen": allergen, "match_type": "direct", "severity": "CONTRAINDICATED"})
        # Class cross-reactivity
        cross_reactivities = {
            "penicillin": ["amoxicillin", "ampicillin", "flucloxacillin", "co-amoxiclav"],
            "sulfa": ["trimethoprim-sulfamethoxazole", "furosemide", "thiazide", "celecoxib"],
            "aspirin": ["nsaid", "ibuprofen", "naproxen", "diclofenac", "indomethacin"],
            "cephalosporin": ["cephalexin", "ceftriaxone", "cefalexin"],
        }
        for cross_trigger, cross_drugs in cross_reactivities.items():
            if cross_trigger in allergy_lower:
                for cd in cross_drugs:
                    if cd in drug_lower:
                        alerts.append({
                            "allergen": allergen,
                            "match_type": "cross_reactivity",
                            "severity": "HIGH_RISK",
                            "note": f"Cross-reactivity between {allergen} and {drug_name}",
                        })

    if alerts:
        return json.dumps({
            "drug_name": drug_name,
            "alert": True,
            "alerts": alerts,
            "recommendation": (
                f"⚠️ ALLERGY ALERT: Do NOT prescribe {drug_name} — "
                f"patient has documented allergy to related substance. "
                "Select an alternative and document decision."
            ),
        }, indent=2)

    return json.dumps({
        "drug_name": drug_name,
        "alert": False,
        "message": f"No allergy alert for {drug_name} against provided allergy list.",
        "allergies_checked": patient_allergies,
    }, indent=2)


@mcp.tool()
def get_contraindications(
    drug_name: str,
    egfr: float = 90.0,
    has_liver_disease: bool = False,
    is_pregnant: bool = False,
    comorbidities: list[str] | None = None,
) -> str:
    """
    Check contraindications for a drug given a patient's clinical context.

    Args:
        drug_name: Name of the drug.
        egfr: Estimated GFR in mL/min/1.73m² (default 90 = normal).
        has_liver_disease: True if patient has significant hepatic impairment.
        is_pregnant: True if patient is pregnant.
        comorbidities: List of active medical conditions.

    Returns:
        JSON with contraindications found, warnings, and safe alternatives.
    """
    drug = _find_drug(drug_name)
    if not drug:
        return json.dumps({"found": False, "drug_name": drug_name})

    comorbidities = comorbidities or []
    comorbidities_lower = [c.lower() for c in comorbidities]

    triggered = []
    warnings = []

    # Renal check
    if drug.get("renal_adjustment") and egfr < 30:
        triggered.append(f"eGFR {egfr:.0f} mL/min — CONTRAINDICATED: {drug.get('renal_note', '')}")
    elif drug.get("renal_adjustment") and egfr < 45:
        warnings.append(f"eGFR {egfr:.0f} mL/min — DOSE REDUCTION required: {drug.get('renal_note', '')}")

    # Hepatic check
    if drug.get("hepatic_adjustment") and has_liver_disease:
        warnings.append(f"Hepatic impairment — CAUTION: {drug.get('hepatic_note', '')}")

    # Pregnancy check
    if is_pregnant:
        preg_ci = [ci for ci in drug.get("contraindications", []) if "pregnan" in ci.lower()]
        if preg_ci:
            triggered.append(f"Pregnancy — CONTRAINDICATED: {'; '.join(preg_ci)}")

    # Comorbidity checks
    for ci in drug.get("contraindications", []):
        ci_lower = ci.lower()
        for comorbidity in comorbidities_lower:
            if any(word in ci_lower for word in comorbidity.split()[:2]):
                triggered.append(f"Active comorbidity '{comorbidity}' triggers: {ci}")

    return json.dumps({
        "drug_name": drug_name,
        "drug_class": drug.get("class"),
        "absolute_contraindications": triggered,
        "warnings": warnings,
        "safe": len(triggered) == 0,
        "monitoring_required": drug.get("monitoring", []),
    }, indent=2)


@mcp.tool()
def get_dosage_guidance(
    drug_name: str,
    indication: str,
    egfr: float = 90.0,
    has_liver_disease: bool = False,
    age: int = 50,
) -> str:
    """
    Provide dosage guidance for a drug, adjusting for renal and hepatic function.

    Args:
        drug_name: Name of the drug.
        indication: The clinical indication for prescribing.
        egfr: Estimated GFR in mL/min/1.73m².
        has_liver_disease: True if significant hepatic impairment.
        age: Patient age in years.

    Returns:
        JSON with recommended dose, adjustment rationale, and titration plan.
    """
    drug = _find_drug(drug_name)
    if not drug:
        return json.dumps({"found": False, "drug_name": drug_name})

    doses = drug.get("standard_doses", ["Refer to BNF/local formulary"])
    recommended = doses[0]  # Start low
    rationale = []
    titration = f"Start at {doses[0]}"

    if len(doses) > 1:
        titration += f"; titrate to {doses[-1]} based on response and tolerance"

    # Renal adjustment
    if drug.get("renal_adjustment"):
        if egfr < 30:
            recommended = "CONTRAINDICATED"
            rationale.append(f"Contraindicated: eGFR {egfr:.0f} < 30 ({drug.get('renal_note')})")
        elif egfr < 45:
            recommended = doses[0]  # Keep lowest dose
            rationale.append(f"Reduced dose: eGFR {egfr:.0f} requires adjustment ({drug.get('renal_note')})")
        else:
            rationale.append(f"eGFR {egfr:.0f} — standard dosing appropriate")

    # Hepatic adjustment
    if drug.get("hepatic_adjustment") and has_liver_disease:
        recommended = doses[0]
        rationale.append(f"Hepatic impairment — conservative dosing: {drug.get('hepatic_note')}")

    # Age adjustment
    if age >= 75:
        recommended = doses[0]
        rationale.append("Age ≥75: Start at lowest dose, titrate slowly, monitor closely")

    return json.dumps({
        "drug_name": drug_name,
        "indication": indication,
        "recommended_starting_dose": recommended,
        "available_doses": doses,
        "titration_plan": titration,
        "rationale": rationale,
        "monitoring": drug.get("monitoring", []),
        "max_dose": f"{drug.get('max_dose_mg_day')} mg/day" if drug.get("max_dose_mg_day") else "See BNF",
    }, indent=2)


# ─── MCP Resources ────────────────────────────────────────────────────────────

@mcp.resource("drug://catalogue")
def list_available_drugs() -> str:
    """List all drugs in the local knowledge base."""
    return json.dumps({
        "total": len(DRUG_DB),
        "drugs": [{"key": k, "name": v["name"], "class": v["class"]} for k, v in DRUG_DB.items()],
    }, indent=2)


@mcp.resource("drug://interactions/summary")
def list_known_interactions() -> str:
    """List all known drug-drug interactions in the database."""
    return json.dumps({
        "total": len(INTERACTIONS),
        "interactions": [
            {
                "drug_a": ix["drug_a"], "drug_b": ix["drug_b"],
                "severity": ix["severity"],
            }
            for ix in INTERACTIONS
        ],
    }, indent=2)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Drug MCP Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"])
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse", port=args.port)
    else:
        mcp.run(transport="stdio")
