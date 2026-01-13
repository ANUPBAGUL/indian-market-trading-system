import pandas as pd
import numpy as np
from src.trigger_agent import TriggerAgent

def create_true_breakout_example():
    """Create textbook true breakout scenario"""
    dates = pd.date_range('2024-01-01', periods=30)
    
    data = []
    base_price = 100.0
    
    for i, date in enumerate(dates):
        if i < 25:
            # Base formation: tight consolidation around 100
            close = 99.0 + np.random.uniform(0, 2)  # Range 99-101
            high = close + np.random.uniform(0.2, 1)
            low = close - np.random.uniform(0.2, 1)
            volume = 1000000 + np.random.normal(0, 100000)  # Normal volume
        else:
            # Breakout day: volume expansion + price breakout + strong close
            if i == 25:  # Breakout bar
                close = 103.0  # Strong close well above base
                high = 103.5   # New high, >2% above base high of 101
                low = 101.5    # Gap up above base
                volume = 2000000  # 2x volume expansion
            else:
                # Follow-through
                close = 103.0 + (i - 25) * 0.3
                high = close + 0.5
                low = close - 0.3
                volume = 1300000
        
        open_price = close + np.random.normal(0, 0.1)
        
        data.append({
            'symbol': 'TRUE_BO',
            'date': date,
            'open': max(open_price, 1),
            'high': max(high, close),
            'low': min(low, close),
            'close': max(close, 1),
            'volume': max(int(volume), 100000)
        })
    
    return pd.DataFrame(data)

def create_false_breakout_example():
    """Create false breakout scenario"""
    dates = pd.date_range('2024-01-01', periods=30)
    
    data = []
    base_price = 100.0
    
    for i, date in enumerate(dates):
        if i < 25:
            # Base formation
            close = base_price + np.random.normal(0, 1)
            high = close + np.random.uniform(0.5, 2)
            low = close - np.random.uniform(0.5, 2)
            volume = 1000000 + np.random.normal(0, 200000)
        else:
            # False breakout: weak volume, poor close
            if i == 25:  # False breakout bar
                close = 100.5  # Weak close, barely above base
                high = 103.0   # High reached but couldn't hold
                low = 99.5     # Weak low
                volume = 1200000  # Only modest volume increase
            else:
                # Failure and reversal
                close = 99.0 - (i - 25) * 0.3
                high = close + 0.5
                low = close - 1
                volume = 800000
        
        open_price = close + np.random.normal(0, 0.2)
        
        data.append({
            'symbol': 'FALSE_BO',
            'date': date,
            'open': max(open_price, 1),
            'high': max(high, close),
            'low': min(low, close),
            'close': max(close, 1),
            'volume': max(int(volume), 100000)
        })
    
    return pd.DataFrame(data)

def create_no_trigger_example():
    """Create normal trading with no trigger"""
    dates = pd.date_range('2024-01-01', periods=30)
    
    data = []
    base_price = 100.0
    
    for i, date in enumerate(dates):
        # Normal trading throughout
        close = base_price + np.random.normal(0, 2)
        high = close + np.random.uniform(1, 3)
        low = close - np.random.uniform(1, 3)
        volume = 1000000 + np.random.normal(0, 300000)
        
        open_price = close + np.random.normal(0, 0.5)
        
        data.append({
            'symbol': 'NO_TRIGGER',
            'date': date,
            'open': max(open_price, 1),
            'high': max(high, close),
            'low': min(low, close),
            'close': max(close, 1),
            'volume': max(int(volume), 100000)
        })
    
    return pd.DataFrame(data)

if __name__ == "__main__":
    # Test all scenarios
    scenarios = [
        ("TRUE BREAKOUT", create_true_breakout_example()),
        ("FALSE BREAKOUT", create_false_breakout_example()),
        ("NO TRIGGER", create_no_trigger_example())
    ]
    
    print("Trigger Agent Analysis:")
    print("=" * 60)
    
    for scenario_name, data in scenarios:
        result = TriggerAgent.run(data)
        
        print(f"\\n{scenario_name} Example:")
        print("-" * 30)
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
        
        # Show the trigger bar details
        trigger_bar = data.iloc[-1]
        print("Trigger Bar Details:")
        print(f"  Date: {trigger_bar['date'].strftime('%Y-%m-%d')}")
        print(f"  OHLC: ${trigger_bar['open']:.2f} / ${trigger_bar['high']:.2f} / ${trigger_bar['low']:.2f} / ${trigger_bar['close']:.2f}")
        print(f"  Volume: {trigger_bar['volume']:,}")
        
        # Calculate base high for context
        base_data = data.tail(21).head(20)  # 20-day base
        base_high = base_data['high'].max()
        print(f"  Base High: ${base_high:.2f}")
        print(f"  Breakout Level: ${base_high * 1.02:.2f} (+2%)")
    
    print("\\n" + "=" * 60)
    print("SETUP vs TRIGGER Explanation:")
    print("=" * 60)
    print("SETUP (Accumulation Agent):")
    print("• Identifies POTENTIAL for breakout")
    print("• Looks for institutional accumulation over weeks/months")
    print("• Evidence: Volume absorption, tight base, relative strength")
    print("• Probabilistic: Suggests higher odds, not certainty")
    print()
    print("TRIGGER (This Agent):")
    print("• Identifies ACTUAL breakout attempt")
    print("• Looks for immediate price/volume action")
    print("• Evidence: Volume expansion, price breakout, strong close")
    print("• Binary: Either triggers or doesn't on specific bar")
    print()
    print("Relationship: SETUP -> TRIGGER -> ENTRY")
    print("• Setup identifies candidates")
    print("• Trigger identifies timing")
    print("• Entry executes the trade")
    print()
    
    print("Why False Breakouts Happen:")
    print("=" * 30)
    print("• WEAK VOLUME: Retail-driven moves lack institutional support")
    print("• POOR CLOSES: Can't hold breakout level = weak demand")
    print("• MARKET CONDITIONS: Bear market kills individual breakouts")
    print("• OVERHEAD SUPPLY: Previous buyers selling at breakeven")
    print("• FAKE MOVES: Algorithms test levels without real intent")
    print()
    print("True Breakout Characteristics:")
    print("• High volume (1.5x+ average)")
    print("• Clean break above resistance (+2%)")
    print("• Strong close (top 50% of candle)")
    print("• All three signals must align")