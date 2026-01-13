import pandas as pd
import numpy as np
from src.features import FeatureComputer

# Create extended sample data for AAPL (60 days for proper feature calculation)
np.random.seed(42)
dates = pd.date_range('2024-01-01', periods=60, freq='D')

# Simulate realistic AAPL price data
base_price = 180.0
prices = []
volumes = []

for i in range(60):
    # Random walk with slight upward bias
    change = np.random.normal(0.002, 0.02)  # 0.2% daily drift, 2% volatility
    base_price *= (1 + change)
    
    # OHLC generation
    open_price = base_price * (1 + np.random.normal(0, 0.005))
    high_price = max(open_price, base_price) * (1 + abs(np.random.normal(0, 0.01)))
    low_price = min(open_price, base_price) * (1 - abs(np.random.normal(0, 0.01)))
    close_price = base_price
    
    prices.append([open_price, high_price, low_price, close_price])
    
    # Volume with some correlation to price movement
    vol_base = 45000000
    vol_multiplier = 1 + abs(change) * 2  # Higher volume on big moves
    volume = int(vol_base * vol_multiplier * (1 + np.random.normal(0, 0.3)))
    volumes.append(volume)

# Create DataFrame
sample_data = pd.DataFrame({
    'symbol': ['AAPL'] * 60,
    'date': dates,
    'open': [p[0] for p in prices],
    'high': [p[1] for p in prices],
    'low': [p[2] for p in prices],
    'close': [p[3] for p in prices],
    'volume': volumes,
    'sector': ['Technology'] * 60
})

if __name__ == "__main__":
    # Compute features
    features_df = FeatureComputer.compute_all(sample_data)
    
    # Show last 10 days with features
    display_cols = ['date', 'close', 'volume', 'atr_14', 'sma_20', 'sma_50', 'rvol_20']
    recent_data = features_df[display_cols].tail(10)
    
    print("AAPL Features (Last 10 Days):")
    print("=" * 80)
    for _, row in recent_data.iterrows():
        print(f"Date: {row['date'].strftime('%Y-%m-%d')}")
        print(f"  Close: ${row['close']:.2f}")
        print(f"  Volume: {row['volume']:,}")
        print(f"  ATR(14): ${row['atr_14']:.2f}")
        print(f"  SMA(20): ${row['sma_20']:.2f}")
        print(f"  SMA(50): ${row['sma_50']:.2f}")
        print(f"  RVOL(20): {row['rvol_20']:.2f}x")
        print()
    
    # Validation checks
    print("Validation Checks:")
    print("=" * 40)
    print(f"ATR(14) non-null from day: {features_df['atr_14'].first_valid_index() + 1}")
    print(f"SMA(20) non-null from day: {features_df['sma_20'].first_valid_index() + 1}")
    print(f"SMA(50) non-null from day: {features_df['sma_50'].first_valid_index() + 1}")
    print(f"RVOL(20) non-null from day: {features_df['rvol_20'].first_valid_index() + 1}")
    
    # Manual validation for last day
    last_day = features_df.iloc[-1]
    manual_sma20 = features_df['close'].tail(20).mean()
    print(f"\nManual SMA(20) check: {manual_sma20:.2f} vs computed: {last_day['sma_20']:.2f}")
    print(f"Match: {abs(manual_sma20 - last_day['sma_20']) < 0.01}")