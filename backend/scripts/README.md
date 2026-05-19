# Backend Scripts

This directory contains utility scripts for backend operations and maintenance.

## Scripts

- `recreate_db.py` - Recreate database schema
- `reset_limits.py` - Reset user limits
- `seed.py` - Seed database with initial data
- `seed_super_admin.py` - Seed super admin user
- `seed_supplier.py` - Seed supplier data
- `sync_recruitment_schema.py` - Sync recruitment schema
- `sync_ussd_pins.py` - Sync USSD PINs
- `migrate_training_materials.py` - Migrate training materials

## Usage

Run scripts from the backend directory using Docker:

```bash
# Run a script
docker-compose exec backend python scripts/seed.py

# Recreate database
docker-compose exec backend python scripts/recreate_db.py
```

## Notes

- All scripts should be run within the Docker container
- Ensure database is running before executing scripts
- Backup data before running destructive operations
