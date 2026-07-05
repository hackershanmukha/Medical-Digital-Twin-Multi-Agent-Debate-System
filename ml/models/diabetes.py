"""
Diabetes Risk Prediction Model using XGBoost.

Predicts probability of Type 2 Diabetes onset or poor glycemic control
based on metabolic, lifestyle, and demographic features.
"""
from dataclasses import dataclass
from typing import Any, Optional
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from pathlib import Path

from config.settings import settings
from digital_twin.models import (
    PatientDigitalTwin,
    DiabetesRiskFactors,
    Gender,
    ActivityLevel,
)


@dataclass
class DiabetesFeatures:
    """
    Feature set for diabetes risk prediction.

    Based on ADA risk factors and FINDRISC score with ML enhancement.
    """
    # Demographics
    age: float
    gender_female: float  # 1 for female (higher risk in some studies)

    # Anthropometric
    bmi: float
    waist_circumference: Optional[float] = None

    # Metabolic Labs
    fasting_glucose: Optional[float] = None   # mg/dL
    hba1c: Optional[float] = None             # %
    triglycerides: Optional[float] = None     # mg/dL
    hdl_cholesterol: Optional[float] = None   # mg/dL

    # Blood Pressure
    systolic_bp: Optional[float] = None

    # Lifestyle
    activity_level: float = 0.0          # 0=sedentary → 4=very_active
    fruit_veg_servings: float = 0.0      # daily servings (diet quality proxy)
    sleep_hours: float = 7.0

    # Risk Factors
    family_history_diabetes: float = 0.0
    gestational_diabetes: float = 0.0
    pcos: float = 0.0
    hypertension: float = 0.0
    on_bp_medication: float = 0.0
    has_prediabetes: float = 0.0         # IFG or IGT

    def to_array(self) -> np.ndarray:
        """Convert to numpy array for model input."""
        features = [
            self.age,
            self.gender_female,
            self.bmi,
            self.waist_circumference if self.waist_circumference is not None else self.bmi * 3.0,
            self.fasting_glucose if self.fasting_glucose is not None else 90.0,
            self.hba1c if self.hba1c is not None else 5.2,
            self.triglycerides if self.triglycerides is not None else 120.0,
            self.hdl_cholesterol if self.hdl_cholesterol is not None else 55.0,
            self.systolic_bp if self.systolic_bp is not None else 120.0,
            self.activity_level,
            self.fruit_veg_servings,
            self.sleep_hours,
            self.family_history_diabetes,
            self.gestational_diabetes,
            self.pcos,
            self.hypertension,
            self.on_bp_medication,
            self.has_prediabetes,
        ]
        return np.array(features).reshape(1, -1)

    def to_dict(self) -> dict[str, float]:
        return {
            "age": self.age,
            "gender_female": self.gender_female,
            "bmi": self.bmi,
            "waist_circumference": self.waist_circumference or self.bmi * 3.0,
            "fasting_glucose": self.fasting_glucose or 90.0,
            "hba1c": self.hba1c or 5.2,
            "triglycerides": self.triglycerides or 120.0,
            "hdl_cholesterol": self.hdl_cholesterol or 55.0,
            "systolic_bp": self.systolic_bp or 120.0,
            "activity_level": self.activity_level,
            "fruit_veg_servings": self.fruit_veg_servings,
            "sleep_hours": self.sleep_hours,
            "family_history_diabetes": self.family_history_diabetes,
            "gestational_diabetes": self.gestational_diabetes,
            "pcos": self.pcos,
            "hypertension": self.hypertension,
            "on_bp_medication": self.on_bp_medication,
            "has_prediabetes": self.has_prediabetes,
        }

    @classmethod
    def feature_names(cls) -> list[str]:
        return [
            "age", "gender_female", "bmi", "waist_circumference",
            "fasting_glucose", "hba1c", "triglycerides", "hdl_cholesterol",
            "systolic_bp", "activity_level", "fruit_veg_servings", "sleep_hours",
            "family_history_diabetes", "gestational_diabetes", "pcos",
            "hypertension", "on_bp_medication", "has_prediabetes",
        ]


