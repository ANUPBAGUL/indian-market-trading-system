"""
Unit tests for Decision Logger - Tests logging and debugging functionality.
"""

import unittest
import tempfile
import os
import json
from datetime import datetime
from src.decision_logger import DecisionLogger


class TestDecisionLogger(unittest.TestCase):
    
    def setUp(self):
        """Set up test logger."""
        self.logger = DecisionLogger()
        self.test_symbol = "AAPL"
        self.test_date = "2024-01-15"
    
    def test_initialization(self):
        """Test DecisionLogger initialization."""
        logger = DecisionLogger()
        self.assertEqual(len(logger.agent_decisions), 0)
        self.assertEqual(len(logger.governor_decisions), 0)
        self.assertEqual(len(logger.trade_rationales), 0)
    
    def test_log_agent_decision(self):
        """Test agent decision logging."""
        self.logger.log_agent_decision(
            agent_name="AccumulationAgent",
            symbol=self.test_symbol,
            date=self.test_date,
            decision_type="ENTRY",
            score=75.5,
            evidence={"volume_absorption": True, "atr": 2.5},
            rationale="Strong accumulation pattern detected"
        )
        
        self.assertEqual(len(self.logger.agent_decisions), 1)
        
        decision = self.logger.agent_decisions[0]
        self.assertEqual(decision['agent_name'], "AccumulationAgent")
        self.assertEqual(decision['symbol'], self.test_symbol)
        self.assertEqual(decision['score'], 75.5)
        self.assertEqual(decision['evidence']['volume_absorption'], True)
        self.assertIn('timestamp', decision)
    
    def test_log_governor_decision(self):
        """Test governor decision logging."""
        self.logger.log_governor_decision(
            symbol=self.test_symbol,
            date=self.test_date,
            signal_type="ENTRY",
            decision="ENTER",
            reason="All risk checks passed",
            risk_checks={"confidence": {"passed": True}},
            portfolio_state={"cash": 50000}
        )
        
        self.assertEqual(len(self.logger.governor_decisions), 1)
        
        decision = self.logger.governor_decisions[0]
        self.assertEqual(decision['decision'], "ENTER")
        self.assertEqual(decision['reason'], "All risk checks passed")
        self.assertTrue(decision['risk_checks']['confidence']['passed'])
    
    def test_log_trade_rationale(self):
        """Test trade rationale logging."""
        self.logger.log_trade_rationale(
            trade_id="AAPL_001",
            symbol=self.test_symbol,
            action="ENTRY",
            date=self.test_date,
            price=150.0,
            agent_scores={"accumulation": 75.0, "trigger": 80.0},
            confidence_score=77.5,
            position_size=100,
            stop_price=145.0,
            complete_rationale="Entry based on strong signals"
        )
        
        self.assertEqual(len(self.logger.trade_rationales), 1)
        
        rationale = self.logger.trade_rationales[0]
        self.assertEqual(rationale['trade_id'], "AAPL_001")
        self.assertEqual(rationale['price'], 150.0)
        self.assertEqual(rationale['confidence_score'], 77.5)
        self.assertEqual(rationale['agent_scores']['accumulation'], 75.0)
    
    def test_get_trade_debug_info(self):
        """Test trade debugging information retrieval."""
        # Add sample decisions
        self.logger.log_agent_decision(
            "AccumulationAgent", self.test_symbol, self.test_date,
            "ENTRY", 75.0, {}, "Test rationale"
        )
        
        self.logger.log_governor_decision(
            self.test_symbol, self.test_date, "ENTRY", "ENTER",
            "Test reason", {}, {}
        )
        
        debug_info = self.logger.get_trade_debug_info(self.test_symbol, self.test_date)
        
        self.assertEqual(debug_info['symbol'], self.test_symbol)
        self.assertEqual(debug_info['date'], self.test_date)
        self.assertEqual(len(debug_info['agent_decisions']), 1)
        self.assertEqual(len(debug_info['governor_decisions']), 1)
        self.assertIn('decision_chain_summary', debug_info)
    
    def test_decision_summary_generation(self):
        """Test decision chain summary generation."""
        # Add multiple agent decisions
        agent_decisions = [
            {
                'agent_name': 'AccumulationAgent',
                'score': 75.0,
                'rationale': 'Strong accumulation'
            },
            {
                'agent_name': 'TriggerAgent', 
                'score': 80.0,
                'rationale': 'Clear breakout'
            }
        ]
        
        governor_decisions = [
            {
                'decision': 'ENTER',
                'reason': 'All checks passed'
            }
        ]
        
        trade_rationales = [
            {
                'action': 'ENTRY',
                'position_size': 100,
                'price': 150.0,
                'confidence_score': 77.5
            }
        ]
        
        summary = self.logger._generate_decision_summary(
            agent_decisions, governor_decisions, trade_rationales
        )
        
        self.assertIn("AGENT ANALYSIS", summary)
        self.assertIn("AccumulationAgent: 75.0", summary)
        self.assertIn("TriggerAgent: 80.0", summary)
        self.assertIn("GOVERNOR DECISION", summary)
        self.assertIn("ENTER", summary)
        self.assertIn("TRADE EXECUTION", summary)
    
    def test_empty_decision_summary(self):
        """Test summary with no decisions."""
        summary = self.logger._generate_decision_summary([], [], [])
        self.assertEqual(summary, "No decisions found for this trade")
    
    def test_bad_trade_analysis(self):
        """Test bad trade analysis generation."""
        # Add entry decisions
        self.logger.log_agent_decision(
            "AccumulationAgent", self.test_symbol, self.test_date,
            "ENTRY", 75.0, {}, "Entry signal"
        )
        
        # Add exit decisions
        exit_date = "2024-01-20"
        self.logger.log_agent_decision(
            "ConfidenceDecay", self.test_symbol, exit_date,
            "EXIT", 45.0, {}, "Confidence decayed"
        )
        
        analysis = self.logger.get_bad_trade_analysis(
            self.test_symbol, self.test_date, exit_date
        )
        
        self.assertIn("BAD TRADE ANALYSIS", analysis)
        self.assertIn(self.test_symbol, analysis)
        self.assertIn("ENTRY DECISION ANALYSIS", analysis)
        self.assertIn("EXIT DECISION ANALYSIS", analysis)
        self.assertIn("DEBUGGING QUESTIONS", analysis)
    
    def test_export_logs(self):
        """Test log export functionality."""
        # Add sample data
        self.logger.log_agent_decision(
            "TestAgent", self.test_symbol, self.test_date,
            "ENTRY", 70.0, {"test": True}, "Test decision"
        )
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            self.logger.export_logs(temp_path)
            
            # Verify file exists and contains data
            self.assertTrue(os.path.exists(temp_path))
            
            with open(temp_path, 'r') as f:
                exported_data = json.load(f)
            
            self.assertIn('agent_decisions', exported_data)
            self.assertIn('governor_decisions', exported_data)
            self.assertIn('trade_rationales', exported_data)
            self.assertIn('export_timestamp', exported_data)
            
            # Verify data integrity
            self.assertEqual(len(exported_data['agent_decisions']), 1)
            self.assertEqual(exported_data['agent_decisions'][0]['agent_name'], "TestAgent")
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_clear_logs(self):
        """Test log clearing functionality."""
        # Add some data
        self.logger.log_agent_decision(
            "TestAgent", self.test_symbol, self.test_date,
            "ENTRY", 70.0, {}, "Test"
        )
        
        self.assertEqual(len(self.logger.agent_decisions), 1)
        
        # Clear logs
        self.logger.clear_logs()
        
        self.assertEqual(len(self.logger.agent_decisions), 0)
        self.assertEqual(len(self.logger.governor_decisions), 0)
        self.assertEqual(len(self.logger.trade_rationales), 0)
    
    def test_multiple_symbols_filtering(self):
        """Test filtering decisions by symbol."""
        # Add decisions for multiple symbols
        self.logger.log_agent_decision(
            "TestAgent", "AAPL", self.test_date, "ENTRY", 70.0, {}, "AAPL decision"
        )
        self.logger.log_agent_decision(
            "TestAgent", "MSFT", self.test_date, "ENTRY", 75.0, {}, "MSFT decision"
        )
        
        # Get debug info for specific symbol
        aapl_debug = self.logger.get_trade_debug_info("AAPL", self.test_date)
        msft_debug = self.logger.get_trade_debug_info("MSFT", self.test_date)
        
        self.assertEqual(len(aapl_debug['agent_decisions']), 1)
        self.assertEqual(len(msft_debug['agent_decisions']), 1)
        self.assertEqual(aapl_debug['agent_decisions'][0]['rationale'], "AAPL decision")
        self.assertEqual(msft_debug['agent_decisions'][0]['rationale'], "MSFT decision")
    
    def test_timestamp_consistency(self):
        """Test that timestamps are properly recorded."""
        before_time = datetime.now()
        
        self.logger.log_agent_decision(
            "TestAgent", self.test_symbol, self.test_date,
            "ENTRY", 70.0, {}, "Test"
        )
        
        after_time = datetime.now()
        
        decision = self.logger.agent_decisions[0]
        decision_time = datetime.fromisoformat(decision['timestamp'])
        
        self.assertGreaterEqual(decision_time, before_time)
        self.assertLessEqual(decision_time, after_time)


if __name__ == '__main__':
    unittest.main()