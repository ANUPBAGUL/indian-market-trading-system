"""
Indian Market Trading Runner - Execute Indian market trading system.

Simple script to run the trading system for Indian markets (NSE/BSE).
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'examples'))

from indian_market_demo import IndianMarketDemo
from backtest_engine import BacktestEngine
from governor import Governor
from kpi_computer import KPIComputer

def run_indian_trading():
    """Run Indian market trading system."""
    
    print("=== INDIAN MARKET TRADING SYSTEM ===")
    print("Market: NSE/BSE")
    print("Currency: INR (Indian Rupees)")
    print("Trading Hours: 9:15 AM - 3:30 PM IST")
    print()
    
    try:
        # Initialize Indian market demo
        demo = IndianMarketDemo()
        
        # Create sample data (in production, load real NSE/BSE data)
        print("Loading Indian market data...")
        stock_data = demo.create_sample_data(days=30)
        
        print(f"Loaded {stock_data['symbol'].nunique()} Indian stocks")
        print("Stocks:", ", ".join(stock_data['symbol'].unique()))
        print()
        
        # Initialize trading components
        backtester = BacktestEngine(initial_capital=500000)  # Rs. 5 Lakhs
        governor = Governor()
        signal_generator = demo.create_indian_signal_generator()
        
        # Run analysis
        print("Running Indian market analysis...")
        results = backtester.run(
            price_data=stock_data,
            signal_generator=signal_generator,
            governor=governor
        )
        
        # Display results
        print()
        print("=== RESULTS ===")
        
        if results['trades']:
            # Calculate KPIs
            kpis = KPIComputer.compute_kpis(
                trades=results['trades'],
                equity_curve=results['equity_curve'],
                signal_data=results.get('signal_log', [])
            )
            
            print(f"Total Trades: {len(results['trades'])}")
            print(f"Expectancy: Rs.{kpis['expectancy']:.0f} per trade")
            print(f"Win Rate: {kpis['win_rate_pct']:.1f}%")
            
            # Show recent signals
            if results['signal_log']:
                recent_signals = results['signal_log'][-5:]  # Last 5 signals
                print()
                print("Recent Signals:")
                for signal in recent_signals:
                    status = "EXECUTED" if signal.get('executed') else "REJECTED"
                    reason = signal.get('rejection_reason', 'N/A')
                    print(f"  {signal['symbol']}: {status} ({reason})")
        else:
            print("No trades executed.")
            print("Consider adjusting confidence thresholds for Indian market conditions.")
        
        print()
        print("Indian market analysis complete.")
        
    except Exception as e:
        print(f"Error running Indian trading system: {e}")
        print("Check Indian market configuration and data availability.")

if __name__ == "__main__":
    run_indian_trading()