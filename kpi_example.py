"""
KPI Computer Examples - Demonstrates performance analysis with sample data.
"""

import sys
sys.path.append('src')
from kpi_computer import KPIComputer
from backtest_engine import Trade


def create_sample_trades():
    """Create sample trades for KPI analysis."""
    trades = [
        # Winning trades
        Trade('AAPL', '2023-01-01', 150.0, '2023-01-05', 165.0, 100, 1500.0, 10.0, 'SIGNAL'),
        Trade('GOOGL', '2023-01-02', 2500.0, '2023-01-08', 2600.0, 10, 1000.0, 4.0, 'SIGNAL'),
        Trade('MSFT', '2023-01-03', 300.0, '2023-01-10', 315.0, 50, 750.0, 5.0, 'SIGNAL'),
        Trade('NVDA', '2023-01-04', 400.0, '2023-01-12', 440.0, 25, 1000.0, 10.0, 'SIGNAL'),
        
        # Losing trades
        Trade('TSLA', '2023-01-05', 200.0, '2023-01-08', 184.0, 100, -1600.0, -8.0, 'STOP'),
        Trade('META', '2023-01-06', 250.0, '2023-01-09', 235.0, 40, -600.0, -6.0, 'STOP'),
        Trade('AMZN', '2023-01-07', 100.0, '2023-01-11', 92.0, 75, -600.0, -8.0, 'STOP'),
        
        # Break-even trade
        Trade('JPM', '2023-01-08', 150.0, '2023-01-15', 150.0, 50, 0.0, 0.0, 'SIGNAL'),
    ]
    return trades


def create_sample_equity_curve():
    """Create sample equity curve for drawdown analysis."""
    return [
        {'date': '2023-01-01', 'total_value': 100000},
        {'date': '2023-01-02', 'total_value': 101500},  # +1.5%
        {'date': '2023-01-03', 'total_value': 102500},  # +2.5% (peak)
        {'date': '2023-01-04', 'total_value': 103250},  # +3.25% (new peak)
        {'date': '2023-01-05', 'total_value': 101650},  # -1.55% from peak
        {'date': '2023-01-06', 'total_value': 101050},  # -2.13% from peak
        {'date': '2023-01-07', 'total_value': 100450},  # -2.71% from peak (max DD)
        {'date': '2023-01-08', 'total_value': 100450},  # Flat
        {'date': '2023-01-09', 'total_value': 101200},  # Recovery
        {'date': '2023-01-10', 'total_value': 102700},  # Back near peak
    ]


def create_confidence_bucket_data():
    """Create sample confidence bucket data for calibration analysis."""
    return [
        # 60-65% confidence bucket
        {'confidence_bucket': '60-65', 'outcome': True},   # Win
        {'confidence_bucket': '60-65', 'outcome': False},  # Loss
        {'confidence_bucket': '60-65', 'outcome': True},   # Win
        {'confidence_bucket': '60-65', 'outcome': False},  # Loss
        {'confidence_bucket': '60-65', 'outcome': True},   # Win (3/5 = 60%)
        
        # 70-75% confidence bucket
        {'confidence_bucket': '70-75', 'outcome': True},   # Win
        {'confidence_bucket': '70-75', 'outcome': True},   # Win
        {'confidence_bucket': '70-75', 'outcome': True},   # Win
        {'confidence_bucket': '70-75', 'outcome': False},  # Loss (3/4 = 75%)
        
        # 80-85% confidence bucket
        {'confidence_bucket': '80-85', 'outcome': True},   # Win
        {'confidence_bucket': '80-85', 'outcome': True},   # Win
        {'confidence_bucket': '80-85', 'outcome': True},   # Win
        {'confidence_bucket': '80-85', 'outcome': True},   # Win
        {'confidence_bucket': '80-85', 'outcome': False},  # Loss
        {'confidence_bucket': '80-85', 'outcome': True},   # Win (5/6 = 83.3%)
    ]


