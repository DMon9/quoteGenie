"""
Comprehensive API Endpoints Test Suite
Tests all backend API endpoints
"""
import requests
import time
from io import BytesIO

BASE_URL = "https://quotegenie-api.fly.dev"

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests = []
    
    def add_pass(self, test_name, details=""):
        self.passed += 1
        self.tests.append({"name": test_name, "status": "PASS", "details": details})
        print(f"[PASS] {test_name}")
        if details:
            print(f"       {details}")
    
    def add_fail(self, test_name, details=""):
        self.failed += 1
        self.tests.append({"name": test_name, "status": "FAIL", "details": details})
        print(f"[FAIL] {test_name}")
        if details:
            print(f"       {details}")
    
    def add_warning(self, test_name, details=""):
        self.warnings += 1
        self.tests.append({"name": test_name, "status": "WARN", "details": details})
        print(f"[WARN] {test_name}")
        if details:
            print(f"       {details}")
    
    def summary(self):
        total = self.passed + self.failed
        pct = (self.passed / total * 100) if total > 0 else 0
        print(f"\n{'='*70}")
        print(f"SUMMARY: {self.passed}/{total} tests passed ({pct:.1f}%)")
        if self.warnings > 0:
            print(f"WARNINGS: {self.warnings}")
        print(f"{'='*70}\n")
        return self.passed == total

def create_test_user(results):
    """Create a test user and return token"""
    email = f"api_test_{int(time.time()*1000)}@example.com"
    password = "ApiTest123"
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": password, "name": "API Test User"}
    )
    
    if response.status_code in [200, 201]:
        return response.json()["access_token"], email
    return None, None

def test_health_endpoints(results):
    """Test health and status endpoints"""
    print("\n--- Testing Health Endpoints ---")
    
    # Test root endpoint
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code == 200:
            results.add_pass("Root endpoint accessible")
        else:
            results.add_fail("Root endpoint", f"Status: {response.status_code}")
    except Exception as e:
        results.add_fail("Root endpoint", str(e))
    
    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            results.add_pass("Health endpoint")
        else:
            results.add_warning("Health endpoint", f"Status: {response.status_code}")
    except:
        results.add_warning("Health endpoint", "Not found or error")

