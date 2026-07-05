"""
MCP Server 2: Patient Data Service
Port: 8002

Provides structured patient record access to AI agents, including:
  - get_patient_summary     : Compact clinical summary for LLM context
  - get_patient_risk_history: Prior debate/risk records for a patient
  - get_abnormal_labs       : Flagged lab results
  - get_medication_list     : Active medications with adherence data
  - get_vitals_trend        : Vital sign history + BP category
  - get_comorbidity_burden  : Condition count + complexity score

The server reads from the SQLite database used by the FastAPI backend.
"""
import asyncio
import json
import os
import sys
from typing import Any, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="patient-service",
    instructions=(
        "Provides read-only structured access to patient clinical records "
        "from the Medical Digital Twin database."
    ),
)

# ─── Database helpers ─────────────────────────────────────────────────────────

def _get_db_path() -> str:
    """Resolve the SQLite database path."""
    from config.settings import settings
    url = settings.database_url  # e.g. sqlite+aiosqlite:///./data/medical_ai.db
    # Strip the async driver prefix and make absolute
    path = url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
    if path.startswith("."):
        path = os.path.join(ROOT, path[2:])
    return path


def _query_sync(query: str, params: tuple = ()) -> list[dict]:
    """Execute a synchronous SQLite query and return rows as dicts."""
    import sqlite3
    db_path = _get_db_path()
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _age_from_dob(dob_str: str) -> Optional[int]:
    """Calculate age from ISO date string."""
    if not dob_str:
        return None
    from datetime import date
    try:
        dob = date.fromisoformat(str(dob_str)[:10])
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return None


def _bmi(height_cm: Any, weight_kg: Any) -> Optional[float]:
    try:
        h, w = float(height_cm), float(weight_kg)
        if h > 0 and w > 0:
            return round(w / (h / 100) ** 2, 1)
    except (TypeError, ValueError, ZeroDivisionError):
        pass
    return None


# ─── MCP Tools ───────────────────────────────────────────────────────────────

@mcp.tool()
def get_patient_summary(patient_id: str) -> str:
    """
    Get a concise clinical summary for a patient suitable for LLM context.

    Args:
        patient_id: UUID of the patient.

    Returns:
        JSON with demographics, conditions, medications, allergies, latest vitals,
        and abnormal labs — formatted for agent consumption.
    """
    # Patient base
    patients = _query_sync("SELECT * FROM patients WHERE id = ?", (patient_id,))
    if not patients:
        return json.dumps({"found": False, "patient_id": patient_id})
    p = patients[0]

    # Conditions
    conditions = _query_sync(
        "SELECT name, icd10_code, severity, status FROM conditions WHERE patient_id = ?",
        (patient_id,),
    )
    active_conditions = [c["name"] for c in conditions if c.get("status") in ("active", "chronic")]

    # Medications
    medications = _query_sync(
        "SELECT name, strength, frequency, indication FROM medications WHERE patient_id = ? AND is_active = 1",
        (patient_id,),
    )

    # Allergies
    allergies = _query_sync(
        "SELECT allergen, allergen_type, reaction, severity FROM allergies WHERE patient_id = ?",
        (patient_id,),
    )

    # Latest vitals
    vitals = _query_sync(
        "SELECT * FROM vitals WHERE patient_id = ? ORDER BY measured_at DESC LIMIT 1",
        (patient_id,),
    )
    v = vitals[0] if vitals else {}

    # Latest labs (abnormal only)
    labs = _query_sync(
        "SELECT test_name, value, unit, flag FROM lab_reports WHERE patient_id = ? "
        "AND flag IN ('H','L','HH','LL') ORDER BY collected_at DESC LIMIT 10",
        (patient_id,),
    )

    age = _age_from_dob(p.get("date_of_birth"))
    bmi = _bmi(v.get("height_cm"), v.get("weight_kg"))

    return json.dumps({
        "found": True,
        "patient_id": patient_id,
        "demographics": {
            "name": f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
            "age": age,
            "gender": p.get("gender"),
            "blood_type": p.get("blood_type"),
        },
        "vitals": {
            "bp": f"{v.get('systolic_bp')}/{v.get('diastolic_bp')} mmHg" if v.get("systolic_bp") else None,
            "heart_rate": v.get("heart_rate"),
            "bmi": bmi,
            "spo2": v.get("oxygen_saturation"),
        },
        "active_conditions": active_conditions,
        "all_conditions": [dict(c) for c in conditions],
        "active_medications": [
            f"{m['name']} {m.get('strength', '')} {m.get('frequency', '')}".strip()
            for m in medications
        ],
        "allergies": [a["allergen"] for a in allergies],
        "abnormal_labs": [
            f"{l['test_name']}: {l['value']} {l.get('unit', '')} [{l.get('flag', '')}]"
            for l in labs
        ],
        "data_source": "medtwin_sqlite",
    }, indent=2)


