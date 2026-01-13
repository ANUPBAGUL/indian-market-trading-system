import pandas as pd
import numpy as np
from src.sector_momentum_agent import SectorMomentumAgent

def create_sector_data():
    """Create sector data with different momentum characteristics"""
    dates = pd.date_range('2024-01-01', periods=30)
    
    sectors_data = []
    
    # Technology - Strong momentum
    tech_base = 300.0
    for i, date in enumerate(dates):
        tech_base *= (1 + np.random.normal(0.002, 0.01))  # +0.2% daily trend
        breadth = 75 + np.random.normal(5, 10) if i > 15 else 60 + np.random.normal(0, 5)  # Improving breadth
        rvol = 1.4 + np.random.normal(0, 0.2)  # High activity
        
        sectors_data.append({
            'date': date,
            'sector': 'Technology',
            'sector_close': tech_base,
            'sector_volume': 500000000,
            'sector_breadth': max(0, min(100, breadth)),
            'sector_rvol': max(0.5, rvol)
        })
    
    # Healthcare - Moderate momentum
    health_base = 250.0
    for i, date in enumerate(dates):
        health_base *= (1 + np.random.normal(0.001, 0.008))  # +0.1% daily trend
        breadth = 55 + np.random.normal(0, 8)  # Stable breadth
        rvol = 1.1 + np.random.normal(0, 0.15)  # Moderate activity
        
        sectors_data.append({
            'date': date,
            'sector': 'Healthcare',
            'sector_close': health_base,
            'sector_volume': 300000000,
            'sector_breadth': max(0, min(100, breadth)),
            'sector_rvol': max(0.5, rvol)
        })
    
    # Energy - Weak momentum
    energy_base = 180.0
    for i, date in enumerate(dates):
        energy_base *= (1 + np.random.normal(-0.001, 0.012))  # -0.1% daily trend
        breadth = 35 + np.random.normal(-2, 8) if i > 15 else 45 + np.random.normal(0, 5)  # Declining breadth
        rvol = 0.9 + np.random.normal(0, 0.1)  # Low activity
        
        sectors_data.append({
            'date': date,
            'sector': 'Energy',
            'sector_close': energy_base,
            'sector_volume': 200000000,
            'sector_breadth': max(0, min(100, breadth)),
            'sector_rvol': max(0.5, rvol)
        })
    
    return pd.DataFrame(sectors_data)

def create_index_data():
    """Create market index data"""
    dates = pd.date_range('2024-01-01', periods=30)
    
    index_data = []
    index_price = 4000.0
    
    for date in dates:
        index_price *= (1 + np.random.normal(0.0005, 0.01))  # Modest uptrend
        
        index_data.append({
            'date': date,
            'close': index_price,
            'volume': 2000000000
        })
    
    return pd.DataFrame(index_data)

if __name__ == "__main__":
    # Create test data
    sector_data = create_sector_data()
    index_data = create_index_data()
    
    # Run sector momentum analysis
    print("Sector Momentum Analysis:")
    print("=" * 50)
    
    results = SectorMomentumAgent.run(sector_data, index_data)
    
    # Sort sectors by score
    sorted_sectors = sorted(results.items(), key=lambda x: x[1].sector_score, reverse=True)
    
    for sector, metrics in sorted_sectors:
        print(f"\\n{sector}:")
        print(f"  Sector Score:           {metrics.sector_score}/100")
        print(f"  Relative Performance:   {metrics.relative_performance:+.1%}")
        print(f"  Breadth Score:          {metrics.breadth_score:.2f}")
        print(f"  RVOL Score:             {metrics.rvol_score:.2f}")
        
        # Interpretation
        if metrics.sector_score >= 75:
            interpretation = "STRONG momentum - Leading sector"
        elif metrics.sector_score >= 50:
            interpretation = "MODERATE momentum - Consider rotation"
        elif metrics.sector_score >= 25:
            interpretation = "WEAK momentum - Underperforming"
        else:
            interpretation = "POOR momentum - Avoid sector"
        
        print(f"  Interpretation:         {interpretation}")
    
    print("\\n" + "=" * 50)
    print("Why Sectors Move Before Stocks:")
    print("=" * 50)
    print("• INSTITUTIONAL FLOW: Large funds rotate billions between sectors")
    print("• ETF ARBITRAGE: Sector ETFs create sector-wide buying/selling")
    print("• THEMATIC INVESTING: Investors chase sector narratives (AI, green energy)")
    print("• RISK ROTATION: Flight to safety/growth drives sector preferences")
    print("• MACRO FACTORS: Interest rates, commodities affect entire sectors")
    print()
    print("Individual stocks follow sector momentum because:")
    print("• Sector ETF flows lift/sink all sector components")
    print("• Relative valuation drives stock selection within sectors")
    print("• Sector sentiment creates halo effects")
    print()
    
    print("How This Improves Continuation:")
    print("=" * 35)
    print("• EARLY DETECTION: Sector momentum precedes individual stock moves")
    print("• FLOW CONFIRMATION: High RVOL confirms institutional participation")
    print("• BREADTH VALIDATION: Strong breadth indicates broad-based moves")
    print("• RELATIVE STRENGTH: Outperforming sectors attract more capital")
    print()
    print("Trading Application:")
    print("• Focus breakouts in high-scoring sectors (75+ score)")
    print("• Avoid breakouts in low-scoring sectors (<25 score)")
    print("• Rotate positions toward leading sectors")
    print("• Use sector scores to filter stock universe")
    
    print("\\n" + "=" * 50)
    print("Sector Scoring Breakdown:")
    print("=" * 50)
    print("Relative Performance (40% weight):")
    print("  >5% outperformance  = 40 points")
    print("  >2% outperformance  = 30 points")
    print("  >0% outperformance  = 20 points")
    print("  Minor underperform  = 10 points")
    print("  Major underperform  =  0 points")
    print()
    print("Breadth Score (35% weight):")
    print("  Based on % stocks above SMA20")
    print("  Includes breadth trend component")
    print("  Max 35 points")
    print()
    print("RVOL Score (25% weight):")
    print("  >=1.5x RVOL = 25 points (high activity)")
    print("  >=1.2x RVOL = 18 points (elevated)")
    print("  >=1.0x RVOL = 13 points (normal)")
    print("  <1.0x RVOL =  5 points (low)")
    
    # Show current sector breadth and RVOL
    print("\\n" + "=" * 50)
    print("Current Sector Metrics:")
    print("=" * 50)
    
    latest_data = sector_data.groupby('sector').tail(1)
    for _, row in latest_data.iterrows():
        print(f"{row['sector']}:")
        print(f"  Current Breadth: {row['sector_breadth']:.1f}%")
        print(f"  Current RVOL:    {row['sector_rvol']:.2f}x")
        print(f"  Price Level:     ${row['sector_close']:.0f}")
        print()