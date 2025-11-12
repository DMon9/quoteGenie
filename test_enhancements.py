"""Test password strengthening and user profile endpoint"""
import requests
import time

BASE_URL = "https://quotegenie-api.fly.dev"

def test_password_strengthening():
    """Test that weak passwords are rejected"""
    print("\n🔐 Testing Password Strengthening...")
    print("=" * 60)
    
    weak_passwords = [
        ("password", "No numbers"),
        ("12345678", "No letters"),
        ("pass123", "Too short (7 chars)"),
        ("abc", "Too short (3 chars)"),
        ("Pass", "Too short, no number"),
    ]
    
    rejected = 0
    accepted = 0
    
    for password, reason in weak_passwords:
        email = f"test_{int(time.time()*1000)}@example.com"
        
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "name": "Test User"
            }
        )
        
        if response.status_code == 400 and "Password must be at least" in response.text:
            print(f"✅ REJECTED: '{password}' - {reason}")
            rejected += 1
        else:
            print(f"❌ ACCEPTED: '{password}' - {reason} (should be rejected)")
            accepted += 1
    
    print(f"\n📊 Password Test Results: {rejected}/5 weak passwords rejected")
    
    # Test a strong password
    email = f"strong_{int(time.time()*1000)}@example.com"
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPass123",
            "name": "Strong User"
        }
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ ACCEPTED: 'StrongPass123' - Valid strong password\n")
        return email, "StrongPass123"
    else:
        print(f"❌ REJECTED: 'StrongPass123' - Should be accepted (strong password)")
        print(f"   Response: {response.status_code} - {response.text}\n")
        return None, None

def test_profile_endpoint(email, password):
    """Test the new profile endpoint"""
    print("\n👤 Testing User Profile Endpoint...")
    print("=" * 60)
    
    if not email or not password:
        print("⚠️ Skipping profile test - no valid user created")
        return
    
    # Login to get token
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    
    # Test profile endpoint
    response = requests.get(
        f"{BASE_URL}/v1/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        profile = response.json()
        print("✅ Profile endpoint accessible")
        print(f"\n📋 Profile Data:")
        print(f"   Email: {profile.get('email')}")
        print(f"   Name: {profile.get('name')}")
        print(f"   Plan: {profile.get('plan')}")
        print(f"   Subscription: {profile.get('subscription_status')}")
        print(f"   Quotes Used: {profile.get('quotes_used')}")
        print(f"   API Calls: {profile.get('api_calls_used')}")
        
        # Verify expected fields
        expected_fields = ['id', 'email', 'name', 'plan', 'api_key', 'created_at', 
                          'subscription_status', 'quotes_used', 'api_calls_used', 'plan_limits']
        
        missing_fields = [field for field in expected_fields if field not in profile]
        
        if missing_fields:
            print(f"\n⚠️ Missing fields: {', '.join(missing_fields)}")
        else:
            print(f"\n✅ All expected fields present")
            
    else:
        print(f"❌ Profile endpoint failed: {response.status_code}")
        print(f"   Response: {response.text}")

def main():
    print("\n" + "="*60)
    print("🧪 AUTHENTICATION ENHANCEMENTS TEST SUITE")
    print("="*60)
    
    # Test password strengthening
    email, password = test_password_strengthening()
    
    # Test profile endpoint
    test_profile_endpoint(email, password)
    
    print("\n" + "="*60)
    print("✅ ENHANCEMENT TESTING COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
