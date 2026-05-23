"""
USSD Load Tests
===============
Load testing for USSD infrastructure using locust.
Tests concurrent session handling and response times.
"""
from __future__ import annotations

import time
from locust import HttpUser, task, between


class USSDUser(HttpUser):
    """Simulates a USSD user."""
    wait_time = between(1, 3)

    def on_start(self):
        self.session_id = f"load_test_{int(time.time())}"
        self.phone = "+263712345678"

    @task(3)
    def new_session(self):
        """Start a new USSD session."""
        self.client.post(
            "/api/v1/ussd/v2/webhook/econet",
            json={
                "sessionId": self.session_id,
                "phoneNumber": self.phone,
                "text": "",
                "serviceCode": "*123#",
                "networkCode": "64501",
            },
        )

    @task(2)
    def continue_session(self):
        """Continue an existing session."""
        self.client.post(
            "/api/v1/ussd/v2/webhook/econet",
            json={
                "sessionId": self.session_id,
                "phoneNumber": self.phone,
                "text": "1",
                "serviceCode": "*123#",
                "networkCode": "64501",
            },
        )

    @task(1)
    def health_check(self):
        """Check USSD health endpoint."""
        self.client.get("/api/v1/ussd/v2/health")
