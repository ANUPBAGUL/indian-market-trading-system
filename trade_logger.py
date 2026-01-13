"""
Simple Trade Logger - Track your daily trading activities.

Run this to log trades and track performance easily.
"""

import csv
import os
from datetime import datetime

class TradeLogger:
    """Simple trade logging system."""
    
    def __init__(self):
        self.log_file = "trade_log.csv"
        self.setup_log_file()
    
    def setup_log_file(self):
        """Create log file with headers if it doesn't exist."""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Date', 'Market', 'Stock', 'Action', 'Shares', 
                    'Entry_Price', 'Stop_Price', 'Confidence', 'Status', 
                    'Exit_Price', 'Exit_Date', 'PnL', 'Notes'
                ])
    
    def log_signal(self, market, stock, action, shares, entry_price, stop_price, confidence):
        """Log a new trading signal."""
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d'),
                market, stock, action, shares, entry_price, stop_price, 
                confidence, 'ACTIVE', '', '', '', ''
            ])
        print(f"Logged: {stock} {action} - {shares} shares at {entry_price}")
    
    def log_exit(self, stock, exit_price, exit_reason):
        """Log trade exit."""
        # In a real implementation, this would update the existing record
        print(f"Exit logged: {stock} at {exit_price} - Reason: {exit_reason}")
        print("Note: Update your CSV file manually with exit details")
    
    def show_active_trades(self):
        """Show currently active trades."""
        print("\n=== ACTIVE TRADES ===")
        try:
            with open(self.log_file, 'r') as f:
                reader = csv.DictReader(f)
                active_count = 0
                for row in reader:
                    if row['Status'] == 'ACTIVE':
                        print(f"{row['Stock']}: {row['Shares']} shares @ {row['Entry_Price']} (Stop: {row['Stop_Price']})")
                        active_count += 1
                
                if active_count == 0:
                    print("No active trades")
        except FileNotFoundError:
            print("No trade log found")

def main():
    """Interactive trade logging."""
    logger = TradeLogger()
    
    print("=== TRADE LOGGER ===")
    print("1. Log new signal")
    print("2. Log trade exit") 
    print("3. Show active trades")
    print("4. Exit")
    
    while True:
        choice = input("\nChoose option (1-4): ").strip()
        
        if choice == '1':
            print("\nLog New Signal:")
            market = input("Market (US/Indian): ")
            stock = input("Stock symbol: ")
            action = input("Action (BUY/SELL): ")
            shares = input("Shares: ")
            entry_price = input("Entry price: ")
            stop_price = input("Stop price: ")
            confidence = input("Confidence %: ")
            
            logger.log_signal(market, stock, action, shares, entry_price, stop_price, confidence)
            
        elif choice == '2':
            print("\nLog Trade Exit:")
            stock = input("Stock symbol: ")
            exit_price = input("Exit price: ")
            exit_reason = input("Exit reason: ")
            
            logger.log_exit(stock, exit_price, exit_reason)
            
        elif choice == '3':
            logger.show_active_trades()
            
        elif choice == '4':
            print("Happy trading!")
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()