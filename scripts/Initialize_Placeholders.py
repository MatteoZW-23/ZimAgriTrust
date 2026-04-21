import os
from pathlib import Path

# Create missing directories
dirs = [
    "docs", 
    "scripts", 
    "tests", 
    "monitoring", 
    "kubernetes", 
    ".github/workflows",
    "backend/alembic/versions", 
    "backend/scripts", 
    "backend/tests",
    "research/data/raw", 
    "research/data/processed", 
    "research/data/external", 
    "research/reports/figures"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Create placeholder files
files = [
    "docs/API.md", 
    "docs/DEPLOYMENT.md", 
    "docs/DEVELOPMENT.md",
    "docs/USER_GUIDE.md",
    "docs/AGENT_GUIDE.md",
    "docs/ARCHITECTURE.md",
    "scripts/deploy.sh", 
    "scripts/backup.sh",
    "scripts/monitor.sh",
    "scripts/rollback.sh",
    "monitoring/prometheus.yml",
    "monitoring/alerts.yml",
    "monitoring/logging.conf"
]

for f in files:
    if not os.path.exists(f):
        Path(f).touch()

print("Directories and placeholders created successfully.")
