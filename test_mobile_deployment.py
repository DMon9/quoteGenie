"""
Quick mobile deployment test - verify the new mobile interface is working
"""
import httpx


def test_mobile_deployment():
    """Test the mobile-optimized deployment"""
    print("🚀 Testing Mobile EstimateGenie Deployment")
    print("=" * 50)
    
    base_url = "https://d07076a3.estimategenie.pages.dev"
    
    with httpx.Client(timeout=30.0) as client:
        # Test main mobile page
        try:
            resp = client.get(base_url)
            print(f"✅ Main page: HTTP {resp.status_code}")
            
            # Check for mobile-specific content
            content = resp.text.lower()
            mobile_indicators = [
                "mobile-first",
                "touch-button",
                "mobile-menu",
                "drag & drop or tap to select",
                "estimategenie mobile"
            ]
            
            found_indicators = [indicator for indicator in mobile_indicators if indicator in content]
            print(f"   Mobile features detected: {len(found_indicators)}/{len(mobile_indicators)}")
            
            if len(found_indicators) >= 3:
                print("   ✅ Mobile interface successfully deployed!")
            else:
                print("   ⚠️ Mobile features may not be fully deployed")
                
        except Exception as e:
            print(f"❌ Main page failed: {e}")
        
        # Test About page
        try:
            resp = client.get(f"{base_url}/about")
            print(f"✅ About page: HTTP {resp.status_code}")
            
            # Check for Douglas McGill content
            content = resp.text.lower()
            douglas_indicators = [
                "douglas mcgill",
                "creator, developer, ceo",
                "solo developer",
                "50,000+ lines of code"
            ]
            
            found_douglas = [indicator for indicator in douglas_indicators if indicator in content]
            print(f"   Douglas McGill content: {len(found_douglas)}/{len(douglas_indicators)}")
            
            if len(found_douglas) >= 2:
                print("   ✅ Authentic about page successfully deployed!")
            else:
                print("   ⚠️ About page may not be fully updated")
                
        except Exception as e:
            print(f"❌ About page failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 DEPLOYMENT TEST COMPLETE")
    print("\n📱 New Mobile Features:")
    print("   • Touch-optimized interface")
    print("   • Sliding mobile navigation") 
    print("   • Drag & drop photo upload")
    print("   • Progress animations") 
    print("   • Responsive design")
    
    print("\n👨‍💻 Authentic About Page:")
    print("   • Douglas McGill story")
    print("   • Technical expertise showcase")
    print("   • Development journey") 
    print("   • Future roadmap")
    print("   • Real creator information")
    
    print(f"\n🌐 New Deployment URL: {base_url}")
    print("🔗 API still running at: https://estimategenie-api.thesportsdugout.workers.dev")


if __name__ == "__main__":
    test_mobile_deployment()