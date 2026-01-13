"""
Position Sizing Examples - Demonstrates hybrid sizing across different scenarios.
"""

import sys
sys.path.append('src')
import pandas as pd
from position_sizer import PositionSizer


def main():
    print("=== HYBRID POSITION SIZING EXAMPLES ===\n")
    
    account_value = 100000  # $100k account
    
    # Example 1: High Confidence, Low Volatility
    print("1. HIGH CONFIDENCE, LOW VOLATILITY")
    size_info = PositionSizer.position_size(
        account_value=account_value,
        entry_price=50.0,
        atr=1.5,           # Low volatility
        confidence_score=87.5,  # High confidence
        daily_volatility=0.025  # 2.5% daily vol
    )
    
    print(f"   Entry: $50.00, ATR: $1.50, Confidence: 87.5%")
    print(f"   Position Size: {size_info['position_size']} shares")
    print(f"   Stop Price: ${size_info['stop_price']}")
    print(f"   Risk Amount: ${size_info['risk_amount']}")
    print(f"   Participation: {size_info['participation_rate']*100:.0f}%")
    print(f"   -> Large position due to high confidence + low volatility\n")
    
    # Example 2: Medium Confidence, High Volatility  
    print("2. MEDIUM CONFIDENCE, HIGH VOLATILITY")
    size_info = PositionSizer.position_size(
        account_value=account_value,
        entry_price=75.0,
        atr=4.5,           # High volatility
        confidence_score=68.2,  # Medium confidence
        daily_volatility=0.08   # 8% daily vol
    )
    
    print(f"   Entry: $75.00, ATR: $4.50, Confidence: 68.2%")
    print(f"   Position Size: {size_info['position_size']} shares")
    print(f"   Stop Price: ${size_info['stop_price']}")
    print(f"   Risk Amount: ${size_info['risk_amount']}")
    print(f"   Participation: {size_info['participation_rate']*100:.0f}%")
    print(f"   Volatility Adj: {size_info['volatility_adjustment']:.2f}x")
    print(f"   -> Small position due to medium confidence + high volatility\n")
    
    # Example 3: Low Confidence (No Trade)
    print("3. LOW CONFIDENCE (NO TRADE)")
    size_info = PositionSizer.position_size(
        account_value=account_value,
        entry_price=25.0,
        atr=1.2,
        confidence_score=55.0,  # Below threshold
        daily_volatility=0.03
    )
    
    print(f"   Entry: $25.00, ATR: $1.20, Confidence: 55.0%")
    print(f"   Position Size: {size_info['position_size']} shares")
    print(f"   Reason: {size_info['reason']}")
    print(f"   -> No trade due to insufficient confidence\n")
    
    # Example 4: Confidence Scaling Demonstration
    print("4. CONFIDENCE SCALING DEMONSTRATION")
    confidence_levels = [62, 68, 73, 78, 83, 88]
    
    print("   Same stock, different confidence levels:")
    print("   Confidence | Participation | Position Size")
    print("   -----------|---------------|---------------")
    
    for conf in confidence_levels:
        size_info = PositionSizer.position_size(
            account_value=account_value,
            entry_price=40.0,
            atr=2.0,
            confidence_score=conf
        )
        
        print(f"   {conf:>8}%   |    {size_info['participation_rate']*100:>6.0f}%    |    {size_info['position_size']:>6} shares")
    
    print()
    
    # Example 5: Batch Processing
    print("5. BATCH PROCESSING EXAMPLE")
    batch_data = pd.DataFrame({
        'symbol': ['AAPL', 'GOOGL', 'TSLA', 'MSFT'],
        'entry_price': [150.0, 2500.0, 200.0, 300.0],
        'atr': [3.5, 45.0, 12.0, 8.0],
        'confidence_score': [85.2, 72.1, 45.8, 89.3],
        'daily_volatility': [0.035, 0.028, 0.095, 0.025]
    })
    
    results = PositionSizer.batch_size(batch_data, account_value)
    
    display_cols = ['symbol', 'confidence_score', 'position_size', 'risk_amount', 'participation_rate']
    print(results[display_cols].to_string(index=False, float_format='%.1f'))
    print()
    
    # Example 6: Risk Consistency Check
    print("6. RISK CONSISTENCY CHECK")
    print("   Verifying consistent dollar risk across different scenarios:")
    
    scenarios = [
        {'name': 'Low Price/Low ATR', 'price': 20.0, 'atr': 0.8, 'conf': 80},
        {'name': 'High Price/High ATR', 'price': 200.0, 'atr': 8.0, 'conf': 80},
        {'name': 'Medium Price/Medium ATR', 'price': 100.0, 'atr': 4.0, 'conf': 80}
    ]
    
    for scenario in scenarios:
        size_info = PositionSizer.position_size(
            account_value=account_value,
            entry_price=scenario['price'],
            atr=scenario['atr'],
            confidence_score=scenario['conf']
        )
        
        print(f"   {scenario['name']:<20}: ${size_info['risk_amount']:>6.0f} risk")
    
    print(f"   -> All scenarios target same ${account_value * 0.01 * 0.85:.0f} risk (1% * 85% participation)")


if __name__ == "__main__":
    main()