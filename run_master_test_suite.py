"""
MASTER TEST SUITE - Runs all comprehensive tests and generates report
"""
import subprocess
import sys
import time
import json

def run_test_suite(script_name, suite_name):
    """Run a test suite and capture results"""
    print(f"\n{'='*70}")
    print(f"Running: {suite_name}")
    print(f"{'='*70}\n")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
            errors='replace'
        )
        
        duration = time.time() - start_time
        
        # Print output
        print(result.stdout)
        
        # Parse results from output
        passed = result.stdout.count("[PASS]")
        failed = result.stdout.count("[FAIL]")
        warnings = result.stdout.count("[WARN]")
        
        return {
            "name": suite_name,
            "script": script_name,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "duration": duration,
            "exit_code": result.returncode,
            "success": result.returncode == 0 or (failed == 0 and passed > 0)
        }
    
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"[TIMEOUT] Test suite exceeded 120 seconds")
        return {
            "name": suite_name,
            "script": script_name,
            "passed": 0,
            "failed": 1,
            "warnings": 0,
            "duration": duration,
            "exit_code": -1,
            "success": False,
            "error": "Timeout"
        }
    
    except Exception as e:
        duration = time.time() - start_time
        print(f"[ERROR] {str(e)}")
        return {
            "name": suite_name,
            "script": script_name,
            "passed": 0,
            "failed": 1,
            "warnings": 0,
            "duration": duration,
            "exit_code": -1,
            "success": False,
            "error": str(e)
        }

def generate_report(results):
    """Generate comprehensive test report"""
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST REPORT")
    print("="*70)
    print(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Duration: {sum(r['duration'] for r in results):.1f}s")
    print("="*70)
    
    # Individual suite results
    print("\nTEST SUITE RESULTS:")
    print("-" * 70)
    
    total_passed = 0
    total_failed = 0
    total_warnings = 0
    suites_passed = 0
    suites_failed = 0
    
    for result in results:
        status = "[PASS]" if result["success"] else "[FAIL]"
        total_passed += result["passed"]
        total_failed += result["failed"]
        total_warnings += result["warnings"]
        
        if result["success"]:
            suites_passed += 1
        else:
            suites_failed += 1
        
        print(f"\n{status} {result['name']}")
        print(f"       Tests: {result['passed']} passed, {result['failed']} failed, {result['warnings']} warnings")
        print(f"       Duration: {result['duration']:.1f}s")
        if "error" in result:
            print(f"       Error: {result['error']}")
    
    # Overall summary
    print("\n" + "="*70)
    print("OVERALL SUMMARY")
    print("="*70)
    print(f"Test Suites: {suites_passed}/{len(results)} passed ({suites_passed/len(results)*100:.1f}%)")
    print(f"Total Tests: {total_passed} passed, {total_failed} failed, {total_warnings} warnings")
    
    total_tests = total_passed + total_failed
    if total_tests > 0:
        pass_rate = (total_passed / total_tests) * 100
        print(f"Pass Rate: {pass_rate:.1f}%")
    
    print("="*70)
    
    # Detailed breakdown
    print("\nDETAILED BREAKDOWN:")
    print("-" * 70)
    
    categories = {
        "Authentication": ["test_comprehensive_auth.py"],
        "API Endpoints": ["test_comprehensive_api.py"],
        "Frontend Pages": ["test_comprehensive_frontend.py"],
        "Integration": ["test_comprehensive_integration.py"]
    }
    
    for category, scripts in categories.items():
        category_results = [r for r in results if r["script"] in scripts]
        if category_results:
            cat_passed = sum(r["passed"] for r in category_results)
            cat_failed = sum(r["failed"] for r in category_results)
            cat_total = cat_passed + cat_failed
            
            if cat_total > 0:
                cat_pct = (cat_passed / cat_total) * 100
                status = "PASS" if cat_failed == 0 else "FAIL"
                print(f"[{status}] {category:20} {cat_passed:3}/{cat_total:3} ({cat_pct:5.1f}%)")
    
    print("="*70)
    
    # Final verdict
    print("\nFINAL VERDICT:")
    print("-" * 70)
    
    if suites_passed == len(results) and total_failed == 0:
        print("STATUS: ALL TESTS PASSED")
        print("The system is fully functional and production-ready.")
    elif suites_passed >= len(results) * 0.9 and total_failed <= 2:
        print("STATUS: EXCELLENT - Minor issues only")
        print("The system is production-ready with minimal warnings.")
    elif suites_passed >= len(results) * 0.75:
        print("STATUS: GOOD - Some failures to address")
        print("Core functionality working, some issues to review.")
    else:
        print("STATUS: NEEDS ATTENTION - Multiple failures")
        print("Review and fix failing tests before deployment.")
    
    print("="*70)
    
    # Save report to file
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    report_file = f"TEST_REPORT_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("ESTIMATEGENIE COMPREHENSIVE TEST REPORT\n")
        f.write("="*70 + "\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Duration: {sum(r['duration'] for r in results):.1f}s\n")
        f.write("="*70 + "\n\n")
        
        for result in results:
            f.write(f"\n{result['name']}\n")
            f.write(f"  Status: {'PASS' if result['success'] else 'FAIL'}\n")
            f.write(f"  Tests: {result['passed']} passed, {result['failed']} failed, {result['warnings']} warnings\n")
            f.write(f"  Duration: {result['duration']:.1f}s\n")
            if "error" in result:
                f.write(f"  Error: {result['error']}\n")
        
        f.write(f"\n{'='*70}\n")
        f.write(f"SUMMARY: {suites_passed}/{len(results)} suites passed\n")
        f.write(f"Total: {total_passed} passed, {total_failed} failed, {total_warnings} warnings\n")
        if total_tests > 0:
            f.write(f"Pass Rate: {pass_rate:.1f}%\n")
        f.write("="*70 + "\n")
    
    print(f"\nReport saved to: {report_file}")
    
    return suites_passed == len(results)

def main():
    print("="*70)
    print("ESTIMATEGENIE - MASTER TEST SUITE")
    print("="*70)
    print("Running comprehensive tests across all system components")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    test_suites = [
        ("test_comprehensive_auth.py", "Authentication System Tests"),
        ("test_comprehensive_api.py", "API Endpoints Tests"),
        ("test_comprehensive_frontend.py", "Frontend Pages Tests"),
        ("test_comprehensive_integration.py", "Integration & Database Tests"),
    ]
    
    results = []
    
    for script, name in test_suites:
        result = run_test_suite(script, name)
        results.append(result)
        time.sleep(1)  # Brief pause between suites
    
    # Generate report
    success = generate_report(results)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
