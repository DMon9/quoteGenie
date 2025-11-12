import requests

pages = [
    'index.html',
    'login.html', 
    'signup.html',
    'dashboard.html',
    'dashboard-new.html',
    'about.html',
    'pricing.html'
]

print("Testing page accessibility on production:\n")
for page in pages:
    url = f"https://estimategenie.net/{page}"
    try:
        r = requests.get(url, timeout=5)
        status = "PASS" if r.status_code == 200 else "FAIL"
        print(f"[{status}] {page}: {r.status_code}")
    except Exception as e:
        print(f"[ERROR] {page}: {e}")