def test_auth_endpoints(results):
    """Test authentication endpoints"""
    print("\n--- Testing Auth Endpoints ---")
    
    email = f"auth_ep_test_{int(time.time()*1000)}@example.com"
    password = "AuthEpTest123"
    
    # Test registration
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": password, "name": "Auth Endpoint Test"}
    )
    
    if response.status_code in [200, 201]:
        data = response.json()
        if all(k in data for k in ["access_token", "token_type", "user"]):
            results.add_pass("Registration endpoint structure")
        else:
            results.add_fail("Registration endpoint", "Missing expected fields")
        token = data["access_token"]
    else:
        results.add_fail("Registration endpoint", f"Status: {response.status_code}")
        return
    
    # Test login
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    
    if response.status_code == 200:
        results.add_pass("Login endpoint")
    else:
        results.add_fail("Login endpoint", f"Status: {response.status_code}")
    
    # Test profile endpoint
    response = requests.get(
        f"{BASE_URL}/v1/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        profile = response.json()
        if profile.get("email") == email:
            results.add_pass("Profile endpoint returns correct user")
        else:
            results.add_fail("Profile endpoint", "Email mismatch")
    else:
        results.add_fail("Profile endpoint", f"Status: {response.status_code}")

def test_quote_endpoints(results):
    """Test quote-related endpoints"""
    print("\n--- Testing Quote Endpoints ---")
    
    token, email = create_test_user(results)
    if not token:
        results.add_fail("Quote test setup", "Could not create user")
        return
    
    # Test GET quotes (should be empty initially)
    response = requests.get(
        f"{BASE_URL}/v1/quotes",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        quotes = response.json()
        if isinstance(quotes, list):
            results.add_pass("GET quotes endpoint", f"Returned list ({len(quotes)} items)")
        else:
            results.add_fail("GET quotes endpoint", "Did not return list")
    else:
        results.add_fail("GET quotes endpoint", f"Status: {response.status_code}")
    
    # Test POST quote with image
    try:
        from PIL import Image
        
        # Create test image
        img = Image.new('RGB', (400, 300), color='skyblue')
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        
        files = {'file': ('test_quote.jpg', buffer.getvalue(), 'image/jpeg')}
        data = {
            'project_name': 'API Test Project',
            'location': 'Test City, TS',
            'description': 'Testing quote creation via API'
        }
        
        response = requests.post(
            f"{BASE_URL}/v1/quotes",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            quote_data = response.json()
            results.add_pass("POST quote endpoint", "Quote created successfully")
            
            # Verify quote is in user's list
            response = requests.get(
                f"{BASE_URL}/v1/quotes",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                quotes = response.json()
                if len(quotes) > 0:
                    results.add_pass("Quote appears in user's list")
                else:
                    results.add_fail("Quote visibility", "Quote not in user's list")
            
        else:
            results.add_fail("POST quote endpoint", f"Status: {response.status_code}, {response.text[:200]}")
    
    except Exception as e:
        results.add_fail("POST quote test", f"Error: {str(e)}")

def test_payment_endpoints(results):
    """Test payment-related endpoints"""
    print("\n--- Testing Payment Endpoints ---")
    
    # Test payment status
    response = requests.get(f"{BASE_URL}/api/v1/payment/status")
    
    if response.status_code == 200:
        data = response.json()
        if "configured" in data:
            results.add_pass("Payment status endpoint")
        else:
            results.add_fail("Payment status endpoint", "Missing 'configured' field")
    else:
        results.add_fail("Payment status endpoint", f"Status: {response.status_code}")
    
    # Test payment config
    response = requests.get(f"{BASE_URL}/api/v1/payment/config")
    
    if response.status_code == 200:
        results.add_pass("Payment config endpoint")
    else:
        results.add_fail("Payment config endpoint", f"Status: {response.status_code}")
    
    # Test webhook info
    response = requests.get(f"{BASE_URL}/api/v1/webhooks/stripe")
    
    if response.status_code == 200:
        data = response.json()
        if "url" in data and "events" in data:
            results.add_pass("Webhook info endpoint", f"{len(data.get('events', []))} events configured")
        else:
            results.add_fail("Webhook info endpoint", "Missing expected fields")
    else:
        results.add_fail("Webhook info endpoint", f"Status: {response.status_code}")

def test_unauthorized_access(results):
    """Test that protected endpoints reject unauthorized access"""
    print("\n--- Testing Unauthorized Access Protection ---")
    
    protected_endpoints = [
        ("GET", "/v1/user/profile"),
        ("GET", "/v1/quotes"),
        ("POST", "/v1/quotes"),
    ]
    
    rejected_count = 0
    
    for method, endpoint in protected_endpoints:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        else:
            response = requests.post(f"{BASE_URL}{endpoint}")
        
        if response.status_code == 401:
            rejected_count += 1
    
    if rejected_count == len(protected_endpoints):
        results.add_pass("Unauthorized access protection", f"{rejected_count}/{len(protected_endpoints)} endpoints protected")
    else:
        results.add_fail("Unauthorized access protection", f"Only {rejected_count}/{len(protected_endpoints)} endpoints protected")

def test_cors_headers(results):
    """Test CORS headers are present"""
    print("\n--- Testing CORS Configuration ---")
    
    response = requests.options(f"{BASE_URL}/api/v1/auth/login")
    
    if "access-control-allow-origin" in response.headers:
        results.add_pass("CORS headers present")
    else:
        results.add_warning("CORS headers", "May not be configured for all origins")

def test_error_handling(results):
    """Test API error handling"""
    print("\n--- Testing Error Handling ---")
    
    # Test invalid JSON
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data="not valid json",
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code in [400, 422]:
        results.add_pass("Invalid JSON handling")
    else:
        results.add_warning("Invalid JSON handling", f"Status: {response.status_code}")
    
    # Test missing required fields
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": "test@test.com"}  # Missing password and name
    )
    
    if response.status_code in [400, 422]:
        results.add_pass("Missing fields validation")
    else:
        results.add_fail("Missing fields validation", f"Status: {response.status_code}")

def main():
    print("="*70)
    print("COMPREHENSIVE API ENDPOINTS TEST")
    print("="*70)
    print(f"Testing: {BASE_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = TestResults()
    
    # Run all tests
    test_health_endpoints(results)
    test_auth_endpoints(results)
    test_quote_endpoints(results)
    test_payment_endpoints(results)
    test_unauthorized_access(results)
    test_cors_headers(results)
    test_error_handling(results)
    
    # Print summary
    success = results.summary()
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
