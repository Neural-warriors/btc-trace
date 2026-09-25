from fastapi import APIRouter, Query
from typing import Optional
from ..models.schemas import AlertListResponse
from ..services import data_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=AlertListResponse)
def get_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(5000, ge=1, le=10000),
    min_risk: float = Query(0.0, ge=0.0, le=1.0),
    max_risk: float = Query(1.0, ge=0.0, le=1.0),
    category: Optional[str] = None,
    entity_type: Optional[str] = None,
    sort_by: str = Query("priority", pattern="^(priority|risk)$")
):
    """
    Get a paginated list of alerts.
    """
    if data_service.data_service is None:
        return AlertListResponse(alerts=[], total=0, page=page, page_size=page_size)
        
    alerts, total = data_service.data_service.get_alerts(
        page=page, 
        page_size=page_size, 
        min_risk=min_risk, 
        max_risk=max_risk, 
        category=category,
        entity_type=entity_type,
        sort_by=sort_by
    )
    return AlertListResponse(alerts=alerts, total=total, page=page, page_size=page_size)
