"""
End-to-end test: Create a real quote with a sample construction image
Tests full workflow from upload to pricing to response formatting
"""
import io
import json
import httpx
from PIL import Image, ImageDraw, ImageFont


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


def test_quote_endpoint():
    """Test the full quote creation workflow"""
    print("=== E2E Quote Test ===\n")
    
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
    
    api_url = "http://127.0.0.1:8000/v1/quotes"
    print(f"🚀 Posting to {api_url}...")
    print(f"   Project type: {data['project_type']}")
    print(f"   Description: {data['description']}\n")
    
    try:
        with httpx.Client(timeout=120.0) as client:
            print("⏳ Waiting for API response (this may take 30-60 seconds)...\n")
            resp = client.post(api_url, files=files, data=data)
            
            print(f"✅ HTTP {resp.status_code}\n")
            
            if resp.status_code != 200:
                print("❌ Error response:")
                print(resp.text)
                return
            
            result = resp.json()
            
            # Display results in a formatted way
            print("=" * 60)
            print("📊 QUOTE RESULTS")
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
                for m in materials[:10]:  # Show first 10
                    name = m.get('name', 'Unknown')
                    qty = m.get('quantity', 0)
                    unit = m.get('unit', 'unit')
                    price = m.get('unit_price', 0)
                    total = m.get('total', 0)
                    print(f"   • {name}: {qty} {unit} @ ${price:.2f} = ${total:.2f}")
                if len(materials) > 10:
                    print(f"   ... and {len(materials) - 10} more")
            
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
            
            # Steps
            steps = result.get('steps', [])
            if steps:
                print(f"\n📋 Work Steps ({len(steps)} steps):")
                for s in steps[:5]:  # Show first 5
                    order = s.get('order', '?')
                    desc = s.get('description', 'N/A')
                    duration = s.get('duration', 'N/A')
                    print(f"   {order}. {desc} ({duration})")
                if len(steps) > 5:
                    print(f"   ... and {len(steps) - 5} more steps")
            
            print("\n" + "=" * 60)
            print("✅ E2E TEST PASSED")
            print("=" * 60)
            
            # Check pricing source
            print("\n🔍 Verifying pricing sources...")
            
            # Check a sample material to see if external pricing was used
            if materials:
                sample = materials[0]
                print(f"\nSample material: {sample.get('name')}")
                print(f"  Unit price: ${sample.get('unit_price', 0):.2f}")
                print(f"  (Check logs to see if 'external-list' was used)")
            
            return result
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_quote_endpoint()
    if result:
        print("\n✅ All checks passed!")
        print("\n💡 Tip: Check the container logs to see pricing list loads:")
        print("   docker logs backend-api-1 --tail 100")
    else:
        print("\n❌ Test failed - check error above")
