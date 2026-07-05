"""
Heart Disease Prediction Model using XGBoost.

Predicts 10-year cardiovascular disease risk based on clinical features
including demographics, vitals, lab results, and lifestyle factors.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Optional
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from pathlib import Path

from config.settings import settings
from digital_twin.models import (
    PatientDigitalTwin,
    CardiovascularRiskFactors,
    Gender,
    SmokingStatus,
)


@dataclass
class HeartDiseaseFeatures:
    """
    Feature set for heart disease prediction.

    Based on Framingham Risk Score and ASCVD Pooled Cohort Equations
    with additional clinical variables for ML enhancement.
    """
    # Demographics (required)
    age: float
    gender_male: float  # 1 for male, 0 for female

    # Blood Pressure (required)
    systolic_bp: float
    diastolic_bp: float
    on_bp_treatment: float  # 1 if on antihypertensive treatment

    # Lipids (required)
    total_cholesterol: float
    hdl_cholesterol: float

    # Metabolic (required)
    has_diabetes: float
    smoker: float

    # Optional fields with defaults
    ldl_cholesterol: Optional[float] = None
    triglycerides: Optional[float] = None
    fasting_glucose: Optional[float] = None
    hba1c: Optional[float] = None
    bmi: Optional[float] = None

    # Lifestyle (with defaults)
    pack_years: float = 0.0
    activity_level: float = 0.0  # 0=sedentary, 1=light, 2=moderate, 3=active, 4=very_active

    # Family History
    family_history_premature_cvd: float = 0.0

    # Additional Clinical
    heart_rate: Optional[float] = None
    waist_circumference: Optional[float] = None
    egfr: Optional[float] = None  # Kidney function

    def to_array(self) -> np.ndarray:
        """Convert to numpy array for model input."""
        features = [
            self.age,
            self.gender_male,
            self.systolic_bp,
            self.diastolic_bp,
            self.on_bp_treatment,
            self.total_cholesterol,
            self.hdl_cholesterol,
            self.ldl_cholesterol if self.ldl_cholesterol is not None else 0.0,
            self.triglycerides if self.triglycerides is not None else 0.0,
            self.has_diabetes,
            self.fasting_glucose if self.fasting_glucose is not None else 0.0,
            self.hba1c if self.hba1c is not None else 0.0,
            self.bmi if self.bmi is not None else 0.0,
            self.smoker,
            self.pack_years,
            self.activity_level,
            self.family_history_premature_cvd,
            self.heart_rate if self.heart_rate is not None else 0.0,
            self.waist_circumference if self.waist_circumference is not None else 0.0,
            self.egfr if self.egfr is not None else 0.0,
        ]
        return np.array(features).reshape(1, -1)

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "age": self.age,
            "gender_male": self.gender_male,
            "systolic_bp": self.systolic_bp,
            "diastolic_bp": self.diastolic_bp,
            "on_bp_treatment": self.on_bp_treatment,
            "total_cholesterol": self.total_cholesterol,
            "hdl_cholesterol": self.hdl_cholesterol,
            "ldl_cholesterol": self.ldl_cholesterol or 0.0,
            "triglycerides": self.triglycerides or 0.0,
            "has_diabetes": self.has_diabetes,
            "fasting_glucose": self.fasting_glucose or 0.0,
            "hba1c": self.hba1c or 0.0,
            "bmi": self.bmi or 0.0,
            "smoker": self.smoker,
            "pack_years": self.pack_years,
            "activity_level": self.activity_level,
            "family_history_premature_cvd": self.family_history_premature_cvd,
            "heart_rate": self.heart_rate or 0.0,
            "waist_circumference": self.waist_circumference or 0.0,
            "egfr": self.egfr or 0.0,
        }

    @classmethod
    def feature_names(cls) -> list[str]:
        """Get ordered list of feature names."""
        return [
            "age", "gender_male", "systolic_bp", "diastolic_bp", "on_bp_treatment",
            "total_cholesterol", "hdl_cholesterol", "ldl_cholesterol", "triglycerides",
            "has_diabetes", "fasting_glucose", "hba1c", "bmi",
            "smoker", "pack_years", "activity_level", "family_history_premature_cvd",
            "heart_rate", "waist_circumference", "egfr"
        ]


class HeartDiseaseModel:
    """
    XGBoost-based Heart Disease Risk Prediction Model.

    Predicts 10-year risk of major cardiovascular events (MI, stroke, CV death).
    Includes both ML prediction and traditional risk score comparison.
    """

    MODEL_VERSION = "1.0.0"
    FEATURE_COUNT = 20

    def __init__(self, model_path: Optional[str] = None):
        self.model: Optional[xgb.XGBClassifier] = None
        self.model_path = model_path or str(settings.models_dir / settings.ml_heart_disease_model)
        self.is_trained = False
        self.feature_importance: dict[str, float] = {}
        self.training_metrics: dict[str, float] = {}

    def build_model(self, **params) -> xgb.XGBClassifier:
        """Build and configure XGBoost model."""
        default_params = {
            "n_estimators": 200,
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_weight": 3,
            "gamma": 0.1,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
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
        **params
    ) -> dict[str, float]:
        """
        Train the heart disease model.

        Args:
            X: Training features (n_samples, n_features)
            y: Training labels (0 = no event, 1 = CVD event within 10 years)
            X_val: Validation features
            y_val: Validation labels
            **params: Additional XGBoost parameters

        Returns:
            Dictionary of training metrics
        """
        self.model = self.build_model(**params)

        eval_set = [(X, y)]
        if X_val is not None and y_val is not None:
            eval_set.append((X_val, y_val))

        self.model.fit(
            X, y,
            eval_set=eval_set,
            verbose=False,
        )

        # Compute feature importance
        self.feature_importance = dict(
            zip(HeartDiseaseFeatures.feature_names(), self.model.feature_importances_)
        )

        # Compute metrics
        from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score

        y_pred_proba = self.model.predict_proba(X)[:, 1]
        y_pred = (y_pred_proba >= 0.5).astype(int)

        self.training_metrics = {
            "train_auc": roc_auc_score(y, y_pred_proba),
            "train_accuracy": accuracy_score(y, y_pred),
            "train_precision": precision_score(y, y_pred, zero_division=0),
            "train_recall": recall_score(y, y_pred, zero_division=0),
            "train_f1": f1_score(y, y_pred, zero_division=0),
        }

        if X_val is not None and y_val is not None:
            y_val_proba = self.model.predict_proba(X_val)[:, 1]
            y_val_pred = (y_val_proba >= 0.5).astype(int)
            self.training_metrics.update({
                "val_auc": roc_auc_score(y_val, y_val_proba),
                "val_accuracy": accuracy_score(y_val, y_val_pred),
                "val_precision": precision_score(y_val, y_val_pred, zero_division=0),
                "val_recall": recall_score(y_val, y_val_pred, zero_division=0),
                "val_f1": f1_score(y_val, y_val_pred, zero_division=0),
            })

        self.is_trained = True
        return self.training_metrics

    def predict_proba(self, features: HeartDiseaseFeatures) -> float:
        """
        Predict probability of CVD event within 10 years.

        Args:
            features: HeartDiseaseFeatures object

        Returns:
            Probability between 0 and 1
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained. Call train() or load() first.")

        X = features.to_array()
        return float(self.model.predict_proba(X)[0, 1])

    def predict(self, features: HeartDiseaseFeatures, threshold: float = 0.5) -> int:
        """
        Predict binary outcome.

        Args:
            features: HeartDiseaseFeatures object
            threshold: Decision threshold (default 0.5)

        Returns:
            1 if high risk, 0 if low risk
        """
        proba = self.predict_proba(features)
        return 1 if proba >= threshold else 0

    def predict_from_digital_twin(self, twin: PatientDigitalTwin) -> dict[str, Any]:
        """
        Predict from a PatientDigitalTwin object.

        Args:
            twin: Complete patient digital twin

        Returns:
            Dictionary with risk prediction and details
        """
        features = self._extract_features(twin)
        risk_score = self.predict_proba(features)
        risk_category = self._categorize_risk(risk_score)

        # Also compute traditional ASCVD score for comparison
        ascvd_score = self._compute_ascvd_score(twin)

        return {
            "patient_id": twin.patient_id,
            "risk_score": risk_score,
            "risk_category": risk_category,
            "risk_percentage": round(risk_score * 100, 1),
            "ascvd_10yr_risk": ascvd_score,
            "model_version": self.MODEL_VERSION,
            "features_used": features.to_dict(),
            "feature_importance": self.feature_importance,
        }

    def _extract_features(self, twin: PatientDigitalTwin) -> HeartDiseaseFeatures:
        """Extract features from digital twin."""
        cvd_factors = CardiovascularRiskFactors.from_digital_twin(twin)

        # Map activity level
        activity_map = {
            "sedentary": 0.0,
            "light": 1.0,
            "moderate": 2.0,
            "active": 3.0,
            "very_active": 4.0,
        }

        return HeartDiseaseFeatures(
            age=float(cvd_factors.age),
            gender_male=1.0 if cvd_factors.gender == Gender.MALE else 0.0,
            systolic_bp=cvd_factors.systolic_bp or 120.0,
            diastolic_bp=cvd_factors.diastolic_bp or 80.0,
            on_bp_treatment=1.0 if cvd_factors.on_bp_treatment else 0.0,
            total_cholesterol=cvd_factors.total_cholesterol or 200.0,
            hdl_cholesterol=cvd_factors.hdl_cholesterol or 50.0,
            ldl_cholesterol=cvd_factors.ldl_cholesterol,
            triglycerides=cvd_factors.triglycerides,
            has_diabetes=1.0 if cvd_factors.has_diabetes else 0.0,
            fasting_glucose=None,  # Could extract from labs
            hba1c=None,
            bmi=twin.bmi,
            smoker=1.0 if cvd_factors.smoker else 0.0,
            pack_years=twin.lifestyle.pack_years,
            activity_level=activity_map.get(twin.lifestyle.activity_level.value, 0.0),
            family_history_premature_cvd=1.0 if cvd_factors.family_history_premature_cvd else 0.0,
            heart_rate=twin.vitals.heart_rate,
            waist_circumference=twin.vitals.waist_circumference_cm,
            egfr=None,  # Could extract from labs
        )

    def _categorize_risk(self, risk_score: float) -> str:
        """Categorize risk based on score."""
        if risk_score < 0.05:
            return "very_low"
        elif risk_score < 0.10:
            return "low"
        elif risk_score < 0.20:
            return "moderate"
        elif risk_score < 0.30:
            return "high"
        else:
            return "very_high"

    def _compute_ascvd_score(self, twin: PatientDigitalTwin) -> Optional[float]:
        """
        Compute traditional ASCVD Pooled Cohort Equation risk score.

        Simplified implementation - in production use validated library.
        """
        cvd_factors = CardiovascularRiskFactors.from_digital_twin(twin)

        # Need minimum required variables
        if not all([cvd_factors.systolic_bp, cvd_factors.total_cholesterol,
                    cvd_factors.hdl_cholesterol]):
            return None

        age = cvd_factors.age
        gender = cvd_factors.gender
        sbp = cvd_factors.systolic_bp
        tc = cvd_factors.total_cholesterol
        hdl = cvd_factors.hdl_cholesterol
        smoker = 1.0 if cvd_factors.smoker else 0.0
        diabetes = 1.0 if cvd_factors.has_diabetes else 0.0
        bp_treated = 1.0 if cvd_factors.on_bp_treatment else 0.0

        # Simplified coefficients (White male/female from 2013 ACC/AHA guideline)
        if gender == Gender.MALE:
            coeffs = {
                "age": 12.344, "tc": 11.853, "hdl": -7.990, "sbp_treated": 1.769,
                "sbp_untreated": 1.797, "smoker": 7.837, "diabetes": 0.658
            }
            mean_survival = 0.88936
            const = 61.18
        else:
            coeffs = {
                "age": -29.799, "tc": 13.540, "hdl": -13.578, "sbp_treated": 2.019,
                "sbp_untreated": 1.957, "smoker": 7.574, "diabetes": 0.691
            }
            mean_survival = 0.95012
            const = -29.18

        # Log transformations
        ln_age = np.log(age)
        ln_tc = np.log(tc)
        ln_hdl = np.log(hdl)
        ln_sbp = np.log(sbp)

        # Linear predictor
        lp = (
            coeffs["age"] * ln_age +
            coeffs["tc"] * ln_tc +
            coeffs["hdl"] * ln_hdl +
            (coeffs["sbp_treated"] if bp_treated else coeffs["sbp_untreated"]) * ln_sbp +
            coeffs["smoker"] * smoker +
            coeffs["diabetes"] * diabetes
        )

        risk = 1 - mean_survival ** np.exp(lp - const)
        return max(0.0, min(1.0, risk))

    def save(self, path: Optional[str] = None) -> None:
        """Save model to disk."""
        if not self.is_trained or self.model is None:
            raise ValueError("No trained model to save.")

        save_path = Path(path or self.model_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            "model": self.model,
            "feature_importance": self.feature_importance,
            "training_metrics": self.training_metrics,
            "model_version": self.MODEL_VERSION,
            "feature_names": HeartDiseaseFeatures.feature_names(),
        }
        joblib.dump(model_data, save_path)

    def load(self, path: Optional[str] = None) -> "HeartDiseaseModel":
        """Load model from disk."""
        load_path = Path(path or self.model_path)
        if not load_path.exists():
            raise FileNotFoundError(f"Model file not found: {load_path}")

        model_data = joblib.load(load_path)
        self.model = model_data["model"]
        self.feature_importance = model_data.get("feature_importance", {})
        self.training_metrics = model_data.get("training_metrics", {})
        self.is_trained = True
        return self

    def get_feature_importance_df(self) -> pd.DataFrame:
        """Get feature importance as DataFrame sorted by importance."""
        if not self.feature_importance:
            return pd.DataFrame()

        df = pd.DataFrame(
            list(self.feature_importance.items()),
            columns=["feature", "importance"]
        ).sort_values("importance", ascending=False)
        return df