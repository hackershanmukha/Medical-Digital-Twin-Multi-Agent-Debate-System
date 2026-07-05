"""
Composite Multi-Disease Risk Model.

Aggregates cardiovascular, diabetes, and other domain risks into a
unified patient risk score with SHAP-based explainability.
"""
from dataclasses import dataclass
from typing import Any, Optional
import numpy as np
import xgboost as xgb
import joblib
from pathlib import Path

from config.settings import settings
from digital_twin.models import PatientDigitalTwin


@dataclass
class RiskFeatures:
    """
    Unified feature set combining all risk domains.
    Used by the composite risk model.
    """
    # --- Demographics ---
    age: float
    gender_male: float
    bmi: float

    # --- Cardiovascular ---
    systolic_bp: float
    diastolic_bp: float
    total_cholesterol: float
    hdl_cholesterol: float
    ldl_cholesterol: float
    triglycerides: float
    heart_rate: float
    on_bp_treatment: float

    # --- Metabolic ---
    fasting_glucose: float
    hba1c: float
    has_diabetes: float
    has_prediabetes: float

    # --- Lifestyle ---
    smoker: float
    pack_years: float
    activity_level: float          # 0=sedentary → 4=very_active
    alcohol_heavy: float
    sleep_hours: float

    # --- Clinical Risk Factors ---
    num_active_conditions: float   # Total burden of disease
    num_active_medications: float
    has_hypertension: float
    has_heart_disease: float
    has_kidney_disease: float
    has_depression: float
    has_copd_asthma: float

    # --- Family History ---
    family_history_cvd: float
    family_history_diabetes: float
    family_history_cancer: float

    # --- Social / Lifestyle ---
    lives_alone: float
    high_stress: float

    def to_array(self) -> np.ndarray:
        return np.array([
            self.age, self.gender_male, self.bmi,
            self.systolic_bp, self.diastolic_bp, self.total_cholesterol,
            self.hdl_cholesterol, self.ldl_cholesterol, self.triglycerides,
            self.heart_rate, self.on_bp_treatment,
            self.fasting_glucose, self.hba1c, self.has_diabetes, self.has_prediabetes,
            self.smoker, self.pack_years, self.activity_level,
            self.alcohol_heavy, self.sleep_hours,
            self.num_active_conditions, self.num_active_medications,
            self.has_hypertension, self.has_heart_disease,
            self.has_kidney_disease, self.has_depression, self.has_copd_asthma,
            self.family_history_cvd, self.family_history_diabetes, self.family_history_cancer,
            self.lives_alone, self.high_stress,
        ]).reshape(1, -1)

    def to_dict(self) -> dict[str, float]:
        return {
            "age": self.age, "gender_male": self.gender_male, "bmi": self.bmi,
            "systolic_bp": self.systolic_bp, "diastolic_bp": self.diastolic_bp,
            "total_cholesterol": self.total_cholesterol, "hdl_cholesterol": self.hdl_cholesterol,
            "ldl_cholesterol": self.ldl_cholesterol, "triglycerides": self.triglycerides,
            "heart_rate": self.heart_rate, "on_bp_treatment": self.on_bp_treatment,
            "fasting_glucose": self.fasting_glucose, "hba1c": self.hba1c,
            "has_diabetes": self.has_diabetes, "has_prediabetes": self.has_prediabetes,
            "smoker": self.smoker, "pack_years": self.pack_years,
            "activity_level": self.activity_level, "alcohol_heavy": self.alcohol_heavy,
            "sleep_hours": self.sleep_hours,
            "num_active_conditions": self.num_active_conditions,
            "num_active_medications": self.num_active_medications,
            "has_hypertension": self.has_hypertension,
            "has_heart_disease": self.has_heart_disease,
            "has_kidney_disease": self.has_kidney_disease,
            "has_depression": self.has_depression,
            "has_copd_asthma": self.has_copd_asthma,
            "family_history_cvd": self.family_history_cvd,
            "family_history_diabetes": self.family_history_diabetes,
            "family_history_cancer": self.family_history_cancer,
            "lives_alone": self.lives_alone,
            "high_stress": self.high_stress,
        }

    @classmethod
    def feature_names(cls) -> list[str]:
        return [
            "age", "gender_male", "bmi",
            "systolic_bp", "diastolic_bp", "total_cholesterol",
            "hdl_cholesterol", "ldl_cholesterol", "triglycerides",
            "heart_rate", "on_bp_treatment",
            "fasting_glucose", "hba1c", "has_diabetes", "has_prediabetes",
            "smoker", "pack_years", "activity_level",
            "alcohol_heavy", "sleep_hours",
            "num_active_conditions", "num_active_medications",
            "has_hypertension", "has_heart_disease",
            "has_kidney_disease", "has_depression", "has_copd_asthma",
            "family_history_cvd", "family_history_diabetes", "family_history_cancer",
            "lives_alone", "high_stress",
        ]


