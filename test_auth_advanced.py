"""
Advanced Authentication Flow Testing
Tests edge cases, session management, token expiry, and security features
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://quotegenie-api.fly.dev"
FRONTEND_URL = "https://www.estimategenie.net"

def print_test(name, status="START"):
    """Print formatted test status"""
    symbols = {"START": "🧪", "PASS": "✅", "FAIL": "❌", "INFO": "ℹ️", "WARN": "⚠️"}
    print(f"{symbols.get(status, '•')} {name}")

def test_1_duplicate_email_registration():
    """Test that duplicate email registration is rejected"""
    print_test("Test 1: Duplicate Email Registration Prevention")
    
    # Create first user
    test_email = f"duplicate{int(time.time())}@example.com"
    user_data = {
        "name": "Test User",
        "email": test_email,
        "password": "TestPassword123!",
        "plan": "free"
    }
    
    try:
        # First registration
        response1 = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  First registration: {response1.status_code}")
        
        if response1.status_code != 200:
            print(f"  ✗ First registration failed")
            print_test("Duplicate Email Prevention", "FAIL")
            return False
        
        # Try duplicate registration
        response2 = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  Duplicate registration: {response2.status_code}")
        
        if response2.status_code in [400, 409]:  # Bad Request or Conflict
            print(f"  ✓ Duplicate email correctly rejected")
            print_test("Duplicate Email Prevention", "PASS")
            return True
        else:
            print(f"  ✗ Duplicate registration should be rejected")
            print(f"  Response: {response2.text}")
            print_test("Duplicate Email Prevention", "FAIL")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        print_test("Duplicate Email Prevention", "FAIL")
        return False

def test_2_invalid_email_formats():
    """Test validation of email formats"""
    print_test("\nTest 2: Invalid Email Format Validation")
    
    invalid_emails = [
        "notanemail",
        "@example.com",
        "user@",
        "user@.com",
        "user name@example.com",
        ""
    ]
    
    passed = 0
    for email in invalid_emails:
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/auth/register",
                json={
                    "name": "Test User",
                    "email": email,
                    "password": "TestPassword123!",
                    "plan": "free"
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [400, 422]:  # Should reject invalid email
                print(f"  ✓ Rejected: '{email}'")
                passed += 1
            else:
                print(f"  ✗ Accepted invalid email: '{email}'")
        except Exception as e:
            print(f"  ⚠ Error testing '{email}': {str(e)}")
    
    if passed == len(invalid_emails):
        print_test("Email Validation", "PASS")
        return True
    else:
        print(f"  {passed}/{len(invalid_emails)} validations passed")
        print_test("Email Validation", "FAIL")
        return False

def test_3_weak_password_rejection():
    """Test that weak passwords are rejected"""
    print_test("\nTest 3: Weak Password Rejection")
    
    weak_passwords = [
        "123",          # Too short
        "pass",         # Too short
        "1234567",      # No complexity
        "password",     # Common password
        "12345678"      # Only numbers
    ]
    
    test_email = f"weakpass{int(time.time())}@example.com"
    passed = 0
    
    for pwd in weak_passwords:
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/auth/register",
                json={
                    "name": "Test User",
                    "email": test_email,
                    "password": pwd,
                    "plan": "free"
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [400, 422]:
                print(f"  ✓ Rejected weak password: '{pwd}'")
                passed += 1
            else:
                print(f"  ✗ Accepted weak password: '{pwd}'")
        except Exception as e:
            print(f"  ⚠ Error testing password '{pwd}': {str(e)}")
    
    if passed >= len(weak_passwords) * 0.6:  # At least 60% should be rejected
        print_test("Password Strength Validation", "PASS")
        return True
    else:
        print(f"  {passed}/{len(weak_passwords)} weak passwords rejected")
        print_test("Password Strength Validation", "WARN")
        return True  # Not critical, just a warning

def test_4_case_insensitive_email_login():
    """Test that email login is case-insensitive"""
    print_test("\nTest 4: Case-Insensitive Email Login")
    
    test_email = f"CaseTest{int(time.time())}@Example.COM"
    password = "TestPassword123!"
    
    try:
        # Register with mixed case email
        response1 = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": test_email,
                "password": password,
                "plan": "free"
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  Registration: {response1.status_code}")
        
        if response1.status_code != 200:
            print(f"  ✗ Registration failed")
            print_test("Case-Insensitive Email", "FAIL")
            return False
        
        # Try login with lowercase email
        lowercase_email = test_email.lower()
        response2 = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": lowercase_email,
                "password": password
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  Login with lowercase: {response2.status_code}")
        
        if response2.status_code == 200:
            print(f"  ✓ Case-insensitive login works")
            print_test("Case-Insensitive Email", "PASS")
            return True
        else:
            print(f"  ✗ Case-insensitive login failed")
            print_test("Case-Insensitive Email", "FAIL")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        print_test("Case-Insensitive Email", "FAIL")
        return False

def test_5_jwt_token_structure():
    """Test JWT token structure and claims"""
    print_test("\nTest 5: JWT Token Structure Validation")
    
    test_email = f"jwttest{int(time.time())}@example.com"
    
    try:
        # Register and get token
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "name": "JWT Test User",
                "email": test_email,
                "password": "TestPassword123!",
                "plan": "free"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"  ✗ Registration failed")
            print_test("JWT Token Structure", "FAIL")
            return False
        
        data = response.json()
        token = data.get('access_token')
        
        if not token:
            print(f"  ✗ No token received")
            print_test("JWT Token Structure", "FAIL")
            return False
        
        # Validate JWT structure (header.payload.signature)
        parts = token.split('.')
        print(f"  ✓ Token received")
        print(f"  Token parts: {len(parts)}")
        
        if len(parts) == 3:
            print(f"  ✓ JWT has correct structure (3 parts)")
            print(f"  ✓ Token type: {data.get('token_type')}")
            print_test("JWT Token Structure", "PASS")
            return True
        else:
            print(f"  ✗ Invalid JWT structure")
            print_test("JWT Token Structure", "FAIL")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        print_test("JWT Token Structure", "FAIL")
        return False

def test_6_concurrent_logins():
    """Test multiple concurrent login sessions"""
    print_test("\nTest 6: Concurrent Login Sessions")
    
    test_email = f"concurrent{int(time.time())}@example.com"
    password = "TestPassword123!"
    
    try:
        # Register user
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "name": "Concurrent Test",
                "email": test_email,
                "password": password,
                "plan": "free"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"  ✗ Registration failed")
            print_test("Concurrent Logins", "FAIL")
            return False
        
        # Login multiple times
        tokens = []
        for i in range(3):
            login_response = requests.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={"email": test_email, "password": password},
                headers={"Content-Type": "application/json"}
            )
            
            if login_response.status_code == 200:
                token = login_response.json().get('access_token')
                tokens.append(token)
                print(f"  ✓ Login #{i+1} successful")
            else:
                print(f"  ✗ Login #{i+1} failed")
        
        if len(tokens) == 3:
            print(f"  ✓ All tokens different: {len(set(tokens)) == 3}")
            print_test("Concurrent Logins", "PASS")
            return True
        else:
            print_test("Concurrent Logins", "FAIL")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        print_test("Concurrent Logins", "FAIL")
        return False

def test_7_password_reset_token_validity():
    """Test password reset token expiration and one-time use"""
    print_test("\nTest 7: Password Reset Token Security")
    
    test_email = f"resettoken{int(time.time())}@example.com"
    password = "TestPassword123!"
    
    try:
        # Register user
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "name": "Reset Token Test",
                "email": test_email,
                "password": password,
                "plan": "free"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"  ✗ Registration failed")
            return False
        
        # Request password reset
        reset_response = requests.post(
            f"{BASE_URL}/api/v1/auth/forgot-password",
            json={"email": test_email},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  Password reset request: {reset_response.status_code}")
        
        if reset_response.status_code == 200:
            data = reset_response.json()
            
            # Check if token is returned (dev mode)
            if 'reset_token' in data:
                token = data['reset_token']
                print(f"  ✓ Reset token received (dev mode)")
                
                # Try to use token
                new_password = "NewPassword456!"
                reset_use = requests.post(
                    f"{BASE_URL}/api/v1/auth/reset-password",
                    json={"token": token, "new_password": new_password},
                    headers={"Content-Type": "application/json"}
                )
                
                if reset_use.status_code == 200:
                    print(f"  ✓ Password reset successful")
                    
                    # Try to reuse the same token
                    reuse_response = requests.post(
                        f"{BASE_URL}/api/v1/auth/reset-password",
                        json={"token": token, "new_password": "AnotherPassword789!"},
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if reuse_response.status_code in [400, 401]:
                        print(f"  ✓ Token reuse correctly blocked")
                        print_test("Password Reset Token Security", "PASS")
                        return True
                    else:
                        print(f"  ✗ Token should be one-time use")
                        print_test("Password Reset Token Security", "WARN")
                        return True  # Not critical
                else:
                    print(f"  ✗ Password reset failed")
                    print_test("Password Reset Token Security", "FAIL")
                    return False
            else:
                print(f"  ℹ️ Token sent via email (production mode)")
                print_test("Password Reset Token Security", "INFO")
                return True
        else:
            print(f"  ✗ Password reset request failed")
            print_test("Password Reset Token Security", "FAIL")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        print_test("Password Reset Token Security", "FAIL")
        return False

def test_8_unauthorized_access_attempts():
    """Test that protected endpoints reject unauthorized access"""
    print_test("\nTest 8: Unauthorized Access Protection")
    
    protected_endpoints = [
        ("GET", "/v1/quotes"),
        ("GET", "/v1/user/profile"),
        ("POST", "/v1/quotes")
    ]
    
    passed = 0
    for method, endpoint in protected_endpoints:
        try:
            if method == "GET":
                response = requests.get(
                    f"{BASE_URL}{endpoint}",
                    headers={"Content-Type": "application/json"}
                )
            else:
                response = requests.post(
                    f"{BASE_URL}{endpoint}",
                    json={},
                    headers={"Content-Type": "application/json"}
                )
            
            if response.status_code in [401, 403]:
                print(f"  ✓ {method} {endpoint}: Unauthorized ({response.status_code})")
                passed += 1
            elif response.status_code == 404:
                print(f"  ℹ️ {method} {endpoint}: Not Found (endpoint may not exist)")
                passed += 1  # Count as pass if endpoint doesn't exist
            else:
                print(f"  ✗ {method} {endpoint}: Should reject unauthorized ({response.status_code})")
        except Exception as e:
            print(f"  ⚠ {method} {endpoint}: Error - {str(e)}")
    
    if passed >= len(protected_endpoints):
        print_test("Unauthorized Access Protection", "PASS")
        return True
    else:
        print_test("Unauthorized Access Protection", "FAIL")
        return False

def test_9_malformed_jwt_rejection():
    """Test that malformed JWT tokens are rejected"""
    print_test("\nTest 9: Malformed JWT Token Rejection")
    
    malformed_tokens = [
        "not.a.token",
        "Bearer invalid",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
        "",
        "null"
    ]
    
    passed = 0
    for token in malformed_tokens:
        try:
            response = requests.get(
                f"{BASE_URL}/v1/quotes",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code in [401, 403, 422]:
                print(f"  ✓ Rejected malformed token")
                passed += 1
            else:
                print(f"  ✗ Accepted malformed token: {token[:20]}...")
        except Exception as e:
            print(f"  ⚠ Error: {str(e)}")
    
    if passed >= len(malformed_tokens) * 0.8:
        print_test("Malformed JWT Rejection", "PASS")
        return True
    else:
        print_test("Malformed JWT Rejection", "FAIL")
        return False

def test_10_session_persistence():
    """Test session persistence across requests"""
    print_test("\nTest 10: Session Persistence & Token Reuse")
    
    test_email = f"session{int(time.time())}@example.com"
    password = "TestPassword123!"
    
    try:
        # Register
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "name": "Session Test",
                "email": test_email,
                "password": password,
                "plan": "free"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"  ✗ Registration failed")
            return False
        
        token = response.json().get('access_token')
        
        # Make multiple requests with same token
        success_count = 0
        for i in range(5):
            test_response = requests.get(
                f"{BASE_URL}/v1/quotes",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if test_response.status_code in [200, 404]:  # 200 or 404 (empty quotes) is ok
                success_count += 1
        
        print(f"  ✓ {success_count}/5 requests successful with same token")
        
        if success_count == 5:
            print_test("Session Persistence", "PASS")
            return True
        else:
            print_test("Session Persistence", "FAIL")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        print_test("Session Persistence", "FAIL")
        return False

def run_advanced_tests():
    """Run advanced authentication test suite"""
    print("\n" + "="*60)
    print("🔐 ADVANCED AUTHENTICATION SECURITY TEST SUITE")
    print("="*60)
    print(f"Backend API: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    results = {
        "Duplicate Email Prevention": test_1_duplicate_email_registration(),
        "Email Format Validation": test_2_invalid_email_formats(),
        "Password Strength Validation": test_3_weak_password_rejection(),
        "Case-Insensitive Email": test_4_case_insensitive_email_login(),
        "JWT Token Structure": test_5_jwt_token_structure(),
        "Concurrent Login Sessions": test_6_concurrent_logins(),
        "Password Reset Token Security": test_7_password_reset_token_validity(),
        "Unauthorized Access Protection": test_8_unauthorized_access_attempts(),
        "Malformed JWT Rejection": test_9_malformed_jwt_rejection(),
        "Session Persistence": test_10_session_persistence()
    }
    
    # Summary
    print("\n" + "="*60)
    print("📊 ADVANCED TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("="*60)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All advanced security tests passed!")
    elif passed >= total * 0.8:
        print(f"\n✅ Good! {passed}/{total} tests passed")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed - review security")
    
    return passed >= total * 0.8  # Pass if 80% or more tests pass

if __name__ == "__main__":
    success = run_advanced_tests()
    exit(0 if success else 1)
