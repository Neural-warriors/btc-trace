from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
from ..models.schemas import SearchResponse
from ..services import data_service

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("", response_model=SearchResponse)
def search(
    query: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    entity_type: Optional[str] = None,
    time_start: Optional[datetime] = None,
    time_end: Optional[datetime] = None,
    min_risk: float = Query(0.0, ge=0.0, le=1.0),
    max_risk: float = Query(1.0, ge=0.0, le=1.0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Search for entities, transactions, or alerts.
    """
    search_query = query or q or ""
    if not search_query or data_service.data_service is None:
        return SearchResponse(results=[], total=0)
        
    results, total = data_service.data_service.search(
        query=search_query,
        entity_type=entity_type,
        time_start=time_start,
        time_end=time_end,
        min_risk=min_risk,
        max_risk=max_risk,
        page=page,
        page_size=page_size
    )
    return SearchResponse(results=results, total=total)
