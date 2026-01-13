"""
Master Trading Runner - Choose between US and Indian markets.

Simple interface to run either US or Indian market trading systems.
"""

import sys
import os

def show_menu():
    """Display market selection menu."""
    print("=" * 50)
    print("TRADING SYSTEM - MARKET SELECTION")
    print("=" * 50)
    print()
    print("Choose your market:")
    print("1. US Markets (NASDAQ/NYSE)")
    print("2. Indian Markets (NSE/BSE)")
    print("3. Both Markets (Sequential)")
    print("4. Exit")
    print()

def run_us_market():
    """Run US market system."""
    print()
    print("Starting US Market Trading System...")
    print("-" * 40)
    
    try:
        # Import and run US system
        from run_us_trading import run_us_trading
        run_us_trading()
    except ImportError:
        print("US trading system not available.")
        print("Run: python examples/paper_trading_example.py")
    except Exception as e:
        print(f"Error: {e}")

def run_indian_market():
    """Run Indian market system."""
    print()
    print("Starting Indian Market Trading System...")
    print("-" * 40)
    
    try:
        # Import and run Indian system
        from run_indian_trading import run_indian_trading
        run_indian_trading()
    except ImportError:
        print("Indian trading system not available.")
        print("Run: python examples/indian_market_demo.py")
    except Exception as e:
        print(f"Error: {e}")

def run_both_markets():
    """Run both market systems."""
    print()
    print("Running Both Market Systems...")
    print("=" * 50)
    
    # Run US market first
    run_us_market()
    
    print()
    print("=" * 50)
    
    # Run Indian market second
    run_indian_market()

def main():
    """Main trading system interface."""
    
    while True:
        show_menu()
        
        try:
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == '1':
                run_us_market()
            elif choice == '2':
                run_indian_market()
            elif choice == '3':
                run_both_markets()
            elif choice == '4':
                print()
                print("Exiting trading system. Happy trading!")
                break
            else:
                print()
                print("Invalid choice. Please enter 1, 2, 3, or 4.")
            
            # Wait for user before showing menu again
            if choice in ['1', '2', '3']:
                print()
                input("Press Enter to continue...")
                print()
                
        except KeyboardInterrupt:
            print()
            print()
            print("Exiting trading system. Happy trading!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again.")

if __name__ == "__main__":
    main()