import sqlite3
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

class DatabaseService:
    """Handles all database operations"""
    
    def __init__(self, db_path: str = "estimategenie.db"):
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Quotes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id TEXT PRIMARY KEY,
                project_type TEXT,
                image_path TEXT,
                vision_results TEXT,
                reasoning TEXT,
                estimate TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Materials table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                price REAL,
                unit TEXT,
                description TEXT,
                updated_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def is_connected(self) -> bool:
        """Check database connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
            return True
        except:
            return False
    
    async def save_quote(self, quote_data: Dict) -> bool:
        """Save a new quote to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO quotes (
                    id, project_type, image_path, vision_results,
                    reasoning, estimate, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                quote_data["id"],
                quote_data["project_type"],
                quote_data["image_path"],
                json.dumps(quote_data["vision_results"]),
                json.dumps(quote_data["reasoning"]),
                json.dumps(quote_data["estimate"]),
                quote_data["status"],
                quote_data["created_at"].isoformat(),
                datetime.utcnow().isoformat()
            ))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Database save error: {e}")
            return False
        finally:
            conn.close()
    
    async def get_quote(self, quote_id: str) -> Optional[Dict]:
        """Retrieve a quote by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_dict(row)
    
    async def list_quotes(
        self,
        limit: int = 10,
        offset: int = 0,
        project_type: Optional[str] = None
    ) -> List[Dict]:
        """List quotes with pagination"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if project_type:
            cursor.execute("""
                SELECT * FROM quotes 
                WHERE project_type = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (project_type, limit, offset))
        else:
            cursor.execute("""
                SELECT * FROM quotes 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    async def update_quote(self, quote_id: str, updates: Dict[str, Any]) -> bool:
        """Update a quote"""
        # Define allowed fields to prevent SQL injection
        ALLOWED_FIELDS = {
            "project_type", "image_path", "vision_results", 
            "reasoning", "estimate", "status"
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Build dynamic update query with validated fields
            fields = []
            values = []
            invalid_field_count = 0
            
            for key, value in updates.items():
                # Validate field name against whitelist
                if key not in ALLOWED_FIELDS:
                    # Count invalid fields without logging field names (security)
                    invalid_field_count += 1
                    continue
                    
                if key in ["estimate", "vision_results", "reasoning"]:
                    value = json.dumps(value)
                fields.append(f"{key} = ?")
                values.append(value)
            
            # Log security event if invalid fields were attempted
            if invalid_field_count > 0:
                import sys
                print(f"Security: Rejected {invalid_field_count} invalid field(s) in update attempt", file=sys.stderr)
            
            if not fields:
                # No valid fields to update
                return False
            
            fields.append("updated_at = ?")
            values.append(datetime.utcnow().isoformat())
            values.append(quote_id)
            
            query = f"UPDATE quotes SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(query, values)
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Database update error: {e}")
            return False
        finally:
            conn.close()
    
    async def delete_quote(self, quote_id: str) -> bool:
        """Delete a quote"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM quotes WHERE id = ?", (quote_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Convert database row to dictionary"""
        data = dict(row)
        
        # Parse JSON fields
        for field in ["vision_results", "reasoning", "estimate"]:
            if field in data and data[field]:
                try:
                    data[field] = json.loads(data[field])
                except:
                    data[field] = {}
        
        return data
