import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_get_market_insights():
    response = client.get("/market-insights/SampleRegion")
    assert response.status_code == 200
    assert "region_name" in response.json()
    assert response.json()["region_name"] == "SampleRegion"

def test_get_market_insights_not_found():
    response = client.get("/market-insights/UnknownRegion")
    assert response.status_code == 404
    assert "detail" in response.json()
