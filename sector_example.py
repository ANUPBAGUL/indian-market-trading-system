import pandas as pd
import numpy as np
from src.features import FeatureComputer
from src.sector_aggregator import SectorAggregator

# Create multi-sector sample data for one trading day
np.random.seed(42)

# Define sectors and representative stocks
sectors_data = {
    'Technology': [
        {'symbol': 'AAPL', 'close': 186.75, 'volume': 45000000},
        {'symbol': 'MSFT', 'close': 387.45, 'volume': 28000000},
        {'symbol': 'GOOGL', 'close': 2668.90, 'volume': 1200000},
        {'symbol': 'NVDA', 'close': 722.48, 'volume': 35000000}
    ],
    'Healthcare': [
        {'symbol': 'JNJ', 'close': 158.32, 'volume': 8500000},
        {'symbol': 'PFE', 'close': 28.45, 'volume': 42000000},
        {'symbol': 'UNH', 'close': 524.67, 'volume': 2800000}
    ],
    'Financial': [
        {'symbol': 'JPM', 'close': 168.55, 'volume': 12000000},
        {'symbol': 'BAC', 'close': 33.21, 'volume': 38000000},
        {'symbol': 'WFC', 'close': 42.88, 'volume': 22000000}
    ]
}

# Generate extended historical data (60 days) for feature computation
def create_extended_data():
    all_data = []
    dates = pd.date_range('2024-01-01', periods=60)
    
    for sector, stocks in sectors_data.items():
        for stock in stocks:
            base_price = stock['close']
            base_volume = stock['volume']
            
            for i, date in enumerate(dates):
                # Simulate price evolution
                price_change = np.random.normal(0, 0.02)  # 2% daily volatility
                current_price = base_price * (1 + price_change * (i + 1) / 60)
                
                # Generate OHLC
                open_price = current_price * (1 + np.random.normal(0, 0.005))
                high_price = current_price * (1 + abs(np.random.normal(0.01, 0.005)))
                low_price = current_price * (1 - abs(np.random.normal(0.01, 0.005)))
                
                # Volume with some variation
                volume = int(base_volume * (1 + np.random.normal(0, 0.3)))
                
                all_data.append({
                    'symbol': stock['symbol'],
                    'date': date,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': current_price,
                    'volume': max(volume, 100000),  # Minimum volume
                    'sector': sector
                })
    
    return pd.DataFrame(all_data)

if __name__ == "__main__":
    # Create extended dataset
    stock_data = create_extended_data()
    
    # Compute features for all stocks
    print("Computing features for all stocks...")
    features_data = FeatureComputer.compute_all(stock_data)
    
    # Aggregate to sector level
    print("Aggregating to sector level...")
    sector_df = SectorAggregator.aggregate_sectors(features_data)
    
    # Show sector stats for the last trading day
    last_date = sector_df['date'].max().strftime('%Y-%m-%d')
    sector_stats = SectorAggregator.get_sector_stats(sector_df, last_date)
    
    print(f"\nSector Statistics for {last_date}:")
    print("=" * 80)
    
    for _, sector in sector_stats.iterrows():
        print(f"Sector: {sector['sector']}")
        print(f"  Close: ${sector['sector_close']:.2f}")
        print(f"  Volume: {sector['sector_volume']:,}")
        print(f"  RVOL: {sector['sector_rvol']:.2f}x")
        print(f"  Breadth: {sector['sector_breadth']:.1f}% above SMA20")
        print(f"  Stock Count: {sector['stock_count']}")
        print()
    
    # Show sector breadth trend over last 10 days
    print("Sector Breadth Trend (Last 10 Days):")
    print("=" * 50)
    
    recent_dates = sorted(sector_df['date'].unique())[-10:]
    breadth_data = []
    
    for date in recent_dates:
        day_stats = SectorAggregator.get_sector_stats(sector_df, date.strftime('%Y-%m-%d'))
        breadth_summary = {
            'date': date.strftime('%Y-%m-%d'),
            'tech_breadth': day_stats[day_stats['sector'] == 'Technology']['sector_breadth'].iloc[0] if len(day_stats[day_stats['sector'] == 'Technology']) > 0 else 0,
            'health_breadth': day_stats[day_stats['sector'] == 'Healthcare']['sector_breadth'].iloc[0] if len(day_stats[day_stats['sector'] == 'Healthcare']) > 0 else 0,
            'finance_breadth': day_stats[day_stats['sector'] == 'Financial']['sector_breadth'].iloc[0] if len(day_stats[day_stats['sector'] == 'Financial']) > 0 else 0
        }
        breadth_data.append(breadth_summary)
    
    breadth_df = pd.DataFrame(breadth_data)
    print(breadth_df.to_string(index=False))