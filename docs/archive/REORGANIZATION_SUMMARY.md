# Project Reorganization Summary

## Overview
Files and folders have been reorganized for better traceability and debugging.

## New Directory Structure

```
Agric/
├── config/                          # Docker & environment configs
│   ├── docker-compose.monitoring.yml
│   ├── docker-compose.override.yml
│   ├── Dockerfile.scheduler
│   ├── .env.example
│   ├── requirements.scheduler.txt
│   └── README.md
├── backend/
│   ├── scripts/                     # Backend utility scripts
│   │   ├── calibrate_ai_core.py
│   │   ├── calibrate_models.py
│   │   ├── recreate_db.py
│   │   ├── reset_limits.py
│   │   ├── seed.py
│   │   ├── sync_recruitment_schema.py
│   │   └── README.md
│   ├── requirements/                # Python dependencies
│   │   ├── requirements.txt
│   │   ├── requirements-core.txt
│   │   ├── requirements-ml.txt
│   │   └── README.md
│   ├── utils/                       # Helper modules
│   │   └── README.md
│   └── app/                         # Main application (unchanged)
├── docs/
│   ├── api/                         # API documentation
│   │   ├── API_REFERENCE.md
│   │   └── README.md
│   ├── guides/                      # Developer guides
│   │   ├── DEVELOPER_GUIDE.md
│   │   ├── MIGRATION_GUIDES.md
│   │   ├── CONTRIBUTING.md
│   │   ├── TERMS_AND_CONDITIONS.md
│   │   ├── Developer_and_Deployment_Guide.md
│   │   └── README.md
│   ├── system/                      # System specifications
│   │   ├── SYSTEM_SPECIFICATION.md
│   │   ├── ADMIN_PANEL_ANALYSIS.md
│   │   ├── COMMAND_CENTER.md
│   │   ├── System_Architecture_and_API.md
│   │   ├── Project_Directory_Tree.txt
│   │   └── README.md
│   ├── training/                    # Training materials
│   │   ├── AGENT_TRAINING_MANUAL.md
│   │   ├── Platform_Walkthroughs.md
│   │   ├── User_and_Agent_Manual.md
│   │   ├── WHATSAPP_ENHANCED_GUIDE.md
│   │   └── README.md
│   ├── ZimAgritrust_Full_Documentation.md
│   ├── ZimAgritrust_Master_Documentation_v4.0.md
│   └── assets/
├── tests/
│   ├── unit/                        # Unit tests
│   ├── integration/                 # Integration tests (existing)
│   └── README.md
├── docker-compose.yml               # Main compose file (root)
└── [other root files unchanged]
```

## Key Changes

### Configuration Files
- Moved Docker and environment configs to `config/`
- Kept `docker-compose.yml` at root (required by Docker Compose)
- Updated `docker-compose.yml` to reference `config/Dockerfile.scheduler`

### Backend Scripts
- Moved all utility scripts from `backend/` to `backend/scripts/`
- Scripts now organized in dedicated location

### Dependencies
- Grouped all requirements files in `backend/requirements/`
- Easier to manage Python dependencies

### Documentation
- Categorized documentation by type:
  - `docs/api/` - API reference
  - `docs/guides/` - Developer guides
  - `docs/system/` - System specs
  - `docs/training/` - Training materials

### Testing
- Created `tests/unit/` for unit tests
- Added comprehensive README in `tests/`

### Utilities
- Created `backend/utils/` for helper modules

## Benefits

1. **Better Traceability**: Files grouped by purpose and type
2. **Easier Debugging**: Clear separation of concerns
3. **Improved Navigation**: Logical directory structure
4. **Documentation**: README files in each major directory
5. **Maintainability**: Easier to find and update files

## Usage Notes

### Running Scripts
```bash
# Run backend scripts via Docker
docker-compose exec backend python scripts/seed.py
```

### Installing Dependencies
```bash
# From backend directory
pip install -r requirements/requirements.txt
```

### Starting Services
```bash
# Use docker-compose from root
docker-compose up
```

## Migration Notes

- Docker Compose configuration updated to reference new paths
- All file movements preserve relative path relationships
- No code changes required for backend application
- Import paths remain unchanged for Python modules
