"""
Governor Agent Examples - Demonstrates decision-making with veto enforcement.
"""

import sys
sys.path.append('src')
import pandas as pd
from governor import Governor, Decision


def main():
    print("=== GOVERNOR AGENT EXAMPLES ===\n")
    
    # Example 1: Approved Entry
    print("1. APPROVED ENTRY")
    decision, reason = Governor.run(
        signal_type='ENTRY',
        symbol='AAPL',
        current_price=150.0,
        confidence_score=78.5,
        position_size=500,
        sector='Technology',
        daily_volume=50000000
    )
    
    print(f"   Signal: ENTRY for AAPL")
    print(f"   Price: $150.00, Confidence: 78.5%, Size: 500 shares")
    print(f"   Decision: {decision.value}")
    print(f"   Reason: {reason}")
    print(f"   -> High-quality setup approved\n")
    
    # Example 2: Rejected Entry (Low Confidence)
    print("2. REJECTED ENTRY - LOW CONFIDENCE")
    decision, reason = Governor.run(
        signal_type='ENTRY',
        symbol='TSLA',
        current_price=200.0,
        confidence_score=55.0,  # Below 60% minimum
        position_size=300,
        sector='Automotive',
        daily_volume=25000000
    )
    
    print(f"   Signal: ENTRY for TSLA")
    print(f"   Price: $200.00, Confidence: 55.0%, Size: 300 shares")
    print(f"   Decision: {decision.value}")
    print(f"   Reason: {reason}")
    print(f"   -> Insufficient confidence vetoed\n")
    
    # Example 3: Rejected Entry (Position Size)
    print("3. REJECTED ENTRY - EXCESSIVE SIZE")
    decision, reason = Governor.run(
        signal_type='ENTRY',
        symbol='GOOGL',
        current_price=2500.0,
        confidence_score=85.0,
        position_size=15000,  # Exceeds 10,000 limit
        sector='Technology',
        daily_volume=1500000
    )
    
    print(f"   Signal: ENTRY for GOOGL")
    print(f"   Price: $2500.00, Confidence: 85.0%, Size: 15,000 shares")
    print(f"   Decision: {decision.value}")
    print(f"   Reason: {reason}")
    print(f"   -> Risk limits enforced\n")
    
    # Example 4: Rejected Entry (Sector Exposure)
    print("4. REJECTED ENTRY - SECTOR EXPOSURE")
    existing_positions = [
        {'symbol': 'AAPL', 'sector': 'Technology'},
        {'symbol': 'MSFT', 'sector': 'Technology'},
        {'symbol': 'NVDA', 'sector': 'Technology'},
        {'symbol': 'JPM', 'sector': 'Financial'}
    ]
    
    decision, reason = Governor.run(
        signal_type='ENTRY',
        symbol='META',
        current_price=300.0,
        confidence_score=72.0,
        position_size=400,
        sector='Technology',  # Would exceed 25% sector limit
        daily_volume=20000000,
        existing_positions=existing_positions
    )
    
    print(f"   Signal: ENTRY for META")
    print(f"   Existing: 3/4 positions in Technology")
    print(f"   Decision: {decision.value}")
    print(f"   Reason: {reason}")
    print(f"   -> Sector concentration prevented\n")
    
    # Example 5: Approved Exit
    print("5. APPROVED EXIT")
    decision, reason = Governor.run(
        signal_type='EXIT',
        symbol='MSFT',
        current_price=310.0,
        confidence_score=70.0,  # Not used for exits
        position_size=0,        # Not used for exits
        sector='Technology',
        daily_volume=30000000,
        position_pnl_pct=12.5,
        decayed_confidence=52.0
    )
    
    print(f"   Signal: EXIT for MSFT")
    print(f"   P&L: +12.5%, Decayed Confidence: 52.0%")
    print(f"   Decision: {decision.value}")
    print(f"   Reason: {reason}")
    print(f"   -> Normal exit conditions met\n")
    
    # Example 6: Force Exit (Low Confidence)
    print("6. FORCE EXIT - LOW CONFIDENCE")
    decision, reason = Governor.run(
        signal_type='EXIT',
        symbol='TSLA',
        current_price=180.0,
        confidence_score=65.0,
        position_size=0,
        sector='Automotive',
        daily_volume=25000000,
        position_pnl_pct=-8.5,
        decayed_confidence=42.0  # Below 45% force exit
    )
    
    print(f"   Signal: EXIT for TSLA")
    print(f"   P&L: -8.5%, Decayed Confidence: 42.0%")
    print(f"   Decision: {decision.value}")
    print(f"   Reason: {reason}")
    print(f"   -> Confidence decay triggered force exit\n")
    
    # Example 7: Force Exit (Excessive Drawdown)
    print("7. FORCE EXIT - EXCESSIVE DRAWDOWN")
    decision, reason = Governor.run(
        signal_type='EXIT',
        symbol='NVDA',
        current_price=420.0,
        confidence_score=70.0,
        position_size=0,
        sector='Technology',
        daily_volume=40000000,
        position_pnl_pct=-9.2,  # Exceeds 8% drawdown limit
        decayed_confidence=55.0
    )
    
    print(f"   Signal: EXIT for NVDA")
    print(f"   P&L: -9.2%, Decayed Confidence: 55.0%")
    print(f"   Decision: {decision.value}")
    print(f"   Reason: {reason}")
    print(f"   -> Drawdown limit enforced\n")
    
    # Example 8: Input Validation Failures
    print("8. INPUT VALIDATION FAILURES")
    
    validation_cases = [
        {
            'name': 'Price too low',
            'price': 3.50,
            'confidence': 75.0,
            'size': 1000,
            'volume': 500000
        },
        {
            'name': 'Insufficient liquidity',
            'price': 50.0,
            'confidence': 75.0,
            'size': 1000,
            'volume': 50000  # Below 100k minimum
        },
        {
            'name': 'Invalid confidence',
            'price': 50.0,
            'confidence': 105.0,  # Above 100%
            'size': 1000,
            'volume': 500000
        }
    ]
    
    for case in validation_cases:
        decision, reason = Governor.run(
            signal_type='ENTRY',
            symbol='TEST',
            current_price=case['price'],
            confidence_score=case['confidence'],
            position_size=case['size'],
            sector='Test',
            daily_volume=case['volume']
        )
        
        print(f"   {case['name']}: {decision.value} - {reason}")
    
    print()
    
    # Example 9: Batch Processing
    print("9. BATCH PROCESSING EXAMPLE")
    batch_data = pd.DataFrame({
        'signal_type': ['ENTRY', 'ENTRY', 'ENTRY', 'EXIT', 'EXIT'],
        'symbol': ['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'NVDA'],
        'current_price': [150.0, 2500.0, 200.0, 310.0, 420.0],
        'confidence_score': [78.5, 85.0, 55.0, 70.0, 75.0],
        'position_size': [500, 100, 300, 0, 0],
        'sector': ['Technology', 'Technology', 'Automotive', 'Technology', 'Technology'],
        'daily_volume': [50000000, 1500000, 25000000, 30000000, 40000000],
        'position_pnl_pct': [None, None, None, 12.5, -9.2],
        'decayed_confidence': [None, None, None, 52.0, 55.0]
    })
    
    results = Governor.batch_decisions(batch_data)
    
    display_cols = ['symbol', 'signal_type', 'confidence_score', 'decision', 'reason']
    print(results[display_cols].to_string(index=False, max_colwidth=50))
    print()
    
    # Example 10: Decision Summary
    print("10. DECISION SUMMARY")
    decisions = [
        (Decision.ENTER, "Entry approved"),
        (Decision.NO_TRADE, "Low confidence"),
        (Decision.NO_TRADE, "Excessive size"),
        (Decision.EXIT, "Normal exit"),
        (Decision.EXIT, "Force exit")
    ]
    
    summary = Governor.get_decision_summary(decisions)
    
    print("   Decision Distribution:")
    for decision_type, count in summary.items():
        print(f"     {decision_type}: {count}")
    
    total_decisions = sum(summary.values())
    approval_rate = (summary['ENTER'] + summary['EXIT']) / total_decisions * 100
    print(f"   Approval Rate: {approval_rate:.1f}%")
    print(f"   -> Governor maintains strict discipline")


if __name__ == "__main__":
    main()