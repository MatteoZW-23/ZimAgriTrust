# Security Monitoring Alerts Configuration

## Overview

This document defines security monitoring alerts for the ZimAgriTrust platform using Prometheus, Grafana, and Loki. These alerts detect suspicious activities and potential security incidents.

## Alert Rules

### Critical Alerts (Immediate Response Required)

#### 1. Brute Force Attack Detection
```yaml
- alert: BruteForceAttackDetected
  expr: rate(agritrust_http_requests_total{status="401"}[5m]) > 10
  for: 2m
  labels:
    severity: critical
    category: authentication
  annotations:
    summary: "Brute force attack detected"
    description: "High rate of 401 unauthorized responses from {{ $labels.client_ip }}"
    runbook_url: "https://docs.zimagritrust.co.zw/security/incidents/brute-force"
```

#### 2. Webhook Signature Failures
```yaml
- alert: WebhookSignatureFailure
  expr: rate(agritrust_business_events_total{event="webhook_signature_failed"}[1m]) > 5
  for: 1m
  labels:
    severity: critical
    category: webhooks
  annotations:
    summary: "Webhook signature verification failures"
    description: "Multiple webhook signature failures detected from {{ $labels.provider }}"
```

#### 3. SQL Injection Attempt
```yaml
- alert: SQLInjectionAttempt
  expr: rate(agritrust_business_events_total{event="sql_injection_blocked"}[1m]) > 1
  for: 1m
  labels:
    severity: critical
    category: injection
  annotations:
    summary: "SQL injection attempt blocked"
    description: "SQL injection attempt blocked from {{ $labels.client_ip }}"
```

#### 4. Escrow Fraud Alert
```yaml
- alert: EscrowFraudDetected
  expr: rate(agritrust_business_events_total{event="fraud_alert"}[5m]) > 1
  for: 1m
  labels:
    severity: critical
    category: fraud
  annotations:
    summary: "Fraud detection triggered"
    description: "Fraud detection engine flagged suspicious activity for user {{ $labels.user_id }}"
```

### High Priority Alerts (Response Within 1 Hour)

#### 5. Rate Limit Breach
```yaml
- alert: RateLimitBreach
  expr: rate(agritrust_business_events_total{event="rate_limit_exceeded"}[5m]) > 20
  for: 5m
  labels:
    severity: high
    category: rate_limiting
  annotations:
    summary: "Rate limit breaches detected"
    description: "Multiple rate limit violations from {{ $labels.client_ip }}"
```

#### 6. Unusual Transaction Volume
```yaml
- alert: UnusualTransactionVolume
  expr: rate(agritrust_business_events_total{event="transaction_created"}[1h]) > 100
  for: 10m
  labels:
    severity: high
    category: transactions
  annotations:
    summary: "Unusual transaction volume"
    description: "Transaction volume {{ $value }} exceeds normal baseline"
```

#### 7. Multiple Failed Admin Logins
```yaml
- alert: AdminLoginFailures
  expr: sum(rate(agritrust_http_requests_total{path=~"/api/v1/admin.*",status="401"}[5m])) > 5
  for: 2m
  labels:
    severity: high
    category: authentication
  annotations:
    summary: "Multiple failed admin login attempts"
    description: "Failed admin login attempts detected from {{ $labels.client_ip }}"
```

#### 8. CSRF Token Mismatch
```yaml
- alert: CSRFTokenMismatch
  expr: rate(agritrust_business_events_total{event="csrf_mismatch"}[5m]) > 10
  for: 5m
  labels:
    severity: high
    category: csrf
  annotations:
    summary: "CSRF token mismatches detected"
    description: "Multiple CSRF validation failures from {{ $labels.client_ip }}"
```

### Medium Priority Alerts (Response Within 4 Hours)

#### 9. High Error Rate
```yaml
- alert: HighErrorRate
  expr: rate(agritrust_http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 5m
  labels:
    severity: medium
    category: availability
  annotations:
    summary: "High error rate detected"
    description: "Error rate {{ $value | humanizePercentage }} exceeds 5% threshold"
```

#### 10. Database Connection Issues
```yaml
- alert: DatabaseConnectionIssues
  expr: up{job="postgres"} == 0
  for: 1m
  labels:
    severity: medium
    category: infrastructure
  annotations:
    summary: "Database connection lost"
    description: "PostgreSQL database is unreachable"
```

#### 11. Redis Connection Issues
```yaml
- alert: RedisConnectionIssues
  expr: up{job="redis"} == 0
  for: 1m
  labels:
    severity: medium
    category: infrastructure
  annotations:
    summary: "Redis connection lost"
    description: "Redis cache is unreachable"
```

#### 12. Celery Queue Backlog
```yaml
- alert: CeleryQueueBacklog
  expr: agritrust_business_events_total{event="queue_depth"} > 1000
  for: 10m
  labels:
    severity: medium
    category: background_jobs
  annotations:
    summary: "Celery queue backlog detected"
    description: "Queue depth {{ $value }} exceeds threshold for {{ $labels.queue_name }}"
```

### Low Priority Alerts (Review Within 24 Hours)

#### 13. Slow API Responses
```yaml
- alert: SlowAPIResponses
  expr: histogram_quantile(0.95, agritrust_http_request_duration_seconds) > 2
  for: 10m
  labels:
    severity: low
    category: performance
  annotations:
    summary: "Slow API responses detected"
    description: "P95 latency {{ $value }}s exceeds 2s threshold for {{ $labels.path }}"
```

#### 14. High Memory Usage
```yaml
- alert: HighMemoryUsage
  expr: process_resident_memory_bytes / 1024 / 1024 / 1024 > 4
  for: 10m
  labels:
    severity: low
    category: infrastructure
  annotations:
    summary: "High memory usage"
    description: "Memory usage {{ $value }}GB exceeds 4GB threshold"
```

