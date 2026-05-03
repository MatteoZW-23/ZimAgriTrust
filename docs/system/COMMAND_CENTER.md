# Admin Command Center Documentation

## Overview

The Admin Command Center is a powerful administrative interface that provides system administrators with comprehensive control over the ZimAgritrust platform. It offers real-time monitoring, system diagnostics, and command-line style operations for advanced platform management.

## Features

### 1. Terminal Interface
A command-line style interface for executing administrative commands with full history tracking and color-coded output.

### 2. System Monitoring
Real-time dashboard displaying:
- Platform metrics (users, listings, orders, escrow)
- Service status (database, WhatsApp, AI models, scraper)
- Agent network statistics
- Financial metrics

### 3. Operations Panel
Quick-access buttons for common administrative tasks:
- Platform synchronization
- Financial reconciliation
- Trust score recomputation
- Data scraping and cleaning
- Database maintenance
- System diagnostics
- Emergency lockdown

## Access

**Role Required:** ADMIN only

**Location:** Admin Dashboard → System Utilities → Command Center

**URL:** `?portal=hq` (HQ Portal)

## Terminal Commands

### System Commands

```bash
help, ?              # Show help message with all available commands
clear, cls           # Clear terminal history
status, sys          # Display comprehensive system status
diagnostics, diag    # Run system diagnostics checks
realtime, rt         # Show real-time statistics
version              # Show platform version information
uptime               # Show system uptime
time, date           # Show current date/time
```

### Platform Operations

```bash
sync                 # Synchronize platform data
reconcile            # Reconcile financial records
recompute-trust      # Recalculate all user trust scores
lockdown on          # Enable emergency platform lockdown
lockdown off         # Disable emergency lockdown
```

### Database Queries

```bash
users                # List all users with details
transactions         # List all transactions
audit, logs          # Show recent system audit logs
```

### Maintenance Operations

```bash
maintenance cleanup  # Clean up old data and expired records
maintenance optimize # Optimize database queries and indexes
maintenance vacuum   # Vacuum database (PostgreSQL)
maintenance reindex  # Reindex database tables
```

### AI & Data Operations

```bash
scrape prices        # Scrape market price data
scrape news          # Scrape agricultural news
scrape weather       # Scrape weather data
scrape all           # Run all scrapers

clean prices         # Clean price data
clean listings       # Clean listing data
clean transactions   # Clean transaction data
clean all            # Run all cleaning pipelines
```

## API Endpoints

### Command Center Endpoints

#### GET `/admin/command-center/system/health`
Returns comprehensive system health metrics including database status, user counts, order statistics, and service status.

**Response:**
```json
{
  "status": "operational",
  "timestamp": "2026-04-25T10:30:00Z",
  "database": {
    "status": "healthy",
    "connection": "active"
  },
  "metrics": {
    "users": { "total": 1250, "active": 980, "new_24h": 45 },
    "listings": { "total": 450, "active": 320 },
    "orders": { "total": 890, "pending": 23, "new_24h": 67 },
    "financial": { "escrow_value": 45678.90, "currency": "USD" },
    "agents": { "total": 45, "active": 38 }
  },
  "services": {
    "api": "online",
    "database": "healthy",
    "whatsapp": "connected",
    "ai_models": "loaded",
    "scraper": "idle"
  }
}
```

#### GET `/admin/command-center/system/diagnostics`
Runs comprehensive system diagnostics and returns health check results.

**Response:**
```json
{
  "timestamp": "2026-04-25T10:30:00Z",
  "checks": [
    {
      "name": "Database Connection",
      "status": "pass",
      "message": "Database connection successful"
    },
    {
      "name": "Data Integrity",
      "status": "pass",
      "message": "Found 0 orphaned orders"
    },
    {
      "name": "Order Processing",
      "status": "warning",
      "message": "Found 2 orders stuck in processing"
    }
  ]
}
```

#### GET `/admin/command-center/system/stats/realtime`
Returns real-time platform statistics for the last hour and 24 hours.

**Response:**
```json
{
  "timestamp": "2026-04-25T10:30:00Z",
  "last_hour": {
    "new_users": 5,
    "new_orders": 12,
    "new_listings": 8
  },
  "last_24h": {
    "new_users": 45,
    "new_orders": 67,
    "new_listings": 34,
    "revenue": 12345.67
  },
  "current": {
    "active_users": 980,
    "pending_orders": 23,
    "active_listings": 320
  }
}
```

#### POST `/admin/command-center/system/maintenance`
Executes system maintenance operations.

**Parameters:**
- `operation`: cleanup | optimize | vacuum | reindex

**Response:**
```json
{
  "operation": "optimize",
  "timestamp": "2026-04-25T10:30:00Z",
  "status": "success",
  "message": "Database optimization completed"
}
```

#### POST `/admin/command-center/system/emergency/lockdown`
Toggles emergency platform lockdown mode.

**Parameters:**
- `enable`: boolean
- `reason`: string

