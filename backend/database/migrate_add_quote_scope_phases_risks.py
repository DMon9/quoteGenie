"""
Migration: Add scope, phases and risks columns to quotes table
Run this to update existing databases
"""

import sqlite3
import os

# Try common database paths
DB_PATHS = [
    os.getenv("DATABASE_PATH", "/data/estimategenie.db"),
    "/app/estimategenie.db",
    "./estimategenie.db"
]


def migrate():
    """Add scope, phases, and risks columns to quotes table."""
    db_path = None
    for p in DB_PATHS:
        if os.path.exists(p):
            db_path = p
            break

    if not db_path:
        db_path = "/app/estimategenie.db"

    print(f"Migrating database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(quotes)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'scope' in columns and 'phases' in columns and 'risks' in columns:
            print("✓ scope, phases, and risks columns already exist")
        else:
            if 'scope' not in columns:
                print("Adding scope column...")
                cursor.execute("ALTER TABLE quotes ADD COLUMN scope TEXT")
            if 'phases' not in columns:
                print("Adding phases column...")
                cursor.execute("ALTER TABLE quotes ADD COLUMN phases TEXT")
            if 'risks' not in columns:
                print("Adding risks column...")
                cursor.execute("ALTER TABLE quotes ADD COLUMN risks TEXT")
            conn.commit()
            print("✓ Added new columns: scope, phases, risks")

        conn.close()
        print("Migration complete!")
        return True

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False


if __name__ == '__main__':
    migrate()
