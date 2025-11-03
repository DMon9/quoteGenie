#!/usr/bin/env python3
"""
Test script to verify environment variables in the API
"""
import httpx
import json

def test_env_vars():
    """Test if we can get environment variable info from the API"""
    try:
        # Test the backend directly
        response = httpx.get("https://quotegenie-api.fly.dev/debug/env", timeout=10.0)
        if response.status_code == 200:
            print("✅ Environment variables accessible:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Failed to get env vars: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error testing env vars: {e}")

if __name__ == "__main__":
    test_env_vars()