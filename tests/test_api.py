import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "healthy")
    assert "uptime_seconds" in data

def test_metrics():
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_transactions" in data
    assert "total_alerts" in data

def test_alerts_list():
    response = client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert "total" in data
    assert isinstance(data["alerts"], list)

def test_data_quality():
    response = client.get("/api/data-quality")
    assert response.status_code == 200
    data = response.json()
    assert "total_records" in data

def test_models_info():
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data

def test_search():
    response = client.get("/api/search?query=test")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data
