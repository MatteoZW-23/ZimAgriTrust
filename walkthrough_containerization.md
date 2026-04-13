# AgriTrust: Sovereign Infrastructure Overview

The AgriTrust platform is now fully containerized, providing a robust, high-performance environment for agricultural trade management in Zimbabwe.

## 🏗️ Master Infrastructure (Docker Compose)

The entire ecosystem is managed through a single `docker-compose.yml` file, ensuring parity across dev, staging, and production.

### 🔌 Orchestrated Services

| Service | Technology | Port | Role |
| :--- | :--- | :--- | :--- |
| **PostgreSQL** | Postgres 16 | 5434 | Sovereign Ledger & Identity Store |
| **Redis** | Redis 7 | 6380 | Session Management & Market Cache |
| **Backend** | Python (FastAPI) | 8080 | Core Escrow & API Logic |
| **Agent Dashboard** | React (Vite) | 3000 | Command Center User Interface |
| **Node Gateway** | Node.js | 3005 | National Sync & Telemetry |
| **USSD Simulator** | Python (Flask) | 5000 | Offline Feature Phone Mock Environment |

---

## 🚀 Deployment Command

To launch the complete enterprise suite from a clean state:

```powershell
docker compose up -d --build
```

## 📊 Operations & Governance

1. **Escrow Security**: All transactions are programmatically locked in the backend fintech module, governed by automated trust scoring.
2. **Zero-Trust Monitoring**: Real-time fraud detection and risk watch panels are accessible via the Dashboard.
3. **Institutional Parity**: The system enforces regional pricing alignment across Zimbabwe's provinces.

---

> [!IMPORTANT]
> **Final Composition State**: The platform is now deterministic, professionalized, and fully documented for one-command execution.
