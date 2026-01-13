"""
Indian Market Demo - Works with sample data, no external dependencies.

Demonstrates the Indian market trading system using generated sample data
that mimics real NSE/BSE stock behavior and patterns.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from backtest_engine import BacktestEngine
from kpi_computer import KPIComputer
from governor import Governor

class IndianMarketDemo:
    """Demo class for Indian market trading system."""
    
    # Major Indian stocks with realistic base prices (INR)
    INDIAN_STOCKS = {
        'RELIANCE': {'price': 2500, 'sector': 'Energy'},
        'TCS': {'price': 3500, 'sector': 'IT'},
        'HDFCBANK': {'price': 1600, 'sector': 'Banking'},
        'INFY': {'price': 1400, 'sector': 'IT'},
        'ICICIBANK': {'price': 900, 'sector': 'Banking'},
        'HINDUNILVR': {'price': 2400, 'sector': 'FMCG'},
        'ITC': {'price': 450, 'sector': 'FMCG'},
        'SBIN': {'price': 600, 'sector': 'Banking'},
        'BHARTIARTL': {'price': 800, 'sector': 'Telecom'},
        'LT': {'price': 2200, 'sector': 'Infrastructure'}
    }
    
    # Indian market parameters
    TRADING_HOURS = {'open': '09:15', 'close': '15:30'}
    MIN_CONFIDENCE = 60.0
    MAX_POSITION_RISK = 2.0  # Higher for Indian volatility
    INITIAL_CAPITAL = 500000  # INR 5 Lakhs
    
    @staticmethod
    def create_sample_data(days: int = 60) -> pd.DataFrame:
        """Create realistic Indian market sample data."""
        
        # Generate trading dates (exclude weekends)
        start_date = datetime.now() - timedelta(days=days+20)
        dates = []
        current = start_date
        
        while len(dates) < days:
            if current.weekday() < 5:  # Monday=0, Friday=4
                dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        
        all_data = []
        
        for symbol, info in IndianMarketDemo.INDIAN_STOCKS.items():
            base_price = info['price']
            sector = info['sector']
            
            # Add some sector-specific volatility
            sector_vol = {
                'Banking': 0.025, 'IT': 0.020, 'FMCG': 0.015,
                'Energy': 0.030, 'Telecom': 0.025, 'Infrastructure': 0.028
            }.get(sector, 0.020)
            
            current_price = base_price
            
            for i, date in enumerate(dates):
                # Generate realistic daily movement
                daily_return = np.random.normal(0.001, sector_vol)  # Slight positive bias
                current_price *= (1 + daily_return)
                
                # Generate OHLC
                open_price = current_price * (0.995 + 0.01 * np.random.random())
                
                # Indian markets can be quite volatile
                daily_range = open_price * sector_vol * (1 + 2 * np.random.random())
                high_price = open_price + daily_range * np.random.random()
                low_price = open_price - daily_range * np.random.random()
                
                # Close within the range
                close_price = low_price + (high_price - low_price) * np.random.random()
                current_price = close_price
                
                # Volume (Indian stocks typically have high volume)
                base_volume = {'RELIANCE': 5000000, 'TCS': 2000000, 'HDFCBANK': 3000000}.get(symbol, 1000000)
                volume = int(base_volume * (0.5 + np.random.random()))
                
                all_data.append({
                    'date': date,
                    'symbol': symbol,
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': volume,
                    'sector': sector
                })
        
        return pd.DataFrame(all_data)
    
    @staticmethod
    def create_indian_signal_generator():
        """Create signal generator for Indian markets."""
        
        def generate_signals(day_data, existing_positions):
            """Generate signals adapted for Indian market conditions."""
            signals = []
            
            for _, row in day_data.iterrows():
                symbol = row['symbol']
                
                # Skip if already have position
                if symbol in existing_positions:
                    continue
                
                # Indian market filters
                if row['close'] < 50 or row['close'] > 5000:  # Price filters
                    continue
                
                if row['volume'] < 100000:  # Volume filter
                    continue
                
                # Simple signal logic for demo
                # Look for momentum with volume
                price_change = (row['close'] - row['open']) / row['open']
                volume_ratio = row['volume'] / 1000000  # Normalize volume
                
                # Indian market signal scoring
                confidence = 50  # Base confidence
                
                # Price momentum (Indian markets love momentum)
                if price_change > 0.02:  # 2% up
                    confidence += 15
                elif price_change > 0.01:  # 1% up
                    confidence += 10
                
                # Volume confirmation (crucial in Indian markets)
                if volume_ratio > 2.0:  # High volume
                    confidence += 10
                elif volume_ratio > 1.5:
                    confidence += 5
                
                # Sector bias (IT and Banking often lead)
                if row['sector'] in ['IT', 'Banking']:
                    confidence += 5
                
                # Range breakout (Indian stocks love breakouts)
                range_position = (row['close'] - row['low']) / (row['high'] - row['low'])
                if range_position > 0.8:  # Close near high
                    confidence += 8
                
                # Apply Indian market minimum confidence
                if confidence < IndianMarketDemo.MIN_CONFIDENCE:
                    continue
                
                # Position sizing (conservative for Indian volatility)
                position_value = IndianMarketDemo.INITIAL_CAPITAL * 0.15  # 15% max per position
                shares = int(position_value / row['close'])
                
                if shares < 1:
                    continue
                
                signal = {
                    'symbol': symbol,
                    'type': 'ENTRY',
                    'confidence': min(confidence, 95),  # Cap at 95%
                    'shares': shares,
                    'sector': row['sector'],
                    'stop_price': row['close'] * 0.92,  # 8% stop (wider for Indian volatility)
                    'reasoning': f"Indian momentum signal: {confidence:.1f}% confidence"
                }
                
                signals.append(signal)
            
            return signals
        
        return generate_signals

def main():
    """Run Indian market demo."""
    
    print("=== INDIAN MARKET TRADING SYSTEM DEMO ===\\n")
    
    # Create sample Indian market data
    print("Generating sample Indian market data...")
    demo = IndianMarketDemo()
    stock_data = demo.create_sample_data(days=60)
    
    print(f"Created data for {stock_data['symbol'].nunique()} Indian stocks")
    print(f"Date range: {stock_data['date'].min()} to {stock_data['date'].max()}")
    print(f"Total records: {len(stock_data)}")
    
    # Show sample prices in INR
    print(f"\\nSample Stock Prices (INR):")
    latest_prices = stock_data[stock_data['date'] == stock_data['date'].max()]
    for _, row in latest_prices.iterrows():
        print(f"  {row['symbol']}: Rs.{row['close']:.2f} ({row['sector']})")
    
    # Show sector distribution
    print(f"\\nSector Distribution:")
    sector_counts = stock_data.groupby('sector')['symbol'].nunique()
    for sector, count in sector_counts.items():
        print(f"  {sector}: {count} stocks")
    
    # Initialize backtesting for Indian market
    print(f"\\nInitializing Indian market backtester...")
    print(f"Initial Capital: Rs.{demo.INITIAL_CAPITAL:,}")
    
    backtester = BacktestEngine(initial_capital=demo.INITIAL_CAPITAL)
    governor = Governor()  # Uses default settings, suitable for Indian markets
    signal_generator = demo.create_indian_signal_generator()
    
    # Run backtest
    print(f"\\nRunning backtest on Indian stocks...")
    
    results = backtester.run(
        price_data=stock_data,
        signal_generator=signal_generator,
        governor=governor
    )
    
    # Analyze results
    print(f"\\n=== INDIAN MARKET BACKTEST RESULTS ===\\n")
    
    if results['trades']:
        # Calculate KPIs
        kpis = KPIComputer.compute_kpis(
            trades=results['trades'],
            equity_curve=results['equity_curve'],
            signal_data=results.get('signal_log', [])
        )
        
        # Display results with Indian formatting
        print(f"PERFORMANCE SUMMARY:")
        print(f"  Total Trades: {len(results['trades'])}")
        print(f"  Expectancy: Rs.{kpis['expectancy']:.0f} per trade")
        print(f"  Win Rate: {kpis['win_rate_pct']:.1f}%")
        print(f"  Max Drawdown: {kpis['max_drawdown_pct']:.1f}%")
        
        # Calculate returns in INR
        final_value = results['equity_curve'][-1]['total_value']
        total_pnl = final_value - demo.INITIAL_CAPITAL
        return_pct = (total_pnl / demo.INITIAL_CAPITAL) * 100
        
        print(f"\\nPORTFOLIO PERFORMANCE:")
        print(f"  Initial Capital: Rs.{demo.INITIAL_CAPITAL:,}")
        print(f"  Final Value: Rs.{final_value:,.0f}")
        print(f"  Total P&L: Rs.{total_pnl:,.0f}")
        print(f"  Return: {return_pct:.1f}%")
        
        # Sector performance analysis
        print(f"\\nSECTOR PERFORMANCE:")
        sector_performance = {}
        
        for trade in results['trades']:
            # Find sector from stock data
            stock_info = stock_data[stock_data['symbol'] == trade.symbol]
            sector = stock_info.iloc[0]['sector'] if not stock_info.empty else 'Unknown'
            
            if sector not in sector_performance:
                sector_performance[sector] = {'trades': 0, 'pnl': 0}
            
            sector_performance[sector]['trades'] += 1
            sector_performance[sector]['pnl'] += trade.pnl
        
        for sector, perf in sector_performance.items():
            avg_pnl = perf['pnl'] / perf['trades'] if perf['trades'] > 0 else 0
            print(f"  {sector}: {perf['trades']} trades, Avg P&L: Rs.{avg_pnl:.0f}")
        
        # Signal quality for Indian markets
        if 'signal_quality_stats' in kpis and kpis['signal_quality_stats']:
            sq = kpis['signal_quality_stats']
            print(f"\\nSIGNAL QUALITY (Indian Markets):")
            print(f"  Conversion Rate: {sq['conversion_rate_pct']:.1f}%")
            print(f"  Signal Accuracy: {sq['signal_accuracy_pct']:.1f}%")
        
        # System assessment for Indian markets
        print(f"\\nSYSTEM ASSESSMENT:")
        if kpis['expectancy'] > 0:
            print(f"  [+] Profitable system for Indian markets")
        else:
            print(f"  [-] System needs tuning for Indian conditions")
        
        if kpis['max_drawdown_pct'] < 15:
            print(f"  [+] Acceptable drawdown for Indian volatility")
        else:
            print(f"  [!] High drawdown - consider reducing position sizes")
        
    else:
        print("No trades generated. Consider:")
        print("- Lowering confidence threshold (currently 60%)")
        print("- Adjusting volume filters for Indian liquidity")
        print("- Reviewing price filters for Indian stock ranges")
    
    print(f"\\n=== INDIAN MARKET INSIGHTS ===\\n")
    print("Key Adaptations Made:")
    print("- Higher position risk (2.0%) for Indian volatility")
    print("- Wider stop losses (8%) for Indian price swings")
    print("- Volume-based signals (crucial in Indian markets)")
    print("- Sector bias towards IT and Banking leaders")
    print("- Momentum-focused approach (Indian markets trend well)")
    
    print(f"\\nNext Steps for Indian Markets:")
    print("- Add more NIFTY 50 stocks to universe")
    print("- Implement rupee cost averaging")
    print("- Add festival season patterns")
    print("- Consider FII flow indicators")
    print("- Integrate with Indian broker APIs")

if __name__ == "__main__":
    main()