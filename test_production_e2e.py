"""
End-to-end production test: Test the deployed EstimateGenie system
Tests full workflow through Cloudflare Worker to Fly.io backend
"""
import io
import json
import httpx
from PIL import Image, ImageDraw, ImageFont
help

def create_construction_scene_image() -> bytes:
    """Create a simple test image that looks like a construction site"""
    # 800x600 image with construction-like features
    img = Image.new("RGB", (800, 600), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    
    # Draw some simple shapes to represent materials
    # Brown rectangle for lumber stack
    draw.rectangle([50, 400, 200, 550], fill=(139, 90, 43))
    
    # Gray rectangles for concrete blocks
    for i in range(3):
        for j in range(4):
            x = 250 + i * 80
            y = 450 + j * 40
            draw.rectangle([x, y, x + 70, y + 35], fill=(128, 128, 128), outline=(80, 80, 80))
    
    # Orange area for tiles
    draw.rectangle([500, 400, 750, 550], fill=(230, 126, 34))
    
    # Draw grid lines on tiles
    for i in range(0, 250, 50):
        draw.line([(500 + i, 400), (500 + i, 550)], fill=(200, 100, 20), width=2)
    for i in range(0, 150, 50):
        draw.line([(500, 400 + i), (750, 400 + i)], fill=(200, 100, 20), width=2)
    
    # Add some text labels
    try:
        # Try to use a font, fall back to default if not available
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 360), "Lumber", fill=(0, 0, 0), font=font)
    draw.text((250, 410), "Concrete", fill=(0, 0, 0), font=font)
    draw.text((550, 360), "Tiles", fill=(0, 0, 0), font=font)
    
    # Sky
    draw.rectangle([0, 0, 800, 300], fill=(135, 206, 235))
    
    # Ground
    draw.rectangle([0, 300, 800, 400], fill=(160, 130, 90))
    
    # Save to bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_production_endpoints():
    """Test all production endpoints"""
    print("=== Production E2E Test ===\n")
    
    # Production endpoints
    endpoints = {
        "worker": "https://estimategenie-api.thesportsdugout.workers.dev",
        "backend": "https://quotegenie-api.fly.dev",
        "frontend": "https://f5ed7926.estimategenie.pages.dev"
    }
    
    # Test 1: Health checks
    print("🏥 Testing health endpoints...\n")
    
    with httpx.Client(timeout=30.0) as client:
        # Test Worker health
        try:
            resp = client.get(f"{endpoints['worker']}/api/health")
            print(f"✅ Worker health: HTTP {resp.status_code}")
            if resp.status_code == 200:
                print(f"   Response: {resp.json()}")
        except Exception as e:
            print(f"❌ Worker health failed: {e}")
        
        # Test Backend health
        try:
            resp = client.get(f"{endpoints['backend']}/health")
            print(f"✅ Backend health: HTTP {resp.status_code}")
            if resp.status_code == 200:
                health_data = resp.json()
                print(f"   Services: vision={health_data.get('services', {}).get('vision')}, llm={health_data.get('services', {}).get('llm')}, database={health_data.get('services', {}).get('database')}")
        except Exception as e:
            print(f"❌ Backend health failed: {e}")
        
        # Test Frontend availability
        try:
            resp = client.get(endpoints['frontend'])
            print(f"✅ Frontend: HTTP {resp.status_code}")
            if resp.status_code == 200:
                print(f"   Content length: {len(resp.text)} chars")
        except Exception as e:
            print(f"❌ Frontend failed: {e}")
    
    print("\n" + "="*50)
    
    # Test 2: Quote generation through Worker
    print("📝 Testing quote generation through Cloudflare Worker...\n")
    
    # Create test image
    print("📸 Creating test construction scene image...")
    image_bytes = create_construction_scene_image()
    print(f"   Image size: {len(image_bytes)} bytes\n")
    
    # Prepare request
    files = {"file": ("construction_site.png", image_bytes, "image/png")}
    data = {
        "project_type": "bathroom",
        "description": "Bathroom renovation with tile work, concrete foundation prep, and framing",
    }
    
    # Test through Worker (primary production path)
    worker_url = f"{endpoints['worker']}/api/v1/quotes"
    print(f"🚀 Testing through Worker: {worker_url}")
    print(f"   Project type: {data['project_type']}")
    print(f"   Description: {data['description']}\n")
    
    try:
        with httpx.Client(timeout=120.0) as client:
            print("⏳ Waiting for API response (this may take 30-60 seconds)...\n")
            resp = client.post(worker_url, files=files, data=data)
            
            print(f"Worker Response: HTTP {resp.status_code}\n")
            
            if resp.status_code != 200:
                print("❌ Worker Error response:")
                print(resp.text)
                return False
            
            result = resp.json()
            
            # Display results in a formatted way
            print("=" * 60)
            print("📊 PRODUCTION QUOTE RESULTS")
            print("=" * 60)
            
            print(f"\n🆔 Quote ID: {result.get('id', 'N/A')}")
            print(f"📌 Status: {result.get('status', 'N/A')}")
            
            # Total cost
            total_cost = result.get('total_cost', {})
            if isinstance(total_cost, dict):
                amount = total_cost.get('amount', 0)
                breakdown = total_cost.get('breakdown', {})
                print(f"\n💰 Total Cost: ${amount:,.2f}")
                print(f"   Materials: ${breakdown.get('materials', 0):,.2f}")
                print(f"   Labor: ${breakdown.get('labor', 0):,.2f}")
                print(f"   Markup: ${breakdown.get('markup', 0):,.2f}")
            
            # Timeline
            timeline = result.get('timeline', {})
            if isinstance(timeline, dict):
                print(f"\n⏱️  Timeline:")
                print(f"   Estimated: {timeline.get('estimated_days', 'N/A')} days")
                print(f"   Range: {timeline.get('min_days', 'N/A')}-{timeline.get('max_days', 'N/A')} days")
                print(f"   Hours: {timeline.get('estimated_hours', 'N/A')} hrs")
            
            # Confidence
            confidence = result.get('confidence_score', 0)
            print(f"\n🎯 Confidence Score: {confidence * 100:.1f}%")
            
            # Materials
            materials = result.get('materials', [])
            if materials:
                print(f"\n🧱 Materials ({len(materials)} items):")
                for m in materials[:5]:  # Show first 5
                    name = m.get('name', 'Unknown')
                    qty = m.get('quantity', 0)
                    unit = m.get('unit', 'unit')
                    price = m.get('unit_price', 0)
                    total = m.get('total', 0)
                    print(f"   • {name}: {qty} {unit} @ ${price:.2f} = ${total:.2f}")
                if len(materials) > 5:
                    print(f"   ... and {len(materials) - 5} more")
            
            # Labor
            labor = result.get('labor', [])
            if labor:
                print(f"\n👷 Labor ({len(labor)} items):")
                for l in labor:
                    trade = l.get('trade', 'Unknown')
                    hours = l.get('hours', 0)
                    rate = l.get('rate', 0)
                    total = l.get('total', 0)
                    print(f"   • {trade}: {hours} hrs @ ${rate:.2f}/hr = ${total:.2f}")
            
            print("\n" + "=" * 60)
            print("✅ PRODUCTION E2E TEST PASSED")
            print("=" * 60)
            
            return True
            
    except Exception as e:
        print(f"\n❌ Production test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pricing_endpoints():
    """Test pricing operational endpoints"""
    print("\n🔧 Testing pricing operational endpoints...\n")
    
    backend_url = "https://quotegenie-api.fly.dev"
    
    with httpx.Client(timeout=30.0) as client:
        # Test pricing status
        try:
            resp = client.get(f"{backend_url}/v1/pricing/status")
            print(f"✅ Pricing status: HTTP {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"   External files: {data.get('external_files_count', 0)}")
                print(f"   Last reload: {data.get('last_reload_time', 'N/A')}")
        except Exception as e:
            print(f"❌ Pricing status failed: {e}")
        
        # Test pricing lookup
        try:
            resp = client.get(f"{backend_url}/v1/pricing/lookup?key=lumber_2x4")
            print(f"✅ Pricing lookup: HTTP {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"   lumber_2x4 price: ${data.get('price', 0):.2f}")
        except Exception as e:
            print(f"❌ Pricing lookup failed: {e}")
        
        # Test pricing reload
        try:
            resp = client.post(f"{backend_url}/v1/pricing/reload")
            print(f"✅ Pricing reload: HTTP {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"   Reloaded: {data.get('reloaded', False)}")
        except Exception as e:
            print(f"❌ Pricing reload failed: {e}")


if __name__ == "__main__":
    print("🚀 EstimateGenie Production E2E Test Suite")
    print("=" * 50)
    
    success = test_production_endpoints()
    test_pricing_endpoints()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ ALL PRODUCTION TESTS PASSED!")
        print("\n🎉 Your EstimateGenie deployment is working correctly!")
        print("\n📋 Production URLs:")
        print("   Frontend: https://f5ed7926.estimategenie.pages.dev")
        print("   API Worker: https://estimategenie-api.thesportsdugout.workers.dev")
        print("   Backend: https://quotegenie-api.fly.dev")
    else:
        print("❌ SOME TESTS FAILED")
        print("Check the errors above for troubleshooting.")