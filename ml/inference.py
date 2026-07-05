"""
Unified ML Inference Engine.

Trains (on synthetic data) and runs all three risk models:
  - HeartDiseaseModel  (cardiovascular risk)
  - DiabetesModel      (metabolic / T2DM risk)
  - RiskModel          (composite multi-domain)

Also provides SHAP-based explanations for any prediction.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

import numpy as np
from sklearn.model_selection import train_test_split

from config.settings import settings
from digital_twin.models import PatientDigitalTwin
from ml.models.heart_disease import HeartDiseaseModel, HeartDiseaseFeatures
from ml.models.diabetes import DiabetesModel, DiabetesFeatures
from ml.models.risk import RiskModel, RiskFeatures

logger = logging.getLogger(__name__)

# ─── Singleton instances ─────────────────────────────────────────────────────

_heart_model: Optional[HeartDiseaseModel] = None
_diabetes_model: Optional[DiabetesModel] = None
_risk_model: Optional[RiskModel] = None


def get_models() -> tuple[HeartDiseaseModel, DiabetesModel, RiskModel]:
    """Return (or initialise) the three singleton model instances."""
    global _heart_model, _diabetes_model, _risk_model

    if _heart_model is None:
        _heart_model = _load_or_train(HeartDiseaseModel, "heart")
    if _diabetes_model is None:
        _diabetes_model = _load_or_train(DiabetesModel, "diabetes")
    if _risk_model is None:
        _risk_model = _load_or_train(RiskModel, "risk")

    return _heart_model, _diabetes_model, _risk_model


def _load_or_train(ModelClass, tag: str):
    """Try to load a pre-trained model; train on synthetic data if missing."""
    model = ModelClass()
    try:
        model.load()
        logger.info(f"[inference] Loaded {tag} model from disk.")
    except FileNotFoundError:
        logger.info(f"[inference] No saved {tag} model found — training on synthetic data …")
        _train_synthetic(model, tag)
        model.save()
        logger.info(f"[inference] {tag} model trained and saved.")
    return model


# ─── Synthetic data generation ───────────────────────────────────────────────

def _train_synthetic(model, tag: str) -> None:
    """
    Generate clinically plausible synthetic training data and train the model.
    Uses stratified sampling so all risk strata are represented.
    """
    rng = np.random.RandomState(42)
    N = 5_000   # enough for a demo-quality model

    if tag == "heart":
        X, y = _make_heart_data(rng, N)
    elif tag == "diabetes":
        X, y = _make_diabetes_data(rng, N)
    else:
        X, y = _make_risk_data(rng, N)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    metrics = model.train(X_train, y_train, X_val, y_val)
    logger.info(f"[inference] {tag} train metrics: {metrics}")


def _make_heart_data(rng: np.random.RandomState, N: int):
    """Generate synthetic cardiovascular risk data."""
    age = rng.uniform(30, 80, N)
    gender_male = rng.randint(0, 2, N).astype(float)
    sbp = rng.normal(130, 20, N).clip(80, 220)
    dbp = rng.normal(80, 12, N).clip(50, 130)
    on_bp_tx = (sbp > 145).astype(float)
    tc = rng.normal(195, 35, N).clip(120, 350)
    hdl = rng.normal(52, 14, N).clip(25, 100)
    ldl = rng.normal(115, 30, N).clip(50, 250)
    trig = rng.normal(135, 50, N).clip(50, 400)
    has_dm = (rng.random(N) < 0.15).astype(float)
    fg = np.where(has_dm, rng.normal(145, 30, N), rng.normal(90, 12, N)).clip(60, 350)
    hba1c = np.where(has_dm, rng.normal(8.0, 1.5, N), rng.normal(5.3, 0.4, N)).clip(4.0, 14.0)
    bmi = rng.normal(27, 5, N).clip(15, 50)
    smoker = (rng.random(N) < 0.22).astype(float)
    pack_years = smoker * rng.exponential(10, N)
    activity = rng.randint(0, 5, N).astype(float)
    fh_cvd = (rng.random(N) < 0.30).astype(float)
    hr = rng.normal(72, 12, N).clip(45, 120)
    wc = bmi * rng.normal(3.2, 0.3, N)
    egfr = rng.normal(80, 20, N).clip(20, 120)

    X = np.column_stack([
        age, gender_male, sbp, dbp, on_bp_tx,
        tc, hdl, ldl, trig, has_dm, fg, hba1c, bmi,
        smoker, pack_years, activity, fh_cvd, hr, wc, egfr,
    ])

    # Clinically motivated label
    risk_score = (
        0.012 * age +
        0.008 * gender_male * 10 +
        0.006 * (sbp - 120) +
        0.005 * (tc - 200) / 10 -
        0.008 * (hdl - 50) / 10 +
        0.020 * has_dm +
        0.025 * smoker +
        0.010 * fh_cvd +
        rng.normal(0, 0.05, N)
    )
    y = (risk_score > risk_score.mean()).astype(int)
    return X, y


def _make_diabetes_data(rng: np.random.RandomState, N: int):
    age = rng.uniform(25, 75, N)
    gender_female = rng.randint(0, 2, N).astype(float)
    bmi = rng.normal(28, 6, N).clip(15, 55)
    wc = bmi * rng.normal(3.1, 0.3, N)
    fg = rng.normal(98, 18, N).clip(60, 300)
    hba1c = rng.normal(5.5, 0.8, N).clip(4.0, 12.0)
    trig = rng.normal(145, 55, N).clip(50, 500)
    hdl = rng.normal(50, 14, N).clip(20, 90)
    sbp = rng.normal(128, 18, N).clip(80, 220)
    activity = rng.randint(0, 5, N).astype(float)
    fv_servings = rng.normal(3, 2, N).clip(0, 10)
    sleep = rng.normal(6.8, 1.2, N).clip(3, 12)
    fh_dm = (rng.random(N) < 0.35).astype(float)
    gdm = gender_female * (rng.random(N) < 0.10).astype(float)
    pcos = gender_female * (rng.random(N) < 0.10).astype(float)
    htn = (sbp > 140).astype(float)
    on_bp_med = htn * (rng.random(N) < 0.6).astype(float)
    has_pre = (fg > 100).astype(float) * (fg < 126).astype(float)

    X = np.column_stack([
        age, gender_female, bmi, wc, fg, hba1c, trig, hdl,
        sbp, activity, fv_servings, sleep,
        fh_dm, gdm, pcos, htn, on_bp_med, has_pre,
    ])

    risk_score = (
        0.010 * age +
        0.012 * (bmi - 25) +
        0.015 * (fg - 90) / 10 +
        0.040 * fh_dm +
        0.030 * has_pre -
        0.008 * activity +
        rng.normal(0, 0.05, N)
    )
    y = (risk_score > risk_score.mean()).astype(int)
    return X, y


def _make_risk_data(rng: np.random.RandomState, N: int):
    age = rng.uniform(25, 85, N)
    gender_male = rng.randint(0, 2, N).astype(float)
    bmi = rng.normal(27.5, 6, N).clip(15, 55)
    sbp = rng.normal(130, 22, N).clip(80, 220)
    dbp = rng.normal(80, 14, N).clip(50, 130)
    tc = rng.normal(195, 38, N).clip(100, 380)
    hdl = rng.normal(52, 14, N).clip(20, 100)
    ldl = rng.normal(115, 32, N).clip(40, 280)
    trig = rng.normal(138, 55, N).clip(40, 500)
    hr = rng.normal(72, 12, N).clip(45, 120)
    on_bp_tx = (sbp > 145).astype(float)
    fg = rng.normal(96, 20, N).clip(60, 400)
    hba1c = rng.normal(5.4, 0.9, N).clip(4.0, 14.0)
    has_dm = (hba1c > 6.5).astype(float)
    has_pre = ((hba1c >= 5.7) & (hba1c < 6.5)).astype(float)
    smoker = (rng.random(N) < 0.20).astype(float)
    pack_years = smoker * rng.exponential(9, N)
    activity = rng.randint(0, 5, N).astype(float)
    alc_heavy = (rng.random(N) < 0.08).astype(float)
    sleep = rng.normal(6.8, 1.2, N).clip(3, 12)
    num_conds = rng.randint(0, 6, N).astype(float)
    num_meds = (num_conds * rng.uniform(0.8, 2.0, N)).clip(0, 12)
    has_htn = (sbp > 140).astype(float)
    has_heart = (rng.random(N) < 0.10).astype(float)
    has_kidney = (rng.random(N) < 0.08).astype(float)
    has_dep = (rng.random(N) < 0.15).astype(float)
    has_copd = (rng.random(N) < 0.07).astype(float)
    fh_cvd = (rng.random(N) < 0.30).astype(float)
    fh_dm = (rng.random(N) < 0.32).astype(float)
    fh_cancer = (rng.random(N) < 0.20).astype(float)
    alone = (rng.random(N) < 0.18).astype(float)
    stress = (rng.random(N) < 0.25).astype(float)

    X = np.column_stack([
        age, gender_male, bmi,
        sbp, dbp, tc, hdl, ldl, trig, hr, on_bp_tx,
        fg, hba1c, has_dm, has_pre,
        smoker, pack_years, activity, alc_heavy, sleep,
        num_conds, num_meds, has_htn, has_heart, has_kidney, has_dep, has_copd,
        fh_cvd, fh_dm, fh_cancer,
        alone, stress,
    ])

    risk_score = (
        0.010 * age +
        0.008 * (sbp - 120) / 20 +
        0.010 * (bmi - 25) / 5 +
        0.015 * smoker +
        0.012 * has_dm +
        0.010 * num_conds / 5 +
        0.008 * fh_cvd -
        0.005 * activity / 4 +
        rng.normal(0, 0.04, N)
    )
    y = (risk_score > risk_score.mean()).astype(int)
    return X, y


# ─── Public Inference API ────────────────────────────────────────────────────

def predict_all_risks(twin: PatientDigitalTwin) -> dict[str, Any]:
    """
    Run all three risk models on a PatientDigitalTwin and return a
    comprehensive risk report.
    """
    heart_model, diabetes_model, risk_model = get_models()

    heart_result = heart_model.predict_from_digital_twin(twin)
    diabetes_result = diabetes_model.predict_from_digital_twin(twin)
    composite_result = risk_model.predict_from_digital_twin(twin)

    # SHAP-style attributions for the composite model
    attributions = {
        feat: round(float(importance), 4)
        for feat, importance in composite_result["feature_importance"].items()
    }

    return {
        "patient_id": twin.patient_id,
        "cardiovascular": {
            "risk_score": heart_result["risk_score"],
            "risk_category": heart_result["risk_category"],
            "risk_percentage": heart_result["risk_percentage"],
            "ascvd_10yr_risk": heart_result.get("ascvd_10yr_risk"),
        },
        "diabetes": {
            "risk_score": diabetes_result["risk_score"],
            "risk_category": diabetes_result["risk_category"],
            "risk_percentage": diabetes_result["risk_percentage"],
            "findrisc_score": diabetes_result.get("findrisc_score"),
        },
        "composite": {
            "risk_score": composite_result["risk_score"],
            "risk_category": composite_result["risk_category"],
            "risk_percentage": composite_result["risk_percentage"],
            "domain_scores": composite_result.get("domain_scores", {}),
        },
        "top_risk_factors": composite_result.get("top_risk_factors", []),
        "explanation_attributions": attributions,
        "predicted_risk": composite_result["risk_score"],  # canonical field for debate
    }
