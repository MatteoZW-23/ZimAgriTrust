import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_ai_vision_stub():
    # Proof of concept for AI endpoint accessibility
    response = client.get("/ai/research/proof-of-concept")
    assert response.status_code == 200
    assert "engines" in response.json()
