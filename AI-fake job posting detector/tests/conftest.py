import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    """Every test gets its own SQLite file, no LLM, and no trained model unless it asks for one."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("MODEL_PATH", str(tmp_path / "missing-model.joblib"))
    monkeypatch.setenv("METRICS_PATH", str(tmp_path / "missing-metrics.json"))
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-that-is-long-enough-123456")
    from app.core.security import limiter

    limiter.reset()
    yield
    try:
        from app.services.prediction_service import reset_prediction_service

        reset_prediction_service()
    except ImportError:
        pass


SCAM_JOB = {
    "job_title": "Remote Data Entry Assistant",
    "company_name": "Global Solutions Inc.",
    "description": "We are looking for a remote data entry assistant to help with our online operations. "
                   "You will be required to pay a small registration fee of $50 before starting.",
    "requirements": "Basic computer skills, good communication",
    "employment_type": "Full-time",
    "salary_range": "$500 - $800 per week",
}

REAL_JOB = {
    "job_title": "Backend Engineer",
    "company_name": "Northwind Logistics",
    "description": "Design, build and test services in Python, review code, and take part in sprint planning with the "
                   "platform team. Health insurance and paid leave are included for all employees.",
    "requirements": "3+ years of experience with Python and SQL.",
    "employment_type": "Full-time",
    "salary_range": "$110,000 per year",
}
