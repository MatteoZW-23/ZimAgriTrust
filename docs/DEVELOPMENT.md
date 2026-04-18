# Developer Onboarding Guide

## Getting Started
1. Clone the repository.
2. Ensure you have Docker OR run services locally. 

## Local Setup (Without Docker)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd agent-dashboard
npm install
npm run dev
```

## Contributing
* Follow PEP 8 guidelines for Python.
* Use conventional commits.
* Submit PRs against the `development` branch.
