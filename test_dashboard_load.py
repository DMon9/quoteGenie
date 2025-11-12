import requests

url = "https://estimategenie.net/dashboard-new"
print(f"Testing: {url}")

try:
    r = requests.get(url, timeout=10)
    print(f"\n[Status Code]: {r.status_code}")
    print(f"[Content-Length]: {len(r.content)} bytes")
    print(f"[Content-Type]: {r.headers.get('content-type')}")
    
    # Check for key content
    html = r.text.lower()
    print(f"\n[Contains 'dashboard']: {'dashboard' in html}")
    print(f"[Contains '<title>']: {'<title>' in html}")
    print(f"[Contains 'script']: {'<script' in html}")
    
    if r.status_code == 200:
        print("\n[SUCCESS] Dashboard page loaded successfully!")
    else:
        print(f"\n[WARNING] Unexpected status code: {r.status_code}")
        
except Exception as e:
    print(f"\n[ERROR] Failed to load dashboard: {e}")
