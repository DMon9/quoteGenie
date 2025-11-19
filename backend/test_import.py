#!/usr/bin/env python3
"""Simple import test to verify syntax is correct"""

try:
    print("Importing models...")
    from models.quote import QuoteResponse, Material, LaborItem, Timeline, WorkStep, Phase, RiskItem
    print("✅ Quote models imported successfully")
    
    print("\nImporting app...")
    import app
    print("✅ App imported successfully")
    
    print("\nAll imports successful!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
