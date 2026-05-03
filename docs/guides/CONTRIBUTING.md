# Contributing to ZimAgritrust

Thank you for your interest in the ZimAgritrust Sovereign Platform. We welcome contributions from the agricultural technology and data science community.

## Development Workflow
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add some amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

## Intelligence Modeling
When adding new ML models, please follow the Sovereign Engineering patterns established in `backend/app/ml/` and include a corresponding research notebook in `research/notebooks/`.

## Quality Standards
- All code must pass `pytest tests/`.
- Document all API endpoints in `docs/API.md`.
- Ensure new models are registered in `scripts/system_audit.py`.
