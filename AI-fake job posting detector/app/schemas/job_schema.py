from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.response_schema import ExplainResponse, RiskIndicator

OPTIONAL_TEXT_FIELDS = ("company_name", "requirements", "employment_type", "salary_range")


class JobPosting(BaseModel):
    job_title: str = Field(min_length=2, max_length=255)
    company_name: str | None = Field(default=None, max_length=255)
    description: str = Field(min_length=20, max_length=10000)
    requirements: str | None = Field(default=None, max_length=5000)
    employment_type: str | None = Field(default=None, max_length=50)
    salary_range: str | None = Field(default=None, max_length=100)

    @field_validator("job_title", "description", mode="before")
    @classmethod
    def _strip_required(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator(*OPTIONAL_TEXT_FIELDS, mode="before")
    @classmethod
    def _blank_to_none(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class PredictRequest(JobPosting):
    save_history: bool = False


class ExplainRequest(JobPosting):
    prediction: str = Field(pattern="^(Fraudulent|Legitimate)$")
    fraud_probability: float = Field(ge=0, le=100)
    risk_indicators: list[RiskIndicator] = Field(default_factory=list, max_length=20)
    analysis_id: int | None = None


class HistorySaveRequest(JobPosting):
    prediction: str = Field(pattern="^(Fraudulent|Legitimate)$")
    fraud_probability: float = Field(ge=0, le=100)
    risk_indicators: list[RiskIndicator] = Field(default_factory=list, max_length=20)
    explanation: ExplainResponse | None = None
    model_used: str | None = Field(default=None, max_length=50)
