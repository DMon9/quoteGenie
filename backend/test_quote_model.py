#!/usr/bin/env python3
"""Test that the QuoteResponse model works correctly with the new Pydantic implementation"""

from models.quote import QuoteResponse, Material, LaborItem, Timeline, WorkStep, Phase, RiskItem
from datetime import datetime, timezone
import json


def test_quote_response_creation():
    """Test creating a QuoteResponse with proper types"""
    
    # Create component objects
    timeline = Timeline(
        estimated_hours=40,
        estimated_days=5,
        min_days=3,
        max_days=7
    )
    
    materials = [
        Material(
            name="Drywall",
            quantity=10,
            unit="sheets",
            unit_price=12.50,
            total=125.00
        ),
        Material(
            name="Paint",
            quantity=5,
            unit="gallons",
            unit_price=35.00,
            total=175.00
        )
    ]
    
    labor = [
        LaborItem(
            trade="Drywall",
            hours=20,
            rate=50.00,
            total=1000.00
        ),
        LaborItem(
            trade="Painting",
            hours=15,
            rate=40.00,
            total=600.00
        )
    ]
    
    steps = [
        WorkStep(order=1, description="Measure and mark walls", duration="1 day"),
        WorkStep(order=2, description="Install drywall", duration="2 days"),
        WorkStep(order=3, description="Paint", duration="1 day")
    ]
    
    phases = [
        Phase(name="Prep", description="Wall preparation", estimated_hours=8),
        Phase(name="Installation", description="Install materials", estimated_hours=20),
        Phase(name="Finishing", description="Paint and finish", estimated_hours=12)
    ]
    
    risks = [
        RiskItem(id="risk_1", description="Water damage", impact="high"),
        RiskItem(id="risk_2", description="Mold discovery", impact="medium")
    ]
    
    # Create the QuoteResponse
    quote = QuoteResponse(
        id="quote_test_123",
        status="completed",
        total_cost={
            "currency": "USD",
            "amount": 2300.00,
            "breakdown": {
                "materials": 300.00,
                "labor": 1600.00,
                "profit": 345.00,
                "contingency": 55.00
            }
        },
        timeline=timeline,
        materials=materials,
        labor=labor,
        steps=steps,
        confidence_score=0.85,
        vision_analysis={"scene": "bathroom", "detected_items": ["tile", "plumbing"]},
        options_applied={"quality": "premium", "contingency_pct": 5},
        scope="bathroom_renovation",
        phases=phases,
        risks=risks,
        created_at=datetime.now(timezone.utc)
    )
    
    # Test serialization
    quote_dict = quote.model_dump()
    print("✅ QuoteResponse serialized successfully")
    print(f"   ID: {quote_dict['id']}")
    print(f"   Status: {quote_dict['status']}")
    print(f"   Total Cost: ${quote_dict['total_cost']['amount']:,.2f}")
    print(f"   Materials: {len(quote_dict['materials'])} items")
    print(f"   Labor: {len(quote_dict['labor'])} items")
    print(f"   Steps: {len(quote_dict['steps'])}")
    print(f"   Phases: {len(quote_dict['phases'])}")
    print(f"   Risks: {len(quote_dict['risks'])}")
    print(f"   Confidence: {quote_dict['confidence_score'] * 100:.0f}%")
    
    # Test JSON serialization
    json_str = quote.model_dump_json()
    print(f"\n✅ QuoteResponse JSON serialized ({len(json_str)} bytes)")
    
    # Test reconstruction from dict
    quote_from_dict = QuoteResponse(**quote_dict)
    print(f"\n✅ QuoteResponse reconstructed from dict")
    print(f"   Reconstructed ID: {quote_from_dict.id}")
    
    print("\n✅ All tests passed!")
    return True


if __name__ == "__main__":
    try:
        test_quote_response_creation()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
