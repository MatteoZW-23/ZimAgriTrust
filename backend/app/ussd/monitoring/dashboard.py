"""
USSD Monitoring Dashboard
=========================
Grafana dashboard configuration for USSD metrics.
"""
from __future__ import annotations

USSD_GRAFANA_DASHBOARD = {
    "dashboard": {
        "title": "ZimAgriTrust USSD Infrastructure",
        "panels": [
            {
                "title": "USSD Request Rate",
                "targets": [
                    {
                        "expr": "rate(ussd_requests_total[5m])",
                        "legendFormat": "{{provider}}"
                    }
                ]
            },
            {
                "title": "USSD Error Rate",
                "targets": [
                    {
                        "expr": "rate(ussd_errors_total[5m])",
                        "legendFormat": "{{provider}} - {{error_type}}"
                    }
                ]
            },
            {
                "title": "USSD Request Latency",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, ussd_request_duration_seconds)",
                        "legendFormat": "95th percentile"
                    }
                ]
            },
            {
                "title": "Active Sessions",
                "targets": [
                    {"expr": "ussd_active_sessions"}
                ]
            },
            {
                "title": "Provider Health",
                "targets": [
                    {
                        "expr": "ussd_provider_health",
                        "legendFormat": "{{provider}}"
                    }
                ]
            },
            {
                "title": "Retry Rate",
                "targets": [
                    {
                        "expr": "rate(ussd_retries_total[5m])",
                        "legendFormat": "{{provider}}"
                    }
                ]
            }
        ]
    }
}
