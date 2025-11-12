"""
Comprehensive Database and Integration Test Suite
Tests database operations and full user workflows
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

def test_user_data_persistence(results):
    """Test that user data persists across requests"""
    print("\n--- Testing User Data Persistence ---")
    
    email = f"persist_test_{int(time.time()*1000)}@example.com"
    password = "PersistTest123"
    name = "Persistence Test User"
    
    # Create user
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": password, "name": name}
    )
    
    if response.status_code not in [200, 201]:
        results.add_fail("User creation for persistence test", f"Status: {response.status_code}")
        return
    
    token1 = response.json()["access_token"]
    
    # Get profile
    response = requests.get(
        f"{BASE_URL}/v1/user/profile",
        headers={"Authorization": f"Bearer {token1}"}
    )
    
    if response.status_code != 200:
        results.add_fail("Initial profile retrieval", f"Status: {response.status_code}")
        return
    
    profile1 = response.json()
    user_id = profile1.get("id")
    
    # Login again (new session)
    time.sleep(1)
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    
    if response.status_code != 200:
        results.add_fail("Re-login", f"Status: {response.status_code}")
        return
    
    token2 = response.json()["access_token"]
    
    # Get profile with new token
    response = requests.get(
        f"{BASE_URL}/v1/user/profile",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    if response.status_code != 200:
        results.add_fail("Profile with new token", f"Status: {response.status_code}")
        return
    
    profile2 = response.json()
    
    # Verify same user
    if profile2.get("id") == user_id and profile2.get("email") == email:
        results.add_pass("User data persists across sessions")
    else:
        results.add_fail("User data persistence", "User ID or email mismatch")

def test_quote_data_persistence(results):
    """Test that quotes persist and are correctly associated with users"""
    print("\n--- Testing Quote Data Persistence ---")
    
    # Create user
    email = f"quote_persist_{int(time.time()*1000)}@example.com"
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": "QuotePersist123", "name": "Quote Persist Test"}
    )
    
    if response.status_code not in [200, 201]:
        results.add_fail("User creation for quote test", f"Status: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    
    # Create quote
    try:
        from PIL import Image
        
        img = Image.new('RGB', (400, 300), color='lightgreen')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        files = {'file': ('persist_test.jpg', buffer.getvalue(), 'image/jpeg')}
        data = {
            'project_name': 'Persistence Test Project',
            'location': 'Test Location',
            'description': 'Testing quote persistence'
        }
        
        response = requests.post(
            f"{BASE_URL}/v1/quotes",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )
        
        if response.status_code != 200:
            results.add_fail("Quote creation for persistence test", f"Status: {response.status_code}")
            return
        
        # Get quotes immediately
        response = requests.get(
            f"{BASE_URL}/v1/quotes",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            results.add_fail("Immediate quote retrieval", f"Status: {response.status_code}")
            return
        
        quotes1 = response.json()
        count1 = len(quotes1) if isinstance(quotes1, list) else 0
        
        # Wait a moment and retrieve again
        time.sleep(2)
        
        response = requests.get(
            f"{BASE_URL}/v1/quotes",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            results.add_fail("Delayed quote retrieval", f"Status: {response.status_code}")
            return
        
        quotes2 = response.json()
        count2 = len(quotes2) if isinstance(quotes2, list) else 0
        
        if count1 == count2 and count1 > 0:
            results.add_pass("Quote data persists", f"{count1} quote(s) consistent")
        else:
            results.add_fail("Quote persistence", f"Count changed: {count1} -> {count2}")
    
    except Exception as e:
        results.add_fail("Quote persistence test", f"Error: {str(e)}")

def test_user_isolation(results):
    """Test that users can only see their own data"""
    print("\n--- Testing User Data Isolation ---")
    
    # Create two users
    email1 = f"user1_{int(time.time()*1000)}@example.com"
    email2 = f"user2_{int(time.time()*1000)}@example.com"
    
    response1 = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email1, "password": "User1Test123", "name": "User 1"}
    )
    
    response2 = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email2, "password": "User2Test123", "name": "User 2"}
    )
    
    if response1.status_code not in [200, 201] or response2.status_code not in [200, 201]:
        results.add_fail("User creation for isolation test", "Could not create test users")
        return
    
    token1 = response1.json()["access_token"]
    token2 = response2.json()["access_token"]
    
    # Create quote for user 1
    try:
        from PIL import Image
        
        img = Image.new('RGB', (200, 200), color='red')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        files = {'file': ('user1_quote.jpg', buffer.getvalue(), 'image/jpeg')}
        data = {'project_name': 'User 1 Project', 'location': 'Location 1'}
        
        response = requests.post(
            f"{BASE_URL}/v1/quotes",
            headers={"Authorization": f"Bearer {token1}"},
            files=files,
            data=data
        )
        
        if response.status_code != 200:
            results.add_warning("Quote creation for user 1", f"Status: {response.status_code}")
    
    except Exception as e:
        results.add_warning("Quote creation for isolation test", str(e))
    
    # Get quotes for both users
    response1 = requests.get(
        f"{BASE_URL}/v1/quotes",
        headers={"Authorization": f"Bearer {token1}"}
    )
    
    response2 = requests.get(
        f"{BASE_URL}/v1/quotes",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    if response1.status_code != 200 or response2.status_code != 200:
        results.add_fail("Quote retrieval for isolation test", "Could not get quotes")
        return
    
    quotes1 = response1.json()
    quotes2 = response2.json()
    
    count1 = len(quotes1) if isinstance(quotes1, list) else 0
    count2 = len(quotes2) if isinstance(quotes2, list) else 0
    
    # User 1 should have at least 1 quote, user 2 should have 0
    if count1 >= 1 and count2 == 0:
        results.add_pass("User data isolation", f"User1: {count1} quotes, User2: {count2} quotes")
    else:
        results.add_fail("User data isolation", f"User1: {count1} quotes, User2: {count2} quotes (expected User2=0)")

def test_concurrent_operations(results):
    """Test handling of concurrent requests"""
    print("\n--- Testing Concurrent Operations ---")
    
    # Create user
    email = f"concurrent_{int(time.time()*1000)}@example.com"
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": "Concurrent123", "name": "Concurrent Test"}
    )
    
    if response.status_code not in [200, 201]:
        results.add_fail("User creation for concurrent test", f"Status: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    
    # Make multiple concurrent requests
    import threading
    
    successes = []
    failures = []
    
    def make_request():
        try:
            response = requests.get(
                f"{BASE_URL}/v1/user/profile",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            if response.status_code == 200:
                successes.append(1)
            else:
                failures.append(1)
        except:
            failures.append(1)
    
    threads = []
    for i in range(5):
        t = threading.Thread(target=make_request)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    success_count = len(successes)
    
    if success_count >= 4:  # Allow 1 failure
        results.add_pass("Concurrent request handling", f"{success_count}/5 successful")
    else:
        results.add_fail("Concurrent requests", f"Only {success_count}/5 successful")

def test_api_rate_limiting(results):
    """Test if API has rate limiting (if implemented)"""
    print("\n--- Testing API Rate Limiting ---")
    
    # Create user
    email = f"rate_limit_{int(time.time()*1000)}@example.com"
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": "RateLimit123", "name": "Rate Limit Test"}
    )
    
    if response.status_code not in [200, 201]:
        results.add_fail("User creation for rate limit test", f"Status: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    
    # Make many rapid requests
    rate_limited = False
    for i in range(20):
        response = requests.get(
            f"{BASE_URL}/v1/user/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 429:  # Too Many Requests
            rate_limited = True
            break
    
    if rate_limited:
        results.add_pass("Rate limiting enabled")
    else:
        results.add_warning("Rate limiting", "Not detected (may not be implemented)")

def test_full_user_workflow(results):
    """Test complete user workflow from signup to quote generation"""
    print("\n--- Testing Full User Workflow ---")
    
    workflow_steps = []
    
    email = f"workflow_{int(time.time()*1000)}@example.com"
    password = "Workflow123"
    
    # Step 1: Register
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": password, "name": "Workflow Test"}
    )
    
    if response.status_code in [200, 201] and "access_token" in response.json():
        workflow_steps.append("Registration")
        token = response.json()["access_token"]
    else:
        results.add_fail("Full workflow - Registration", f"Status: {response.status_code}")
        return
    
    # Step 2: Get Profile
    response = requests.get(
        f"{BASE_URL}/v1/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        workflow_steps.append("Profile Retrieval")
    else:
        results.add_fail("Full workflow - Profile", f"Status: {response.status_code}")
    
    # Step 3: Create Quote
    try:
        from PIL import Image
        
        img = Image.new('RGB', (300, 300), color='blue')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        files = {'file': ('workflow.jpg', buffer.getvalue(), 'image/jpeg')}
        data = {
            'project_name': 'Workflow Test Project',
            'location': 'Workflow Location',
            'description': 'Testing complete workflow'
        }
        
        response = requests.post(
            f"{BASE_URL}/v1/quotes",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            workflow_steps.append("Quote Creation")
        else:
            results.add_warning("Full workflow - Quote Creation", f"Status: {response.status_code}")
    
    except Exception as e:
        results.add_warning("Full workflow - Quote Creation", str(e))
    
    # Step 4: Retrieve Quotes
    response = requests.get(
        f"{BASE_URL}/v1/quotes",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        workflow_steps.append("Quote Retrieval")
    
    # Step 5: Re-login
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    
    if response.status_code == 200:
        workflow_steps.append("Re-login")
    
    if len(workflow_steps) >= 4:
        results.add_pass("Full user workflow", f"{len(workflow_steps)}/5 steps completed: {', '.join(workflow_steps)}")
    else:
        results.add_fail("Full user workflow", f"Only {len(workflow_steps)}/5 steps completed")

def main():
    print("="*70)
    print("COMPREHENSIVE DATABASE & INTEGRATION TEST")
    print("="*70)
    print(f"Testing: {BASE_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = TestResults()
    
    # Run all tests
    test_user_data_persistence(results)
    test_quote_data_persistence(results)
    test_user_isolation(results)
    test_concurrent_operations(results)
    test_api_rate_limiting(results)
    test_full_user_workflow(results)
    
    # Print summary
    success = results.summary()
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
