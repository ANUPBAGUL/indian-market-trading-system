import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.earnings_agent import EarningsAgent

def create_earnings_calendar():
    """Create sample earnings calendar"""
    current_date = datetime(2024, 2, 15)
    
    return pd.DataFrame([
        {'symbol': 'AAPL', 'earnings_date': current_date + timedelta(days=5)},   # Future
        {'symbol': 'MSFT', 'earnings_date': current_date - timedelta(days=3)},   # Past - bullish reaction
        {'symbol': 'GOOGL', 'earnings_date': current_date - timedelta(days=7)},  # Past - bearish reaction
        {'symbol': 'TSLA', 'earnings_date': current_date - timedelta(days=1)},   # Past - neutral reaction
        {'symbol': 'NVDA', 'earnings_date': current_date + timedelta(days=10)},  # Future
    ])

def create_stock_data():
    """Create stock data with different post-earnings reactions"""
    current_date = datetime(2024, 2, 15)
    stock_data = {}
    
    # MSFT - Bullish reaction (beat expectations)
    msft_dates = pd.date_range(current_date - timedelta(days=10), current_date + timedelta(days=2), freq='D')
    msft_data = []
    
    for i, date in enumerate(msft_dates):
        if i < 7:  # Pre-earnings
            close = 400 + np.random.normal(0, 5)
            volume = 25000000 + np.random.normal(0, 2000000)
        elif i == 7:  # Earnings day - gap up
            close = 420  # +5% gap up
            volume = 60000000  # 2.4x volume surge
        else:  # Post-earnings continuation
            close = 420 + (i - 7) * 2
            volume = 35000000
        
        msft_data.append({
            'date': date,
            'open': close + np.random.uniform(-2, 2),
            'high': close + abs(np.random.normal(3, 1)),
            'low': close - abs(np.random.normal(3, 1)),
            'close': close,
            'volume': max(int(volume), 1000000)
        })
    
    stock_data['MSFT'] = pd.DataFrame(msft_data)
    
    # GOOGL - Bearish reaction (missed expectations)
    googl_dates = pd.date_range(current_date - timedelta(days=14), current_date + timedelta(days=2), freq='D')
    googl_data = []
    
    for i, date in enumerate(googl_dates):
        if i < 7:  # Pre-earnings
            close = 2800 + np.random.normal(0, 20)
            volume = 1500000 + np.random.normal(0, 200000)
        elif i == 7:  # Earnings day - gap down
            close = 2650  # -5.4% gap down
            volume = 4000000  # 2.7x volume surge
        else:  # Post-earnings weakness
            close = 2650 - (i - 7) * 10
            volume = 2200000
        
        googl_data.append({
            'date': date,
            'open': close + np.random.uniform(-10, 10),
            'high': close + abs(np.random.normal(15, 5)),
            'low': close - abs(np.random.normal(15, 5)),
            'close': close,
            'volume': max(int(volume), 100000)
        })
    
    stock_data['GOOGL'] = pd.DataFrame(googl_data)
    
    # TSLA - Neutral reaction (met expectations, no surprise)
    tsla_dates = pd.date_range(current_date - timedelta(days=8), current_date + timedelta(days=2), freq='D')
    tsla_data = []
    
    for i, date in enumerate(tsla_dates):
        if i < 7:  # Pre-earnings
            close = 200 + np.random.normal(0, 8)
            volume = 40000000 + np.random.normal(0, 5000000)
        else:  # Post-earnings - minimal reaction
            close = 202 + np.random.normal(0, 3)  # +1% move, within normal range
            volume = 42000000  # Only 1.05x volume, no surge
        
        tsla_data.append({
            'date': date,
            'open': close + np.random.uniform(-3, 3),
            'high': close + abs(np.random.normal(5, 2)),
            'low': close - abs(np.random.normal(5, 2)),
            'close': close,
            'volume': max(int(volume), 1000000)
        })
    
    stock_data['TSLA'] = pd.DataFrame(tsla_data)
    
    return stock_data

