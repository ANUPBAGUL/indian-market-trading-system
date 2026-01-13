"""
Test Runner - Executes all unit and integration tests for the trading system.

Runs comprehensive tests to verify system functionality including:
- Signal Quality KPI
- Indian Market Integration
- Complete System Workflows
- Error Handling and Robustness
"""

import unittest
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_all_tests():
    """Run all tests and generate a comprehensive report."""
    
    print("=" * 60)
    print("TRADING SYSTEM TEST SUITE")
    print("=" * 60)
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    print(f"\\nDiscovered {suite.countTestCases()} test cases")
    print("\\nRunning tests...\\n")
    
    result = runner.run(suite)
    
    # Generate summary report
    print("\\n" + "=" * 60)
    print("TEST SUMMARY REPORT")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    passed = total_tests - failures - errors - skipped
    
    print(f"Total Tests Run: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failures}")
    print(f"Errors: {errors}")
    print(f"Skipped: {skipped}")
    
    success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Detailed failure/error reporting
    if result.failures:
        print(f"\\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            error_msg = traceback.split('\\n')[-2] if '\\n' in traceback else traceback
            print(f"- {test}: {error_msg}")
    
    if hasattr(result, 'skipped') and result.skipped:
        print(f"\\nSKIPPED ({len(result.skipped)}):")
        for test, reason in result.skipped:
            print(f"- {test}: {reason}")
    
    # System health assessment
    print(f"\\nSYSTEM HEALTH ASSESSMENT:")
    if success_rate >= 90:
        print("[+] EXCELLENT - System is highly reliable")
    elif success_rate >= 75:
        print("[+] GOOD - System is mostly reliable")
    elif success_rate >= 50:
        print("[!] FAIR - System has some issues")
    else:
        print("[-] POOR - System needs significant fixes")
    
    # Component-specific insights
    print(f"\\nCOMPONENT STATUS:")
    
    # Check core functionality
    core_tests = [t for t in result.failures + result.errors if 'integration' in str(t[0]).lower()]
    if not core_tests:
        print("[+] Core System: All integration tests passed")
    else:
        print(f"[-] Core System: {len(core_tests)} integration issues")
    
    # Check Signal Quality KPI
    signal_tests = [t for t in result.failures + result.errors if 'signal_quality' in str(t[0]).lower()]
    if not signal_tests:
        print("[+] Signal Quality KPI: Working correctly")
    else:
        print(f"[-] Signal Quality KPI: {len(signal_tests)} issues")
    
    # Check Indian Market
    indian_tests = [t for t in result.failures + result.errors if 'indian' in str(t[0]).lower()]
    if not indian_tests:
        print("[+] Indian Market: Integration successful")
    else:
        print(f"[-] Indian Market: {len(indian_tests)} issues")
    
    print(f"\\nRECOMMENDATIONS:")
    if success_rate >= 90:
        print("- System is ready for production use")
        print("- Continue with regular monitoring")
    elif success_rate >= 75:
        print("- Address failing tests before production")
        print("- System core functionality is solid")
    else:
        print("- Significant debugging required")
        print("- Review failed components before proceeding")
    
    print("\\n" + "=" * 60)
    
    return result.wasSuccessful()

def run_specific_test_suite(test_name):
    """Run a specific test suite."""
    
    test_files = {
        'signal': 'test_signal_quality.py',
        'integration': 'test_integration.py',
        'all': None  # Run all tests
    }
    
    if test_name not in test_files:
        print(f"Unknown test suite: {test_name}")
        print(f"Available options: {list(test_files.keys())}")
        return False
    
    if test_name == 'all':
        return run_all_tests()
    
    # Run specific test file
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_files[test_name].replace('.py', ''))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    # Check command line arguments
    if len(sys.argv) > 1:
        test_suite = sys.argv[1].lower()
        success = run_specific_test_suite(test_suite)
    else:
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)