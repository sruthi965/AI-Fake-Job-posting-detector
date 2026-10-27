from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.auth import get_optional_user, rate_limit
from app.database import repository
from app.schemas.job_schema import ExplainRequest, PredictRequest
from app.schemas.response_schema import ExplainResponse, PredictResponse
from app.services.llm_service import generate_explanation
from app.services.prediction_service import get_prediction_service

router = APIRouter(tags=["analysis"])

JOB_FIELDS = ("job_title", "company_name", "description", "requirements", "employment_type", "salary_range")


@router.post("/predict", response_model=PredictResponse, summary="Analyze a job posting and get a prediction")
def predict(payload: PredictRequest, user: dict | None = Depends(get_optional_user)):
    job = payload.model_dump(include=set(JOB_FIELDS))
    result = get_prediction_service().predict(job)
    # History is only stored for signed-in users who ask for it.
    if payload.save_history and user:
        result["analysis_id"] = repository.save_analysis(user["id"], {**job, **result})
    return result


@router.post(
    "/explain",
    response_model=ExplainResponse,
    summary="Generate a plain-language explanation for an analysis",
    dependencies=[Depends(rate_limit("explain", 10, 600))],
)
def explain(payload: ExplainRequest, user: dict | None = Depends(get_optional_user)):
    job = payload.model_dump(include=set(JOB_FIELDS))
    indicators = [i.model_dump() for i in payload.risk_indicators]
    explanation = generate_explanation(job, payload.prediction, payload.fraud_probability, indicators)
    if payload.analysis_id and user:
        repository.update_explanation(payload.analysis_id, user["id"], explanation)
    return explanation