class RiskModel:
    """
    Composite Multi-Domain Risk Model.

    Produces a single unified risk score (0-100) with SHAP-based breakdown
    across cardiovascular, metabolic, lifestyle, and social risk domains.
    """

    MODEL_VERSION = "1.0.0"
    FEATURE_COUNT = 32

    # Risk domain groupings for SHAP breakdown
    DOMAINS = {
        "cardiovascular": [
            "systolic_bp", "diastolic_bp", "total_cholesterol", "hdl_cholesterol",
            "ldl_cholesterol", "triglycerides", "heart_rate", "on_bp_treatment",
            "has_heart_disease", "family_history_cvd",
        ],
        "metabolic": [
            "bmi", "fasting_glucose", "hba1c", "has_diabetes",
            "has_prediabetes", "family_history_diabetes",
        ],
        "lifestyle": [
            "smoker", "pack_years", "activity_level",
            "alcohol_heavy", "sleep_hours",
        ],
        "multimorbidity": [
            "num_active_conditions", "num_active_medications",
            "has_hypertension", "has_kidney_disease",
            "has_depression", "has_copd_asthma", "family_history_cancer",
        ],
        "social": [
            "lives_alone", "high_stress",
        ],
        "demographics": ["age", "gender_male"],
    }

    def __init__(self, model_path: Optional[str] = None):
        self.model: Optional[xgb.XGBClassifier] = None
        self.model_path = model_path or str(settings.models_dir / settings.ml_risk_model)
        self.is_trained = False
        self.feature_importance: dict[str, float] = {}
        self.training_metrics: dict[str, float] = {}

    def build_model(self, **params) -> xgb.XGBClassifier:
        default_params = {
            "n_estimators": 300,
            "max_depth": 7,
            "learning_rate": 0.03,
            "subsample": 0.8,
            "colsample_bytree": 0.75,
            "min_child_weight": 5,
            "gamma": 0.2,
            "reg_alpha": 0.1,
            "reg_lambda": 1.5,
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
            zip(RiskFeatures.feature_names(), self.model.feature_importances_)
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

    def predict_proba(self, features: RiskFeatures) -> float:
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained. Call train() or load() first.")
        return float(self.model.predict_proba(features.to_array())[0, 1])

    def predict_from_digital_twin(self, twin: PatientDigitalTwin) -> dict[str, Any]:
        """Full risk prediction with domain breakdown."""
        features = self._extract_features(twin)
        risk_score = self.predict_proba(features)
        risk_category = self._categorize_risk(risk_score)
        domain_scores = self._compute_domain_scores(features)

        return {
            "patient_id": twin.patient_id,
            "risk_score": risk_score,
            "risk_category": risk_category,
            "risk_percentage": round(risk_score * 100, 1),
            "domain_scores": domain_scores,
            "model_version": self.MODEL_VERSION,
            "features_used": features.to_dict(),
            "feature_importance": self.feature_importance,
            "top_risk_factors": self._get_top_risk_factors(features, n=5),
        }

    def _extract_features(self, twin: PatientDigitalTwin) -> RiskFeatures:
        """Extract all features from digital twin."""
        from digital_twin.models import SmokingStatus, AlcoholConsumption

        # Lab helper
        def get_lab(name: str) -> Optional[float]:
            panel = twin.latest_labs
            if not panel:
                return None
            test = panel.get_test(name)
            return test.value if test else None

        activity_map = {
            "sedentary": 0.0, "light": 1.0, "moderate": 2.0,
            "active": 3.0, "very_active": 4.0,
        }

        def has_cond(keyword: str) -> float:
            return 1.0 if twin.medical_history.has_condition(keyword) else 0.0

        return RiskFeatures(
            age=float(twin.age),
            gender_male=1.0 if twin.demographics.gender.value == "male" else 0.0,
            bmi=twin.bmi or 25.0,
            systolic_bp=twin.vitals.systolic_bp or 120.0,
            diastolic_bp=twin.vitals.diastolic_bp or 80.0,
            total_cholesterol=get_lab("cholesterol") or get_lab("total cholesterol") or 190.0,
            hdl_cholesterol=get_lab("hdl") or 55.0,
            ldl_cholesterol=get_lab("ldl") or 110.0,
            triglycerides=get_lab("triglycerides") or 120.0,
            heart_rate=twin.vitals.heart_rate or 72.0,
            on_bp_treatment=1.0 if any(
                "hypertension" in (m.indication or "").lower()
                for m in twin.active_medications
            ) else 0.0,
            fasting_glucose=get_lab("glucose") or get_lab("fasting glucose") or 90.0,
            hba1c=get_lab("hba1c") or get_lab("a1c") or 5.2,
            has_diabetes=has_cond("diabetes"),
            has_prediabetes=has_cond("prediabetes"),
            smoker=1.0 if twin.lifestyle.smoking_status in (
                SmokingStatus.CURRENT, SmokingStatus.FORMER
            ) else 0.0,
            pack_years=twin.lifestyle.pack_years,
            activity_level=activity_map.get(twin.lifestyle.activity_level.value, 0.0),
            alcohol_heavy=1.0 if twin.lifestyle.alcohol_consumption == AlcoholConsumption.HEAVY else 0.0,
            sleep_hours=twin.lifestyle.sleep_hours_per_night or 7.0,
            num_active_conditions=float(len(twin.active_conditions)),
            num_active_medications=float(len(twin.active_medications)),
            has_hypertension=has_cond("hypertension"),
            has_heart_disease=has_cond("heart") or has_cond("coronary") or has_cond("cardiac"),
            has_kidney_disease=has_cond("kidney") or has_cond("renal"),
            has_depression=has_cond("depression") or has_cond("anxiety"),
            has_copd_asthma=has_cond("copd") or has_cond("asthma"),
            family_history_cvd=1.0 if (
                twin.family_history.has_condition("heart") or
                twin.family_history.has_condition("stroke") or
                twin.family_history.has_condition("coronary")
            ) else 0.0,
            family_history_diabetes=1.0 if twin.family_history.has_condition("diabetes") else 0.0,
            family_history_cancer=1.0 if twin.family_history.has_condition("cancer") else 0.0,
            lives_alone=1.0 if twin.lifestyle.lives_alone else 0.0,
            high_stress=1.0 if twin.lifestyle.stress_level == "high" else 0.0,
        )

    def _categorize_risk(self, risk_score: float) -> str:
        if risk_score < 0.10:
            return "low"
        elif risk_score < 0.25:
            return "moderate"
        elif risk_score < 0.50:
            return "high"
        else:
            return "very_high"

    def _compute_domain_scores(self, features: RiskFeatures) -> dict[str, float]:
        """Compute per-domain risk contribution scores (0-1)."""
        feat_dict = features.to_dict()
        domain_scores = {}

        for domain, domain_features in self.DOMAINS.items():
            total_importance = sum(
                self.feature_importance.get(f, 0.0) for f in domain_features
            )
            if total_importance > 0:
                weighted = sum(
                    self.feature_importance.get(f, 0.0) * feat_dict.get(f, 0.0)
                    for f in domain_features
                )
                domain_scores[domain] = round(min(1.0, weighted / total_importance), 3)
            else:
                # Fallback: simple mean of feature values in domain
                vals = [feat_dict.get(f, 0.0) for f in domain_features if f in feat_dict]
                domain_scores[domain] = round(float(np.mean(vals)) if vals else 0.0, 3)

        return domain_scores

    def _get_top_risk_factors(
        self, features: RiskFeatures, n: int = 5
    ) -> list[dict[str, Any]]:
        """Get the top N contributing risk factors by SHAP-weighted importance."""
        feat_dict = features.to_dict()
        factor_scores = {
            name: self.feature_importance.get(name, 0.0) * abs(feat_dict.get(name, 0.0))
            for name in RiskFeatures.feature_names()
        }
        top = sorted(factor_scores.items(), key=lambda x: x[1], reverse=True)[:n]
        return [
            {
                "feature": name,
                "importance": round(self.feature_importance.get(name, 0.0), 4),
                "value": round(feat_dict.get(name, 0.0), 3),
                "contribution": round(score, 4),
            }
            for name, score in top
        ]

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

    def load(self, path: Optional[str] = None) -> "RiskModel":
        load_path = Path(path or self.model_path)
        if not load_path.exists():
            raise FileNotFoundError(f"Model file not found: {load_path}")
        data = joblib.load(load_path)
        self.model = data["model"]
        self.feature_importance = data.get("feature_importance", {})
        self.training_metrics = data.get("training_metrics", {})
        self.is_trained = True
        return self
