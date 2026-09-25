from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    data_loaded: bool
    model_loaded: bool

class AlertResponse(BaseModel):
    alert_id: str
    entity_id: str
    entity_type: str
    risk_score: float
    confidence_score: float
    priority_score: float
    alert_category: str
    top_contributing_features: Any = None
    linked_transactions: List[str] = []
    linked_wallets: List[str] = []
    linked_ips: List[str] = []
    graph_metrics: Any = None
    temporal_evidence: Any = None
    network_evidence: Any = None
    model_name: str = ""
    model_version: str = ""
    dataset_version: str = ""
    source_records: Any = None
    explanation: str = ""
    caveat: str = ""
    created_at: Optional[datetime] = None

class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    page: int = 1
    page_size: int = 20

class EntityResponse(BaseModel):
    entity_id: str
    entity_type: str
    risk_score: float
    confidence_score: Optional[float] = None
    priority: Optional[float] = None
    category: Optional[str] = None
    explanation: Optional[str] = None
    reasons: Optional[List[str]] = None
    features: Any = None
    transactions: List[str] = []
    ips: List[str] = []
    wallets: List[str] = []

class TimelineEntry(BaseModel):
    date: str
    count: int

class TimelineResponse(BaseModel):
    entries: List[TimelineEntry]
    time_range_start: str
    time_range_end: str

class NeighborhoodResponse(BaseModel):
    center_entity: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class TransactionResponse(BaseModel):
    txid: str
    timestamp: datetime
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    input_addresses: List[str] = []
    output_addresses: List[str] = []
    input_amounts: List[float] = []
    output_amounts: List[float] = []
    fee: Optional[float] = None
    script_type: Optional[str] = None
    geo_country: Optional[str] = None
    asn: Optional[str] = None
    risk_score: float = 0.0

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total: int

class MetricsResponse(BaseModel):
    total_transactions: int
    total_wallets: int
    total_ips: int
    total_asns: int = 0
    total_alerts: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    model_accuracy: float
    graph_nodes: int
    graph_edges: int
    processing_time_seconds: float
    time_range_start: Optional[str] = None
    time_range_end: Optional[str] = None
    timeline_data: Optional[List[dict]] = None

class DataQualityResponse(BaseModel):
    total_records: int
    train_records: Optional[int] = 0
    validation_records: Optional[int] = 0
    test_records: Optional[int] = 0
    feature_count: Optional[int] = 0
    generated_at: Optional[str] = ""
    valid_records: Optional[int] = 0
    quarantined_records: Optional[int] = 0
    missing_values: Any = {}
    duplicate_count: Optional[int] = 0
    invalid_fields: Any = {}

class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    model_type: str
    training_date: str
    feature_count: int
    metrics: Any = {}
    dataset_version: str
    random_seed: int = 42
    feature_names: Optional[List[str]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    train_rows: Optional[int] = None
    val_rows: Optional[int] = None
    test_rows: Optional[int] = None
    total_alerts: Optional[int] = None

class IngestResponse(BaseModel):
    status: str
    records_processed: int
    records_valid: int
    records_quarantined: int
    processing_time_seconds: float