@mcp.tool()
def get_patient_risk_history(patient_id: str, limit: int = 5) -> str:
    """
    Retrieve past debate and risk assessment records for a patient.

    Args:
        patient_id: UUID of the patient.
        limit: Max number of records to return (default 5).

    Returns:
        JSON list of past debate summaries with risk scores and dates.
    """
    debates = _query_sync(
        "SELECT id, predicted_risk, final_consensus_report, created_at "
        "FROM debates WHERE patient_id = ? ORDER BY created_at DESC LIMIT ?",
        (patient_id, limit),
    )
    if not debates:
        return json.dumps({
            "patient_id": patient_id,
            "found": False,
            "message": "No prior debate records found for this patient.",
        })

    return json.dumps({
        "patient_id": patient_id,
        "found": True,
        "total_debates": len(debates),
        "debates": [
            {
                "id": d["id"],
                "predicted_risk": round(float(d["predicted_risk"]) * 100, 1),
                "created_at": str(d["created_at"]),
                "consensus_preview": (d.get("final_consensus_report") or "")[:300] + "...",
            }
            for d in debates
        ],
    }, indent=2)


@mcp.tool()
def get_abnormal_labs(patient_id: str, critical_only: bool = False) -> str:
    """
    Retrieve abnormal laboratory results for a patient.

    Args:
        patient_id: UUID of the patient.
        critical_only: If True, only return critical values (HH or LL flags).

    Returns:
        JSON list of abnormal lab results with clinical interpretation.
    """
    flag_filter = "('HH', 'LL')" if critical_only else "('H', 'L', 'HH', 'LL', 'A')"
    labs = _query_sync(
        f"SELECT test_name, value, unit, flag, reference_range_low, reference_range_high, "
        f"collected_at FROM lab_reports WHERE patient_id = ? AND flag IN {flag_filter} "
        f"ORDER BY collected_at DESC",
        (patient_id,),
    )

    if not labs:
        return json.dumps({
            "patient_id": patient_id,
            "found": False,
            "message": "No abnormal lab values found.",
        })

    def interpret(flag: str) -> str:
        return {"H": "High", "L": "Low", "HH": "Critically High", "LL": "Critically Low",
                "A": "Abnormal"}.get(flag or "", "Abnormal")

    return json.dumps({
        "patient_id": patient_id,
        "critical_only": critical_only,
        "total": len(labs),
        "results": [
            {
                "test": l["test_name"],
                "value": l["value"],
                "unit": l.get("unit", ""),
                "flag": l.get("flag", ""),
                "interpretation": interpret(l.get("flag", "")),
                "ref_range": f"{l.get('reference_range_low', '?')}–{l.get('reference_range_high', '?')}",
                "collected_at": str(l.get("collected_at", "")),
            }
            for l in labs
        ],
    }, indent=2)


@mcp.tool()
def get_medication_list(patient_id: str, active_only: bool = True) -> str:
    """
    Get a structured list of patient medications.

    Args:
        patient_id: UUID of the patient.
        active_only: If True, only return currently active medications.

    Returns:
        JSON list with medication name, dose, frequency, indication, and start date.
    """
    active_clause = "AND is_active = 1" if active_only else ""
    meds = _query_sync(
        f"SELECT name, generic_name, strength, route, frequency, indication, "
        f"start_date, end_date, is_active FROM medications "
        f"WHERE patient_id = ? {active_clause} ORDER BY start_date",
        (patient_id,),
    )

    return json.dumps({
        "patient_id": patient_id,
        "active_only": active_only,
        "total": len(meds),
        "medications": [dict(m) for m in meds],
    }, indent=2)


