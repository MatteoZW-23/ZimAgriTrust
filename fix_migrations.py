import re
from pathlib import Path

# Pattern to find enum creation lines
enum_create_pattern = r'(\w+_enum)\.create\(op\.get_bind\(\), checkfirst=True\)'
# Pattern to find enum usage in columns
enum_usage_pattern = r'sa\.Column\("(\w+)", (\w+_enum),'

# Directory containing migration files
migrations_dir = Path("c:/Users/MJ/Desktop/Agric/backend/alembic/versions")

# Process each migration file
for migration_file in migrations_dir.glob("*.py"):
    if migration_file.name.startswith("__"):
        continue
    
    content = migration_file.read_text()
    original_content = content
    
    # Find all enum definitions
    enum_defs = {}
    for match in re.finditer(r'(\w+_enum) = sa\.Enum\([^)]+\)', content):
        enum_name = match.group(1)
        # Extract the enum values and name
        enum_def_match = re.search(rf'{enum_name} = sa\.Enum\(([^)]+)\)', content)
        if enum_def_match:
            enum_defs[enum_name] = enum_def_match.group(1)
    
    if not enum_defs:
        continue
    
    # Add text import if not present
    if 'from sqlalchemy import text' not in content:
        content = content.replace(
            'from alembic import op',
            'from sqlalchemy import text\nfrom alembic import op'
        )
    
    # Add bind = op.get_bind() if not present in upgrade function
    if 'bind = op.get_bind()' not in content:
        content = content.replace(
            'def upgrade() -> None:',
            'def upgrade() -> None:\n    bind = op.get_bind()'
        )
    
    # Replace enum.create() calls with try/except blocks
    for enum_name, enum_def in enum_defs.items():
        # Extract enum type name from the definition
        type_name_match = re.search(r'name="([^"]+)"', enum_def)
        if type_name_match:
            type_name = type_name_match.group(1)
            # Extract enum values
            values_match = re.search(r'"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"', enum_def)
            if values_match:
                # This is a simple approach - for complex enums, we might need better parsing
                # For now, let's just use the raw definition
                pass
    
    # Replace enum usage in columns with postgresql.ENUM
    for enum_name in enum_defs.keys():
        # Find the type name from the enum definition
        type_name_match = re.search(rf'{enum_name} = sa\.Enum\([^)]*name="([^"]+)"[^)]*\)', content)
        if type_name_match:
            type_name = type_name_match.group(1)
            # Replace sa.Column("field", enum_name, ...) with postgresql.ENUM
            content = re.sub(
                rf'sa\.Column\("([^"]+)", {enum_name},',
                rf'sa.Column("\1", postgresql.ENUM(name="{type_name}", create_type=False),',
                content
            )
    
    # Replace enum.create() calls with try/except blocks
    for enum_name in enum_defs.keys():
        type_name_match = re.search(rf'{enum_name} = sa\.Enum\([^)]*name="([^"]+)"[^)]*\)', content)
        if type_name_match:
            type_name = type_name_match.group(1)
            # Extract the enum values from the definition
            values_match = re.search(rf'{enum_name} = sa\.Enum\(([^)]+)\)', content)
            if values_match:
                enum_values = values_match.group(1)
                # Replace the .create() call
                old_pattern = rf'{enum_name}\.create\(op\.get_bind\(\), checkfirst=True\)'
                new_code = f'''try:
        bind.execute(text("CREATE TYPE {type_name} AS ENUM ({enum_values})"))
    except Exception:
        pass'''
                content = re.sub(old_pattern, new_code, content)
    
    if content != original_content:
        migration_file.write_text(content)
        print(f"Fixed {migration_file.name}")

print("Done!")
