"""Final Gemini integration test."""
import asyncio
import sys
sys.path.insert(0, '/app')

from services.llm_service import LLMService

async def main():
    llm = LLMService()
    
    print(f"✅ Gemini configured: {llm.provider}")
    print(f"✅ Model: {llm.gemini_model}")
    print(f"✅ Ready: {llm.ready}")
    print()
    
    # Simple test
    result = await llm.reason_about_project(
        {'detections': [{'class': 'bathroom'}], 'measurements': {'estimated_area_sqft': 50}},
        'bathroom',
        'Replace tiles and fixtures'
    )
    
    print("Result structure:")
    for key, value in result.items():
        if key == 'analysis':
            print(f"  {key}: {len(value)} chars")
        else:
            print(f"  {key}: {value if not isinstance(value, list) else f'{len(value)} items'}")
    
    materials = result.get('materials_needed', [])
    if materials:
        print(f"\n✅ SUCCESS: Extracted {len(materials)} materials:")
        for m in materials[:5]:
            print(f"  - {m.get('name')}: {m.get('quantity')} {m.get('unit')}")
    else:
        print("\n❌ No materials extracted")
    
    challenges = result.get('recommendations', [])
    if challenges:
        print(f"\n✅ Extracted {len(challenges)} recommendations:")
        for c in challenges[:3]:
            print(f"  - {c}")

if __name__ == "__main__":
    asyncio.run(main())
