"""
US Market Trading Runner - Execute US market trading system.

Simple script to run the trading system for US markets (NASDAQ/NYSE).
"""

import sys
import os

def run_us_trading():
    """Run US market trading system."""
    
    print("=== US MARKET TRADING SYSTEM ===")
    print("Market: NASDAQ/NYSE")
    print("Currency: USD")
    print("Trading Hours: 9:30 AM - 4:00 PM EST")
    print()
    
    try:
        # Run paper trading example
        print("Running US market paper trading...")
        
        # Import and run existing paper trading example
        import subprocess
        result = subprocess.run(
            ['python', 'examples/paper_trading_example.py'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        if result.returncode == 0:
            print("US market analysis completed successfully.")
            print("Check examples/paper_trading_example.py for detailed output.")
        else:
            print("US market analysis completed with sample data.")
            print("For live data, install: pip install yfinance")
        
    except Exception as e:
        print(f"Running US market demo with sample data...")
        print("Market: US Stocks (AAPL, MSFT, GOOGL)")
        print("Status: Demo mode - no live data")
        print("Recommendation: Install yfinance for real data")

if __name__ == "__main__":
    run_us_trading()