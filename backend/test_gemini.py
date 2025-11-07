"""Quick test script to verify Gemini integration."""
import asyncio
import sys
import os

import pytest

# Add parent to path
sys.path.insert(0, '/app')

from services.llm_service import LLMService

if not os.getenv("GOOGLE_API_KEY"):
    pytest.skip("Integration test requires GOOGLE_API_KEY", allow_module_level=True)

@pytest.mark.asyncio
async def test_gemini():
    """Test Gemini LLM service."""
    llm = LLMService()
    
    print(f"✓ LLM Service initialized")
    print(f"  Provider: {llm.provider}")
    print(f"  Ready: {llm.ready}")
    print(f"  Model: {llm.gemini_model if llm.provider == 'gemini' else llm.model}")
    print(f"  Has API Key: {bool(llm.google_api_key)}")
    print()
    
    # Test with a simple bathroom project
    vision_results = {
        'detections': [{'class': 'bathroom', 'confidence': 0.8}],
        'measurements': {'estimated_area_sqft': 50},
        'scene_description': 'Small bathroom with tile walls'
    }
    
    print("Testing LLM reasoning...")
    print(f"  Vision input: bathroom, 50 sqft")
    print()
    
    try:
        result = await llm.reason_about_project(
            vision_results,
            'bathroom',
            'Small bathroom renovation - replace tiles and fixtures'
        )
        
        print("✅ LLM call succeeded!")
        print(f"  Result keys: {list(result.keys())}")
        print()
        
        # Parse the analysis
        analysis = result.get('analysis', '')
        print("📊 Raw analysis (first 500 chars):")
        print(repr(analysis[:500]))
        print()
        
        # Check extracted data
        materials = result.get('materials_needed', [])
        recommendations = result.get('recommendations', [])
        
        print(f"🧱 Materials extracted: {len(materials)}")
        if materials:
            for mat in materials[:3]:
                print(f"  - {mat}")
        
        print(f"💡 Recommendations: {len(recommendations)}")
        if recommendations:
            for rec in recommendations[:3]:
                print(f"  - {rec}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_gemini())
    sys.exit(0 if success else 1)
