"""
Comprehensive Frontend Pages Test Suite
Tests all frontend pages for loading and basic functionality
"""
import requests
import re
import time

FRONTEND_URL = "https://estimategenie.net"

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests = []
    
    def add_pass(self, test_name, details=""):
        self.passed += 1
        self.tests.append({"name": test_name, "status": "PASS", "details": details})
        print(f"[PASS] {test_name}")
        if details:
            print(f"       {details}")
    
    def add_fail(self, test_name, details=""):
        self.failed += 1
        self.tests.append({"name": test_name, "status": "FAIL", "details": details})
        print(f"[FAIL] {test_name}")
        if details:
            print(f"       {details}")
    
    def add_warning(self, test_name, details=""):
        self.warnings += 1
        self.tests.append({"name": test_name, "status": "WARN", "details": details})
        print(f"[WARN] {test_name}")
        if details:
            print(f"       {details}")
    
    def summary(self):
        total = self.passed + self.failed
        pct = (self.passed / total * 100) if total > 0 else 0
        print(f"\n{'='*70}")
        print(f"SUMMARY: {self.passed}/{total} tests passed ({pct:.1f}%)")
        if self.warnings > 0:
            print(f"WARNINGS: {self.warnings}")
        print(f"{'='*70}\n")
        return self.passed == total

def test_page_loading(results):
    """Test that all main pages load correctly"""
    print("\n--- Testing Page Loading ---")
    
    pages = [
        ("index.html", "Homepage"),
        ("features.html", "Features"),
        ("pricing.html", "Pricing"),
        ("about.html", "About"),
        ("contact.html", "Contact"),
        ("blog.html", "Blog"),
        ("case-studies.html", "Case Studies"),
        ("docs.html", "Documentation"),
        ("signup.html", "Signup"),
        ("login.html", "Login"),
        ("dashboard.html", "Dashboard"),
        ("checkout.html", "Checkout"),
    ]
    
    for page, name in pages:
        try:
            response = requests.get(f"{FRONTEND_URL}/{page}", timeout=10)
            
            if response.status_code == 200:
                size_kb = len(response.content) / 1024
                results.add_pass(f"{name} page loads", f"{size_kb:.1f}KB")
            elif response.status_code == 404:
                results.add_fail(f"{name} page", "404 Not Found")
            else:
                results.add_fail(f"{name} page", f"Status: {response.status_code}")
        
        except Exception as e:
            results.add_fail(f"{name} page", f"Error: {str(e)}")

def test_page_metadata(results):
    """Test page titles and meta tags"""
    print("\n--- Testing Page Metadata ---")
    
    response = requests.get(f"{FRONTEND_URL}/index.html")
    
    if response.status_code == 200:
        html = response.text
        
        # Check for title
        if "<title>" in html:
            results.add_pass("Homepage has title tag")
        else:
            results.add_fail("Homepage title", "Missing title tag")
        
        # Check for viewport
        if 'name="viewport"' in html:
            results.add_pass("Homepage has viewport meta")
        else:
            results.add_fail("Homepage viewport", "Missing viewport meta")
        
        # Check for charset
        if 'charset=' in html or 'charset =' in html:
            results.add_pass("Homepage has charset")
        else:
            results.add_fail("Homepage charset", "Missing charset")

def test_static_assets(results):
    """Test loading of CSS and JS files"""
    print("\n--- Testing Static Assets ---")
    
    # Test CSS
    css_urls = [
        "/assets/css/main.css",
    ]
    
    for css_url in css_urls:
        try:
            response = requests.get(f"{FRONTEND_URL}{css_url}", timeout=10)
            if response.status_code == 200:
                results.add_pass(f"CSS: {css_url}")
            elif response.status_code == 404:
                results.add_warning(f"CSS: {css_url}", "404 - May be using CDN")
            else:
                results.add_warning(f"CSS: {css_url}", f"Status: {response.status_code}")
        except:
            results.add_warning(f"CSS: {css_url}", "Error loading")
    
    # Test if Tailwind CDN is referenced
    response = requests.get(f"{FRONTEND_URL}/index.html")
    if "tailwindcss.com" in response.text:
        results.add_pass("Tailwind CSS CDN referenced")

def test_form_pages(results):
    """Test forms on signup and contact pages"""
    print("\n--- Testing Form Pages ---")
    
    # Test signup page
    response = requests.get(f"{FRONTEND_URL}/signup.html")
    
    if response.status_code == 200:
        html = response.text
        
        # Check for form elements
        checks = {
            "Email input": 'type="email"' in html,
            "Password input": 'type="password"' in html,
            "Submit button": 'type="submit"' in html or 'button' in html.lower(),
        }
        
        passed = sum(checks.values())
        total = len(checks)
        
        if passed == total:
            results.add_pass("Signup form elements", f"{passed}/{total} elements found")
        else:
            results.add_warning("Signup form elements", f"Only {passed}/{total} elements found")
    
    # Test login page
    response = requests.get(f"{FRONTEND_URL}/login.html")
    
    if response.status_code == 200:
        html = response.text
        
        if 'type="email"' in html and 'type="password"' in html:
            results.add_pass("Login form elements")
        else:
            results.add_warning("Login form elements", "Missing expected inputs")
    
    # Test contact page
    response = requests.get(f"{FRONTEND_URL}/contact.html")
    
    if response.status_code == 200:
        html = response.text
        
        if 'type="email"' in html or 'email' in html.lower():
            results.add_pass("Contact form present")
        else:
            results.add_warning("Contact form", "May not have email input")