if __name__ == "__main__":
    # Create test data
    earnings_calendar = create_earnings_calendar()
    stock_data = create_stock_data()
    current_date = datetime(2024, 2, 15)
    
    # Run earnings analysis
    print("Earnings & Events Analysis:")
    print("=" * 50)
    
    results = EarningsAgent.run(stock_data, earnings_calendar, current_date)
    
    # Sort by days to earnings
    sorted_results = sorted(results.items(), key=lambda x: x[1].days_to_earnings)
    
    for symbol, event in sorted_results:
        print(f"\\n{symbol}:")
        print(f"  Earnings Date:      {event.earnings_date.strftime('%Y-%m-%d')}")
        print(f"  Days to Earnings:   {event.days_to_earnings}")
        
        if event.days_to_earnings < 0:
            print(f"  Post-Earnings:      {event.post_reaction}")
            
            # Show the actual price action
            if symbol in stock_data:
                stock_df = stock_data[symbol]
                earnings_date = event.earnings_date
                
                # Find pre and post earnings data
                stock_df['date'] = pd.to_datetime(stock_df['date'])
                earnings_idx = None
                
                for i, row in stock_df.iterrows():
                    if row['date'].date() >= earnings_date.date():
                        earnings_idx = i
                        break
                
                if earnings_idx is not None and earnings_idx > 0:
                    pre_close = stock_df['close'].iloc[earnings_idx - 1]
                    post_close = stock_df['close'].iloc[min(earnings_idx + 2, len(stock_df) - 1)]
                    price_change = (post_close / pre_close - 1) * 100
                    
                    pre_volume = stock_df['volume'].iloc[max(0, earnings_idx - 3):earnings_idx].mean()
                    post_volume = stock_df['volume'].iloc[earnings_idx:earnings_idx + 3].mean()
                    volume_surge = post_volume / pre_volume if pre_volume > 0 else 1
                    
                    print(f"  Price Change:       {price_change:+.1f}%")
                    print(f"  Volume Surge:       {volume_surge:.1f}x")
        else:
            print(f"  Status:             Upcoming earnings")
            
            # Show risk warning for upcoming earnings
            if event.days_to_earnings <= 7:
                print(f"  Risk Warning:       HIGH - Earnings within 1 week")
            elif event.days_to_earnings <= 14:
                print(f"  Risk Warning:       MEDIUM - Earnings within 2 weeks")
            else:
                print(f"  Risk Warning:       LOW - Earnings >2 weeks away")
    
    print("\\n" + "=" * 50)
    print("Why Earnings Are Binary Risk:")
    print("=" * 50)
    print("• BINARY OUTCOME: Beat/miss expectations = immediate repricing")
    print("• VOLATILITY EXPLOSION: Options premiums spike before earnings")
    print("• GAP RISK: Stocks can gap 5-15% overnight on earnings")
    print("• UNPREDICTABLE: Even 'good' earnings can disappoint on guidance")
    print("• TECHNICAL BREAKDOWN: Chart patterns become irrelevant post-earnings")
    print()
    print("Risk Management:")
    print("• Reduce position size 1-2 weeks before earnings")
    print("• Avoid new entries 5 days before earnings")
    print("• Use wider stops during earnings season")
    print("• Consider closing positions before earnings")
    print()
    
    print("How Price/Volume Beats Headlines:")
    print("=" * 40)
    print("• HEADLINES LAG: Price moves before news is published")
    print("• VOLUME CONFIRMS: High volume validates price moves")
    print("• INSTITUTIONAL FLOW: Big money moves before retail reads news")
    print("• MARKET EFFICIENCY: Price discovery happens in milliseconds")
    print("• SENTIMENT NOISE: Headlines often mislead vs actual results")
    print()
    print("Price/Volume Analysis:")
    print("• Bullish: >3% move + >1.5x volume surge")
    print("• Bearish: <-3% move + >1.5x volume surge")
    print("• Neutral: <3% move OR no volume confirmation")
    print()
    
    print("Example Reactions:")
    print("=" * 20)
    print("MSFT: +5% gap up + 2.4x volume = BULLISH")
    print("  -> Strong beat, raised guidance, institutional buying")
    print()
    print("GOOGL: -5.4% gap down + 2.7x volume = BEARISH")
    print("  -> Revenue miss, weak guidance, institutional selling")
    print()
    print("TSLA: +1% move + 1.05x volume = NEUTRAL")
    print("  -> Met expectations, no surprises, normal trading")
    print()
    
    print("Trading Implications:")
    print("• BULLISH reactions: Look for continuation patterns")
    print("• BEARISH reactions: Avoid catching falling knives")
    print("• NEUTRAL reactions: Resume normal technical analysis")
    print("• Always wait for volume confirmation before acting")