"""
Decision Logging Example - Demonstrates trade explainability and debugging.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.decision_logger import DecisionLogger


def simulate_trade_with_logging():
    """Simulate a complete trade with full decision logging."""
    
    logger = DecisionLogger()
    
    # Simulate a trade: AAPL entry on 2024-01-15, exit on 2024-01-22
    symbol = "AAPL"
    entry_date = "2024-01-15"
    exit_date = "2024-01-22"
    
    print("=== SIMULATING TRADE WITH DECISION LOGGING ===\n")
    
    # === ENTRY DECISION PROCESS ===
    print("1. AGENT ANALYSIS PHASE:")
    
    # Accumulation Agent Decision
    logger.log_agent_decision(
        agent_name="AccumulationAgent",
        symbol=symbol,
        date=entry_date,
        decision_type="ENTRY",
        score=78.5,
        evidence={
            "volume_absorption": True,
            "volatility_compression": True,
            "tight_base": False,
            "relative_strength": 85.2,
            "atr_14": 2.45,
            "volume_ratio": 1.8
        },
        rationale="Strong accumulation pattern: volume absorption detected with 1.8x avg volume, volatility compressed to 2.45 ATR, relative strength at 85.2%. Missing tight base formation reduces confidence."
    )
    
    # Trigger Agent Decision
    logger.log_agent_decision(
        agent_name="TriggerAgent",
        symbol=symbol,
        date=entry_date,
        decision_type="ENTRY",
        score=85.0,
        evidence={
            "volume_expansion": True,
            "breakout_from_base": True,
            "candle_acceptance": True,
            "volume_multiple": 2.3,
            "breakout_level": 185.50,
            "current_price": 186.25
        },
        rationale="Clear breakout trigger: 2.3x volume expansion, clean break above $185.50 resistance, strong candle acceptance at $186.25. All trigger conditions met."
    )
    
    # Sector Momentum Agent Decision
    logger.log_agent_decision(
        agent_name="SectorMomentumAgent",
        symbol=symbol,
        date=entry_date,
        decision_type="ENTRY",
        score=72.0,
        evidence={
            "sector_performance": 68.5,
            "breadth_score": 75.2,
            "rvol_score": 72.8,
            "sector": "Technology",
            "relative_performance": 1.15
        },
        rationale="Technology sector showing moderate momentum: 68.5% performance score, breadth at 75.2%, RVOL at 72.8%. Sector supportive but not exceptional."
    )
    
    # Earnings Agent Decision
    logger.log_agent_decision(
        agent_name="EarningsAgent",
        symbol=symbol,
        date=entry_date,
        decision_type="ENTRY",
        score=65.0,
        evidence={
            "days_to_earnings": 45,
            "post_earnings_reaction": "Neutral",
            "earnings_calendar_risk": "Low",
            "historical_volatility": 0.28
        },
        rationale="Earnings neutral: 45 days until next earnings, last reaction was neutral, low calendar risk. No significant earnings catalyst or risk."
    )
    
    print("   AccumulationAgent: 78.5 - Strong accumulation with volume absorption")
    print("   TriggerAgent: 85.0 - Clear breakout with volume confirmation")
    print("   SectorMomentumAgent: 72.0 - Moderate sector support")
    print("   EarningsAgent: 65.0 - Neutral earnings environment")
    
    # === GOVERNOR DECISION ===
    print("\n2. GOVERNOR RISK ASSESSMENT:")
    
    logger.log_governor_decision(
        symbol=symbol,
        date=entry_date,
        signal_type="ENTRY",
        decision="ENTER",
        reason="All risk checks passed: confidence 75.1% above 65% threshold, position size within limits, sector exposure acceptable at 35%",
        risk_checks={
            "confidence_threshold": {"required": 65.0, "actual": 75.1, "passed": True},
            "position_limit": {"max_positions": 5, "current": 3, "passed": True},
            "sector_limit": {"max_exposure": 40.0, "current": 35.0, "passed": True},
            "cash_available": {"required": 18625.0, "available": 45000.0, "passed": True}
        },
        portfolio_state={
            "total_positions": 3,
            "cash_balance": 45000.0,
            "sector_exposures": {"Technology": 35.0, "Healthcare": 15.0},
            "total_value": 125000.0
        }
    )
    
    print("   Decision: ENTER")
    print("   Reason: All risk checks passed, confidence 75.1% > 65% threshold")
    
    # === TRADE EXECUTION ===
    print("\n3. TRADE EXECUTION:")
    
    logger.log_trade_rationale(
        trade_id="AAPL_20240115_001",
        symbol=symbol,
        action="ENTRY",
        date=entry_date,
        price=186.25,
        agent_scores={
            "accumulation": 78.5,
            "trigger": 85.0,
            "sector_momentum": 72.0,
            "earnings": 65.0
        },
        confidence_score=75.1,
        position_size=100,
        stop_price=181.85,
        complete_rationale="Entry based on strong breakout signal (85.0) with accumulation support (78.5). Moderate sector momentum (72.0) and neutral earnings (65.0) provide adequate backdrop. Weighted confidence of 75.1% justifies 1% risk position. Stop set at $181.85 (2.4% below entry) based on 2x ATR."
    )
    
    print("   ENTRY: 100 shares at $186.25")
    print("   Stop Loss: $181.85")
    print("   Confidence: 75.1%")
    
    # === EXIT DECISION PROCESS (Simulating a losing trade) ===
    print("\n" + "="*50)
    print("4. EXIT DECISION PROCESS (7 days later):")
    
    # Confidence Decay (position aged, price stagnant)
    logger.log_agent_decision(
        agent_name="ConfidenceDecay",
        symbol=symbol,
        date=exit_date,
        decision_type="EXIT",
        score=45.0,
        evidence={
            "time_decay": 3.5,  # 7 days * 0.5%
            "stagnation_decay": 2.0,  # Price moved <1%
            "sector_decay": 1.5,  # Sector weakened
            "original_confidence": 75.1,
            "decayed_confidence": 45.0
        },
        rationale="Confidence decayed from 75.1% to 45.0%: time decay 3.5% (7 days), stagnation decay 2.0% (price flat), sector decay 1.5% (tech weakness). Below 50% threshold triggers exit consideration."
    )
    
    # Governor Exit Decision
    logger.log_governor_decision(
        symbol=symbol,
        date=exit_date,
        signal_type="EXIT",
        decision="EXIT",
        reason="Confidence decay below 50% threshold (45.0%), position showing 2.1% loss, no improvement in 7 days",
        risk_checks={
            "confidence_threshold": {"required": 50.0, "actual": 45.0, "passed": False},
            "max_loss_limit": {"max_loss": -5.0, "current_loss": -2.1, "passed": True},
            "time_limit": {"max_days": 30, "current_days": 7, "passed": True}
        },
        portfolio_state={
            "total_positions": 4,
            "unrealized_pnl": -387.50,
            "total_value": 124612.50
        }
    )
    
    # Exit Trade
    logger.log_trade_rationale(
        trade_id="AAPL_20240115_001",
        symbol=symbol,
        action="EXIT",
        date=exit_date,
        price=182.38,
        agent_scores={
            "confidence_decay": 45.0
        },
        confidence_score=45.0,
        position_size=100,
        stop_price=181.85,
        complete_rationale="Exit due to confidence decay below 50% threshold. Original thesis invalidated by price stagnation and sector weakness. Loss of $387 (2.1%) acceptable within risk parameters. Exit before stop loss triggered."
    )
    
    print("   ConfidenceDecay: 45.0 - Below 50% threshold")
    print("   Governor: EXIT - Confidence decay triggered")
    print("   EXIT: 100 shares at $182.38")
    print("   Loss: -$387 (-2.1%)")
    
    return logger, symbol, entry_date, exit_date


def demonstrate_trade_debugging():
    """Demonstrate how to debug a bad trade using decision logs."""
    
    # Simulate the trade
    logger, symbol, entry_date, exit_date = simulate_trade_with_logging()
    
    print("\n" + "="*60)
    print("TRADE DEBUGGING ANALYSIS")
    print("="*60)
    
    # Get complete debugging information
    debug_analysis = logger.get_bad_trade_analysis(symbol, entry_date, exit_date)
    print(debug_analysis)
    
    print("\n" + "="*60)
    print("DETAILED DECISION LOGS")
    print("="*60)
    
    # Show detailed entry decision
    entry_debug = logger.get_trade_debug_info(symbol, entry_date)
    print("\nENTRY DECISION BREAKDOWN:")
    print(entry_debug['decision_chain_summary'])
    
    # Show detailed exit decision
    exit_debug = logger.get_trade_debug_info(symbol, exit_date)
    print("\nEXIT DECISION BREAKDOWN:")
    print(exit_debug['decision_chain_summary'])
    
    print("\n" + "="*60)
    print("HOW TO DEBUG A BAD TRADE")
    print("="*60)
    
    debugging_guide = """
1. ANALYZE ENTRY DECISION:
   • Were agent scores justified by actual market conditions?
   • Did the breakout signal hold or fail immediately?
   • Was sector momentum assessment accurate?
   • Were there hidden risks not captured by agents?

2. EXAMINE GOVERNOR LOGIC:
   • Did risk checks properly assess the situation?
   • Was position sizing appropriate for confidence level?
   • Were portfolio limits correctly enforced?

3. REVIEW EXIT TIMING:
   • Did confidence decay trigger at the right time?
   • Was the exit decision based on system rules or emotion?
   • Could the stop loss have been better positioned?

4. IDENTIFY SYSTEM IMPROVEMENTS:
   • Which agent provided the weakest signal?
   • Should confidence thresholds be adjusted?
   • Are there missing risk factors to consider?

5. MARKET CONTEXT ANALYSIS:
   • What external events affected the trade?
   • Did market regime change during the position?
   • Were there sector-specific developments?
"""
    
    print(debugging_guide)
    
    # Export logs for further analysis
    logger.export_logs("trade_debug_logs.json")
    print("Complete logs exported to: trade_debug_logs.json")


if __name__ == '__main__':
    demonstrate_trade_debugging()