"""
Test authentication flow with production API
"""
import requests
import json
import sys
from datetime import datetime

API_BASE = "https://api.estimategenie.net"

def test_health():
    """Test API health check"""
    print("\n=== Testing API Health ===")
    try:
        response = requests.get(f"{API_BASE}/health")
        data = response.json()
        print(f"✓ Status: {data.get('status')}")
        print(f"✓ Services: {json.dumps(data.get('services', {}), indent=2)}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_register(email, name, password):
    """Test user registration"""
    print("\n=== Testing Registration ===")
    try:
        payload = {
            "email": email,
            "name": name,
            "password": password,
            "plan": "free"
        }
        response = requests.post(
            f"{API_BASE}/api/v1/auth/register",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ User registered successfully")
            print(f"✓ Access token: {data.get('access_token', 'N/A')[:20]}...")
            print(f"✓ User ID: {data.get('user', {}).get('id', 'N/A')}")
            print(f"✓ API Key: {data.get('user', {}).get('api_key', 'N/A')[:20]}...")
            return data
        else:
            data = response.json()
            print(f"✗ Registration failed: {data.get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"✗ Registration error: {e}")
        return None

def test_login(email, password):
    """Test user login"""
    print("\n=== Testing Login ===")
    try:
        payload = {
            "email": email,
            "password": password
        }
        response = requests.post(
            f"{API_BASE}/api/v1/auth/login",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Login successful")
            print(f"✓ Access token: {data.get('access_token', 'N/A')[:20]}...")
            print(f"✓ User: {data.get('user', {}).get('name', 'N/A')}")
            return data
        else:
            data = response.json()
            print(f"✗ Login failed: {data.get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"✗ Login error: {e}")
        return None

def test_get_me(token):
    """Test getting current user info"""
    print("\n=== Testing Get User Info ===")
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(
            f"{API_BASE}/api/v1/auth/me",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ User info retrieved")
            print(f"  - Name: {data.get('name')}")
            print(f"  - Email: {data.get('email')}")
            print(f"  - Plan: {data.get('plan')}")
            print(f"  - Quotes Used: {data.get('quotes_used')}/{data.get('limits', {}).get('quotes_per_month', 'N/A')}")
            return data
        else:
            print(f"✗ Failed to get user info: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Get user error: {e}")
        return None

def main():
    print("=" * 60)
    print("EstimateGenie Auth Flow Test")
    print("=" * 60)
    
    # Test health
    if not test_health():
        print("\n✗ API not healthy, aborting tests")
        sys.exit(1)
    
    # Generate unique test email
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    test_email = f"test_{timestamp}@example.com"
    test_name = "Test User"
    test_password = "testpass123"
    
    print(f"\nTest credentials:")
    print(f"  Email: {test_email}")
    print(f"  Name: {test_name}")
    print(f"  Password: {test_password}")
    
    # Test registration
    reg_data = test_register(test_email, test_name, test_password)
    if not reg_data:
        print("\n✗ Registration failed, aborting remaining tests")
        sys.exit(1)
    
    token = reg_data.get('access_token')
    
    # Test login
    login_data = test_login(test_email, test_password)
    if not login_data:
        print("\n✗ Login failed")
    else:
        token = login_data.get('access_token')
    
    # Test get user info
    if token:
        test_get_me(token)
    
    print("\n" + "=" * 60)
    print("✓ Auth flow tests completed")
    print("=" * 60)

if __name__ == "__main__":
    main()
