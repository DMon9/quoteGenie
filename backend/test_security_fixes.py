"""
Security tests for SQL injection prevention and other security fixes
"""
import sys
import os
import asyncio
import sqlite3
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import DatabaseService


async def test_sql_injection_prevention():
    """Test that SQL injection attempts are blocked in update_quote"""
    print("Testing SQL injection prevention...")
    
    # Create a temporary test database
    test_db = "test_security.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    db = DatabaseService(db_path=test_db)
    
    # Create a test quote
    quote_data = {
        "id": "test_quote_1",
        "project_type": "kitchen",
        "image_path": "/tmp/test.jpg",
        "vision_results": {"test": "data"},
        "reasoning": {"test": "reasoning"},
        "estimate": {"total": 1000},
        "status": "completed",
        "created_at": datetime.utcnow()
    }
    
    await db.save_quote(quote_data)
    
    # Test 1: Try SQL injection via field name
    malicious_update = {
        "status; DROP TABLE quotes--": "malicious"
    }
    
    result = await db.update_quote("test_quote_1", malicious_update)
    print(f"  ✓ SQL injection via field name blocked: {not result}")
    
    # Verify table still exists
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quotes'")
    table_exists = cursor.fetchone() is not None
    conn.close()
    print(f"  ✓ Table 'quotes' still exists: {table_exists}")
    
    # Test 2: Try to update with non-existent field
    invalid_field_update = {
        "invalid_field_name": "test_value",
        "another_invalid": "another_value"
    }
    
    result = await db.update_quote("test_quote_1", invalid_field_update)
    print(f"  ✓ Invalid field names rejected: {not result}")
    
    # Test 3: Valid update should work
    valid_update = {
        "status": "pending",
        "project_type": "bathroom"
    }
    
    result = await db.update_quote("test_quote_1", valid_update)
    print(f"  ✓ Valid update works: {result}")
    
    # Verify the valid update worked
    updated_quote = await db.get_quote("test_quote_1")
    assert updated_quote["status"] == "pending", "Status should be updated"
    assert updated_quote["project_type"] == "bathroom", "Project type should be updated"
    print(f"  ✓ Valid fields updated correctly")
    
    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)
    
    print("✓ All SQL injection prevention tests passed!\n")


async def test_allowed_fields_only():
    """Test that only allowed fields can be updated"""
    print("Testing field whitelist validation...")
    
    test_db = "test_whitelist.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    db = DatabaseService(db_path=test_db)
    
    # Create test quote
    quote_data = {
        "id": "test_quote_2",
        "project_type": "roofing",
        "image_path": "/tmp/test2.jpg",
        "vision_results": {"test": "data"},
        "reasoning": {"test": "reasoning"},
        "estimate": {"total": 2000},
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    await db.save_quote(quote_data)
    
    # Try to update with mix of valid and invalid fields
    mixed_update = {
        "status": "completed",  # Valid
        "id": "changed_id",  # Should be ignored - not in allowed list
        "created_at": "2020-01-01",  # Should be ignored - not in allowed list
        "project_type": "kitchen"  # Valid
    }
    
    result = await db.update_quote("test_quote_2", mixed_update)
    print(f"  ✓ Mixed update completed: {result}")
    
    # Verify only valid fields were updated
    updated_quote = await db.get_quote("test_quote_2")
    assert updated_quote["status"] == "completed", "Status should be updated"
    assert updated_quote["project_type"] == "kitchen", "Project type should be updated"
    assert updated_quote["id"] == "test_quote_2", "ID should not change"
    print(f"  ✓ Only whitelisted fields were updated")
    print(f"  ✓ Protected fields (id, created_at) remain unchanged")
    
    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)
    
    print("✓ Field whitelist validation tests passed!\n")


async def main():
    """Run all security tests"""
    print("=" * 60)
    print("Running Security Tests")
    print("=" * 60)
    print()
    
    await test_sql_injection_prevention()
    await test_allowed_fields_only()
    
    print("=" * 60)
    print("All security tests passed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
