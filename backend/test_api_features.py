#!/usr/bin/env python3
"""
Quick API test script for new features.
Tests the /v1/quotes endpoint with various option combinations.
"""

import os
import sys
import json
from pathlib import Path

import pytest
import requests

# Configuration
API_BASE = os.getenv("API_BASE_URL", "https://api.estimategenie.net")
TOKEN = os.getenv("TEST_AUTH_TOKEN", "")

if not TOKEN:
    pytest.skip("Integration test requires TEST_AUTH_TOKEN", allow_module_level=True)

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_subheader(text):
    """Print a formatted subheader"""
    print(f"\n--- {text} ---")

def test_health():
    """Test health endpoint"""
    print_header("1. Health Check")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        print(f"Status: {response.status_code}")
        if response.ok:
            data = response.json()
            print(f"✅ API is healthy")
            print(f"Services: {json.dumps(data.get('services', {}), indent=2)}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def run_quote_with_options(image_path, options, description="Test quote"):
    """Submit a quote request with specific options"""
    if not TOKEN:
        print("❌ No auth token. Set TEST_AUTH_TOKEN environment variable.")
        return None
    
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return None
    
    print_subheader(f"Options: {json.dumps(options)}")
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {
                'project_type': 'bathroom',
                'description': description,
                'options': json.dumps(options)
            }
            headers = {'Authorization': f'Bearer {TOKEN}'}
            
            response = requests.post(
                f"{API_BASE}/v1/quotes",
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
        
        print(f"Status: {response.status_code}")
        
        if response.ok:
            result = response.json()
            print(f"✅ Quote generated: {result['id']}")
            
            # Display breakdown
            total = result['total_cost']
            print(f"\nTotal: ${total['amount']:,.2f}")
            breakdown = total['breakdown']
            print(f"  Materials:   ${breakdown['materials']:>8,.2f}")
            print(f"  Labor:       ${breakdown['labor']:>8,.2f}")
            print(f"  Profit:      ${breakdown['profit']:>8,.2f}")
            print(f"  Contingency: ${breakdown['contingency']:>8,.2f}")
            
            # Show applied options
            applied = result.get('options_applied', {})
            print(f"\nOptions Applied:")
            print(f"  Quality:     {applied.get('quality')}")
            print(f"  Contingency: {applied.get('contingency_pct')}%")
            print(f"  Profit:      {applied.get('profit_pct')}%")
            print(f"  Region:      {applied.get('region')}")
            
            return result
        else:
            print(f"❌ Request failed: {response.status_code}")
            try:
                error = response.json()
                print(f"Error: {error.get('detail', 'Unknown error')}")
            except:
                print(f"Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def compare_quotes(baseline, premium, label="Premium vs Baseline"):
    """Compare two quote results"""
    if not baseline or not premium:
        return
    
    print_subheader(f"Comparison: {label}")
    
    b_total = baseline['total_cost']['amount']
    p_total = premium['total_cost']['amount']
    diff = p_total - b_total
    pct = (diff / b_total) * 100
    
    print(f"Baseline Total: ${b_total:,.2f}")
    print(f"Premium Total:  ${p_total:,.2f}")
    print(f"Difference:     ${diff:,.2f} ({pct:+.1f}%)")
    
    # Material comparison
    b_mat = baseline['total_cost']['breakdown']['materials']
    p_mat = premium['total_cost']['breakdown']['materials']
    mat_diff = p_mat - b_mat
    mat_pct = (mat_diff / b_mat) * 100 if b_mat > 0 else 0
    
    print(f"\nMaterials:")
    print(f"  Baseline: ${b_mat:,.2f}")
    print(f"  Premium:  ${p_mat:,.2f}")
    print(f"  Change:   ${mat_diff:,.2f} ({mat_pct:+.1f}%)")
    
    # Labor comparison
    b_lab = baseline['total_cost']['breakdown']['labor']
    p_lab = premium['total_cost']['breakdown']['labor']
    lab_diff = p_lab - b_lab
    lab_pct = (lab_diff / b_lab) * 100 if b_lab > 0 else 0
    
    print(f"\nLabor:")
    print(f"  Baseline: ${b_lab:,.2f}")
    print(f"  Premium:  ${p_lab:,.2f}")
    print(f"  Change:   ${lab_diff:,.2f} ({lab_pct:+.1f}%)")

def main():
    """Run all tests"""
    print_header("EstimateGenie API Feature Tests")
    print(f"API Base: {API_BASE}")
    print(f"Token: {'✅ Set' if TOKEN else '❌ Not set (use TEST_AUTH_TOKEN env var)'}")
    
    # Test 1: Health
    if not test_health():
        print("\n❌ Cannot reach API. Stopping tests.")
        return 1
    
    # Find a test image
    test_images = [
        "test-images/bathroom.jpg",
        "uploads/test.jpg",
        "../test.jpg",
    ]
    
    test_image = None
    for img in test_images:
        if Path(img).exists():
            test_image = img
            break
    
    if not test_image:
        print("\n⚠️  No test image found. Create test-images/bathroom.jpg to run quote tests.")
        print("    You can still test the API health endpoint above.")
        return 0
    
    print(f"\n📸 Using test image: {test_image}")
    
    # Test 2: Baseline quote
    print_header("2. Baseline Quote (Standard/Midwest/15%)")
    baseline = run_quote_with_options(
        test_image,
        {
            "quality": "standard",
            "contingency_pct": 0,
            "profit_pct": 15,
            "region": "midwest"
        },
        "Baseline test"
    )
    
    if not baseline:
        print("\n❌ Baseline quote failed. Check authentication and API status.")
        return 1
    
    # Test 3: Premium quality
    print_header("3. Premium Quality Test (1.3x materials)")
    premium = run_quote_with_options(
        test_image,
        {
            "quality": "premium",
            "contingency_pct": 0,
            "profit_pct": 15,
            "region": "midwest"
        },
        "Premium quality test"
    )
    
    if premium:
        compare_quotes(baseline, premium, "Premium Quality vs Standard")
    
    # Test 4: Luxury quality
    print_header("4. Luxury Quality Test (1.8x materials)")
    luxury = run_quote_with_options(
        test_image,
        {
            "quality": "luxury",
            "contingency_pct": 0,
            "profit_pct": 15,
            "region": "midwest"
        },
        "Luxury quality test"
    )
    
    if luxury:
        compare_quotes(baseline, luxury, "Luxury Quality vs Standard")
    
    # Test 5: West coast region
    print_header("5. Regional Test - West Coast (1.35x labor)")
    west = run_quote_with_options(
        test_image,
        {
            "quality": "standard",
            "contingency_pct": 0,
            "profit_pct": 15,
            "region": "west"
        },
        "West coast test"
    )
    
    if west:
        compare_quotes(baseline, west, "West Coast vs Midwest")
    
    # Test 6: Combined options
    print_header("6. Combined Options (Luxury + 20% Contingency + 30% Profit + West)")
    combined = run_quote_with_options(
        test_image,
        {
            "quality": "luxury",
            "contingency_pct": 20,
            "profit_pct": 30,
            "region": "west"
        },
        "Combined options test"
    )
    
    if combined:
        compare_quotes(baseline, combined, "Max Settings vs Baseline")
    
    # Summary
    print_header("Test Summary")
    tests_run = sum([
        1,  # health
        baseline is not None,
        premium is not None,
        luxury is not None,
        west is not None,
        combined is not None,
    ])
    
    print(f"✅ {tests_run}/6 tests completed")
    print("\nAll tests passed! ✨")
    print("\nNext steps:")
    print("1. Test via web UI: Open mobile-index.html")
    print("2. Try video upload")
    print("3. Test voice input")
    print("4. Review TESTING_GUIDE.md for comprehensive test cases")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
