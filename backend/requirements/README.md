# Python Dependencies

This directory contains Python requirement files for the backend.

## Files

- `requirements.txt` - Core dependencies for the main application
- `requirements-core.txt` - Essential core dependencies
- `requirements-ml.txt` - Machine learning dependencies

## Usage

Install dependencies:

```bash
# Install all dependencies
pip install -r requirements.txt

# Install ML dependencies
pip install -r requirements-ml.txt
```

## Notes

- Dependencies are managed via Docker in production
- Use virtual environments for local development
- Keep versions pinned for reproducibility
