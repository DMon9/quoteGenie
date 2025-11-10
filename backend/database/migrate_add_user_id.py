"""
Migration: Add user_id column to quotes table
Run this to update existing databases
"""

import sqlite3
import os

# Try multiple possible database paths
DB_PATHS = [
    os.getenv("DATABASE_PATH", "/data/estimategenie.db"),
    "/app/estimategenie.db",
    "./estimategenie.db"
]

def migrate():
    """Add user_id column to quotes table"""
    
    # Find the database
    db_path = None
    for path in DB_PATHS:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        # Try to connect to default path anyway (will create if needed)
        db_path = "/app/estimategenie.db"
    
    print(f"Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(quotes)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'user_id' in columns:
            print("✓ user_id column already exists")
        else:
            print("Adding user_id column...")
            cursor.execute("ALTER TABLE quotes ADD COLUMN user_id TEXT")
            conn.commit()
            print("✓ user_id column added successfully")
        
        conn.close()
        print("Migration complete!")
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate()
