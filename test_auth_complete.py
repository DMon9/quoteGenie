"""
Complete Authentication Flow Testing
Tests signup, login, logout, password reset on live production site
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://quotegenie-api.fly.dev"
FRONTEND_URL = "https://www.estimategenie.net"

# Test user data
TEST_USER = {
    "name": "Test User Auth Flow",
    "email": f"testauth{int(time.time())}@example.com",  # Unique email
    "password": "TestPassword123!",
    "plan": "free"
}

def print_test(name, status="START"):
    """Print formatted test status"""
    symbols = {"START": "🧪", "PASS": "✅", "FAIL": "❌", "INFO": "ℹ️"}
    print(f"{symbols.get(status, '•')} {name}")

def test_1_signup():
    """Test user registration"""
    print_test("Test 1: User Signup")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=TEST_USER,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ User registered successfully")
            print(f"  ✓ User ID: {data.get('user', {}).get('id')}")
            print(f"  ✓ Email: {data.get('user', {}).get('email')}")
            print(f"  ✓ Plan: {data.get('user', {}).get('plan')}")
            print(f"  ✓ Access token received: {bool(data.get('access_token'))}")
            
            # Store token for next tests
            TEST_USER['token'] = data.get('access_token')
            TEST_USER['user_id'] = data.get('user', {}).get('id')
            
            # Verify plan is forced to 'free'
            if data.get('user', {}).get('plan') == 'free':
                print_test("Plan enforcement (forced to 'free')", "PASS")
            else:
                print_test(f"Plan should be 'free' but got '{data.get('user', {}).get('plan')}'", "FAIL")
            
            return True
        else:
            print(f"  ✗ Registration failed: {response.text}")
            print_test("Signup", "FAIL")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        print_test("Signup", "FAIL")
        return False

def test_2_login():
    """Test user login"""
    print_test("\nTest 2: User Login")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": TEST_USER['email'],
                "password": TEST_USER['password']
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Login successful")
            print(f"  ✓ Access token received: {bool(data.get('access_token'))}")
            print(f"  ✓ Token type: {data.get('token_type')}")
            
            # Update token
            TEST_USER['token'] = data.get('access_token')
            print_test("Login", "PASS")
            return True
        else:
            print(f"  ✗ Login failed: {response.text}")
            print_test("Login", "FAIL")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        print_test("Login", "FAIL")
        return False

def test_3_protected_endpoint():
    """Test accessing protected endpoint with JWT token"""
    print_test("\nTest 3: Protected Endpoint Access (Auth Verification)")
    
    if 'token' not in TEST_USER:
        print("  ✗ No token available, skipping")
        print_test("Protected Endpoint", "FAIL")
        return False
    
    try:
        # Try to get user's quotes (requires authentication)
        response = requests.get(
            f"{BASE_URL}/api/v1/quotes",
            headers={
                "Authorization": f"Bearer {TEST_USER['token']}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Authenticated access successful")
            print(f"  ✓ Quotes retrieved: {len(data.get('quotes', []))}")
            print_test("Protected Endpoint Access", "PASS")
            return True
        elif response.status_code == 401:
            print(f"  ✗ Authentication failed (token invalid)")
            print_test("Protected Endpoint Access", "FAIL")
            return False
        else:
            print(f"  ⚠ Unexpected response: {response.text}")
            print_test("Protected Endpoint Access", "FAIL")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        print_test("Protected Endpoint Access", "FAIL")
        return False

def test_4_forgot_password():
    """Test forgot password flow"""
    print_test("\nTest 4: Forgot Password")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/forgot-password",
            json={"email": TEST_USER['email']},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Password reset requested successfully")
            print(f"  ✓ Message: {data.get('message')}")
            
            # In dev mode, token is returned
            if 'reset_token' in data:
                print(f"  ✓ Reset token received (dev mode)")
                TEST_USER['reset_token'] = data['reset_token']
            
            print_test("Forgot Password", "PASS")
            return True
        else:
            print(f"  ✗ Request failed: {response.text}")
            print_test("Forgot Password", "FAIL")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        print_test("Forgot Password", "FAIL")
        return False

def test_5_reset_password():
    """Test password reset with token"""
    print_test("\nTest 5: Reset Password")
    
    if 'reset_token' not in TEST_USER:
        print("  ⚠ No reset token available (expected in production)")
        print("  ℹ️ In production, token would be sent via email")
        print_test("Reset Password", "INFO")
        return True
    
    try:
        new_password = "NewTestPassword456!"
        
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/reset-password",
            json={
                "token": TEST_USER['reset_token'],
                "new_password": new_password
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Password reset successful")
            print(f"  ✓ Message: {data.get('message')}")
            
            # Try logging in with new password
            print("\n  Testing login with new password...")
            login_response = requests.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={
                    "email": TEST_USER['email'],
                    "password": new_password
                },
                headers={"Content-Type": "application/json"}
            )
            
            if login_response.status_code == 200:
                print(f"  ✓ Login with new password successful")
                print_test("Reset Password", "PASS")
                # Update password for future tests
                TEST_USER['password'] = new_password
                return True
            else:
                print(f"  ✗ Login with new password failed")
                print_test("Reset Password", "FAIL")
                return False
        else:
            print(f"  ✗ Password reset failed: {response.text}")
            print_test("Reset Password", "FAIL")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        print_test("Reset Password", "FAIL")
        return False

def test_6_invalid_login():
    """Test login with wrong password"""
    print_test("\nTest 6: Invalid Login (Wrong Password)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": TEST_USER['email'],
                "password": "WrongPassword123!"
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print(f"  ✓ Correctly rejected invalid credentials")
            print_test("Invalid Login Rejection", "PASS")
            return True
        else:
            print(f"  ✗ Should have rejected invalid credentials")
            print_test("Invalid Login Rejection", "FAIL")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        print_test("Invalid Login Rejection", "FAIL")
        return False

def test_7_frontend_pages():
    """Test frontend authentication pages are accessible"""
    print_test("\nTest 7: Frontend Pages Accessibility")
    
    pages = [
        ("Signup", f"{FRONTEND_URL}/signup.html"),
        ("Login", f"{FRONTEND_URL}/login.html"),
        ("Forgot Password", f"{FRONTEND_URL}/forgot-password.html"),
        ("Reset Password", f"{FRONTEND_URL}/reset-password.html"),
        ("Dashboard", f"{FRONTEND_URL}/dashboard-new.html")
    ]
    
    all_passed = True
    for name, url in pages:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"  ✓ {name}: Accessible")
            else:
                print(f"  ✗ {name}: Status {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"  ✗ {name}: Error - {str(e)}")
            all_passed = False
    
    if all_passed:
        print_test("Frontend Pages", "PASS")
    else:
        print_test("Frontend Pages", "FAIL")
    
    return all_passed

def run_all_tests():
    """Run complete authentication test suite"""
    print("\n" + "="*60)
    print("🧪 ESTIMATEGENIE AUTHENTICATION FLOW TEST SUITE")
    print("="*60)
    print(f"Backend API: {BASE_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    print(f"Test User Email: {TEST_USER['email']}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    results = {
        "User Signup": test_1_signup(),
        "User Login": test_2_login(),
        "Protected Endpoint Access": test_3_protected_endpoint(),
        "Forgot Password": test_4_forgot_password(),
        "Reset Password": test_5_reset_password(),
        "Invalid Login Rejection": test_6_invalid_login(),
        "Frontend Pages": test_7_frontend_pages()
    }
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
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
        print("\n🎉 All authentication tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
