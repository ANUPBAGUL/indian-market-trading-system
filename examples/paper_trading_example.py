"""
Paper Trading Example - Demonstrates daily signal generation without execution.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime
from src.paper_trading_engine import PaperTradingEngine


def create_current_market_data():
    """Create simulated current market data."""
    today = datetime.now().strftime('%Y-%m-%d')
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'SPY']
    
    # Create 30 days of data ending today
    dates = pd.date_range(end=today, periods=30, freq='D')
    
    market_data = []
    for date in dates:
        for symbol in symbols:
            base_prices = {
                'AAPL': 185.0, 'MSFT': 380.0, 'GOOGL': 140.0, 
                'TSLA': 250.0, 'NVDA': 875.0, 'SPY': 485.0
            }
            
            days_from_start = (date - dates[0]).days
            trend = 1 + (days_from_start * 0.001)
            noise = np.random.normal(1, 0.02)
            
            base_price = base_prices[symbol]
            price = base_price * trend * noise
            
            # Add signal patterns
            if symbol == 'AAPL' and days_from_start > 20:
                price *= 1.01  # Accumulation pattern
            
            if symbol == 'TSLA' and days_from_start > 25:
                price *= 1.03  # Breakout setup
            
            market_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'symbol': symbol,
                'open': price * 0.995,
                'high': price * 1.025,
                'low': price * 0.975,
                'close': price,
                'volume': np.random.randint(1000000, 5000000)
            })
    
    return pd.DataFrame(market_data)


def main():
    """Demonstrate paper trading daily signal generation."""
    
    print("=== PAPER TRADING DAILY SESSION ===\n")
    
    # Initialize paper trading engine
    engine = PaperTradingEngine()
    
    # Get current market data
    print("Fetching current market data...")
    market_data = create_current_market_data()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Define trading universe
    universe = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    print(f"Analyzing {len(universe)} symbols for {today}")
    print(f"Market data: {len(market_data)} records loaded\n")
    
    # Add existing paper position for demo
    engine.paper_positions = {
        'MSFT': {
            'entry_price': 375.0,
            'shares': 50,
            'stop_price': 367.5,
            'entry_date': '2024-01-10'
        }
    }
    engine.paper_cash = 80000.0
    
    print("Current paper positions:")
    for symbol, pos in engine.paper_positions.items():
        print(f"  {symbol}: {pos['shares']} shares @ ${pos['entry_price']:.2f}")
    print()
    
    # Generate daily signals
    print("Generating trading signals...")
    signals = engine.generate_daily_signals(market_data, today, universe)
    
    # Generate and display report
    report = engine.generate_daily_report(signals)
    print(report)
    
    # Show difference explanation
    print("\n" + "="*60)
    print("BACKTEST vs PAPER TRADING vs LIVE TRADING")
    print("="*60)
    
    comparison = """
+---------------+-----------------+-----------------+-----------------+
| Aspect        | Backtesting     | Paper Trading   | Live Trading    |
+---------------+-----------------+-----------------+-----------------+
| Data Source   | Historical Data | Current Market  | Current Market  |
| Execution     | Simulated       | Manual Review   | Automated       |
| Risk          | No Money        | No Real Money   | Real Money      |
| Purpose       | Strategy Test   | Live Validation | Profit/Loss     |
| Timing        | Historical      | Real-time       | Real-time       |
| Market Impact | None            | None            | Yes (slippage)  |
| Emotions      | None            | Simulated       | Real            |
| Fills         | Perfect         | Manual          | Market-based    |
+---------------+-----------------+-----------------+-----------------+
"""
    print(comparison)
    
    print("\nKEY DIFFERENCES EXPLAINED:")
    print("• BACKTESTING: Tests strategy on past data with perfect hindsight")
    print("• PAPER TRADING: Uses current market for signal generation, no execution")
    print("• LIVE TRADING: Real money execution with market impact and emotions")
    print("\nPAPER TRADING BENEFITS:")
    print("• Bridge between backtesting and live trading")
    print("• Test with current market conditions")
    print("• No financial risk while learning")
    print("• Manual oversight of all decisions")
    
    return signals


if __name__ == '__main__':
    signals = main()
    print(f"\n=== SESSION COMPLETE ===")
    print(f"Signals: {len(signals['entry_signals'])} entry, {len(signals['exit_signals'])} exit")
    print("Next: Review signals and make manual trading decisions")