@mcp.tool()
def get_comorbidity_burden(patient_id: str) -> str:
    """
    Calculate the comorbidity burden and complexity score for a patient.

    Provides Charlson Comorbidity Index (CCI) estimation and identifies
    high-risk condition clusters.

    Args:
        patient_id: UUID of the patient.

    Returns:
        JSON with CCI score, condition count, complexity category, and flags.
    """
    conditions = _query_sync(
        "SELECT name, severity, status FROM conditions WHERE patient_id = ?",
        (patient_id,),
    )
    active = [c for c in conditions if c.get("status") in ("active", "chronic")]

    # Simplified CCI mapping
    cci_map = {
        "myocardial infarction": 1, "congestive heart failure": 1, "peripheral vascular": 1,
        "cerebrovascular": 1, "stroke": 1, "dementia": 1, "chronic pulmonary": 1, "copd": 1,
        "connective tissue": 1, "rheumatoid": 1, "peptic ulcer": 1, "mild liver": 1,
        "diabetes": 1, "hemi": 2, "paraple": 2, "renal": 2, "kidney": 2,
        "moderate liver": 3, "severe liver": 3, "metastatic": 6, "cancer": 2, "tumor": 2,
        "aids": 6, "hiv": 6,
    }

    cci_score = 0
    matched = []
    for cond in active:
        name_lower = cond["name"].lower()
        for keyword, weight in cci_map.items():
            if keyword in name_lower:
                cci_score += weight
                matched.append({"condition": cond["name"], "cci_weight": weight, "keyword": keyword})
                break

    # Complexity category
    if cci_score == 0:
        complexity = "low"
    elif cci_score <= 2:
        complexity = "moderate"
    elif cci_score <= 4:
        complexity = "high"
    else:
        complexity = "very_high"

    # 10-year mortality estimate from CCI (simplified)
    mortality_estimates = {0: "~10%", 1: "~26%", 2: "~52%", 3: "~85%", 4: "~85%"}
    mortality_10yr = mortality_estimates.get(min(cci_score, 4), ">85%")

    # High-risk flags
    flags = []
    condition_names_lower = [c["name"].lower() for c in active]
    if any("diabetes" in n for n in condition_names_lower) and any("heart" in n or "cardiac" in n for n in condition_names_lower):
        flags.append("⚠️ Diabetes + CVD combination — high CV risk")
    if any("kidney" in n or "renal" in n for n in condition_names_lower):
        flags.append("⚠️ Renal impairment — drug dose adjustment required")
    if len(active) >= 5:
        flags.append(f"⚠️ Multimorbidity ({len(active)} conditions) — polypharmacy risk")

    return json.dumps({
        "patient_id": patient_id,
        "total_conditions": len(conditions),
        "active_conditions": len(active),
        "charlson_comorbidity_index": cci_score,
        "complexity_category": complexity,
        "estimated_10yr_mortality": mortality_10yr,
        "cci_contributions": matched,
        "clinical_flags": flags,
    }, indent=2)


@mcp.tool()
def get_vitals_trend(patient_id: str, limit: int = 10) -> str:
    """
    Retrieve vital sign history for trend analysis.

    Args:
        patient_id: UUID of the patient.
        limit: Number of historical readings (default 10).

    Returns:
        JSON with time-series vitals and BP categorisation per ACC/AHA guidelines.
    """
    vitals = _query_sync(
        "SELECT systolic_bp, diastolic_bp, heart_rate, oxygen_saturation, "
        "temperature_c, weight_kg, height_cm, measured_at "
        "FROM vitals WHERE patient_id = ? ORDER BY measured_at DESC LIMIT ?",
        (patient_id, limit),
    )
    if not vitals:
        return json.dumps({"patient_id": patient_id, "found": False, "message": "No vitals recorded."})

    def bp_category(sbp, dbp) -> str:
        if sbp is None or dbp is None:
            return "unknown"
        sbp, dbp = float(sbp), float(dbp)
        if sbp < 120 and dbp < 80:
            return "Normal"
        elif sbp < 130 and dbp < 80:
            return "Elevated"
        elif sbp < 140 or dbp < 90:
            return "Stage 1 HTN"
        else:
            return "Stage 2 HTN"

    readings = []
    for v in vitals:
        readings.append({
            "measured_at": str(v.get("measured_at", "")),
            "systolic_bp": v.get("systolic_bp"),
            "diastolic_bp": v.get("diastolic_bp"),
            "bp_category": bp_category(v.get("systolic_bp"), v.get("diastolic_bp")),
            "heart_rate": v.get("heart_rate"),
            "spo2": v.get("oxygen_saturation"),
            "temp_c": v.get("temperature_c"),
            "bmi": _bmi(v.get("height_cm"), v.get("weight_kg")),
        })

    return json.dumps({
        "patient_id": patient_id,
        "found": True,
        "readings_count": len(readings),
        "vitals_history": readings,
        "latest": readings[0] if readings else None,
    }, indent=2)


# ─── MCP Resources ────────────────────────────────────────────────────────────

@mcp.resource("patients://count")
def patient_count() -> str:
    """Return total number of patients in the database."""
    rows = _query_sync("SELECT COUNT(*) as count FROM patients")
    count = rows[0]["count"] if rows else 0
    return json.dumps({"total_patients": count})


@mcp.resource("patients://schema")
def patient_schema() -> str:
    """Return the patient data schema for agent context."""
    return json.dumps({
        "tables": ["patients", "conditions", "allergies", "medications", "lab_reports", "vitals", "debates"],
        "patient_fields": ["id", "first_name", "last_name", "date_of_birth", "gender", "blood_type"],
        "vitals_fields": ["systolic_bp", "diastolic_bp", "heart_rate", "oxygen_saturation", "height_cm", "weight_kg"],
        "lab_flags": {"H": "High", "L": "Low", "HH": "Critically High", "LL": "Critically Low", "N": "Normal"},
    })


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Patient MCP Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"])
    parser.add_argument("--port", type=int, default=8002)
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse", port=args.port)
    else:
        mcp.run(transport="stdio")
