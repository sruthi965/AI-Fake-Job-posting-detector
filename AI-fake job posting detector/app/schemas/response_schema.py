from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RiskIndicator(BaseModel):
    code: str
    label: str
    severity: Literal["low", "medium", "high"]
    evidence: str | None = None


class PredictResponse(BaseModel):
    prediction: Literal["Fraudulent", "Legitimate"]
    is_fraudulent: bool
    fraud_probability: float = Field(description="Percentage from 0 to 100")
    risk_level: Literal["low", "medium", "high"]
    risk_indicators: list[RiskIndicator]
    model_used: str
    analysis_id: int | None = None
    disclaimer: str


class ExplanationReason(BaseModel):
    title: str
    detail: str


class ExplainResponse(BaseModel):
    summary: str
    reasons: list[ExplanationReason]
    recommendation: str
    source: Literal["llm", "template"]


class HistoryItem(BaseModel):
    id: int
    job_title: str
    company_name: str | None = None
    prediction: str
    fraud_probability: float
    created_at: str | None = None


class HistoryDetail(HistoryItem):
    description: str
    requirements: str | None = None
    employment_type: str | None = None
    salary_range: str | None = None
    risk_indicators: list[RiskIndicator] = []
    explanation: ExplainResponse | None = None
    model_used: str | None = None


class HistoryPage(BaseModel):
    items: list[HistoryItem]
    page: int
    page_size: int
    total: int


class UserStats(BaseModel):
    total_analyses: int
    fraudulent: int
    legitimate: int
    average_probability: float


class ModelInfo(BaseModel):
    model_loaded: bool
    scoring_mode: Literal["classifier", "rules-only"]
    model_name: str | None = None
    trained_at: str | None = None
    threshold: float = 0.5
    metrics_available: bool
    supported_input_fields: list[str]
    app_version: str
