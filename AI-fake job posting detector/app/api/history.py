from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import get_current_user
from app.database import repository
from app.schemas.job_schema import HistorySaveRequest
from app.schemas.response_schema import HistoryDetail, HistoryPage

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=HistoryPage, summary="List your past analyses")
def list_history(
    page: int = Query(1, ge=1, le=10000),
    page_size: int = Query(10, ge=1, le=50),
    user: dict = Depends(get_current_user),
):
    items, total = repository.list_analyses(user["id"], page, page_size)
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.post("", response_model=HistoryDetail, status_code=201, summary="Save an analysis to your history")
def save_history(payload: HistorySaveRequest, user: dict = Depends(get_current_user)):
    data = payload.model_dump()
    analysis_id = repository.save_analysis(user["id"], data)
    return repository.get_analysis(analysis_id, user["id"])


@router.get("/{analysis_id}", response_model=HistoryDetail, summary="Get one saved analysis")
def get_history_item(analysis_id: int, user: dict = Depends(get_current_user)):
    item = repository.get_analysis(analysis_id, user["id"])
    if item is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return item


@router.delete("/{analysis_id}", status_code=204, summary="Delete a saved analysis")
def delete_history_item(analysis_id: int, user: dict = Depends(get_current_user)):
    if not repository.delete_analysis(analysis_id, user["id"]):
        raise HTTPException(status_code=404, detail="Analysis not found")