def test_navigation(results):
    """Test navigation links"""
    print("\n--- Testing Navigation ---")
    
    response = requests.get(f"{FRONTEND_URL}/index.html")
    
    if response.status_code == 200:
        html = response.text
        
        # Check for navigation links
        nav_links = [
            ("Features", "features" in html.lower()),
            ("Pricing", "pricing" in html.lower()),
            ("Login", "login" in html.lower()),
            ("Sign up", "signup" in html.lower() or "sign-up" in html.lower() or "sign up" in html.lower()),
        ]
        
        found = sum(1 for _, exists in nav_links if exists)
        total = len(nav_links)
        
        if found >= total - 1:  # Allow one missing
            results.add_pass("Navigation links present", f"{found}/{total} found")
        else:
            results.add_warning("Navigation links", f"Only {found}/{total} found")

def test_responsive_design(results):
    """Test responsive design indicators"""
    print("\n--- Testing Responsive Design ---")
    
    response = requests.get(f"{FRONTEND_URL}/index.html")
    
    if response.status_code == 200:
        html = response.text
        
        # Check for responsive classes (Tailwind)
        responsive_indicators = {
            "Small breakpoint (sm:)": "sm:" in html,
            "Medium breakpoint (md:)": "md:" in html,
            "Large breakpoint (lg:)": "lg:" in html,
            "Flex layout": "flex" in html,
            "Grid layout": "grid" in html,
        }
        
        passed = sum(responsive_indicators.values())
        total = len(responsive_indicators)
        
        if passed >= 3:
            results.add_pass("Responsive design indicators", f"{passed}/{total} found")
        else:
            results.add_warning("Responsive design", f"Only {passed}/{total} indicators found")

def test_accessibility(results):
    """Test basic accessibility features"""
    print("\n--- Testing Accessibility ---")
    
    response = requests.get(f"{FRONTEND_URL}/index.html")
    
    if response.status_code == 200:
        html = response.text
        
        a11y_features = {
            "Alt attributes": 'alt="' in html,
            "ARIA labels": "aria-label" in html,
            "Lang attribute": 'lang=' in html,
            "Semantic HTML": "<nav" in html or "<header" in html or "<main" in html,
        }
        
        passed = sum(a11y_features.values())
        total = len(a11y_features)
        
        if passed >= 3:
            results.add_pass("Accessibility features", f"{passed}/{total} found")
        else:
            results.add_warning("Accessibility", f"Only {passed}/{total} features found")

def test_ssl_security(results):
    """Test SSL and security headers"""
    print("\n--- Testing SSL & Security ---")
    
    # Test HTTPS
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        
        if response.url.startswith("https://"):
            results.add_pass("HTTPS enabled")
        else:
            results.add_fail("HTTPS", "Site not using HTTPS")
        
        # Check security headers
        security_headers = [
            "strict-transport-security",
            "x-content-type-options",
            "x-frame-options",
        ]
        
        found_headers = sum(1 for h in security_headers if h in response.headers)
        
        if found_headers > 0:
            results.add_pass("Security headers", f"{found_headers}/{len(security_headers)} present")
        else:
            results.add_warning("Security headers", "None found (may be handled by CDN)")
    
    except Exception as e:
        results.add_fail("SSL test", str(e))

def test_performance(results):
    """Test basic performance metrics"""
    print("\n--- Testing Performance ---")
    
    start = time.time()
    response = requests.get(f"{FRONTEND_URL}/index.html", timeout=10)
    load_time = time.time() - start
    
    if response.status_code == 200:
        if load_time < 2.0:
            results.add_pass("Page load time", f"{load_time:.2f}s (excellent)")
        elif load_time < 5.0:
            results.add_pass("Page load time", f"{load_time:.2f}s (good)")
        else:
            results.add_warning("Page load time", f"{load_time:.2f}s (slow)")
        
        # Check page size
        size_kb = len(response.content) / 1024
        
        if size_kb < 500:
            results.add_pass("Page size", f"{size_kb:.1f}KB (optimized)")
        elif size_kb < 1000:
            results.add_pass("Page size", f"{size_kb:.1f}KB (acceptable)")
        else:
            results.add_warning("Page size", f"{size_kb:.1f}KB (large)")

def main():
    print("="*70)
    print("COMPREHENSIVE FRONTEND PAGES TEST")
    print("="*70)
    print(f"Testing: {FRONTEND_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = TestResults()
    
    # Run all tests
    test_page_loading(results)
    test_page_metadata(results)
    test_static_assets(results)
    test_form_pages(results)
    test_navigation(results)
    test_responsive_design(results)
    test_accessibility(results)
    test_ssl_security(results)
    test_performance(results)
    
    # Print summary
    success = results.summary()
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