class DiabetesModel:
    """
    XGBoost-based Diabetes Risk Prediction Model.

    Predicts 5-year risk of Type 2 Diabetes onset.
    Also flags prediabetes and provides actionable recommendations.
    """

    MODEL_VERSION = "1.0.0"
    FEATURE_COUNT = 18

    def __init__(self, model_path: Optional[str] = None):
        self.model: Optional[xgb.XGBClassifier] = None
        self.model_path = model_path or str(settings.models_dir / settings.ml_diabetes_model)
        self.is_trained = False
        self.feature_importance: dict[str, float] = {}
        self.training_metrics: dict[str, float] = {}

    def build_model(self, **params) -> xgb.XGBClassifier:
        default_params = {
            "n_estimators": 200,
            "max_depth": 5,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_weight": 3,
            "gamma": 0.1,
            "scale_pos_weight": 2.5,   # Diabetes class imbalance
            "objective": "binary:logistic",
            "eval_metric": "auc",
            "random_state": 42,
            "n_jobs": -1,
            "verbosity": 0,
        }
        default_params.update(params)
        return xgb.XGBClassifier(**default_params)

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        **params,
    ) -> dict[str, float]:
        from sklearn.metrics import roc_auc_score, accuracy_score, f1_score

        self.model = self.build_model(**params)
        eval_set = [(X, y)]
        if X_val is not None and y_val is not None:
            eval_set.append((X_val, y_val))

        self.model.fit(X, y, eval_set=eval_set, verbose=False)

        self.feature_importance = dict(
            zip(DiabetesFeatures.feature_names(), self.model.feature_importances_)
        )

        y_proba = self.model.predict_proba(X)[:, 1]
        y_pred = (y_proba >= 0.5).astype(int)
        self.training_metrics = {
            "train_auc": roc_auc_score(y, y_proba),
            "train_accuracy": accuracy_score(y, y_pred),
            "train_f1": f1_score(y, y_pred, zero_division=0),
        }
        self.is_trained = True
        return self.training_metrics

    def predict_proba(self, features: DiabetesFeatures) -> float:
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained. Call train() or load() first.")
        X = features.to_array()
        return float(self.model.predict_proba(X)[0, 1])

    def predict_from_digital_twin(self, twin: PatientDigitalTwin) -> dict[str, Any]:
        features = self._extract_features(twin)
        risk_score = self.predict_proba(features)
        risk_category = self._categorize_risk(risk_score)

        # Compute traditional FINDRISC-inspired score
        findrisc = self._compute_findrisc(twin)

        return {
            "patient_id": twin.patient_id,
            "risk_score": risk_score,
            "risk_category": risk_category,
            "risk_percentage": round(risk_score * 100, 1),
            "findrisc_score": findrisc,
            "model_version": self.MODEL_VERSION,
            "features_used": features.to_dict(),
            "feature_importance": self.feature_importance,
        }

    def _extract_features(self, twin: PatientDigitalTwin) -> DiabetesFeatures:
        dm_factors = DiabetesRiskFactors.from_digital_twin(twin)

        activity_map = {
            "sedentary": 0.0, "light": 1.0, "moderate": 2.0,
            "active": 3.0, "very_active": 4.0,
        }

        has_htn = twin.medical_history.has_condition("hypertension")
        on_bp_med = any(
            "hypertension" in (m.indication or "").lower()
            for m in twin.active_medications
        )
        has_prediabetes = (
            twin.medical_history.has_condition("prediabetes") or
            twin.medical_history.has_condition("impaired fasting")
        )

        return DiabetesFeatures(
            age=float(dm_factors.age),
            gender_female=1.0 if dm_factors.gender == Gender.FEMALE else 0.0,
            bmi=dm_factors.bmi or 25.0,
            waist_circumference=twin.vitals.waist_circumference_cm,
            fasting_glucose=dm_factors.fasting_glucose,
            hba1c=dm_factors.hba1c,
            triglycerides=dm_factors.triglycerides,
            hdl_cholesterol=dm_factors.hdl_cholesterol,
            systolic_bp=dm_factors.systolic_bp,
            activity_level=activity_map.get(twin.lifestyle.activity_level.value, 0.0),
            fruit_veg_servings=float(
                twin.lifestyle.fruit_servings_per_day + twin.lifestyle.vegetable_servings_per_day
            ),
            sleep_hours=twin.lifestyle.sleep_hours_per_night or 7.0,
            family_history_diabetes=1.0 if dm_factors.family_history_diabetes else 0.0,
            gestational_diabetes=1.0 if dm_factors.gestational_diabetes else 0.0,
            pcos=1.0 if dm_factors.pcos else 0.0,
            hypertension=1.0 if has_htn else 0.0,
            on_bp_medication=1.0 if on_bp_med else 0.0,
            has_prediabetes=1.0 if has_prediabetes else 0.0,
        )

    def _categorize_risk(self, risk_score: float) -> str:
        if risk_score < 0.05:
            return "very_low"
        elif risk_score < 0.10:
            return "low"
        elif risk_score < 0.20:
            return "moderate"
        elif risk_score < 0.35:
            return "high"
        else:
            return "very_high"

    def _compute_findrisc(self, twin: PatientDigitalTwin) -> int:
        """Simplified FINDRISC score (0-26 scale)."""
        score = 0
        # Age
        if twin.age >= 45 and twin.age < 55:
            score += 2
        elif twin.age >= 55 and twin.age < 65:
            score += 3
        elif twin.age >= 65:
            score += 4
        # BMI
        bmi = twin.bmi or 25.0
        if 25 <= bmi < 30:
            score += 1
        elif bmi >= 30:
            score += 3
        # Waist circumference
        wc = twin.vitals.waist_circumference_cm
        if wc:
            if wc >= 94 and twin.demographics.gender.value == "male":
                score += 3
            elif wc >= 80 and twin.demographics.gender.value == "female":
                score += 3
        # Activity
        if twin.lifestyle.activity_level.value == "sedentary":
            score += 2
        # Diet (fruit/veg)
        servings = twin.lifestyle.fruit_servings_per_day + twin.lifestyle.vegetable_servings_per_day
        if servings < 3:
            score += 1
        # BP medication
        if any("hypertension" in (m.indication or "").lower() for m in twin.active_medications):
            score += 2
        # Family history
        if twin.family_history.has_condition("diabetes"):
            score += 5
        return score

    def save(self, path: Optional[str] = None) -> None:
        if not self.is_trained or self.model is None:
            raise ValueError("No trained model to save.")
        save_path = Path(path or self.model_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "model": self.model,
            "feature_importance": self.feature_importance,
            "training_metrics": self.training_metrics,
            "model_version": self.MODEL_VERSION,
        }, save_path)

    def load(self, path: Optional[str] = None) -> "DiabetesModel":
        load_path = Path(path or self.model_path)
        if not load_path.exists():
            raise FileNotFoundError(f"Model file not found: {load_path}")
        data = joblib.load(load_path)
        self.model = data["model"]
        self.feature_importance = data.get("feature_importance", {})
        self.training_metrics = data.get("training_metrics", {})
        self.is_trained = True
        return self
