"""
Run all EstimateGenie test suites in sequence
"""
import subprocess
import sys
import time

def run_test(script_name, description):
    """Run a test script and report results"""
    print("\n" + "="*70)
    print(f"🧪 {description}")
    print("="*70)
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        print(f"⏱️ {description} - TIMEOUT")
        return False
    
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("🚀 ESTIMATEGENIE - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("test_auth_advanced.py", "Authentication Security Tests"),
        ("test_enhancements.py", "Password & Profile Enhancements"),
        ("test_quote_generation.py", "Quote Generation End-to-End"),
        ("test_stripe_payment.py", "Stripe Payment Integration"),
        ("test_dashboard.py", "Dashboard Functionality"),
        ("test_mobile_responsiveness.py", "Mobile Responsiveness"),
    ]
    
    results = []
    
    for script, description in tests:
        passed = run_test(script, description)
        results.append((description, passed))
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for description, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {status:12} - {description}")
    
    print()
    print(f"   Total: {passed_count}/{total_count} test suites passed")
    print(f"   Success Rate: {(passed_count/total_count)*100:.1f}%")
    
    print("\n" + "="*70)
    
    if passed_count == total_count:
        print("🎉 ALL TESTS PASSED - SYSTEM READY")
    elif passed_count >= total_count * 0.8:
        print("✅ MOSTLY PASSING - MINOR ISSUES TO ADDRESS")
    else:
        print("⚠️ MULTIPLE FAILURES - REVIEW NEEDED")
    
    print("="*70)
    print(f"\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nFor detailed results, see TESTING_SUMMARY.txt")
    print()
    
    return passed_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
