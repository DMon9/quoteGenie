"""
Comprehensive Authentication System Test Suite
No emoji characters for Windows compatibility
"""
import requests
import time
import json

BASE_URL = "https://quotegenie-api.fly.dev"

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
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
    
    def summary(self):
        total = self.passed + self.failed
        pct = (self.passed / total * 100) if total > 0 else 0
        print(f"\n{'='*70}")
        print(f"SUMMARY: {self.passed}/{total} tests passed ({pct:.1f}%)")
        print(f"{'='*70}\n")
        return self.passed == total

def test_user_registration(results):
    """Test basic user registration"""
    print("\n--- Testing User Registration ---")
    
    email = f"reg_test_{int(time.time()*1000)}@example.com"
    
    # Test successful registration
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": "ValidPass123", "name": "Test User"}
    )
    
    if response.status_code in [200, 201]:
        data = response.json()
        if "access_token" in data:
            results.add_pass("User registration successful", f"Token received")
        else:
            results.add_fail("User registration", "No token in response")
    else:
        results.add_fail("User registration", f"Status: {response.status_code}")
    
    # Test duplicate email
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": "ValidPass123", "name": "Test User"}
    )
    
    if response.status_code in [400, 409]:
        results.add_pass("Duplicate email prevention")
    else:
        results.add_fail("Duplicate email prevention", f"Status: {response.status_code}")

def test_email_validation(results):
    """Test email format validation"""
    print("\n--- Testing Email Validation ---")
    
    invalid_emails = [
        "notanemail",
        "@example.com",
        "user@",
        "user @example.com",
        "user@.com",
        "user..name@example.com"
    ]
    
    rejected = 0
    for email in invalid_emails:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={"email": email, "password": "ValidPass123", "name": "Test"}
        )
        if response.status_code == 400:
            rejected += 1
    
    if rejected == len(invalid_emails):
        results.add_pass("Email validation", f"{rejected}/{len(invalid_emails)} invalid emails rejected")
    else:
        results.add_fail("Email validation", f"Only {rejected}/{len(invalid_emails)} rejected")

def test_password_strength(results):
    """Test password strength validation"""
    print("\n--- Testing Password Strength ---")
    
    weak_passwords = [
        ("password", "No numbers"),
        ("12345678", "No letters"),
        ("pass123", "Too short"),
        ("abc", "Too short"),
        ("Pass", "Too short, no number")
    ]
    
    rejected = 0
    for pwd, reason in weak_passwords:
        email = f"pwd_test_{int(time.time()*1000)}@example.com"
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={"email": email, "password": pwd, "name": "Test"}
        )
        if response.status_code == 400 and "Password must be at least" in response.text:
            rejected += 1
    
    if rejected == len(weak_passwords):
        results.add_pass("Password strength validation", f"{rejected}/{len(weak_passwords)} weak passwords rejected")
    else:
        results.add_fail("Password strength validation", f"Only {rejected}/{len(weak_passwords)} rejected")

def test_login_functionality(results):
    """Test login with various scenarios"""
    print("\n--- Testing Login Functionality ---")
    
    # Create test user
    email = f"login_test_{int(time.time()*1000)}@example.com"
    password = "LoginTest123"
    
    reg_response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": password, "name": "Login Test"}
    )
    
    if reg_response.status_code not in [200, 201]:
        results.add_fail("Login test setup", "Could not create test user")
        return
    
    # Test correct credentials
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    
    if response.status_code == 200 and "access_token" in response.json():
        results.add_pass("Login with correct credentials")
        token = response.json()["access_token"]
    else:
        results.add_fail("Login with correct credentials", f"Status: {response.status_code}")
        return
    
    # Test wrong password
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword123"}
    )
    
    if response.status_code == 401:
        results.add_pass("Login with wrong password rejected")
    else:
        results.add_fail("Login with wrong password", f"Status: {response.status_code}")
    
    # Test case-insensitive email
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email.upper(), "password": password}
    )
    
    if response.status_code == 200:
        results.add_pass("Case-insensitive email login")
    else:
        results.add_fail("Case-insensitive email login", f"Status: {response.status_code}")

