"""
Confidence Decay Examples - Demonstrates systematic confidence reduction.
"""

import sys
sys.path.append('src')
import pandas as pd
from confidence_decay import ConfidenceDecay


def main():
    print("=== CONFIDENCE DECAY EXAMPLES ===\n")
    
    # Example 1: Time-Based Decay
    print("1. TIME-BASED DECAY")
    decay_info = ConfidenceDecay.decay_confidence(
        initial_confidence=80.0,
        position_age_days=18,  # Beyond grace period
        entry_price=50.0,
        current_price=52.0,
        price_5_days_ago=51.8,
        sector_performance_5d=1.5,
        market_performance_5d=1.2
    )
    
    print(f"   Initial Confidence: 80.0%")
    print(f"   Position Age: 18 days (8 days past grace period)")
    print(f"   Time Decay: {decay_info['decay_factors'].get('time_decay', 0):.1f}%")
    print(f"   Decayed Confidence: {decay_info['decayed_confidence']}%")
    print(f"   -> Aging positions lose conviction systematically\n")
    
    # Example 2: Price Stagnation Decay
    print("2. PRICE STAGNATION DECAY")
    decay_info = ConfidenceDecay.decay_confidence(
        initial_confidence=75.0,
        position_age_days=8,  # Within grace period
        entry_price=100.0,
        current_price=100.5,  # Minimal movement
        price_5_days_ago=100.2,  # <2% movement
        sector_performance_5d=0.8,
        market_performance_5d=1.0
    )
    
    print(f"   Initial Confidence: 75.0%")
    print(f"   Price Movement: $100.20 -> $100.50 (0.3% in 5 days)")
    print(f"   Stagnation Decay: {decay_info['decay_factors'].get('stagnation_decay', 0):.1f}%")
    print(f"   Decayed Confidence: {decay_info['decayed_confidence']}%")
    print(f"   -> Sideways movement reduces conviction\n")
    
    # Example 3: Sector Weakness Decay
    print("3. SECTOR WEAKNESS DECAY")
    decay_info = ConfidenceDecay.decay_confidence(
        initial_confidence=70.0,
        position_age_days=6,
        entry_price=25.0,
        current_price=26.0,
        price_5_days_ago=25.5,
        sector_performance_5d=-2.5,  # Sector weak
        market_performance_5d=0.8    # Market positive
    )
    
    print(f"   Initial Confidence: 70.0%")
    print(f"   Sector Performance: -2.5% vs Market +0.8%")
    print(f"   Relative Performance: -3.3% (sector underperforming)")
    print(f"   Sector Decay: {decay_info['decay_factors'].get('sector_decay', 0):.1f}%")
    print(f"   Decayed Confidence: {decay_info['decayed_confidence']}%")
    print(f"   -> Sector weakness impacts individual positions\n")
    
    # Example 4: Multiple Decay Factors
    print("4. MULTIPLE DECAY FACTORS")
    decay_info = ConfidenceDecay.decay_confidence(
        initial_confidence=65.0,
        position_age_days=22,  # Old position
        entry_price=75.0,
        current_price=74.5,   # Slight loss + stagnant
        price_5_days_ago=74.8,  # Minimal movement
        sector_performance_5d=-1.8,  # Weak sector
        market_performance_5d=0.5    # Positive market
    )
    
    print(f"   Initial Confidence: 65.0%")
    print(f"   Multiple Decay Factors:")
    for factor, value in decay_info['decay_factors'].items():
        print(f"     {factor.replace('_', ' ').title()}: {value:.1f}%")
    print(f"   Total Decay: {decay_info['total_decay']}%")
    print(f"   Decayed Confidence: {decay_info['decayed_confidence']}%")
    print(f"   Force Exit: {decay_info['force_exit']}")
    print(f"   -> Multiple factors compound decay effect\n")
    
    # Example 5: Trade Lifecycle Timeline
    print("5. TRADE LIFECYCLE TIMELINE")
    print("   Tracking confidence decay over 25 days:")
    print("   Day | Price | Conf | Decay Factors           | Action")
    print("   ----|-------|------|-------------------------|--------")
    
    timeline_data = [
        {'day': 1, 'price': 50.0, 'price_5d_ago': 50.0, 'sector': 0.5, 'market': 0.3},
        {'day': 5, 'price': 52.0, 'price_5d_ago': 50.0, 'sector': 1.2, 'market': 0.8},
        {'day': 10, 'price': 53.5, 'price_5d_ago': 52.0, 'sector': 0.8, 'market': 1.0},
        {'day': 15, 'price': 53.8, 'price_5d_ago': 53.5, 'sector': -0.5, 'market': 0.5},
        {'day': 20, 'price': 53.6, 'price_5d_ago': 53.8, 'sector': -1.8, 'market': 0.2},
        {'day': 25, 'price': 53.4, 'price_5d_ago': 53.6, 'sector': -2.2, 'market': 0.5},
    ]
    
    initial_confidence = 78.0
    entry_price = 50.0
    
    for data in timeline_data:
        decay_info = ConfidenceDecay.decay_confidence(
            initial_confidence=initial_confidence,
            position_age_days=data['day'],
            entry_price=entry_price,
            current_price=data['price'],
            price_5_days_ago=data['price_5d_ago'],
            sector_performance_5d=data['sector'],
            market_performance_5d=data['market']
        )
        
        # Build decay factors string
        factors = []
        for factor, value in decay_info['decay_factors'].items():
            factors.append(f"{factor.split('_')[0][:4]}:{value:.1f}")
        factors_str = ", ".join(factors) if factors else "none"
        
        action = "FORCE EXIT" if decay_info['force_exit'] else "hold"
        
        print(f"   {data['day']:>3} | ${data['price']:>5.2f} | {decay_info['decayed_confidence']:>4.1f} | "
              f"{factors_str:<23} | {action}")
    
    print("   -> Systematic decay forces disciplined exits\n")
    
    # Example 6: Batch Processing
    print("6. BATCH PROCESSING EXAMPLE")
    batch_data = pd.DataFrame({
        'symbol': ['AAPL', 'GOOGL', 'TSLA', 'MSFT'],
        'initial_confidence': [85.0, 72.0, 68.0, 79.0],
        'position_age_days': [12, 18, 25, 8],
        'entry_price': [150.0, 2500.0, 200.0, 300.0],
        'current_price': [152.0, 2480.0, 198.0, 305.0],
        'price_5_days_ago': [151.5, 2485.0, 198.2, 304.8],
        'sector_performance_5d': [0.8, -1.5, -2.8, 1.2],
        'market_performance_5d': [0.5, 0.5, 0.5, 0.5]
    })
    
    results = ConfidenceDecay.batch_decay(batch_data)
    
    display_cols = ['symbol', 'initial_confidence', 'decayed_confidence', 'total_decay', 'force_exit']
    print(results[display_cols].to_string(index=False, float_format='%.1f'))
    print()
    
    # Example 7: Force Exit Scenarios
    print("7. FORCE EXIT SCENARIOS")
    scenarios = [
        {'name': 'Healthy Position', 'confidence': 65.0, 'exit': False},
        {'name': 'Marginal Position', 'confidence': 47.0, 'exit': False},
        {'name': 'Weak Position', 'confidence': 43.0, 'exit': True},
        {'name': 'Failed Position', 'confidence': 35.0, 'exit': True},
    ]
    
    for scenario in scenarios:
        should_exit = ConfidenceDecay.should_force_exit(scenario['confidence'])
        status = "FORCE EXIT" if should_exit else "CONTINUE"
        print(f"   {scenario['name']:<17}: {scenario['confidence']:>4.1f}% confidence -> {status}")
    
    print(f"   -> Positions below {ConfidenceDecay.MIN_CONFIDENCE}% confidence are force exited")


if __name__ == "__main__":
    main()