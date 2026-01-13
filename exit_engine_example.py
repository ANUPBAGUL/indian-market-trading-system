"""
Exit Engine Examples - Demonstrates ATR stop evolution across different scenarios.
"""

import sys
sys.path.append('src')
import pandas as pd
from exit_engine import ExitEngine


def main():
    print("=== ATR EXIT ENGINE EXAMPLES ===\n")
    
    # Example 1: New Position (Initial Stop)
    print("1. NEW POSITION - INITIAL STOP SETTING")
    exit_info = ExitEngine.update(
        current_price=50.00,
        entry_price=50.00,
        current_atr=2.00,
        sma20=49.50,
        existing_stop=None,  # New position
        position_age_days=0
    )
    
    print(f"   Entry: $50.00, Current: $50.00, ATR: $2.00")
    print(f"   Initial Stop: ${exit_info['stop_price']}")
    print(f"   K-Factor: {exit_info['k_factor']}x ({exit_info['trend_strength']} trend)")
    print(f"   ATR Distance: ${exit_info['atr_distance']}")
    print(f"   -> Protective stop set at entry\n")
    
    # Example 2: Profitable Position (Trailing Stop)
    print("2. PROFITABLE POSITION - TRAILING STOP")
    exit_info = ExitEngine.update(
        current_price=55.00,
        entry_price=50.00,
        current_atr=2.20,
        sma20=52.00,
        existing_stop=46.00,  # Previous stop
        position_age_days=8
    )
    
    print(f"   Entry: $50.00, Current: $55.00, ATR: $2.20")
    print(f"   Previous Stop: $46.00 -> New Stop: ${exit_info['stop_price']}")
    print(f"   K-Factor: {exit_info['k_factor']}x ({exit_info['trend_strength']} trend)")
    print(f"   P&L: {exit_info['profit_loss_pct']}%")
    print(f"   Stop Type: {exit_info['stop_type']}")
    print(f"   -> Stop trails higher with price\n")
    
    # Example 3: Strong Trend (Wide Stops)
    print("3. STRONG TREND - WIDE STOPS")
    exit_info = ExitEngine.update(
        current_price=60.00,
        entry_price=50.00,
        current_atr=2.50,
        sma20=56.00,  # Price well above SMA
        existing_stop=52.50,
        position_age_days=15
    )
    
    print(f"   Entry: $50.00, Current: $60.00, ATR: $2.50")
    print(f"   Price vs SMA20: $60.00 vs $56.00 (strong trend)")
    print(f"   Previous Stop: $52.50 -> New Stop: ${exit_info['stop_price']}")
    print(f"   K-Factor: {exit_info['k_factor']}x (wide for strong trend)")
    print(f"   P&L: {exit_info['profit_loss_pct']}%")
    print(f"   -> Wide stops allow trend to continue\n")
    
    # Example 4: Weak Trend (Tight Stops)
    print("4. WEAK TREND - TIGHT STOPS")
    exit_info = ExitEngine.update(
        current_price=51.00,
        entry_price=50.00,
        current_atr=1.80,
        sma20=50.80,  # Price near SMA
        existing_stop=48.00,
        position_age_days=3
    )
    
    print(f"   Entry: $50.00, Current: $51.00, ATR: $1.80")
    print(f"   Price vs SMA20: $51.00 vs $50.80 (weak trend)")
    print(f"   Previous Stop: $48.00 -> New Stop: ${exit_info['stop_price']}")
    print(f"   K-Factor: {exit_info['k_factor']}x (tight for weak trend)")
    print(f"   P&L: {exit_info['profit_loss_pct']}%")
    print(f"   -> Tight stops protect against reversal\n")
    
    # Example 5: Stop Evolution Timeline
    print("5. STOP EVOLUTION TIMELINE")
    print("   Tracking one position over 15 days:")
    print("   Day | Price | ATR  | SMA20 | Stop  | K-Factor | Trend")
    print("   ----|-------|------|-------|-------|----------|--------")
    
    timeline_data = [
        {'day': 1, 'price': 50.00, 'atr': 2.00, 'sma20': 49.50, 'prev_stop': None},
        {'day': 3, 'price': 52.00, 'atr': 2.10, 'sma20': 50.20, 'prev_stop': 46.00},
        {'day': 5, 'price': 54.50, 'atr': 2.20, 'sma20': 51.00, 'prev_stop': 47.80},
        {'day': 8, 'price': 57.00, 'atr': 2.40, 'sma20': 52.50, 'prev_stop': 50.10},
        {'day': 12, 'price': 59.50, 'atr': 2.60, 'sma20': 54.80, 'prev_stop': 52.20},
        {'day': 15, 'price': 61.00, 'atr': 2.50, 'sma20': 56.20, 'prev_stop': 54.00},
    ]
    
    entry_price = 50.00
    for data in timeline_data:
        exit_info = ExitEngine.update(
            current_price=data['price'],
            entry_price=entry_price,
            current_atr=data['atr'],
            sma20=data['sma20'],
            existing_stop=data['prev_stop'],
            position_age_days=data['day']
        )
        
        print(f"   {data['day']:>3} | ${data['price']:>5.2f} | ${data['atr']:>4.2f} | "
              f"${data['sma20']:>5.2f} | ${exit_info['stop_price']:>5.2f} | "
              f"{exit_info['k_factor']:>6.1f}x | {exit_info['trend_strength']:>6}")
    
    print("   -> Stops trail higher as trend strengthens\n")
    
    # Example 6: Batch Processing
    print("6. BATCH PROCESSING EXAMPLE")
    batch_data = pd.DataFrame({
        'symbol': ['AAPL', 'GOOGL', 'TSLA', 'MSFT'],
        'current_price': [155.00, 2650.00, 220.00, 310.00],
        'entry_price': [150.00, 2500.00, 200.00, 300.00],
        'current_atr': [3.50, 50.00, 15.00, 8.00],
        'sma20': [152.00, 2580.00, 205.00, 308.00],
        'existing_stop': [147.00, 2450.00, 185.00, 294.00],
        'position_age_days': [5, 12, 3, 8]
    })
    
    results = ExitEngine.batch_update(batch_data)
    
    display_cols = ['symbol', 'current_price', 'stop_price', 'k_factor', 'trend_strength', 'profit_loss_pct']
    print(results[display_cols].to_string(index=False, float_format='%.2f'))
    print()
    
    # Example 7: Stop-Out Detection
    print("7. STOP-OUT DETECTION")
    scenarios = [
        {'name': 'Safe Position', 'price': 52.00, 'stop': 48.00, 'stopped': False},
        {'name': 'At Stop Level', 'price': 48.00, 'stop': 48.00, 'stopped': True},
        {'name': 'Below Stop', 'price': 47.50, 'stop': 48.00, 'stopped': True},
    ]
    
    for scenario in scenarios:
        is_stopped = ExitEngine.is_stopped_out(scenario['price'], scenario['stop'])
        status = "STOPPED OUT" if is_stopped else "HOLDING"
        print(f"   {scenario['name']:<15}: Price ${scenario['price']:>5.2f}, "
              f"Stop ${scenario['stop']:>5.2f} -> {status}")
    
    print(f"   -> Positions exit when price <= stop level")


if __name__ == "__main__":
    main()