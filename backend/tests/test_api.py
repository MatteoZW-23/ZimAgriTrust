import pytest
from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_listings(client: TestClient):
    response = client.get("/api/v1/listings/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_listing_unauthorized(client: TestClient):
    response = client.post("/api/v1/listings/", json={
        "crop_type": "maize",
        "quantity": 100,
        "price_per_unit": 0.35,
        "grade": "Grade A",
        "location": "Harare"
    })
    # Should return 401 Unauthorized
    assert response.status_code == 401
