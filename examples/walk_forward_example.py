"""
Walk-Forward Testing Example - Demonstrates robustness validation.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.walk_forward_tester import WalkForwardTester


def create_sample_data():
    """Create sample market data for walk-forward testing."""
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
    
    data = []
    for date in dates:
        for symbol in symbols:
            # Simulate realistic price movements
            base_price = {'AAPL': 150, 'MSFT': 250, 'GOOGL': 2800, 'TSLA': 200, 'AMZN': 3200}[symbol]
            
            # Add trend and noise
            days_from_start = (date - dates[0]).days
            trend = 1 + (days_from_start * 0.0002)  # Slight upward trend
            noise = np.random.normal(1, 0.02)  # 2% daily volatility
            
            price = base_price * trend * noise
            
            data.append({
                'symbol': symbol,
                'date': date.strftime('%Y-%m-%d'),
                'open': price * 0.99,
                'high': price * 1.02,
                'low': price * 0.98,
                'close': price,
                'volume': np.random.randint(500000, 2000000),
                'sector': 'Technology'
            })
    
    return pd.DataFrame(data)


def main():
    """Demonstrate walk-forward testing."""
    print("=== WALK-FORWARD ROBUSTNESS TESTING ===\n")
    
    # Create sample data
    print("Generating sample market data...")
    data = create_sample_data()
    print(f"Created data: {len(data)} records, {data['date'].min()} to {data['date'].max()}\n")
    
    # Initialize walk-forward tester
    # 6-month train, 2-month test, 1-month steps
    tester = WalkForwardTester(
        train_days=180,  # 6 months training
        test_days=60,    # 2 months testing  
        step_days=30     # 1 month steps
    )
    
    # Define frozen parameters (no re-optimization allowed)
    frozen_params = {
        'max_positions': 5,
        'sector_limit': 0.4,
        'confidence_threshold': 65,
        'risk_per_trade': 0.01,
        'atr_multiplier': 2.0
    }
    
    print("FROZEN PARAMETERS (No Re-optimization):")
    for param, value in frozen_params.items():
        print(f"  {param}: {value}")
    print()
    
    # Run walk-forward testing
    print("Running walk-forward testing...")
    results = tester.run_walk_forward(
        data=data,
        start_date='2021-01-01',
        end_date='2023-06-30',
        frozen_params=frozen_params
    )
    
    # Display results
    print(f"Completed {results['total_windows']} windows\n")
    
    # Show individual window results
    print("INDIVIDUAL WINDOW RESULTS:")
    print("Window | Test Period        | Trades | Expectancy | Win Rate | Max DD")
    print("-------|--------------------|---------|-----------|---------|---------")
    
    for window in results['window_results'][:10]:  # Show first 10 windows
        kpis = window['kpis']
        print(f"{window['window_id']:6} | {window['test_start']} to {window['test_end'][:7]} | "
              f"{window['trades_count']:7} | ${kpis['expectancy']:8.2f} | "
              f"{kpis['win_rate_pct']:6.1f}% | {kpis['max_drawdown_pct']:6.1f}%")
    
    if len(results['window_results']) > 10:
        print(f"... and {len(results['window_results']) - 10} more windows")
    print()
    
    # Generate and display summary report
    summary_report = tester.generate_summary_report(results)
    print(summary_report)
    
    # Demonstrate overfitting detection
    print("\n" + "="*60)
    print("OVERFITTING DETECTION ANALYSIS")
    print("="*60)
    
    robust_metrics = results['robustness_metrics']
    
    print(f"\nKEY ROBUSTNESS INDICATORS:")
    print(f"• Profitable Windows: {robust_metrics['profitable_windows_pct']:.1f}%")
    print(f"  -> Good systems: >60% | Overfitted: <40%")
    
    print(f"• Expectancy Consistency: ${robust_metrics['expectancy_std']:.2f} std dev")
    print(f"  -> Robust systems: <$20 | Overfitted: >$50")
    
    print(f"• Performance Range: ${robust_metrics['expectancy_range']['min']:.2f} to ${robust_metrics['expectancy_range']['max']:.2f}")
    print(f"  -> Stable systems show smaller ranges")
    
    consistency_score = robust_metrics['consistency_score']
    print(f"\nOVERALL CONSISTENCY SCORE: {consistency_score:.1f}")
    
    if consistency_score > 50:
        verdict = "ROBUST - Low overfitting risk"
    elif consistency_score > 30:
        verdict = "MODERATE - Monitor for degradation"  
    else:
        verdict = "WEAK - High overfitting risk"
    
    print(f"VERDICT: {verdict}")
    
    print(f"\nWHY WALK-FORWARD KILLS OVERFITTING:")
    print(f"1. TEMPORAL SEPARATION: Training data never overlaps with test data")
    print(f"2. FROZEN PARAMETERS: No re-optimization on new data prevents curve-fitting")
    print(f"3. MULTIPLE PERIODS: {results['total_windows']} independent tests reveal consistency")
    print(f"4. FUTURE VALIDATION: Each test uses strictly unseen future data")
    print(f"5. PERFORMANCE VARIANCE: High variability indicates parameter instability")


if __name__ == '__main__':
    main()