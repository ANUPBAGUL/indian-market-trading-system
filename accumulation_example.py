import pandas as pd
import numpy as np
from src.features import FeatureComputer
from src.sector_aggregator import SectorAggregator
from src.accumulation_agent import AccumulationAgent

def create_accumulation_scenario():
    """Create stock data showing accumulation pattern"""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=60)
    
    # Simulate strong accumulation pattern
    data = []
    base_price = 500.0
    base_volume = 30000000
    
    for i, date in enumerate(dates):
        if i < 20:
            # Normal trading phase
            price_change = np.random.normal(0, 0.025)
            volume_mult = 1 + np.random.normal(0, 0.4)
        elif i < 50:
            # Strong accumulation phase
            price_change = np.random.normal(0.001, 0.005)  # Very low volatility
            volume_mult = 2.0 + np.random.normal(0, 0.3)  # High volume
            # Keep price in tight range around 500
            if base_price > 510:
                base_price = 508
            elif base_price < 495:
                base_price = 497
        else:
            # Post-accumulation
            price_change = np.random.normal(0.003, 0.015)
            volume_mult = 1.3 + np.random.normal(0, 0.3)
        
        # Apply price change
        base_price *= (1 + price_change)
        
        # Generate OHLC with tight ranges during accumulation
        if 20 <= i < 50:
            # Tight intraday ranges during accumulation
            open_price = base_price * (1 + np.random.normal(0, 0.001))
            high_price = base_price * (1 + abs(np.random.normal(0.002, 0.001)))
            low_price = base_price * (1 - abs(np.random.normal(0.002, 0.001)))
        else:
            open_price = base_price * (1 + np.random.normal(0, 0.003))
            high_price = base_price * (1 + abs(np.random.normal(0.008, 0.003)))
            low_price = base_price * (1 - abs(np.random.normal(0.008, 0.003)))
        
        close_price = base_price
        
        # Generate volume
        volume = int(base_volume * volume_mult)
        
        data.append({
            'symbol': 'NVDA',
            'date': date,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': max(volume, 1000000),
            'sector': 'Technology'
        })
    
    return pd.DataFrame(data)

def create_sector_data():
    """Create corresponding sector data"""
    np.random.seed(123)
    dates = pd.date_range('2024-01-01', periods=60)
    
    data = []
    sector_price = 300.0
    
    for date in dates:
        # Sector moves more slowly than individual stock
        sector_price *= (1 + np.random.normal(0.0005, 0.015))
        
        data.append({
            'date': date,
            'sector': 'Technology',
            'sector_close': sector_price,
            'sector_volume': 500000000,
            'sector_rvol': 1.0,
            'sector_breadth': 60.0
        })
    
    return pd.DataFrame(data)

if __name__ == "__main__":
    # Create test data
    stock_data = create_accumulation_scenario()
    sector_data = create_sector_data()
    
    # Compute features
    print("Computing technical features...")
    stock_with_features = FeatureComputer.compute_all(stock_data)
    
    # Run accumulation analysis
    print("Running accumulation analysis...")
    result = AccumulationAgent.run(stock_with_features, sector_data)
    
    # Display results
    print("\nNVDA Accumulation Analysis:")
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
    
    # Show recent price action
    print("Recent Price Action (Last 10 Days):")
    print("-" * 40)
    recent_data = stock_with_features.tail(10)
    
    for _, row in recent_data.iterrows():
        print(f"{row['date'].strftime('%Y-%m-%d')}: "
              f"${row['close']:.2f} "
              f"(Vol: {row['volume']:,}, "
              f"ATR: ${row['atr_14']:.2f})")
    
    # Interpretation
    print(f"\nInterpretation:")
    print("-" * 20)
    score = result['accumulation_score']
    
    if score >= 75:
        interpretation = "Strong accumulation pattern detected. Multiple evidence flags confirm institutional interest."
    elif score >= 50:
        interpretation = "Moderate accumulation signals. Some evidence of institutional activity."
    elif score >= 25:
        interpretation = "Weak accumulation signals. Limited evidence of institutional interest."
    else:
        interpretation = "No significant accumulation detected. Normal trading pattern."
    
    print(interpretation)
    
    # Show accumulation timeline
    print(f"\nAccumulation Timeline Analysis:")
    print("-" * 35)
    
    # Analyze different periods
    periods = [
        (10, 30, "Early Phase"),
        (30, 50, "Accumulation Phase"),
        (50, 60, "Late Phase")
    ]
    
    for start, end, phase_name in periods:
        if end <= len(stock_with_features):
            phase_data = stock_with_features.iloc[start:end]
            phase_result = AccumulationAgent.run(phase_data, sector_data.iloc[start:end])
            
            print(f"{phase_name}: Score {phase_result['accumulation_score']}/100")
            
            # Show which flags were active
            phase_evidence = phase_result['evidence']
            active_flags = []
            if phase_evidence.volume_absorption:
                active_flags.append("Volume")
            if phase_evidence.volatility_compression:
                active_flags.append("Compression")
            if phase_evidence.tight_base:
                active_flags.append("Base")
            if phase_evidence.relative_strength:
                active_flags.append("Strength")
            
            if active_flags:
                print(f"  Active: {', '.join(active_flags)}")
            else:
                print(f"  No significant flags")