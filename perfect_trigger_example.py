import pandas as pd
import numpy as np
from src.trigger_agent import TriggerAgent

def create_perfect_trigger():
    """Create perfect trigger scenario with all signals"""
    dates = pd.date_range('2024-01-01', periods=26)
    
    data = []
    
    for i, date in enumerate(dates):
        if i < 25:
            # Tight base formation around 100
            close = 100.0 + np.random.uniform(-0.5, 0.5)
            high = close + np.random.uniform(0.2, 0.8)
            low = close - np.random.uniform(0.2, 0.8)
            volume = 1000000 + np.random.normal(0, 50000)
        else:
            # Perfect trigger bar
            close = 103.5   # Strong close (top of candle)
            high = 104.0    # >2% above base high of ~101
            low = 102.0     # Gap up
            volume = 2000000  # 2x volume expansion
        
        open_price = close + np.random.normal(0, 0.05)
        
        data.append({
            'symbol': 'PERFECT',
            'date': date,
            'open': max(open_price, 1),
            'high': max(high, close),
            'low': min(low, close),
            'close': max(close, 1),
            'volume': max(int(volume), 100000)
        })
    
    return pd.DataFrame(data)

if __name__ == "__main__":
    # Test perfect trigger
    perfect_data = create_perfect_trigger()
    result = TriggerAgent.run(perfect_data)
    
    print("PERFECT TRIGGER Example:")
    print("=" * 40)
    print(f"Trigger Active: {'YES' if result['trigger_active'] else 'NO'}")
    print()
    
    print("Individual Signals:")
    signals = result['signals']
    print(f"  Volume Expansion:   {'YES' if signals.volume_expansion else 'NO'}")
    print(f"  Breakout from Base: {'YES' if signals.breakout_from_base else 'NO'}")
    print(f"  Candle Acceptance:  {'YES' if signals.candle_acceptance else 'NO'}")
    print()
    
    print("Signal Metrics:")
    metrics = result['metrics']
    print(f"  Volume Ratio:       {metrics['volume_ratio']:.2f}x")
    print(f"  Breakout %:         {metrics['breakout_percentage']:+.1%}")
    print(f"  Close Position:     {metrics['close_position']:.1%}")
    print()
    
    # Show trigger bar
    trigger_bar = perfect_data.iloc[-1]
    print("Trigger Bar Details:")
    print(f"  Date: {trigger_bar['date'].strftime('%Y-%m-%d')}")
    print(f"  OHLC: ${trigger_bar['open']:.2f} / ${trigger_bar['high']:.2f} / ${trigger_bar['low']:.2f} / ${trigger_bar['close']:.2f}")
    print(f"  Volume: {trigger_bar['volume']:,}")
    
    # Show base context
    base_data = perfect_data.tail(21).head(20)
    base_high = base_data['high'].max()
    base_avg_vol = base_data['volume'].mean()
    print(f"  Base High: ${base_high:.2f}")
    print(f"  Base Avg Volume: {base_avg_vol:,.0f}")
    print(f"  Breakout Level: ${base_high * 1.02:.2f} (+2%)")
    
    print()
    print("Why This Triggers:")
    print("-" * 20)
    print(f"+ Volume: {trigger_bar['volume']:,} vs {base_avg_vol:,.0f} avg = {trigger_bar['volume']/base_avg_vol:.1f}x")
    print(f"+ Breakout: ${trigger_bar['high']:.2f} vs ${base_high * 1.02:.2f} threshold")
    print(f"+ Close: {((trigger_bar['close'] - trigger_bar['low']) / (trigger_bar['high'] - trigger_bar['low']) * 100):.0f}% of candle range")
    
    print()
    print("This is a VALID TRIGGER for entry consideration")