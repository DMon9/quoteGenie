"""Quick test to identify which email validation is failing"""
import requests
import time

BASE_URL = "https://quotegenie-api.fly.dev"

invalid_emails = [
    ("notanemail", "No @ symbol"),
    ("@example.com", "Missing local part"),
    ("user@", "Missing domain"),
    ("user @example.com", "Space in email"),
    ("user@.com", "Domain starts with dot"),
    ("user..name@example.com", "Double dots"),
]

print("Testing individual email formats:\n")

for email, reason in invalid_emails:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": "ValidPass123", "name": "Test"}
    )
    
    status = "REJECTED" if response.status_code == 400 else "ACCEPTED"
    print(f"[{status}] '{email}' - {reason}")
    if status == "ACCEPTED":
        print(f"         Response: {response.status_code} - {response.text[:100]}")

print("\nTest complete")