**Response:**
```json
{
  "lockdown_enabled": true,
  "reason": "Security incident detected",
  "activated_by": "Admin User",
  "timestamp": "2026-04-25T10:30:00Z",
  "message": "Emergency lockdown enabled"
}
```

#### GET `/admin/command-center/system/logs/recent`
Retrieves recent system logs.

**Parameters:**
- `limit`: number (default: 50)
- `level`: all | error | warning | info

**Response:**
```json
[
  {
    "timestamp": "2026-04-25T10:30:00Z",
    "level": "info",
    "message": "System operational",
    "source": "command_center"
  }
]
```

### Existing System Endpoints

#### POST `/admin/system/sync-platform`
Synchronizes platform data with fresh demo data.

#### POST `/admin/system/reconcile`
Runs financial reconciliation across all transactions.

#### POST `/admin/system/recompute-trust`
Recalculates trust scores for all users.

#### POST `/admin/system/lockdown`
Toggles system lockdown mode (legacy endpoint).

**Parameters:**
- `enable`: boolean

## Usage Examples

### Example 1: Check System Health
```bash
> status
```
Output:
```
╔════════════════════════════════════════════════════════════╗
║                    SYSTEM STATUS REPORT                    ║
╚════════════════════════════════════════════════════════════╝

PLATFORM METRICS:
  Total Users:         1250
  Active Users:        980
  Active Listings:     320
  Pending Orders:      23
  Escrow Value:        $45678.90

AGENT NETWORK:
  Total Agents:        45
  Active Agents:       38

SERVICES:
  Database:            healthy
  WhatsApp:            connected
  AI Models:           5 loaded
  Data Scraper:        idle

Last Updated:          4/25/2026, 10:30:00 AM
```

### Example 2: Run System Diagnostics
```bash
> diagnostics
```
Output:
```
CHECK                          STATUS         MESSAGE
────────────────────────────────────────────────────────────────────────────────
Database Connection            PASS           Database connection successful
Data Integrity                 PASS           Found 0 orphaned orders
Order Processing               WARNING        Found 2 orders stuck in processing
Escrow Balance                 PASS           Total escrow: $45678.90

Timestamp: 4/25/2026, 10:30:00 AM
```

### Example 3: View Real-time Statistics
```bash
> realtime
```
Output:
```
╔════════════════════════════════════════════════════════════╗
║                  REAL-TIME STATISTICS                      ║
╚════════════════════════════════════════════════════════════╝

LAST HOUR:
  New Users:           5
  New Orders:          12
  New Listings:        8

LAST 24 HOURS:
  New Users:           45
  New Orders:          67
  New Listings:        34
  Revenue:             $12345.67

CURRENT:
  Active Users:        980
  Pending Orders:      23
  Active Listings:     320

Timestamp:             4/25/2026, 10:30:00 AM
```

### Example 4: Emergency Lockdown
```bash
> lockdown on
```
Output:
```
⚠ LOCKDOWN MODE ENABLED
{
  "lockdown_enabled": true,
  "reason": "Manual lockdown via command center",
  "activated_by": "Admin User",
  "timestamp": "2026-04-25T10:30:00Z",
  "message": "Emergency lockdown enabled"
}
```

## Security Considerations

1. **Admin-Only Access**: Command Center is restricted to users with ADMIN role
2. **Audit Logging**: All commands are logged in the system audit trail
3. **Confirmation Prompts**: Dangerous operations (like lockdown) require confirmation
4. **Session Tracking**: All operations are tied to the authenticated admin user
5. **Rate Limiting**: Consider implementing rate limits for sensitive operations

## Best Practices

1. **Regular Monitoring**: Check system status daily
2. **Diagnostic Runs**: Run diagnostics weekly or after major updates
3. **Maintenance Windows**: Schedule maintenance operations during low-traffic periods
4. **Backup Before Operations**: Always ensure recent backups before running maintenance
5. **Document Actions**: Use the audit logs to track all administrative actions
6. **Test in Staging**: Test commands in staging environment before production use

## Troubleshooting

### Command Not Recognized
- Type `help` to see all available commands
- Check for typos in command names
- Ensure you have the latest version

### API Connection Errors
- Verify backend is running
- Check authentication token is valid
- Review network connectivity

### Slow Response Times
- Check database connection
- Review system resource usage
- Consider running `maintenance optimize`

### Stuck Operations
- Check system logs for errors
- Verify database connectivity
- Contact system administrator if issue persists

## Future Enhancements

- [ ] Real-time WebSocket updates for system metrics
- [ ] Custom command scripting support
- [ ] Scheduled maintenance operations
- [ ] Advanced query builder for database operations
- [ ] Export system reports to PDF/CSV
- [ ] Multi-admin collaboration features
- [ ] Command history search and filtering
- [ ] Automated health check alerts

## Support

For issues or questions about the Command Center:
- Check system logs: `> audit`
- Run diagnostics: `> diagnostics`
- Contact: admin@ZimAgritrust.co.zw
