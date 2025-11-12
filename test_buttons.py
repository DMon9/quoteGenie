import requests

url = "https://estimategenie.net"

print("Testing homepage JavaScript loading...\n")

try:
    r = requests.get(url, timeout=10)
    html = r.text.lower()
    
    print(f"[Status]: {r.status_code}")
    print(f"\n[JavaScript Files Check]:")
    print(f"  - cta-buttons.js referenced: {'cta-buttons.js' in html}")
    print(f"  - api-config.js referenced: {'api-config.js' in html}")
    print(f"  - nav.js referenced: {'nav.js' in html}")
    
    print(f"\n[Button Detection]:")
    print(f"  - 'Try Free Now' button: {'try free now' in html}")
    print(f"  - 'Watch Demo' button: {'watch demo' in html}")
    print(f"  - 'Log In' button: {'log in' in html}")
    print(f"  - 'Start Free Trial' button: {'start free trial' in html}")
    
    # Check if JS files are accessible
    js_files = [
        'assets/js/cta-buttons.js',
        'assets/js/api-config.js',
        'assets/js/nav.js'
    ]
    
    print(f"\n[JavaScript File Accessibility]:")
    for js_file in js_files:
        js_url = f"{url}/{js_file}"
        js_response = requests.get(js_url, timeout=5)
        status = "PASS" if js_response.status_code == 200 else "FAIL"
        print(f"  [{status}] {js_file}: {js_response.status_code}")
    
    print("\n[SUCCESS] Homepage loaded successfully!")
    
except Exception as e:
    print(f"[ERROR] {e}")
