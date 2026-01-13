"""Test the master trading runner with automated input."""

import sys
import os

# Add the main directory to path
sys.path.append(os.path.dirname(__file__))

def test_master_runner():
    """Test the master runner functionality."""
    
    print("Testing Master Trading Runner...")
    print()
    
    # Test US market
    print("1. Testing US Market System:")
    try:
        from run_us_trading import run_us_trading
        run_us_trading()
        print("   [PASS] US Market system working")
    except Exception as e:
        print(f"   [FAIL] US Market error: {e}")
    
    print()
    
    # Test Indian market
    print("2. Testing Indian Market System:")
    try:
        from run_indian_trading import run_indian_trading
        run_indian_trading()
        print("   [PASS] Indian Market system working")
    except Exception as e:
        print(f"   [FAIL] Indian Market error: {e}")
    
    print()
    print("Master runner test complete!")
    print()
    print("To use interactively, run: python run_trading.py")

if __name__ == "__main__":
    test_master_runner()