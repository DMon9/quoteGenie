"""
Debug Session Persistence Issue
Test JWT token creation and verification
"""

import requests
import json

BASE_URL = "https://quotegenie-api.fly.dev"

# Create a new test user
test_email = f"debugsession{int(__import__('time').time())}@example.com"
password = "TestPassword123!"

print("="*60)
print("🔍 DEBUGGING SESSION PERSISTENCE")
print("="*60)

# Step 1: Register
print("\n1️⃣ Registering user...")
register_response = requests.post(
    f"{BASE_URL}/api/v1/auth/register",
    json={
        "name": "Debug User",
        "email": test_email,
        "password": password,
        "plan": "free"
    },
    headers={"Content-Type": "application/json"}
)

print(f"   Status: {register_response.status_code}")
if register_response.status_code == 200:
    register_data = register_response.json()
    token = register_data.get('access_token')
    print(f"   ✓ Registration successful")
    print(f"   Token type: {register_data.get('token_type')}")
    print(f"   Token length: {len(token) if token else 0} chars")
    print(f"   Token preview: {token[:50]}..." if token else "   No token")
else:
    print(f"   ✗ Registration failed: {register_response.text}")
    exit(1)

# Step 2: Test token immediately
print("\n2️⃣ Testing token immediately after registration...")
test1 = requests.get(
    f"{BASE_URL}/v1/quotes",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
)
print(f"   Status: {test1.status_code}")
print(f"   Response: {test1.text[:200] if test1.text else 'Empty'}")

# Step 3: Login to get fresh token
print("\n3️⃣ Logging in to get fresh token...")
login_response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={"email": test_email, "password": password},
    headers={"Content-Type": "application/json"}
)

print(f"   Status: {login_response.status_code}")
if login_response.status_code == 200:
    login_data = login_response.json()
    login_token = login_data.get('access_token')
    print(f"   ✓ Login successful")
    print(f"   Token type: {login_data.get('token_type')}")
    print(f"   Token length: {len(login_token) if login_token else 0} chars")
    print(f"   Same as registration token: {token == login_token}")
else:
    print(f"   ✗ Login failed: {login_response.text}")
    exit(1)

# Step 4: Test login token
print("\n4️⃣ Testing login token...")
test2 = requests.get(
    f"{BASE_URL}/v1/quotes",
    headers={
        "Authorization": f"Bearer {login_token}",
        "Content-Type": "application/json"
    }
)
print(f"   Status: {test2.status_code}")
print(f"   Response: {test2.text[:200] if test2.text else 'Empty'}")

# Step 5: Test with various header formats
print("\n5️⃣ Testing different auth header formats...")

formats = [
    ("Bearer {token}", f"Bearer {login_token}"),
    ("bearer {token}", f"bearer {login_token}"),
    ("{token}", login_token)
]

for desc, auth_value in formats:
    test_response = requests.get(
        f"{BASE_URL}/v1/quotes",
        headers={"Authorization": auth_value}
    )
    print(f"   '{desc}': {test_response.status_code}")

# Step 6: Check if endpoint exists
print("\n6️⃣ Checking if /v1/quotes endpoint exists...")
test3 = requests.get(f"{BASE_URL}/v1/quotes")
print(f"   Without auth: {test3.status_code}")
print(f"   Response: {test3.text[:200] if test3.text else 'Empty'}")

# Step 7: Try a different endpoint
print("\n7️⃣ Testing /api/v1/ping endpoint...")
test4 = requests.get(f"{BASE_URL}/api/v1/ping")
print(f"   Status: {test4.status_code}")
print(f"   Response: {test4.text[:200] if test4.text else 'Empty'}")

print("\n" + "="*60)
print("Debug complete!")
print("="*60)
