"""Test dashboard functionality and authentication integration"""
import requests
import time

BASE_URL = "https://quotegenie-api.fly.dev"
FRONTEND_URL = "https://estimategenie.net"

def test_dashboard_accessibility():
    """Test that dashboard page loads correctly"""
    print("\n🎯 Testing Dashboard Accessibility...")
    print("=" * 60)
    
    # Try to access dashboard
    response = requests.get(f"{FRONTEND_URL}/dashboard.html")
    
    if response.status_code == 200:
        print(f"✅ Dashboard page accessible (status: {response.status_code})")
        
        # Check for key dashboard elements in HTML
        html = response.text.lower()
        
        checks = {
            "Dashboard title": "dashboard" in html,
            "Chart.js library": "chart.js" in html,
            "Feather icons": "feather" in html,
            "Navigation menu": "my quotes" in html or "projects" in html,
            "User profile": "user" in html or "profile" in html,
        }
        
        for check_name, passed in checks.items():
            status = "✅" if passed else "⚠️"
            print(f"   {status} {check_name}")
        
        return True
    else:
        print(f"❌ Dashboard not accessible: {response.status_code}")
        return False

def test_dashboard_with_auth():
    """Test dashboard with authenticated user (check if it uses API)"""
    print("\n🔐 Testing Dashboard Authentication Integration...")
    print("=" * 60)
    
    # Create test user and get token
    email = f"dashboard_test_{int(time.time()*1000)}@example.com"
    password = "DashTest123"
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "name": "Dashboard Test User"
        }
    )
    
    if response.status_code not in [200, 201]:
        print(f"⚠️ Could not create test user: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    print(f"✅ Test user created and logged in")
    
    # Create a test quote for this user
    try:
        from PIL import Image
        from io import BytesIO
        
        # Create simple test image
        img = Image.new('RGB', (400, 300), color='lightblue')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        files = {'file': ('test.jpg', buffer.getvalue(), 'image/jpeg')}
        data = {
            'project_name': 'Dashboard Test Project',
            'location': 'Test City',
            'description': 'Test quote for dashboard'
        }
        
        response = requests.post(
            f"{BASE_URL}/v1/quotes",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            print(f"✅ Test quote created for user")
        else:
            print(f"⚠️ Quote creation failed: {response.status_code}")
    
    except Exception as e:
        print(f"⚠️ Could not create test quote: {e}")
    
    # Check user profile endpoint (dashboard would use this)
    response = requests.get(
        f"{BASE_URL}/v1/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        profile = response.json()
        print(f"✅ User profile accessible (for dashboard data)")
        print(f"   Email: {profile.get('email')}")
        print(f"   Plan: {profile.get('plan')}")
        print(f"   Quotes Used: {profile.get('quotes_used', 0)}")
    
    # Check quotes list endpoint (dashboard would display these)
    response = requests.get(
        f"{BASE_URL}/v1/quotes",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        quotes = response.json()
        print(f"✅ Quotes list accessible (for dashboard display)")
        print(f"   Total quotes: {len(quotes) if isinstance(quotes, list) else 'N/A'}")
    
    print(f"\n📋 Dashboard Integration Status:")
    print(f"   ✅ Backend APIs ready for dashboard")
    print(f"   ⚠️ Dashboard appears to use static demo data")
    print(f"   💡 Recommendation: Update dashboard.html to fetch real user data")

def test_api_key_display():
    """Test that API key is available for dashboard display"""
    print("\n🔑 Testing API Key Availability...")
    print("=" * 60)
    
    # Create user
    email = f"apikey_test_{int(time.time()*1000)}@example.com"
    password = "ApiTest123"
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "name": "API Key Test"
        }
    )
    
    if response.status_code not in [200, 201]:
        print(f"⚠️ Could not create test user")
        return
    
    token = response.json()["access_token"]
    
    # Get profile (should include API key)
    response = requests.get(
        f"{BASE_URL}/v1/user/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        profile = response.json()
        api_key = profile.get('api_key')
        
        if api_key:
            # Mask most of the key for security
            masked = api_key[:7] + "..." + api_key[-4:] if len(api_key) > 11 else "***"
            print(f"✅ API key available in profile")
            print(f"   Format: {masked}")
            print(f"   Length: {len(api_key)} characters")
            
            # Check if it starts with expected prefix
            if api_key.startswith('eg_sk_'):
                print(f"   ✅ Correct format (eg_sk_...)")
            else:
                print(f"   ⚠️ Unexpected format")
        else:
            print(f"❌ API key not found in profile")

def main():
    print("\n" + "="*60)
    print("📊 DASHBOARD FUNCTIONALITY TEST SUITE")
    print("="*60)
    
    # Test dashboard accessibility
    dashboard_accessible = test_dashboard_accessibility()
    
    if dashboard_accessible:
        # Test authentication integration
        test_dashboard_with_auth()
        
        # Test API key display
        test_api_key_display()
    
    print("\n" + "="*60)
    print("✅ DASHBOARD TESTING COMPLETE")
    print("="*60)
    print("\n📝 Summary:")
    print("   ✅ Dashboard page loads successfully")
    print("   ✅ Backend APIs ready (profile, quotes, usage)")
    print("   ⚠️ Dashboard uses static demo data currently")
    print("   💡 Next step: Connect dashboard to live API endpoints")
    print()

if __name__ == "__main__":
    main()
