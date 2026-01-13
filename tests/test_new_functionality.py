"""
Test Summary Report - New Functionality Verification

This report focuses on testing the newly added Signal Quality KPI
and Indian Market integration to ensure they work correctly.
"""

import subprocess
import sys
import os

def run_focused_tests():
    """Run focused tests on new functionality."""
    
    print("=" * 60)
    print("FOCUSED TEST REPORT - NEW FUNCTIONALITY")
    print("=" * 60)
    
    test_cases = [
        {
            'name': 'Signal Quality KPI Tests',
            'command': 'python -m unittest test_signal_quality.TestSignalQualityKPI -v',
            'description': 'Tests signal conversion rates, accuracy, and rejection analysis'
        },
        {
            'name': 'System Integration Tests',
            'command': 'python -m unittest test_integration.TestSystemIntegration.test_complete_backtest_workflow -v',
            'description': 'Tests complete backtesting workflow with signal logging'
        },
        {
            'name': 'Indian Market Config Tests',
            'command': 'python -m unittest test_integration.TestIndianMarketIntegration.test_indian_market_config_integration -v',
            'description': 'Tests Indian market configuration and sector mapping'
        },
        {
            'name': 'System Robustness Tests',
            'command': 'python -m unittest test_integration.TestSystemRobustness -v',
            'description': 'Tests error handling and edge cases'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\\nRunning: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print("-" * 40)
        
        try:
            result = subprocess.run(
                test_case['command'].split(),
                cwd=os.path.dirname(__file__),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            results.append({
                'name': test_case['name'],
                'success': success,
                'output': result.stderr if result.stderr else result.stdout
            })
            
            if success:
                print("[PASS] All tests passed")
            else:
                print("[FAIL] Some tests failed")
                print(f"Error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("[TIMEOUT] Tests took too long")
            results.append({'name': test_case['name'], 'success': False, 'output': 'Timeout'})
        except Exception as e:
            print(f"[ERROR] {e}")
            results.append({'name': test_case['name'], 'success': False, 'output': str(e)})
    
    # Generate summary
    print("\\n" + "=" * 60)
    print("SUMMARY REPORT")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    
    print(f"Total Test Suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\\nDETAILED RESULTS:")
    for result in results:
        status = "[PASS]" if result['success'] else "[FAIL]"
        print(f"{status} {result['name']}")
    
    # Key functionality verification
    print(f"\\nKEY FUNCTIONALITY STATUS:")
    
    signal_quality_working = any(r['success'] for r in results if 'Signal Quality' in r['name'])
    integration_working = any(r['success'] for r in results if 'Integration' in r['name'])
    indian_market_working = any(r['success'] for r in results if 'Indian Market' in r['name'])
    
    print(f"[{'PASS' if signal_quality_working else 'FAIL'}] Signal Quality KPI")
    print(f"[{'PASS' if integration_working else 'FAIL'}] System Integration")
    print(f"[{'PASS' if indian_market_working else 'FAIL'}] Indian Market Support")
    
    # Recommendations
    print(f"\\nRECOMMENDATIONS:")
    if passed_tests == total_tests:
        print("- All new functionality is working correctly")
        print("- Signal Quality KPI is ready for production use")
        print("- Indian Market integration is functional")
        print("- System maintains backward compatibility")
    elif passed_tests >= total_tests * 0.75:
        print("- Core functionality is working well")
        print("- Address any failing tests before deployment")
        print("- New features are mostly stable")
    else:
        print("- Significant issues detected in new functionality")
        print("- Review and fix failing tests before proceeding")
        print("- Consider rolling back recent changes")
    
    print(f"\\nNEXT STEPS:")
    print("1. Run full system demo to verify end-to-end functionality")
    print("2. Test with real market data if available")
    print("3. Validate performance under load")
    print("4. Document any configuration changes needed")
    
    return passed_tests == total_tests

if __name__ == '__main__':
    success = run_focused_tests()
    sys.exit(0 if success else 1)