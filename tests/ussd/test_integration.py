"""
USSD Integration Tests
======================
End-to-end tests for USSD flows with database.

Uses a TestClient with base_url="http://localhost" so that TrustedHostMiddleware
(configured with ALLOWED_HOSTS=localhost,127.0.0.1) does not reject requests.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def client(db: Session):
    """Test client with database, using allowed host."""
    from app.main import app
    return TestClient(app, base_url="http://localhost")


def test_econet_webhook_new_session(client: TestClient, db: Session):
    """Test Econet webhook for new session."""
    response = client.post(
        "/api/v1/ussd/v2/webhook/econet",
        json={
            "sessionId": "int_test_123",
            "phoneNumber": "+263712345678",
            "text": "",
            "serviceCode": "*123#",
            "networkCode": "64501",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data or "ussd_response" in data


def test_netone_webhook_new_session(client: TestClient, db: Session):
    """Test NetOne webhook for new session."""
    response = client.post(
        "/api/v1/ussd/v2/webhook/netone",
        json={
            "session_id": "int_test_456",
            "msisdn": "+263712345678",
            "ussd_string": "",
            "short_code": "*123#",
            "msg_type": "initiation",
        },
    )
    assert response.status_code == 200


def test_telecel_webhook_new_session(client: TestClient, db: Session):
    """Test Telecel webhook for new session."""
    response = client.post(
        "/api/v1/ussd/v2/webhook/telecel",
        json={
            "sid": "int_test_789",
            "phone": "+263712345678",
            "input": "",
            "code": "*123#",
            "type": "begin",
        },
    )
    assert response.status_code == 200


def test_simulator_endpoint(client: TestClient, db: Session):
    """Test simulator endpoint."""
    response = client.post(
        "/api/v1/ussd/simulator/simulate",
        json={
            "phone": "+263712345678",
            "provider": "econet",
            "text": "",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "session_id" in data


def test_health_endpoint(client: TestClient):
    """Test USSD health endpoint."""
    response = client.get("/api/v1/ussd/v2/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "active_sessions" in data
