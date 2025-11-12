"""Test Stripe payment integration and subscription flow"""
import requests
import time
import os

BASE_URL = "https://quotegenie-api.fly.dev"

def test_payment_configuration():
    """Test that Stripe is properly configured"""
    print("\n💳 Testing Payment Configuration...")
    print("=" * 60)
    
    # Check payment status
    response = requests.get(f"{BASE_URL}/api/v1/payment/status")
    
    if response.status_code == 200:
        status = response.json()
        configured = status.get("configured", False)
        
        if configured:
            print("✅ Stripe payment service is configured")
        else:
            print("⚠️ Stripe payment service is NOT configured")
            print("   This is expected for test/development environments")
        
        return configured
    else:
        print(f"❌ Failed to check payment status: {response.status_code}")
        return False

def test_payment_config_endpoint():
    """Test payment config endpoint (publishable key)"""
    print("\n🔑 Testing Payment Config Endpoint...")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/v1/payment/config")
    
    if response.status_code == 200:
        config = response.json()
        
        if config.get("configured"):
            print("✅ Payment config endpoint accessible")
            
            # Check for publishable key (shouldn't expose it fully in logs)
            if config.get("publishableKey"):
                key = config["publishableKey"]
                masked_key = key[:7] + "..." + key[-4:] if len(key) > 11 else "***"
                print(f"   Publishable Key: {masked_key}")
        else:
            print("⚠️ Payment config not fully configured")
            print(f"   Response: {config}")
    else:
        print(f"❌ Payment config endpoint failed: {response.status_code}")

def test_webhook_info():
    """Test webhook information endpoint"""
    print("\n🪝 Testing Webhook Information...")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/v1/webhooks/stripe")
    
    if response.status_code == 200:
        info = response.json()
        print("✅ Webhook info endpoint accessible")
        print(f"   URL: {info.get('url', 'N/A')}")
        print(f"   Method: {info.get('method', 'N/A')}")
        print(f"   Configured: {info.get('configured', False)}")
        
        events = info.get('events', [])
        if events:
            print(f"   Events monitored: {len(events)}")
            for event in events:
                print(f"      - {event}")
    else:
        print(f"❌ Webhook info endpoint failed: {response.status_code}")

def test_pro_signup_with_checkout():
    """Test signing up for Pro plan (creates checkout session)"""
    print("\n🚀 Testing Pro Plan Signup (Checkout Session Creation)...")
    print("=" * 60)
    
    email = f"pro_test_{int(time.time()*1000)}@example.com"
    password = "ProTest123"
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "name": "Pro Test User",
            "plan": "pro"  # Request pro plan during signup
        }
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        data = response.json()
        
        # Check if checkout session was created
        if "checkout_session_id" in data:
            print("✅ Checkout session created")
            print(f"   Session ID: {data['checkout_session_id'][:20]}...")
            
            if "checkout_url" in data:
                print(f"   Checkout URL available: Yes")
            
            print(f"   Message: {data.get('message', 'N/A')}")
            
            # User should still be on free plan until payment completes
            if "access_token" in data:
                token = data["access_token"]
                profile_response = requests.get(
                    f"{BASE_URL}/v1/user/profile",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if profile_response.status_code == 200:
                    profile = profile_response.json()
                    current_plan = profile.get("plan", "unknown")
                    print(f"   Current Plan: {current_plan} (should be 'free' until payment)")
                    
                    if current_plan == "free":
                        print("✅ User correctly starts on free plan")
                    else:
                        print("⚠️ User on unexpected plan")
        
        elif response.status_code == 503:
            print("⚠️ Payment service not configured (expected for test environments)")
            print(f"   Message: {data.get('detail', 'N/A')}")
        
        else:
            print("ℹ️ No checkout session (may have registered as free)")
            print(f"   Response: {data}")
    
    else:
        print(f"❌ Pro signup failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")

def test_subscription_upgrade_endpoint():
    """Test if there's an upgrade endpoint for existing users"""
    print("\n⬆️ Testing Subscription Upgrade Endpoint...")
    print("=" * 60)
    
    # First create a free user
    email = f"upgrade_test_{int(time.time()*1000)}@example.com"
    password = "UpgradeTest123"
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "name": "Upgrade Test User"
        }
    )
    
    if response.status_code not in [200, 201]:
        print(f"⚠️ Could not create test user: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    
    # Try to find upgrade endpoint
    upgrade_endpoints = [
        "/api/v1/subscription/upgrade",
        "/api/v1/payment/upgrade",
        "/v1/subscription/upgrade",
        "/api/v1/checkout/create"
    ]
    
    found_endpoint = False
    
    for endpoint in upgrade_endpoints:
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            json={"plan": "pro"}
        )
        
        if response.status_code != 404:
            found_endpoint = True
            print(f"✅ Found upgrade endpoint: {endpoint}")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            break
    
    if not found_endpoint:
        print("ℹ️ No dedicated upgrade endpoint found")
        print("   Note: Users upgrade by signing up with plan='pro' parameter")

def main():
    print("\n" + "="*60)
    print("💳 STRIPE PAYMENT INTEGRATION TEST SUITE")
    print("="*60)
    
    # Test configuration
    is_configured = test_payment_configuration()
    
    # Test config endpoint
    test_payment_config_endpoint()
    
    # Test webhook info
    test_webhook_info()
    
    # Test pro signup with checkout
    test_pro_signup_with_checkout()
    
    # Test upgrade endpoint
    test_subscription_upgrade_endpoint()
    
    print("\n" + "="*60)
    print("✅ PAYMENT TESTING COMPLETE")
    print("="*60)
    
    if not is_configured:
        print("\n⚠️ NOTE: Payment service not fully configured")
        print("   This is normal for development/test environments")
        print("   In production, ensure STRIPE_SECRET_KEY and")
        print("   STRIPE_PUBLISHABLE_KEY are set in Fly.io secrets")
    
    print()

if __name__ == "__main__":
    main()
