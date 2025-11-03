#!/usr/bin/env python3
"""
Test script for advanced options in quote generation.
Validates that quality, contingency, profit, and region parameters work correctly.
"""

import json
from services.estimation_service import EstimationService


def test_advanced_options():
    """Test advanced options calculation"""
    service = EstimationService()
    
    # Mock vision results and reasoning
    vision_results = {
        "detections": [
            {"label": "tile", "confidence": 0.95},
            {"label": "grout", "confidence": 0.90}
        ]
    }
    
    reasoning = {
        "materials_needed": [
            {"name": "tile", "quantity": 100, "unit": "sqft"},
            {"name": "grout", "quantity": 2, "unit": "bag"},
            {"name": "thin_set_mortar", "quantity": 3, "unit": "bag"}
        ],
        "analysis": {
            "labor_hours": 16
        }
    }
    
    print("=" * 60)
    print("Testing Advanced Options")
    print("=" * 60)
    
    # Test 1: Standard quality, no options
    print("\n1. BASELINE (Standard quality, 15% profit, midwest)")
    import asyncio
    result1 = asyncio.run(service.calculate_estimate(
        vision_results,
        reasoning,
        "bathroom"
    ))
    print(f"   Total: ${result1['total_cost']['amount']:,.2f}")
    print(f"   Materials: ${result1['total_cost']['breakdown']['materials']:,.2f}")
    print(f"   Labor: ${result1['total_cost']['breakdown']['labor']:,.2f}")
    print(f"   Profit: ${result1['total_cost']['breakdown']['profit']:,.2f}")
    print(f"   Contingency: ${result1['total_cost']['breakdown']['contingency']:,.2f}")
    
    # Test 2: Premium quality
    print("\n2. PREMIUM QUALITY (1.3x material multiplier)")
    result2 = asyncio.run(service.calculate_estimate(
        vision_results,
        reasoning,
        "bathroom",
        advanced_options={"quality": "premium"}
    ))
    print(f"   Total: ${result2['total_cost']['amount']:,.2f}")
    print(f"   Materials: ${result2['total_cost']['breakdown']['materials']:,.2f} (was ${result1['total_cost']['breakdown']['materials']:,.2f})")
    material_increase = result2['total_cost']['breakdown']['materials'] - result1['total_cost']['breakdown']['materials']
    print(f"   Material increase: ${material_increase:,.2f} (~30% expected)")
    
    # Test 3: Luxury quality
    print("\n3. LUXURY QUALITY (1.8x material multiplier)")
    result3 = asyncio.run(service.calculate_estimate(
        vision_results,
        reasoning,
        "bathroom",
        advanced_options={"quality": "luxury"}
    ))
    print(f"   Total: ${result3['total_cost']['amount']:,.2f}")
    print(f"   Materials: ${result3['total_cost']['breakdown']['materials']:,.2f} (was ${result1['total_cost']['breakdown']['materials']:,.2f})")
    material_increase = result3['total_cost']['breakdown']['materials'] - result1['total_cost']['breakdown']['materials']
    print(f"   Material increase: ${material_increase:,.2f} (~80% expected)")
    
    # Test 4: Contingency
    print("\n4. CONTINGENCY (10%)")
    result4 = asyncio.run(service.calculate_estimate(
        vision_results,
        reasoning,
        "bathroom",
        advanced_options={"contingency_pct": 10}
    ))
    print(f"   Total: ${result4['total_cost']['amount']:,.2f}")
    print(f"   Contingency: ${result4['total_cost']['breakdown']['contingency']:,.2f}")
    subtotal = result4['total_cost']['breakdown']['materials'] + result4['total_cost']['breakdown']['labor']
    expected_contingency = subtotal * 0.10
    print(f"   Expected contingency: ${expected_contingency:,.2f}")
    
    # Test 5: Profit margin
    print("\n5. PROFIT MARGIN (25%)")
    result5 = asyncio.run(service.calculate_estimate(
        vision_results,
        reasoning,
        "bathroom",
        advanced_options={"profit_pct": 25}
    ))
    print(f"   Total: ${result5['total_cost']['amount']:,.2f}")
    print(f"   Profit: ${result5['total_cost']['breakdown']['profit']:,.2f}")
    subtotal = result5['total_cost']['breakdown']['materials'] + result5['total_cost']['breakdown']['labor']
    expected_profit = subtotal * 0.25
    print(f"   Expected profit: ${expected_profit:,.2f}")
    
    # Test 6: Region - West Coast
    print("\n6. REGION - WEST COAST (1.35x labor)")
    result6 = asyncio.run(service.calculate_estimate(
        vision_results,
        reasoning,
        "bathroom",
        advanced_options={"region": "west"}
    ))
    print(f"   Total: ${result6['total_cost']['amount']:,.2f}")
    print(f"   Labor: ${result6['total_cost']['breakdown']['labor']:,.2f} (was ${result1['total_cost']['breakdown']['labor']:,.2f})")
    labor_increase = result6['total_cost']['breakdown']['labor'] - result1['total_cost']['breakdown']['labor']
    print(f"   Labor increase: ${labor_increase:,.2f} (~35% expected)")
    
    # Test 7: Region - South
    print("\n7. REGION - SOUTH (0.85x labor)")
    result7 = asyncio.run(service.calculate_estimate(
        vision_results,
        reasoning,
        "bathroom",
        advanced_options={"region": "south"}
    ))
    print(f"   Total: ${result7['total_cost']['amount']:,.2f}")
    print(f"   Labor: ${result7['total_cost']['breakdown']['labor']:,.2f} (was ${result1['total_cost']['breakdown']['labor']:,.2f})")
    labor_decrease = result1['total_cost']['breakdown']['labor'] - result7['total_cost']['breakdown']['labor']
    print(f"   Labor decrease: ${labor_decrease:,.2f} (~15% expected)")
    
    # Test 8: Combined (luxury + high margins + west coast)
    print("\n8. COMBINED (luxury + 30% profit + 20% contingency + west)")
    result8 = asyncio.run(service.calculate_estimate(
        vision_results,
        reasoning,
        "bathroom",
        advanced_options={
            "quality": "luxury",
            "profit_pct": 30,
            "contingency_pct": 20,
            "region": "west"
        }
    ))
    print(f"   Total: ${result8['total_cost']['amount']:,.2f} (was ${result1['total_cost']['amount']:,.2f})")
    print(f"   Materials: ${result8['total_cost']['breakdown']['materials']:,.2f}")
    print(f"   Labor: ${result8['total_cost']['breakdown']['labor']:,.2f}")
    print(f"   Profit (30%): ${result8['total_cost']['breakdown']['profit']:,.2f}")
    print(f"   Contingency (20%): ${result8['total_cost']['breakdown']['contingency']:,.2f}")
    increase_pct = ((result8['total_cost']['amount'] - result1['total_cost']['amount']) / result1['total_cost']['amount']) * 100
    print(f"   Total increase: {increase_pct:.1f}%")
    
    # Verify options_applied is returned
    print("\n9. OPTIONS TRACKING")
    print(f"   Options applied: {json.dumps(result8['options_applied'], indent=4)}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_advanced_options()
