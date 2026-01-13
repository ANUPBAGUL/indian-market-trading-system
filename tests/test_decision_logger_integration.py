"""
Integration tests for Decision Logger - Tests complete logging workflows.
"""

import unittest
import tempfile
import os
import json
from src.decision_logger import DecisionLogger


class TestDecisionLoggerIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up integration test environment."""
        self.logger = DecisionLogger()
    
    def test_complete_trade_logging_workflow(self):
        """Test complete trade from entry to exit with full logging."""
        symbol = "AAPL"
        entry_date = "2024-01-15"
        exit_date = "2024-01-22"
        
        # === ENTRY PHASE ===
        
        # Log all agent decisions for entry
        agents_data = [
            ("AccumulationAgent", 78.5, {"volume_absorption": True, "relative_strength": 85.2}),
            ("TriggerAgent", 85.0, {"breakout_from_base": True, "volume_multiple": 2.3}),
            ("SectorMomentumAgent", 72.0, {"sector_performance": 68.5, "breadth_score": 75.2}),
            ("EarningsAgent", 65.0, {"days_to_earnings": 45, "earnings_risk": "Low"})
        ]
        
        for agent_name, score, evidence in agents_data:
            self.logger.log_agent_decision(
                agent_name=agent_name,
                symbol=symbol,
                date=entry_date,
                decision_type="ENTRY",
                score=score,
                evidence=evidence,
                rationale=f"{agent_name} analysis for {symbol}"
            )
        
        # Log Governor entry decision
        self.logger.log_governor_decision(
            symbol=symbol,
            date=entry_date,
            signal_type="ENTRY",
            decision="ENTER",
            reason="Confidence 75.1% above threshold",
            risk_checks={
                "confidence_threshold": {"required": 65.0, "actual": 75.1, "passed": True},
                "position_limit": {"max": 5, "current": 3, "passed": True}
            },
            portfolio_state={"cash": 50000, "positions": 3}
        )
        
        # Log trade execution
        self.logger.log_trade_rationale(
            trade_id="AAPL_20240115_001",
            symbol=symbol,
            action="ENTRY",
            date=entry_date,
            price=186.25,
            agent_scores={"accumulation": 78.5, "trigger": 85.0, "sector": 72.0, "earnings": 65.0},
            confidence_score=75.1,
            position_size=100,
            stop_price=181.85,
            complete_rationale="Entry based on strong breakout with accumulation support"
        )
        
        # === EXIT PHASE ===
        
        # Log confidence decay
        self.logger.log_agent_decision(
            agent_name="ConfidenceDecay",
            symbol=symbol,
            date=exit_date,
            decision_type="EXIT",
            score=45.0,
            evidence={
                "time_decay": 3.5,
                "stagnation_decay": 2.0,
                "original_confidence": 75.1,
                "decayed_confidence": 45.0
            },
            rationale="Confidence decayed below 50% threshold"
        )
        
        # Log Governor exit decision
        self.logger.log_governor_decision(
            symbol=symbol,
            date=exit_date,
            signal_type="EXIT",
            decision="EXIT",
            reason="Confidence decay triggered exit",
            risk_checks={
                "confidence_threshold": {"required": 50.0, "actual": 45.0, "passed": False}
            },
            portfolio_state={"unrealized_pnl": -387.5}
        )
        
        # Log exit execution
        self.logger.log_trade_rationale(
            trade_id="AAPL_20240115_001",
            symbol=symbol,
            action="EXIT",
            date=exit_date,
            price=182.38,
            agent_scores={"confidence_decay": 45.0},
            confidence_score=45.0,
            position_size=100,
            stop_price=181.85,
            complete_rationale="Exit due to confidence decay, -2.1% loss acceptable"
        )
        
        # === VERIFICATION ===
        
        # Verify all logs were captured
        self.assertEqual(len(self.logger.agent_decisions), 5)  # 4 entry + 1 exit
        self.assertEqual(len(self.logger.governor_decisions), 2)  # entry + exit
        self.assertEqual(len(self.logger.trade_rationales), 2)  # entry + exit
        
        # Verify entry debug info
        entry_debug = self.logger.get_trade_debug_info(symbol, entry_date)
        self.assertEqual(len(entry_debug['agent_decisions']), 4)
        self.assertEqual(len(entry_debug['governor_decisions']), 1)
        self.assertEqual(len(entry_debug['trade_rationales']), 1)
        
        # Verify exit debug info
        exit_debug = self.logger.get_trade_debug_info(symbol, exit_date)
        self.assertEqual(len(exit_debug['agent_decisions']), 1)
        self.assertEqual(len(exit_debug['governor_decisions']), 1)
        self.assertEqual(len(exit_debug['trade_rationales']), 1)
        
        # Verify bad trade analysis
        analysis = self.logger.get_bad_trade_analysis(symbol, entry_date, exit_date)
        self.assertIn("AccumulationAgent: 78.5", analysis)
        self.assertIn("ConfidenceDecay: 45.0", analysis)
        self.assertIn("DEBUGGING QUESTIONS", analysis)
    
    def test_multiple_trades_logging(self):
        """Test logging multiple concurrent trades."""
        symbols = ["AAPL", "MSFT", "GOOGL"]
        date = "2024-01-15"
        
        # Log decisions for multiple symbols
        for i, symbol in enumerate(symbols):
            score = 70.0 + (i * 5)  # Different scores for each
            
            self.logger.log_agent_decision(
                agent_name="AccumulationAgent",
                symbol=symbol,
                date=date,
                decision_type="ENTRY",
                score=score,
                evidence={"test_data": i},
                rationale=f"Analysis for {symbol}"
            )
            
            self.logger.log_governor_decision(
                symbol=symbol,
                date=date,
                signal_type="ENTRY",
                decision="ENTER",
                reason=f"Approved {symbol}",
                risk_checks={"passed": True},
                portfolio_state={"position_count": i + 1}
            )
        
        # Verify each symbol has separate logs
        for symbol in symbols:
            debug_info = self.logger.get_trade_debug_info(symbol, date)
            self.assertEqual(len(debug_info['agent_decisions']), 1)
            self.assertEqual(debug_info['agent_decisions'][0]['symbol'], symbol)
    
    def test_decision_chain_reconstruction(self):
        """Test reconstructing complete decision chain for analysis."""
        symbol = "TSLA"
        date = "2024-02-01"
        
        # Create complex decision scenario
        agent_scores = [
            ("AccumulationAgent", 82.0, "Strong institutional buying"),
            ("TriggerAgent", 45.0, "Weak breakout signal"),
            ("SectorMomentumAgent", 88.0, "EV sector momentum"),
            ("EarningsAgent", 30.0, "Earnings risk high")
        ]
        
        for agent_name, score, rationale in agent_scores:
            self.logger.log_agent_decision(
                agent_name=agent_name,
                symbol=symbol,
                date=date,
                decision_type="ENTRY",
                score=score,
                evidence={"score": score},
                rationale=rationale
            )
        
        # Governor rejects due to mixed signals
        self.logger.log_governor_decision(
            symbol=symbol,
            date=date,
            signal_type="ENTRY",
            decision="NO_TRADE",
            reason="Mixed agent signals, weak trigger despite strong accumulation",
            risk_checks={"signal_quality": {"passed": False}},
            portfolio_state={"risk_budget": "preserved"}
        )
        
        # Verify decision chain
        debug_info = self.logger.get_trade_debug_info(symbol, date)
        summary = debug_info['decision_chain_summary']
        
        # Should contain all agent scores
        self.assertIn("AccumulationAgent: 82.0", summary)
        self.assertIn("TriggerAgent: 45.0", summary)
        self.assertIn("SectorMomentumAgent: 88.0", summary)
        self.assertIn("EarningsAgent: 30.0", summary)
        
        # Should show Governor rejection
        self.assertIn("NO_TRADE", summary)
        self.assertIn("Mixed agent signals", summary)
    
    def test_export_import_workflow(self):
        """Test complete export/import workflow for audit purposes."""
        # Create comprehensive logging scenario
        trades_data = [
            ("AAPL", "2024-01-15", 75.0, "ENTER"),
            ("MSFT", "2024-01-16", 68.0, "ENTER"),
            ("GOOGL", "2024-01-17", 82.0, "NO_TRADE")
        ]
        
        for symbol, date, score, decision in trades_data:
            self.logger.log_agent_decision(
                "AccumulationAgent", symbol, date, "ENTRY", score, {}, f"Analysis for {symbol}"
            )
            
            self.logger.log_governor_decision(
                symbol, date, "ENTRY", decision, f"Decision for {symbol}", {}, {}
            )
            
            if decision == "ENTER":
                self.logger.log_trade_rationale(
                    f"{symbol}_001", symbol, "ENTRY", date, 100.0, {"accumulation": score},
                    score, 100, 95.0, f"Trade rationale for {symbol}"
                )
        
        # Export logs
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            self.logger.export_logs(temp_path)
            
            # Verify export structure
            with open(temp_path, 'r') as f:
                exported_data = json.load(f)
            
            self.assertEqual(len(exported_data['agent_decisions']), 3)
            self.assertEqual(len(exported_data['governor_decisions']), 3)
            self.assertEqual(len(exported_data['trade_rationales']), 2)  # Only ENTER decisions
            
            # Verify data integrity
            symbols_in_export = {d['symbol'] for d in exported_data['agent_decisions']}
            self.assertEqual(symbols_in_export, {"AAPL", "MSFT", "GOOGL"})
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_performance_analysis_workflow(self):
        """Test logging for performance analysis and system improvement."""
        # Simulate a series of trades with outcomes
        trade_scenarios = [
            ("AAPL", "2024-01-15", [78, 85, 72, 65], "WIN", 2.5),
            ("MSFT", "2024-01-16", [65, 45, 88, 70], "LOSS", -1.8),
            ("GOOGL", "2024-01-17", [82, 90, 75, 60], "WIN", 3.2),
            ("TSLA", "2024-01-18", [55, 40, 65, 45], "LOSS", -2.1)
        ]
        
        for symbol, date, scores, outcome, pnl_pct in trade_scenarios:
            agent_names = ["AccumulationAgent", "TriggerAgent", "SectorMomentumAgent", "EarningsAgent"]
            
            # Log agent decisions
            for agent_name, score in zip(agent_names, scores):
                self.logger.log_agent_decision(
                    agent_name, symbol, date, "ENTRY", score, {"outcome": outcome}, 
                    f"{agent_name} scored {score} for {outcome} trade"
                )
            
            # Calculate weighted confidence
            confidence = sum(scores) / len(scores)
            
            # Log Governor decision
            decision = "ENTER" if confidence > 60 else "NO_TRADE"
            self.logger.log_governor_decision(
                symbol, date, "ENTRY", decision, f"Confidence {confidence:.1f}%", 
                {"confidence_check": {"passed": confidence > 60}}, {}
            )
            
            # Log trade if entered (all scenarios have confidence > 60)
            self.logger.log_trade_rationale(
                f"{symbol}_001", symbol, "ENTRY", date, 100.0, 
                dict(zip(["acc", "trig", "sect", "earn"], scores)),
                confidence, 100, 95.0, f"Trade resulted in {outcome} ({pnl_pct}%)"
            )
        
        # Analyze patterns in logs
        winning_trades = []
        losing_trades = []
        
        for rationale in self.logger.trade_rationales:
            if "WIN" in rationale['complete_rationale']:
                winning_trades.append(rationale)
            elif "LOSS" in rationale['complete_rationale']:
                losing_trades.append(rationale)
        
        # Verify pattern analysis capability
        self.assertEqual(len(winning_trades), 2)  # AAPL, GOOGL
        self.assertEqual(len(losing_trades), 2)   # MSFT, TSLA
        
        # Check that we can identify agent performance patterns
        all_agent_decisions = self.logger.agent_decisions
        trigger_scores = [d['score'] for d in all_agent_decisions if d['agent_name'] == 'TriggerAgent']
        
        # TriggerAgent scores: [85, 45, 90, 40] - high scores correlate with wins
        self.assertIn(85, trigger_scores)  # AAPL win
        self.assertIn(90, trigger_scores)  # GOOGL win
        self.assertIn(45, trigger_scores)  # MSFT loss
        self.assertIn(40, trigger_scores)  # TSLA loss
    
    def test_debugging_workflow_integration(self):
        """Test complete debugging workflow for system improvement."""
        # Simulate a problematic trade that needs debugging
        symbol = "NVDA"
        entry_date = "2024-03-01"
        exit_date = "2024-03-08"
        
        # Entry looked good but failed
        entry_agents = [
            ("AccumulationAgent", 85.0, {"volume_absorption": True}, "Strong buying pressure"),
            ("TriggerAgent", 88.0, {"clean_breakout": True}, "Perfect breakout pattern"),
            ("SectorMomentumAgent", 45.0, {"sector_weak": True}, "Semiconductor weakness"),
            ("EarningsAgent", 75.0, {"earnings_safe": True}, "No earnings risk")
        ]
        
        for agent_name, score, evidence, rationale in entry_agents:
            self.logger.log_agent_decision(
                agent_name, symbol, entry_date, "ENTRY", score, evidence, rationale
            )
        
        # Governor approved despite sector weakness
        self.logger.log_governor_decision(
            symbol, entry_date, "ENTRY", "ENTER",
            "Strong individual signals override sector weakness",
            {"override_sector": True}, {"sector_exposure": 25.0}
        )
        
        # Trade executed
        self.logger.log_trade_rationale(
            "NVDA_001", symbol, "ENTRY", entry_date, 800.0,
            {"acc": 85.0, "trig": 88.0, "sect": 45.0, "earn": 75.0},
            73.25, 50, 760.0, "High conviction despite sector headwinds"
        )
        
        # Exit due to sector collapse
        self.logger.log_agent_decision(
            "ConfidenceDecay", symbol, exit_date, "EXIT", 25.0,
            {"sector_collapse": True, "individual_strength_failed": True},
            "Sector weakness overwhelmed individual strength"
        )
        
        self.logger.log_governor_decision(
            symbol, exit_date, "EXIT", "EXIT",
            "Sector risk materialized, cut losses",
            {"sector_risk_realized": True}, {"loss_pct": -8.5}
        )
        
        # Generate debugging analysis
        analysis = self.logger.get_bad_trade_analysis(symbol, entry_date, exit_date)
        
        # Verify debugging insights are captured
        self.assertIn("SectorMomentumAgent: 45.0", analysis)
        self.assertIn("Semiconductor weakness", analysis)
        self.assertIn("Sector weakness overwhelmed", analysis)
        self.assertIn("DEBUGGING QUESTIONS", analysis)
        
        # This analysis would reveal: 
        # 1. Sector agent was correct (45.0 score)
        # 2. Governor override logic needs review
        # 3. Sector risk management insufficient
        
        # Verify we can extract this insight programmatically
        entry_debug = self.logger.get_trade_debug_info(symbol, entry_date)
        sector_decision = next(
            d for d in entry_debug['agent_decisions'] 
            if d['agent_name'] == 'SectorMomentumAgent'
        )
        
        self.assertEqual(sector_decision['score'], 45.0)
        self.assertTrue(sector_decision['evidence']['sector_weak'])
        
        # This low score should have been a stronger warning signal


if __name__ == '__main__':
    unittest.main()