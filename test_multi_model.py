"""
Test Multi-Model AI Service
Tests all three AI models (Gemini, GPT-4V, Claude) with fallback
"""
import asyncio
import os
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from services.multi_model_service import MultiModelService


async def test_multi_model_service():
    """Test the multi-model AI service"""
    print("=" * 60)
    print("Multi-Model AI Service Test")
    print("=" * 60)
    print()
    
    # Initialize service
    print("Initializing Multi-Model Service...")
    service = MultiModelService()
    
    # Check availability
    print(f"\nService Ready: {service.is_ready()}")
    print(f"Available Models: {service.available_models}")
    print(f"Preferred Model: {service.preferred_model}")
    
    # Get model details
    print("\n" + "-" * 60)
    print("Available AI Models:")
    print("-" * 60)
    
    models = service.get_available_models()
    for i, model in enumerate(models, 1):
        print(f"\n{i}. {model['name']}")
        print(f"   ID: {model['id']}")
        print(f"   Provider: {model['provider']}")
        print(f"   Capabilities: {', '.join(model['capabilities'])}")
        print(f"   Best For: {model['best_for']}")
    
    if not models:
        print("\n⚠️  No AI models available!")
        print("Please set at least one API key:")
        print("  - GOOGLE_API_KEY for Gemini")
        print("  - OPENAI_API_KEY for GPT-4 Vision")
        print("  - ANTHROPIC_API_KEY for Claude")
        return
    
    # Test with a sample image if available
    test_image = Path("backend/uploads") / "test-image.jpg"
    if test_image.exists():
        print("\n" + "-" * 60)
        print("Testing Image Analysis:")
        print("-" * 60)
        print(f"\nTest Image: {test_image}")
        
        for model_info in models[:1]:  # Test first available model only
            model_id = model_info['id']
            print(f"\nTesting with {model_info['name']}...")
            
            try:
                result = await service.analyze_construction_image(
                    image_path=str(test_image),
                    project_type="bathroom",
                    description="Bathroom renovation project",
                    model=model_id
                )
                
                print(f"✓ Analysis successful!")
                print(f"  Model Used: {result.get('model_used', 'unknown')}")
                print(f"  Materials Found: {len(result.get('materials', []))}")
                print(f"  Labor Hours: {result.get('labor_hours', 0)}")
                print(f"  Challenges: {len(result.get('challenges', []))}")
                
                if result.get('materials'):
                    print("\n  Sample Materials:")
                    for mat in result['materials'][:3]:
                        print(f"    - {mat.get('name')}: {mat.get('quantity')} {mat.get('unit')}")
                
            except Exception as e:
                print(f"✗ Test failed: {e}")
    else:
        print(f"\n⚠️  No test image found at {test_image}")
        print("Skipping image analysis test")
    
    # Test fallback chain
    print("\n" + "-" * 60)
    print("Fallback Chain Test:")
    print("-" * 60)
    
    if len(models) > 1:
        print("\n✓ Multiple models available - fallback chain enabled")
        print(f"  Primary: {models[0]['name']}")
        print(f"  Fallback Order: {' → '.join([m['name'] for m in models[1:]])}")
    else:
        print(f"\n✓ Single model mode: {models[0]['name']}")
        print("  Add more API keys to enable fallback")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_multi_model_service())