def main():
    print("=== KPI COMPUTER EXAMPLES ===\n")
    
    # Create sample data
    trades = create_sample_trades()
    equity_curve = create_sample_equity_curve()
    confidence_data = create_confidence_bucket_data()
    
    print("Sample Data Summary:")
    print(f"  Trades: {len(trades)}")
    print(f"  Equity Curve Points: {len(equity_curve)}")
    print(f"  Confidence Records: {len(confidence_data)}")
    print()
    
    # Compute KPIs
    kpis = KPIComputer.compute_kpis(
        trades=trades,
        equity_curve=equity_curve,
        confidence_buckets=confidence_data
    )
    
    # Generate and display report
    report = KPIComputer.generate_report(kpis)
    print(report)
    print()
    
    # Detailed analysis examples
    print("=== DETAILED ANALYSIS ===\n")
    
    # Example 1: Expectancy Analysis
    print("1. EXPECTANCY ANALYSIS")
    winning_trades = [t for t in trades if t.pnl > 0]
    losing_trades = [t for t in trades if t.pnl < 0]
    
    print(f"   Winning Trades: {len(winning_trades)}")
    print(f"   Losing Trades: {len(losing_trades)}")
    print(f"   Win Rate: {kpis['win_rate_pct']}%")
    print(f"   Average Win: ${kpis['trade_statistics']['avg_win']}")
    print(f"   Average Loss: ${kpis['trade_statistics']['avg_loss']}")
    print(f"   Expectancy: ${kpis['expectancy']}")
    print(f"   -> Positive expectancy indicates profitable system\n")
    
    # Example 2: Drawdown Analysis
    print("2. DRAWDOWN ANALYSIS")
    values = [point['total_value'] for point in equity_curve]
    peak_value = max(values)
    trough_value = min(values[values.index(peak_value):])
    
    print(f"   Peak Portfolio Value: ${peak_value:,.0f}")
    print(f"   Trough Value: ${trough_value:,.0f}")
    print(f"   Maximum Drawdown: {kpis['max_drawdown_pct']}%")
    print(f"   -> Drawdown shows worst-case risk exposure\n")
    
    # Example 3: Confidence Calibration
    print("3. CONFIDENCE CALIBRATION ANALYSIS")
    bucket_stats = kpis['confidence_bucket_stats']
    
    total_calibration_error = 0
    bucket_count = 0
    
    for bucket, stats in bucket_stats.items():
        expected = stats['expected_win_rate']
        actual = stats['actual_win_rate']
        error = stats['calibration_error']
        
        print(f"   {bucket} Bucket:")
        print(f"     Expected Win Rate: {expected}%")
        print(f"     Actual Win Rate: {actual}%")
        print(f"     Calibration Error: {error}%")
        print(f"     Sample Size: {stats['trades']} trades")
        
        total_calibration_error += error
        bucket_count += 1
        print()
    
    avg_calibration_error = total_calibration_error / bucket_count if bucket_count > 0 else 0
    print(f"   Average Calibration Error: {avg_calibration_error:.1f}%")
    print(f"   -> Lower error indicates better confidence calibration\n")
    
    # Example 4: System Comparison
    print("4. SYSTEM COMPARISON EXAMPLE")
    
    # Create comparison systems
    systems = {
        'Current System': kpis,
        'High Win Rate System': {
            'expectancy': 25.0,
            'win_rate_pct': 85.0,
            'max_drawdown_pct': 8.5,
            'trade_statistics': {'avg_win': 50.0, 'avg_loss': -200.0}
        },
        'Low Win Rate System': {
            'expectancy': 75.0,
            'win_rate_pct': 45.0,
            'max_drawdown_pct': 12.0,
            'trade_statistics': {'avg_win': 300.0, 'avg_loss': -150.0}
        }
    }
    
    print("   System Comparison:")
    print("   System              | Expectancy | Win Rate | Max DD | Avg Win | Avg Loss")
    print("   --------------------|------------|----------|--------|---------|----------")
    
    for name, system_kpis in systems.items():
        stats = system_kpis.get('trade_statistics', {})
        print(f"   {name:<19} | ${system_kpis['expectancy']:>9.0f} | "
              f"{system_kpis['win_rate_pct']:>7.1f}% | {system_kpis['max_drawdown_pct']:>5.1f}% | "
              f"${stats.get('avg_win', 0):>6.0f} | ${stats.get('avg_loss', 0):>7.0f}")
    
    print()
    print("   Key Insights:")
    print("   • Current System: Balanced approach with moderate expectancy")
    print("   • High Win Rate: Feels good but lower expectancy due to large losses")
    print("   • Low Win Rate: Higher expectancy despite fewer wins - better system")
    print("   -> Expectancy is the ultimate measure of system profitability")


if __name__ == "__main__":
    main()