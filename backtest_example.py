"""
Backtest Engine Examples - Demonstrates realistic daily backtesting.
"""

import sys
sys.path.append('src')
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtest_engine import BacktestEngine
from governor import Governor


def generate_sample_data(start_date: str, end_date: str, symbols: list) -> pd.DataFrame:
    """Generate sample OHLCV data for backtesting."""
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    dates = [d for d in dates if d.weekday() < 5]  # Only weekdays
    
    data = []
    np.random.seed(42)  # Reproducible results
    
    for symbol in symbols:
        base_price = np.random.uniform(50, 200)
        
        for i, date in enumerate(dates):
            # Generate realistic OHLCV data
            prev_close = base_price if i == 0 else data[-1]['close']
            
            # Random walk with slight upward bias
            daily_return = np.random.normal(0.0005, 0.02)  # 0.05% daily drift, 2% volatility
            
            open_price = prev_close * (1 + np.random.normal(0, 0.005))  # Gap
            close_price = open_price * (1 + daily_return)
            
            # High/Low based on intraday volatility
            intraday_range = abs(np.random.normal(0, 0.015))
            high_price = max(open_price, close_price) * (1 + intraday_range)
            low_price = min(open_price, close_price) * (1 - intraday_range)
            
            volume = int(np.random.uniform(100000, 5000000))
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'symbol': symbol,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
    
    return pd.DataFrame(data)


def simple_signal_generator(day_data: pd.DataFrame, existing_positions: dict) -> list:
    """Simple signal generator for demonstration."""
    signals = []
    
    for _, row in day_data.iterrows():
        symbol = row['symbol']
        
        # Simple momentum strategy: buy if close > 5-day average
        # (In real implementation, this would use proper technical indicators)
        
        # Entry signal: random chance for demonstration
        if symbol not in existing_positions and np.random.random() < 0.05:  # 5% chance
            signals.append({
                'type': 'ENTRY',
                'symbol': symbol,
                'confidence': np.random.uniform(60, 90),
                'shares': 100,
                'sector': 'Technology',
                'stop_price': row['close'] * 0.92  # 8% stop loss
            })
        
        # Exit signal: random chance for existing positions
        elif symbol in existing_positions and np.random.random() < 0.03:  # 3% chance
            signals.append({
                'type': 'EXIT',
                'symbol': symbol,
                'decayed_confidence': np.random.uniform(40, 60)
            })
    
    return signals


def main():
    print("=== BACKTEST ENGINE EXAMPLE ===\n")
    
    # Generate sample data
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    
    print("Generating sample price data...")
    price_data = generate_sample_data(start_date, end_date, symbols)
    print(f"Generated {len(price_data)} price records for {len(symbols)} symbols")
    print(f"Date range: {price_data['date'].min()} to {price_data['date'].max()}\n")
    
    # Initialize backtest engine
    initial_capital = 100000
    backtester = BacktestEngine(initial_capital=initial_capital)
    
    print("Running backtest...")
    results = backtester.run(
        price_data=price_data,
        signal_generator=simple_signal_generator,
        governor=Governor
    )
    
    print("\n=== BACKTEST RESULTS ===")
    
    # Performance metrics
    metrics = results['metrics']
    print(f"Initial Capital: ${initial_capital:,.0f}")
    print(f"Final Value: ${metrics['final_value']:,.0f}")
    print(f"Total Return: {metrics['total_return_pct']:.1f}%")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Win Rate: {metrics['win_rate_pct']:.1f}%")
    print(f"Average Win: ${metrics['avg_win']:.0f}")
    print(f"Average Loss: ${metrics['avg_loss']:.0f}")
    print()
    
    # Trade log sample
    trades = results['trades']
    if trades:
        print("=== TRADE LOG SAMPLE ===")
        print("Symbol | Entry Date | Entry Price | Exit Date  | Exit Price | P&L    | P&L% | Reason")
        print("-------|------------|-------------|------------|------------|--------|------|-------")
        
        for trade in trades[:10]:  # Show first 10 trades
            print(f"{trade.symbol:<6} | {trade.entry_date} | ${trade.entry_price:>9.2f} | "
                  f"{trade.exit_date or 'OPEN':<10} | ${trade.exit_price or 0:>9.2f} | "
                  f"${trade.pnl:>6.0f} | {trade.pnl_pct:>4.1f}% | {trade.exit_reason}")
        
        if len(trades) > 10:
            print(f"... and {len(trades) - 10} more trades")
        print()
    
    # Equity curve sample
    equity_curve = results['equity_curve']
    if equity_curve:
        print("=== EQUITY CURVE SAMPLE ===")
        print("Date       | Cash     | Positions | Total Value | # Pos")
        print("-----------|----------|-----------|-------------|------")
        
        # Show every 30th day
        for i in range(0, len(equity_curve), 30):
            point = equity_curve[i]
            print(f"{point['date']} | ${point['cash']:>8.0f} | "
                  f"${point['positions_value']:>9.0f} | ${point['total_value']:>11.0f} | "
                  f"{point['num_positions']:>4}")
        
        # Show final day
        if len(equity_curve) > 1:
            final_point = equity_curve[-1]
            print(f"{final_point['date']} | ${final_point['cash']:>8.0f} | "
                  f"${final_point['positions_value']:>9.0f} | ${final_point['total_value']:>11.0f} | "
                  f"{final_point['num_positions']:>4}")
        print()
    
    # Risk analysis
    if len(equity_curve) > 1:
        print("=== RISK ANALYSIS ===")
        values = [point['total_value'] for point in equity_curve]
        peak = max(values)
        trough = min(values[values.index(peak):]) if peak in values else min(values)
        max_drawdown = ((trough - peak) / peak) * 100
        
        print(f"Peak Portfolio Value: ${peak:,.0f}")
        print(f"Maximum Drawdown: {max_drawdown:.1f}%")
        
        # Calculate volatility (simplified)
        returns = []
        for i in range(1, len(values)):
            daily_return = (values[i] - values[i-1]) / values[i-1]
            returns.append(daily_return)
        
        if returns:
            volatility = np.std(returns) * np.sqrt(252) * 100  # Annualized
            print(f"Annualized Volatility: {volatility:.1f}%")
        print()
    
    print("=== BACKTEST ASSUMPTIONS ===")
    print("• Next-open execution: Signals generated after close, filled at next open")
    print("• Stop orders: Triggered when low price hits stop level")
    print("• No slippage: Orders filled at exact prices")
    print("• No transaction costs: Simplified for demonstration")
    print("• Governor approval: All trades subject to risk management rules")


if __name__ == "__main__":
    main()