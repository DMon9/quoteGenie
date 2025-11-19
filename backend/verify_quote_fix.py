#!/usr/bin/env python3
"""
Verification script for quote generation fix
Tests that QuoteResponse properly validates and serializes with the new Pydantic models
"""

import json
from datetime import datetime, timezone


def test_quote_response_validation():
    """Test that QuoteResponse properly validates data from estimation service"""
    
    print("=" * 70)
    print("TESTING QUOTE RESPONSE VALIDATION")
    print("=" * 70)
    
    # Simulate data returned from estimation service
    estimate = {
        "total_cost": {
            "currency": "USD",
            "amount": 2500.00,
            "breakdown": {
                "materials": 1000.00,
                "labor": 1200.00,
                "profit": 250.00,
                "contingency": 50.00
            }
        },
        "materials": [
            {
                "name": "Drywall",
                "quantity": 10,
                "unit": "sheets",
                "unit_price": 12.50,
                "total": 125.00
            },
            {
                "name": "Paint",
                "quantity": 5,
                "unit": "gallons",
                "unit_price": 35.00,
                "total": 175.00
            }
        ],
        "labor": [
            {
                "trade": "Drywall",
                "hours": 20,
                "rate": 50.00,
                "total": 1000.00
            }
        ],
        "timeline": {
            "estimated_hours": 40,
            "estimated_days": 5,
            "min_days": 3,
            "max_days": 7
        },
        "steps": [
            {"order": 1, "description": "Prep", "duration": "1 day"},
            {"order": 2, "description": "Install", "duration": "2 days"}
        ],
        "confidence_score": 0.85,
        "options_applied": {"quality": "standard"}
    }
    
    advanced_options = {
        "phases": [
            {"name": "Phase 1", "description": "Preparation", "estimated_hours": 8}
        ],
        "risks": [
            {"id": "r1", "description": "Mold", "impact": "high"}
        ],
        "scope": "bathroom_reno"
    }
    
    # Import and test the models
    try:
        from models.quote import (
            QuoteResponse, Material, LaborItem, Timeline, WorkStep, Phase, RiskItem
        )
        print("✅ Models imported successfully\n")
    except ImportError as e:
        print(f"❌ Failed to import models: {e}")
        return False
    
    # Build objects as done in create_quote endpoint
    try:
        # Build timeline
        timeline_data = estimate["timeline"]
        timeline_obj = Timeline(
            estimated_hours=timeline_data.get("estimated_hours", 0),
            estimated_days=timeline_data.get("estimated_days", 1),
            min_days=timeline_data.get("min_days", 1),
            max_days=timeline_data.get("max_days", 1)
        )
        print("✅ Timeline object created")
        
        # Build materials
        materials_list = [
            Material(
                name=m.get("name", ""),
                quantity=m.get("quantity", 0),
                unit=m.get("unit", "unit"),
                unit_price=m.get("unit_price", 0),
                total=m.get("total", 0)
            )
            for m in estimate.get("materials", [])
        ]
        print(f"✅ Materials list created ({len(materials_list)} items)")
        
        # Build labor
        labor_list = [
            LaborItem(
                trade=l.get("trade", ""),
                hours=l.get("hours", 0),
                rate=l.get("rate", 0),
                total=l.get("total", 0)
            )
            for l in estimate.get("labor", [])
        ]
        print(f"✅ Labor list created ({len(labor_list)} items)")
        
        # Build steps
        steps_list = [
            WorkStep(
                order=s.get("order", 0),
                description=s.get("description", ""),
                duration=s.get("duration", "")
            )
            for s in estimate.get("steps", [])
        ]
        print(f"✅ Steps list created ({len(steps_list)} items)")
        
        # Build phases
        phases_list = [
            Phase(
                name=p.get("name", ""),
                description=p.get("description", ""),
                estimated_hours=p.get("estimated_hours", 0)
            )
            for p in advanced_options.get("phases", [])
        ]
        print(f"✅ Phases list created ({len(phases_list)} items)")
        
        # Build risks
        risks_list = [
            RiskItem(
                id=r.get("id", ""),
                description=r.get("description", ""),
                impact=r.get("impact", "medium")
            )
            for r in advanced_options.get("risks", [])
        ]
        print(f"✅ Risks list created ({len(risks_list)} items)")
        
        # Create QuoteResponse
        quote = QuoteResponse(
            id="quote_test_12345",
            status="completed",
            total_cost=estimate["total_cost"],
            timeline=timeline_obj,
            materials=materials_list,
            labor=labor_list,
            steps=steps_list,
            confidence_score=estimate["confidence_score"],
            vision_analysis={"scene": "bathroom"},
            options_applied=estimate.get("options_applied"),
            scope=advanced_options.get("scope"),
            phases=phases_list if phases_list else None,
            risks=risks_list if risks_list else None,
            created_at=datetime.now(timezone.utc)
        )
        print("✅ QuoteResponse created successfully\n")
        
    except Exception as e:
        print(f"❌ Failed to create response objects: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test serialization
    try:
        quote_dict = quote.model_dump()
        print(f"✅ QuoteResponse serialized to dict ({len(quote_dict)} fields)")
        
        quote_json = quote.model_dump_json()
        print(f"✅ QuoteResponse serialized to JSON ({len(quote_json)} bytes)")
        
        # Parse JSON to verify it's valid
        parsed = json.loads(quote_json)
        print(f"✅ JSON is valid and parseable")
        
        # Display sample of data
        print(f"\n📊 Sample Response Data:")
        print(f"   Quote ID: {parsed['id']}")
        print(f"   Status: {parsed['status']}")
        print(f"   Total Cost: ${parsed['total_cost']['amount']:,.2f}")
        print(f"   Materials: {len(parsed['materials'])} items")
        print(f"   Labor: {len(parsed['labor'])} items")
        print(f"   Steps: {len(parsed['steps'])}")
        print(f"   Phases: {len(parsed.get('phases') or [])}")
        print(f"   Risks: {len(parsed.get('risks') or [])}")
        print(f"   Confidence: {parsed['confidence_score'] * 100:.1f}%")
        
    except Exception as e:
        print(f"❌ Serialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED - Quote generation fix is working!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = test_quote_response_validation()
    exit(0 if success else 1)