#### 15. Disk Space Low
```yaml
- alert: DiskSpaceLow
  expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
  for: 10m
  labels:
    severity: low
    category: infrastructure
  annotations:
    summary: "Disk space low"
    description: "Disk usage {{ $value | humanizePercentage }} exceeds 90% threshold"
```

## Log-Based Alerts (Loki)

### 16. Secret in Logs
```yaml
- alert: SecretInLogs
  expr: |
    count_over_time({app="backend", level="error"} |~ "(SECRET_KEY|password|token)" [5m]) > 0
  labels:
    severity: critical
    category: data_leak
  annotations:
    summary: "Potential secret leaked in logs"
    description: "Secret detected in error logs"
```

### 17. Scanner Detection
```yaml
- alert: ScannerDetected
  expr: |
    count_over_time({app="backend", level="warning"} |~ "SECURITY.*scanner" [5m]) > 10
  labels:
    severity: medium
    category: reconnaissance
  annotations:
    summary: "Security scanner detected"
    description: "Security scanning activity detected from {{ $labels.client_ip }}"
```

### 18. Privilege Escalation Attempt
```yaml
- alert: PrivilegeEscalationAttempt
  expr: |
    count_over_time({app="backend", level="warning"} |~ "SECURITY.*privilege" [5m]) > 0
  labels:
    severity: high
    category: authorization
  annotations:
    summary: "Privilege escalation attempt"
    description: "Attempt to escalate privileges detected"
```

## Alert Notification Channels

### Critical Alerts
- **SMS:** +263-XXX-XXX-XXXX (Security Team)
- **Email:** security@zimagritrust.co.zw
- **Slack:** #security-alerts-critical
- **PagerDuty:** Security On-Call

### High Priority Alerts
- **Email:** security@zimagritrust.co.zw
- **Slack:** #security-alerts
- **Microsoft Teams:** Security Channel

### Medium Priority Alerts
- **Email:** devops@zimagritrust.co.zw
- **Slack:** #ops-alerts

### Low Priority Alerts
- **Email:** devops@zimagritrust.co.zw
- **Slack:** #ops-alerts (non-urgent)

## Alert Suppression Rules

### Maintenance Windows
```yaml
- match:
    alertname: "HighErrorRate"
  start_time: "02:00"
  end_time: "04:00"
  timezone: "Africa/Harare"
  comment: "Scheduled maintenance window"
```

### Known Safe IPs
```yaml
- match_re:
    client_ip: "(192.168.1.0/24|10.0.0.0/8)"
  alertname: "BruteForceAttackDetected"
  comment: "Internal network - ignore brute force alerts"
```

### Load Testing
```yaml
- match:
    environment: "staging"
  alertname: "RateLimitBreach"
  comment: "Load testing in progress"
```

## Grafana Dashboard Configuration

### Security Overview Dashboard
- **Panel 1:** Failed Authentication Rate (graph)
- **Panel 2:** Webhook Signature Failures (stat)
- **Panel 3:** Fraud Alerts (table)
- **Panel 4:** Rate Limit Violations (graph)
- **Panel 5:** CSRF Failures (stat)
- **Panel 6:** Admin Login Attempts (graph)
- **Panel 7:** SQL Injection Attempts (stat)
- **Panel 8:** Top Suspicious IPs (table)

## Incident Response Procedures

### Critical Alert Response
1. **Acknowledge alert** within 5 minutes
2. **Investigate source** - check logs, identify affected systems
3. **Contain threat** - block IP, revoke sessions if needed
4. **Document incident** - create incident ticket
5. **Notify stakeholders** - security team, management
6. **Post-mortem** - document root cause and prevention measures

### High Priority Alert Response
1. **Acknowledge alert** within 30 minutes
2. **Assess impact** - determine if immediate action needed
3. **Implement fix** - if critical, escalate to critical
4. **Monitor** - watch for related alerts
5. **Document** - update incident log

### Medium/Low Priority Alert Response
1. **Acknowledge alert** within 4 hours
2. **Investigate** - determine if action needed
3. **Schedule fix** - add to backlog if not urgent
4. **Monitor** - watch for escalation

## Testing Alerts

### Alert Testing Procedure
1. **Test in staging** before production
2. **Verify notification channels** - ensure alerts are received
3. **Check alert thresholds** - adjust if too sensitive
4. **Document test results** - record in alert testing log

### Test Commands
```bash
# Trigger brute force alert
for i in {1..20}; do curl -X POST https://staging.zimagritrust.co.zw/api/v1/auth/login -d '{"phone":"test","password":"wrong"}'; done

# Trigger webhook signature failure
curl -X POST https://staging.zimagritrust.co.zw/api/v1/whatsapp/webhook -H "X-WhatsApp-Signature: invalid" -d '{"test":true}'

# Trigger rate limit alert
for i in {1..30}; do curl https://staging.zimagritrust.co.zw/api/v1/listings; done
```

## Maintenance

### Weekly Tasks
- Review alert firing history
- Adjust thresholds if needed
- Update suppression rules
- Test notification channels

### Monthly Tasks
- Review all alert rules
- Add new alerts for emerging threats
- Remove obsolete alerts
- Update documentation

### Quarterly Tasks
- Full alert audit
- Update runbooks
- Train team on new alerts
- Review notification channel effectiveness

## Contact Information

- **Security Team:** security@zimagritrust.co.zw
- **DevOps Team:** devops@zimagritrust.co.zw
- **On-Call:** +263-XXX-XXX-XXXX
- **Emergency:** +263-XXX-XXX-XXXX

---

**Last Updated:** 2026-05-27
**Next Review:** 2026-06-27
