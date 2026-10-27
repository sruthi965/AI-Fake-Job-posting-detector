"""Loads the trained classifier and produces predictions.

If no trained model is found the service falls back to the rule-based score so the application
still runs, and reports ``model_used = "rules-only"`` so the interface can say so.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from threading import Lock

import joblib

from app.core.config import get_settings
from app.services.preprocessing import build_text
from app.services.risk_analysis import analyze_risks, risk_level, rule_score

logger = logging.getLogger(__name__)

DISCLAIMER = "This prediction is an estimate, not proof of fraud. Verify the employer through official channels before sharing personal information or making payments."
INPUT_FIELDS = ["job_title", "company_name", "description", "requirements", "employment_type", "salary_range"]


class PredictionService:
    def __init__(self, model_path: Path | None = None) -> None:
        self._model_path = model_path
        self._bundle: dict | None = None
        self._lock = Lock()

    @property
    def model_loaded(self) -> bool:
        return self._bundle is not None

    def load(self) -> bool:
        path = self._model_path or get_settings().model_path
        with self._lock:
            if not Path(path).exists():
                logger.warning("No trained model at %s; using rule-based scoring only.", path)
                self._bundle = None
                return False
            # Only load model files you trained yourself: joblib/pickle can execute code.
            self._bundle = joblib.load(path)
            return True

    def predict(self, job: dict) -> dict:
        indicators = analyze_risks(job)
        threshold = 0.5
        if self._bundle is not None:
            pipeline = self._bundle["pipeline"]
            threshold = float(self._bundle.get("threshold", 0.5))
            probability = float(pipeline.predict_proba([build_text(job)])[0][1])
            model_used = str(self._bundle.get("name", "classifier"))
        else:
            probability = rule_score(indicators)
            model_used = "rules-only"
        is_fraud = probability >= threshold
        return {
            "prediction": "Fraudulent" if is_fraud else "Legitimate",
            "is_fraudulent": is_fraud,
            "fraud_probability": round(probability * 100, 1),
            "risk_level": risk_level(probability),
            "risk_indicators": indicators,
            "model_used": model_used,
            "analysis_id": None,
            "disclaimer": DISCLAIMER,
        }

    def info(self) -> dict:
        settings = get_settings()
        bundle = self._bundle or {}
        return {
            "model_loaded": self.model_loaded,
            "scoring_mode": "classifier" if self.model_loaded else "rules-only",
            "model_name": bundle.get("name"),
            "trained_at": bundle.get("trained_at"),
            "threshold": float(bundle.get("threshold", 0.5)),
            "metrics_available": settings.metrics_path.exists(),
            "supported_input_fields": INPUT_FIELDS,
        }


def load_metrics() -> dict | None:
    path = get_settings().metrics_path
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


_service: PredictionService | None = None
_service_lock = Lock()


def get_prediction_service() -> PredictionService:
    global _service
    with _service_lock:
        if _service is None:
            _service = PredictionService()
            _service.load()
        return _service


def reset_prediction_service() -> None:
    global _service
    with _service_lock:
        _service = None
