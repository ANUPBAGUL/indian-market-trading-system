import pandas as pd
import numpy as np
from src.features import FeatureComputer
from src.accumulation_agent import AccumulationAgent

def create_perfect_accumulation():
    """Create textbook accumulation pattern"""
    dates = pd.date_range('2024-01-01', periods=60)
    
    data = []
    
    for i, date in enumerate(dates):
        if i < 20:
            # Pre-accumulation: normal volatility, normal volume
            close = 500 + np.random.normal(0, 10)
            high = close + np.random.uniform(3, 8)
            low = close - np.random.uniform(3, 8)
            volume = 30000000 + np.random.normal(0, 5000000)
        elif i < 50:
            # Accumulation phase: tight range, high volume
            close = 500 + np.random.normal(0, 2)  # Very tight price range
            high = close + np.random.uniform(0.5, 2)  # Small intraday ranges
            low = close - np.random.uniform(0.5, 2)
            volume = 60000000 + np.random.normal(0, 10000000)  # 2x normal volume
        else:
            # Post-accumulation: expanding range
            close = 500 + (i - 50) * 2 + np.random.normal(0, 3)  # Slight uptrend
            high = close + np.random.uniform(2, 5)
            low = close - np.random.uniform(2, 5)
            volume = 35000000 + np.random.normal(0, 8000000)
        
        open_price = close + np.random.normal(0, 1)
        
        data.append({
            'symbol': 'PERFECT',
            'date': date,
            'open': max(open_price, 1),
            'high': max(high, close),
            'low': min(low, close),
            'close': max(close, 1),
            'volume': max(int(volume), 1000000),
            'sector': 'Technology'
        })
    
    return pd.DataFrame(data)

def create_outperforming_sector():
    """Create sector that underperforms the stock"""
    dates = pd.date_range('2024-01-01', periods=60)
    
    data = []
    sector_price = 300.0
    
    for i, date in enumerate(dates):
        # Sector declines slightly while stock accumulates
        if i < 50:
            sector_price *= (1 + np.random.normal(-0.001, 0.01))  # Slight decline
        else:
            sector_price *= (1 + np.random.normal(0.0005, 0.01))  # Slight recovery
        
        data.append({
            'date': date,
            'sector': 'Technology',
            'sector_close': sector_price,
            'sector_volume': 500000000,
            'sector_rvol': 1.0,
            'sector_breadth': 50.0
        })
    
    return pd.DataFrame(data)

if __name__ == "__main__":
    # Create perfect accumulation scenario
    stock_data = create_perfect_accumulation()
    sector_data = create_outperforming_sector()
    
    # Compute features
    print("Computing technical features...")
    stock_with_features = FeatureComputer.compute_all(stock_data)
    
    # Run accumulation analysis
    print("Running accumulation analysis...")
    result = AccumulationAgent.run(stock_with_features, sector_data)
    
    # Display results
    print("\\nPERFECT Accumulation Analysis:")
    print("=" * 50)
    print(f"Accumulation Score: {result['accumulation_score']}/100")
    print()
    
    print("Evidence Flags:")
    evidence = result['evidence']
    print(f"  Volume Absorption:      {'YES' if evidence.volume_absorption else 'NO'}")
    print(f"  Volatility Compression: {'YES' if evidence.volatility_compression else 'NO'}")
    print(f"  Tight Base:             {'YES' if evidence.tight_base else 'NO'}")
    print(f"  Relative Strength:      {'YES' if evidence.relative_strength else 'NO'}")
    print()
    
    print("Detailed Metrics:")
    metrics = result['metrics']
    print(f"  Volume Ratio:           {metrics['volume_ratio']:.2f}x")
    print(f"  Compression Ratio:      {metrics['compression_ratio']:.2f}")
    print(f"  Range Percentage:       {metrics['range_percentage']:.1%}")
    print(f"  Relative Performance:   {metrics['relative_performance']:+.1%}")
    print()
    
    # Show what accumulation looks like
    print("What Real Accumulation Looks Like:")
    print("=" * 40)
    print("BEFORE (Days 10-20): Normal trading")
    before_period = stock_with_features.iloc[10:20]
    avg_volume_before = before_period['volume'].mean()
    avg_range_before = ((before_period['high'] - before_period['low']) / before_period['close']).mean()
    print(f"  Average Volume: {avg_volume_before:,.0f}")
    print(f"  Average Range:  {avg_range_before:.1%}")
    print()
    
    print("DURING (Days 30-40): Accumulation phase")
    during_period = stock_with_features.iloc[30:40]
    avg_volume_during = during_period['volume'].mean()
    avg_range_during = ((during_period['high'] - during_period['low']) / during_period['close']).mean()
    print(f"  Average Volume: {avg_volume_during:,.0f} ({avg_volume_during/avg_volume_before:.1f}x)")
    print(f"  Average Range:  {avg_range_during:.1%} ({avg_range_during/avg_range_before:.1f}x)")
    print(f"  Price Movement: Tight ${during_period['close'].min():.0f}-${during_period['close'].max():.0f}")
    print()
    
    print("AFTER (Days 50-60): Post-accumulation")
    after_period = stock_with_features.iloc[50:60]
    avg_volume_after = after_period['volume'].mean()
    avg_range_after = ((after_period['high'] - after_period['low']) / after_period['close']).mean()
    price_change = (after_period['close'].iloc[-1] / during_period['close'].mean() - 1) * 100
    print(f"  Average Volume: {avg_volume_after:,.0f}")
    print(f"  Average Range:  {avg_range_after:.1%}")
    print(f"  Price Change:   {price_change:+.1f}% from accumulation base")
    print()
    
    # Explain what this means
    print("Why This Is Probabilistic, Not Predictive:")
    print("=" * 45)
    print("• Accumulation suggests institutional interest, not guaranteed success")
    print("• Many accumulation patterns fail to break out")
    print("• Market conditions can override individual stock patterns")
    print("• False positives occur when retail mimics institutional behavior")
    print("• Score indicates probability, not certainty of future moves")
    print()
    
    print("What Accumulation Looks Like in Real Markets:")
    print("=" * 50)
    print("• VOLUME ABSORPTION: Stock absorbs heavy selling without declining")
    print("• VOLATILITY COMPRESSION: Daily ranges shrink as supply dries up")
    print("• TIGHT BASE: Price holds near recent highs despite time passage")
    print("• RELATIVE STRENGTH: Outperforms sector during market weakness")
    print()
    print("Real Examples: AAPL (2019), TSLA (2020), NVDA (2023)")
    print("All showed months of accumulation before major breakouts")