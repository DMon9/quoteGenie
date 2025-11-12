"""
Test registration error handling and response format
"""
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_weak_password_error_format():
    """Test that weak password returns proper error structure"""
    payload = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "weak",  # Too short, no numbers
        "plan": "free"
    }
    
    response = client.post("/api/v1/auth/register", json=payload)
    
    assert response.status_code == 400
    data = response.json()
    
    # Check error structure
    assert "message" in data, "Response should include 'message' field"
    assert "detail" in data, "Response should include 'detail' field"
    assert "status_code" in data, "Response should include 'status_code' field"
    
    # Check message content
    message = data["message"].lower()
    assert "password" in message, f"Error message should mention password: {data['message']}"
    assert "8" in message or "character" in message, f"Error should mention length requirement: {data['message']}"


def test_invalid_email_error_format():
    """Test that invalid email returns proper error structure"""
    payload = {
        "email": "not-an-email",
        "name": "Test User",
        "password": "ValidPass123",
        "plan": "free"
    }
    
    response = client.post("/api/v1/auth/register", json=payload)
    
    assert response.status_code == 400
    data = response.json()
    
    # Check error structure
    assert "message" in data
    assert "detail" in data
    assert "status_code" in data
    
    # Check message content
    message = data["message"].lower()
    assert "email" in message, f"Error message should mention email: {data['message']}"


def test_duplicate_email_error_format():
    """Test that duplicate email returns proper error structure"""
    # First registration
    payload = {
        "email": "duplicate@example.com",
        "name": "First User",
        "password": "ValidPass123",
        "plan": "free"
    }
    
    first_response = client.post("/api/v1/auth/register", json=payload)
    assert first_response.status_code in [200, 201], "First registration should succeed"
    
    # Attempt duplicate registration
    second_response = client.post("/api/v1/auth/register", json=payload)
    
    assert second_response.status_code == 400
    data = second_response.json()
    
    # Check error structure
    assert "message" in data
    assert "detail" in data
    assert "status_code" in data
    
    # Check message content
    message = data["message"].lower()
    assert "email" in message or "already" in message or "registered" in message, \
        f"Error should indicate duplicate email: {data['message']}"


def test_missing_name_error_format():
    """Test that missing name returns proper error structure"""
    payload = {
        "email": "test@example.com",
        "name": "",  # Empty name
        "password": "ValidPass123",
        "plan": "free"
    }
    
    response = client.post("/api/v1/auth/register", json=payload)
    
    assert response.status_code == 400
    data = response.json()
    
    # Check error structure
    assert "message" in data
    assert "detail" in data
    assert "status_code" in data
    
    # Check message content
    message = data["message"].lower()
    assert "name" in message, f"Error message should mention name: {data['message']}"


def test_successful_registration_format():
    """Test that successful registration returns expected structure"""
    payload = {
        "email": f"success-{pytest.timestamp if hasattr(pytest, 'timestamp') else 'test'}@example.com",
        "name": "Success User",
        "password": "ValidPass123",
        "plan": "free"
    }
    
    response = client.post("/api/v1/auth/register", json=payload)
    
    assert response.status_code in [200, 201]
    data = response.json()
    
    # Check success response structure
    assert "access_token" in data, "Success should include access_token"
    assert "token_type" in data, "Success should include token_type"
    assert "user" in data, "Success should include user object"
    
    user = data["user"]
    assert "email" in user
    assert "name" in user
    assert "plan" in user
    assert user["plan"] == "free"


def test_password_without_letters():
    """Test password with numbers but no letters"""
    payload = {
        "email": "numbers-only@example.com",
        "name": "Test User",
        "password": "12345678",  # Only numbers
        "plan": "free"
    }
    
    response = client.post("/api/v1/auth/register", json=payload)
    
    assert response.status_code == 400
    data = response.json()
    assert "message" in data
    assert "password" in data["message"].lower()


def test_password_without_numbers():
    """Test password with letters but no numbers"""
    payload = {
        "email": "letters-only@example.com",
        "name": "Test User",
        "password": "onlyletters",  # Only letters
        "plan": "free"
    }
    
    response = client.post("/api/v1/auth/register", json=payload)
    
    assert response.status_code == 400
    data = response.json()
    assert "message" in data
    assert "password" in data["message"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
