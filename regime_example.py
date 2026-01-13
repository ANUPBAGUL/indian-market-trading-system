import pandas as pd
import numpy as np
from src.regime_detector import RegimeDetector

def create_market_index_data():
    """Create simulated market index data with different regime periods"""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=200, freq='D')
    
    # Simulate different market phases
    data = []
    base_price = 4000  # SPY-like starting price
    
    for i, date in enumerate(dates):
        # Create different regime periods
        if i < 50:  # Bull market (risk_on)
            trend = 0.0008  # Strong upward trend
            volatility = 0.012
        elif i < 100:  # Correction (risk_off)
            trend = -0.0015  # Downward trend
            volatility = 0.025
        elif i < 150:  # Recovery (risk_on)
            trend = 0.0012  # Strong recovery
            volatility = 0.015
        else:  # Sideways (neutral)
            trend = 0.0002  # Minimal trend
            volatility = 0.010
        
        # Generate price with trend and noise
        daily_return = trend + np.random.normal(0, volatility)
        base_price *= (1 + daily_return)
        
        # Generate OHLC
        open_price = base_price * (1 + np.random.normal(0, 0.002))
        high_price = base_price * (1 + abs(np.random.normal(0.005, 0.003)))
        low_price = base_price * (1 - abs(np.random.normal(0.005, 0.003)))
        close_price = base_price
        
        data.append({
            'date': date,
            'symbol': 'SPY',
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': int(50000000 * (1 + np.random.normal(0, 0.3)))
        })
    
    return pd.DataFrame(data)

if __name__ == "__main__":
    # Create market index data
    index_data = create_market_index_data()
    
    # Detect regimes
    regime_data = RegimeDetector.detect_regime(index_data)
    
    # Show regime transitions over time
    print("Market Regime Detection Results:")
    print("=" * 60)
    
    # Display sample periods
    sample_periods = [
        (30, 40, "Bull Market Period"),
        (70, 80, "Correction Period"), 
        (120, 130, "Recovery Period"),
        (170, 180, "Sideways Period")
    ]
    
    for start, end, period_name in sample_periods:
        print(f"\n{period_name} (Days {start}-{end}):")
        period_data = regime_data.iloc[start:end+1]
        
        for _, row in period_data.iterrows():
            if not pd.isna(row['trend_slope']):
                print(f"  {row['date'].strftime('%Y-%m-%d')}: "
                      f"Close=${row['close']:.0f}, "
                      f"SMA50=${row['index_sma50']:.0f}, "
                      f"Slope={row['trend_slope']:.3f}, "
                      f"Regime={row['regime']}")
    
    # Regime distribution
    print(f"\nRegime Distribution (Last 100 Days):")
    print("=" * 40)
    recent_regimes = regime_data.tail(100)['regime'].value_counts()
    for regime, count in recent_regimes.items():
        percentage = (count / len(recent_regimes)) * 100
        print(f"{regime}: {count} days ({percentage:.1f}%)")
    
    # Show regime transitions
    print(f"\nRegime Transitions:")
    print("=" * 30)
    regime_changes = []
    prev_regime = None
    
    for _, row in regime_data.iterrows():
        current_regime = row['regime']
        if prev_regime and prev_regime != current_regime:
            regime_changes.append({
                'date': row['date'],
                'from': prev_regime,
                'to': current_regime,
                'price': row['close']
            })
        prev_regime = current_regime
    
    # Show last 10 regime changes
    for change in regime_changes[-10:]:
        print(f"{change['date'].strftime('%Y-%m-%d')}: "
              f"{change['from']} -> {change['to']} "
              f"(Price: ${change['price']:.0f})")
    
    # Performance by regime
    print(f"\nPrice Performance by Regime:")
    print("=" * 35)
    
    for regime in ['risk_on', 'neutral', 'risk_off']:
        regime_data_subset = regime_data[regime_data['regime'] == regime]
        if len(regime_data_subset) > 1:
            start_price = regime_data_subset['close'].iloc[0]
            end_price = regime_data_subset['close'].iloc[-1]
            performance = ((end_price / start_price) - 1) * 100
            avg_slope = regime_data_subset['trend_slope'].mean()
            
            print(f"{regime}: {performance:+.1f}% return, "
                  f"avg slope: {avg_slope:.4f}")