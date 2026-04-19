import sys
import os
from sqlalchemy import text, inspect
from app.db.session import engine

def migrate():
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        # --- USERS TABLE MIGRATION ---
        print("[INFO] Checking 'users' table...")
        
        # We'll use direct SQL with IF NOT EXISTS where possible to be safe
        
        # Rename wallet_balance to balance_zig if possible
        try:
            inspector = inspect(engine)
            columns = [c['name'] for c in inspector.get_columns("users")]
            if "wallet_balance" in columns and "balance_zig" not in columns:
                print("[ACTION] Renaming 'wallet_balance' to 'balance_zig' in 'users'...")
                conn.execute(text("ALTER TABLE users RENAME COLUMN wallet_balance TO balance_zig"))
                conn.commit()
        except Exception as e:
            print(f"[DEBUG] Rename wallet_balance failed (might already be done): {e}")

        # Rename pending_earnings to pending_usd if possible
        try:
            inspector = inspect(engine)
            columns = [c['name'] for c in inspector.get_columns("users")]
            if "pending_earnings" in columns and "pending_usd" not in columns:
                print("[ACTION] Renaming 'pending_earnings' to 'pending_usd' in 'users'...")
                conn.execute(text("ALTER TABLE users RENAME COLUMN pending_earnings TO pending_usd"))
                conn.commit()
        except Exception as e:
            print(f"[DEBUG] Rename pending_earnings failed (might already be done): {e}")
            
        # Add missing columns using IF NOT EXISTS
        add_cols = [
            ("balance_zig", "DOUBLE PRECISION DEFAULT 0.0"),
            ("pending_usd", "DOUBLE PRECISION DEFAULT 0.0"),
            ("pending_zig", "DOUBLE PRECISION DEFAULT 0.0"),
        ]
        
        for col, col_type in add_cols:
            print(f"[ACTION] Ensuring column '{col}' exists in 'users'...")
            conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {col_type}"))
            conn.commit()

        # --- AGENTS TABLE MIGRATION ---
        print("[INFO] Checking 'agents' table...")
        
        agent_add_cols = [
            ("province", "VARCHAR(50)"),
            ("district", "VARCHAR(50)"),
            ("rating", "DOUBLE PRECISION DEFAULT 5.0"),
            ("current_load", "INTEGER DEFAULT 0"),
            ("is_available", "BOOLEAN DEFAULT TRUE"),
            ("avg_response_time", "DOUBLE PRECISION DEFAULT 24.0"),
            ("updated_at", "TIMESTAMP WITH TIME ZONE")
        ]
        
        for col, col_type in agent_add_cols:
            print(f"[ACTION] Ensuring column '{col}' exists in 'agents'...")
            conn.execute(text(f"ALTER TABLE agents ADD COLUMN IF NOT EXISTS {col} {col_type}"))
            conn.commit()

    print("SUCCESS: Schema synchronization complete!")

if __name__ == "__main__":
    # Add project root to sys.path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(project_root)
    migrate()
