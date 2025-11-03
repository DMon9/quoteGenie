#!/usr/bin/env python3
"""
Test dynamic quote generation with corrected API key
"""
import httpx
import json
from PIL import Image, ImageDraw
import io

def test_dynamic_quote():
    """Test if we get different responses for different project types"""
    
    # Create a kitchen image
    img = Image.new('RGB', (400, 300), 'lightblue')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 350, 250], fill='white')
    draw.text((100, 120), 'KITCHEN', fill='black')
    
    buf = io.BytesIO()
    img.save(buf, 'JPEG')
    buf.seek(0)
    
    files = {'file': ('kitchen.jpg', buf, 'image/jpeg')}
    data = {
        'project_type': 'kitchen', 
        'description': 'Complete kitchen renovation with granite countertops, custom cabinets, and hardwood floors'
    }
    
    try:
        print("🧪 Testing dynamic quote generation...")
        response = httpx.post(
            'https://estimategenie-api.thesportsdugout.workers.dev/api/v1/quotes',
            files=files,
            data=data,
            timeout=60
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Quote ID: {result['id']}")
            print(f"💰 Total Cost: ${result['total_cost']['amount']}")
            print("🧱 Materials:")
            for material in result['materials'][:5]:
                print(f"   - {material['name']}: {material['quantity']} {material['unit']} @ ${material['unit_price']} = ${material['total']}")
            
            # Check if we're getting kitchen-specific materials
            material_names = [m['name'].lower() for m in result['materials']]
            if any(kitchen_item in ' '.join(material_names) for kitchen_item in ['cabinet', 'granite', 'countertop', 'appliance', 'tile']):
                print("🎉 SUCCESS: Getting kitchen-specific materials!")
            else:
                print("⚠️  Still getting generic materials (drywall, paint, etc.)")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_dynamic_quote()