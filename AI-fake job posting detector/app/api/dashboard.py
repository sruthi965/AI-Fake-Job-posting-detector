from __future__ import annotations

from fastapi import APIRouter, Depends

from app import __version__
from app.api.auth import get_current_user
from app.database import repository
from app.schemas.response_schema import ModelInfo, UserStats
from app.services.prediction_service import get_prediction_service, load_metrics

router = APIRouter(tags=["dashboard"])


@router.get("/model-info", response_model=ModelInfo, summary="Model version and supported input fields")
def model_info():
    return {**get_prediction_service().info(), "app_version": __version__}


@router.get("/dashboard/model-performance", summary="Evaluation metrics saved by the training script")
def model_performance():
    metrics = load_metrics()
    return metrics if metrics else {"available": False}


@router.get("/dashboard/stats", response_model=UserStats, summary="Summary of your own analyses")
def user_stats(user: dict = Depends(get_current_user)):
    return repository.user_stats(user["id"])
