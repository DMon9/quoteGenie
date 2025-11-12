"""
Quick deployment health check for production endpoints.
"""
import requests
import time

BACKEND_URL = "https://quotegenie-api.fly.dev"
FRONTEND_URL = "https://estimategenie.net"

def test_backend_health():
    """Test backend API health"""
    print("\n[BACKEND HEALTH CHECK]")
    print("=" * 60)
    
    try:
        # Test health endpoint
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        print(f"Health endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            print("[PASS] Backend health check")
        else:
            print(f"[FAIL] Backend returned {response.status_code}")
            return False
            
        # Test API docs
        response = requests.get(f"{BACKEND_URL}/docs", timeout=10)
        print(f"API docs: {response.status_code}")
        if response.status_code == 200:
            print("[PASS] API documentation accessible")
        else:
            print(f"[WARN] API docs returned {response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"[FAIL] Backend health check failed: {e}")
        return False

def test_frontend_health():
    """Test frontend accessibility"""
    print("\n[FRONTEND HEALTH CHECK]")
    print("=" * 60)
    
    try:
        # Test main page
        response = requests.get(FRONTEND_URL, timeout=10)
        print(f"Main page: {response.status_code}")
        if response.status_code == 200:
            print(f"Page size: {len(response.content)} bytes")
            print("[PASS] Frontend accessible")
        else:
            print(f"[FAIL] Frontend returned {response.status_code}")
            return False
            
        # Test www subdomain
        response = requests.get(f"https://www.estimategenie.net", timeout=10)
        print(f"WWW subdomain: {response.status_code}")
        if response.status_code == 200:
            print("[PASS] WWW subdomain accessible")
        else:
            print(f"[WARN] WWW subdomain returned {response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"[FAIL] Frontend health check failed: {e}")
        return False

def test_auth_flow():
    """Test authentication endpoints"""
    print("\n[AUTH FLOW CHECK]")
    print("=" * 60)
    
    try:
        # Test registration endpoint exists
        test_email = f"test_{int(time.time())}@example.com"
        test_password = "Test123456"  # Strong password
        
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "name": f"Test User {int(time.time())}"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"Registration: {response.status_code}")
            print("[PASS] Registration endpoint working")
            
            # Test login
            response = requests.post(
                f"{BACKEND_URL}/api/v1/auth/login",
                json={
                    "email": test_email,
                    "password": test_password
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"Login: {response.status_code}")
                token = response.json().get("access_token")
                print(f"Token received: {token[:20]}...")
                print("[PASS] Login endpoint working")
                
                # Test profile endpoint with token
                response = requests.get(
                    f"{BACKEND_URL}/api/v1/user/profile",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"Profile: {response.status_code}")
                    profile = response.json()
                    print(f"User plan: {profile.get('plan')}")
                    print("[PASS] Profile endpoint working")
                else:
                    print(f"[WARN] Profile returned {response.status_code}")
                    
                return True
            else:
                print(f"[FAIL] Login returned {response.status_code}")
                return False
        else:
            print(f"[FAIL] Registration returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Auth flow check failed: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("DEPLOYMENT HEALTH CHECK")
    print("=" * 60)
    print(f"Backend: {BACKEND_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "Backend Health": test_backend_health(),
        "Frontend Health": test_frontend_health(),
        "Auth Flow": test_auth_flow()
    }
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT SUMMARY")
    print("=" * 60)
    
    for test, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test}")
    
    total = len(results)
    passed = sum(results.values())
    
    print("\n" + "=" * 60)
    print(f"Overall: {passed}/{total} checks passed ({passed/total*100:.1f}%)")
    print("=" * 60)
    
    if passed == total:
        print("\n[SUCCESS] All deployment health checks passed!")
        print("Production deployment is LIVE and OPERATIONAL")
    else:
        print(f"\n[WARNING] {total - passed} check(s) failed")
        print("Review the failures above")

if __name__ == "__main__":
    main()
