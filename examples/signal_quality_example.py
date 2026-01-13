"""
Signal Quality KPI Example - Demonstrates signal tracking and quality analysis.

This example shows how the Signal Quality KPI measures signal conversion rates,
accuracy, and rejection reasons to optimize signal generation.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from kpi_computer import KPIComputer
from backtest_engine import Trade

def main():
    """Demonstrate Signal Quality KPI with sample data."""
    
    # Sample signal data (what would come from backtest_engine.signal_log)
    signal_data = [
        # Executed signals that became profitable trades
        {'date': '2024-01-02', 'symbol': 'AAPL', 'type': 'ENTRY', 'confidence': 75.0, 'executed': True, 'rejection_reason': None},
        {'date': '2024-01-03', 'symbol': 'MSFT', 'type': 'ENTRY', 'confidence': 80.0, 'executed': True, 'rejection_reason': None},
        
        # Executed signals that became losing trades
        {'date': '2024-01-04', 'symbol': 'GOOGL', 'type': 'ENTRY', 'confidence': 70.0, 'executed': True, 'rejection_reason': None},
        
        # Rejected signals
        {'date': '2024-01-05', 'symbol': 'TSLA', 'type': 'ENTRY', 'confidence': 65.0, 'executed': False, 'rejection_reason': 'Governor rejected: Low confidence'},
        {'date': '2024-01-06', 'symbol': 'NVDA', 'type': 'ENTRY', 'confidence': 72.0, 'executed': False, 'rejection_reason': 'Insufficient cash'},
        {'date': '2024-01-07', 'symbol': 'AMD', 'type': 'ENTRY', 'confidence': 68.0, 'executed': False, 'rejection_reason': 'Already have position'},
        {'date': '2024-01-08', 'symbol': 'META', 'type': 'ENTRY', 'confidence': 74.0, 'executed': False, 'rejection_reason': 'Governor rejected: Sector limit'},
        
        # Exit signals
        {'date': '2024-01-10', 'symbol': 'AAPL', 'type': 'EXIT', 'confidence': 0.0, 'executed': True, 'rejection_reason': None},
        {'date': '2024-01-11', 'symbol': 'MSFT', 'type': 'EXIT', 'confidence': 0.0, 'executed': True, 'rejection_reason': None},
        {'date': '2024-01-12', 'symbol': 'GOOGL', 'type': 'EXIT', 'confidence': 0.0, 'executed': True, 'rejection_reason': None},
    ]
    
    # Sample trade data (corresponding to executed entry signals)
    trades = [
        Trade(symbol='AAPL', entry_date='2024-01-02', entry_price=150.0, 
              exit_date='2024-01-10', exit_price=155.0, shares=100, pnl=500.0, pnl_pct=3.33),
        Trade(symbol='MSFT', entry_date='2024-01-03', entry_price=300.0, 
              exit_date='2024-01-11', exit_price=310.0, shares=50, pnl=500.0, pnl_pct=3.33),
        Trade(symbol='GOOGL', entry_date='2024-01-04', entry_price=120.0, 
              exit_date='2024-01-12', exit_price=115.0, shares=80, pnl=-400.0, pnl_pct=-4.17),
    ]
    
    # Sample equity curve
    equity_curve = [
        {'date': '2024-01-01', 'total_value': 100000},
        {'date': '2024-01-15', 'total_value': 100600},
    ]
    
    print("=== SIGNAL QUALITY KPI EXAMPLE ===\\n")
    
    # Compute KPIs including Signal Quality
    kpis = KPIComputer.compute_kpis(
        trades=trades,
        equity_curve=equity_curve,
        signal_data=signal_data
    )
    
    # Display results
    print("SIGNAL QUALITY ANALYSIS:")
    sq = kpis['signal_quality_stats']
    print(f"Total Signals Generated: {sq['total_signals']}")
    print(f"Signals Executed: {sq['executed_signals']} ({sq['conversion_rate_pct']:.1f}%)")
    print(f"Signal Accuracy: {sq['signal_accuracy_pct']:.1f}% (profitable trades)")
    print(f"Profitable Signals: {sq['profitable_signals']}")
    print()
    
    print("REJECTION BREAKDOWN:")
    for reason, count in sq['rejection_reasons'].items():
        pct = (count / sq['total_signals'] * 100)
        print(f"  {reason}: {count} signals ({pct:.1f}%)")
    print()
    
    # Generate full report
    print(KPIComputer.generate_report(kpis))
    
    print("\\n=== KEY INSIGHTS ===")
    print("• Signal Quality KPI helps identify bottlenecks in signal execution")
    print("• Conversion rate shows how many signals actually become trades")
    print("• Signal accuracy measures profitability of executed signals")
    print("• Rejection reasons help optimize signal generation and risk management")
    print("• Use this data to tune confidence thresholds and Governor rules")

if __name__ == "__main__":
    main()