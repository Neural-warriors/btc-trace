from fastapi import APIRouter
from ..models.schemas import MetricsResponse, DataQualityResponse, ModelInfoResponse
from ..services import data_service

router = APIRouter(tags=["System"])

@router.get("/metrics", response_model=MetricsResponse)
def get_metrics():
    """
    Get system-wide metrics and statistics.
    """
    if data_service.data_service is None:
        return MetricsResponse(
            total_transactions=0, total_wallets=0, total_ips=0, total_alerts=0,
            high_risk_count=0, medium_risk_count=0, low_risk_count=0,
            model_accuracy=0.0, graph_nodes=0, graph_edges=0, processing_time_seconds=0.0
        )
    return data_service.data_service.get_metrics()

@router.get("/data-quality", response_model=DataQualityResponse)
def get_data_quality():
    """
    Get data quality reports.
    """
    if data_service.data_service is None:
        return DataQualityResponse(
            total_records=0, valid_records=0, quarantined_records=0,
            missing_values={}, duplicate_count=0, invalid_fields={}
        )
    return data_service.data_service.get_data_quality()

@router.get("/timeline")
def get_timeline():
    if data_service.data_service is None:
        return {"entries": [], "time_range_start": "", "time_range_end": ""}
    return data_service.data_service.get_timeline()

@router.get("/models", response_model=ModelInfoResponse)
def get_model_info():
    """
    Get information about the currently loaded ML model.
    """
    if data_service.data_service is None:
        return ModelInfoResponse(
            model_name="unknown", model_version="unknown", model_type="unknown",
            training_date="1970-01-01T00:00:00Z", feature_count=0, metrics={},
            dataset_version="unknown", random_seed=42
        )
    return data_service.data_service.get_model_info()