def test_token_validation(results):
    """Test JWT token validation"""
    print("\n--- Testing Token Validation ---")
    
    # Create user and get token
    email = f"token_test_{int(time.time()*1000)}@example.com"
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": "TokenTest123", "name": "Token Test"}
    )
    
    if response.status_code not in [200, 201]:
        results.add_fail("Token test setup", "Could not create user")
        return
    
    token = response.json()["access_token"]
    
    # Test valid token
    response = requests.get(
        f"{BASE_URL}/v1/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        results.add_pass("Valid token authentication")
    else:
        results.add_fail("Valid token authentication", f"Status: {response.status_code}")
    
    # Test invalid token
    response = requests.get(
        f"{BASE_URL}/v1/user/profile",
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    
    if response.status_code == 401:
        results.add_pass("Invalid token rejection")
    else:
        results.add_fail("Invalid token rejection", f"Status: {response.status_code}")
    
    # Test missing token
    response = requests.get(f"{BASE_URL}/v1/user/profile")
    
    if response.status_code == 401:
        results.add_pass("Missing token rejection")
    else:
        results.add_fail("Missing token rejection", f"Status: {response.status_code}")

def test_user_profile_endpoint(results):
    """Test user profile endpoint"""
    print("\n--- Testing User Profile Endpoint ---")
    
    # Create user
    email = f"profile_test_{int(time.time()*1000)}@example.com"
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": "ProfileTest123", "name": "Profile Test"}
    )
    
    if response.status_code not in [200, 201]:
        results.add_fail("Profile test setup", "Could not create user")
        return
    
    token = response.json()["access_token"]
    
    # Get profile
    response = requests.get(
        f"{BASE_URL}/v1/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        profile = response.json()
        
        # Check required fields
        required_fields = ['id', 'email', 'name', 'plan', 'api_key', 'created_at',
                          'subscription_status', 'quotes_used', 'api_calls_used', 'plan_limits']
        
        missing = [f for f in required_fields if f not in profile]
        
        if not missing:
            results.add_pass("Profile endpoint returns all fields")
        else:
            results.add_fail("Profile endpoint fields", f"Missing: {missing}")
        
        # Validate API key format
        if profile.get('api_key', '').startswith('eg_sk_'):
            results.add_pass("API key format valid")
        else:
            results.add_fail("API key format", f"Got: {profile.get('api_key', 'N/A')[:10]}")
    else:
        results.add_fail("Profile endpoint", f"Status: {response.status_code}")

def test_session_persistence(results):
    """Test that tokens work across multiple requests"""
    print("\n--- Testing Session Persistence ---")
    
    # Create user
    email = f"session_test_{int(time.time()*1000)}@example.com"
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": "SessionTest123", "name": "Session Test"}
    )
    
    if response.status_code not in [200, 201]:
        results.add_fail("Session test setup", "Could not create user")
        return
    
    token = response.json()["access_token"]
    
    # Make multiple requests with same token
    successes = 0
    for i in range(5):
        response = requests.get(
            f"{BASE_URL}/v1/user/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            successes += 1
    
    if successes == 5:
        results.add_pass("Session persistence", "5/5 requests successful")
    else:
        results.add_fail("Session persistence", f"Only {successes}/5 requests successful")

def main():
    print("="*70)
    print("COMPREHENSIVE AUTHENTICATION SYSTEM TEST")
    print("="*70)
    print(f"Testing: {BASE_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = TestResults()
    
    # Run all tests
    test_user_registration(results)
    test_email_validation(results)
    test_password_strength(results)
    test_login_functionality(results)
    test_token_validation(results)
    test_user_profile_endpoint(results)
    test_session_persistence(results)
    
    # Print summary
    success = results.summary()
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
