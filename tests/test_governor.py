"""
Unit tests for Governor - Tests individual methods and decision logic.
"""

import unittest
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from governor import Governor, Decision


class TestGovernor(unittest.TestCase):
    
    def test_input_validation(self):
        """Test input validation logic."""
        # Valid inputs
        result = Governor._validate_inputs(50.0, 75.0, 1000, 500000, 'ENTRY')
        self.assertIsNone(result)
        
        # Invalid price (too low)
        result = Governor._validate_inputs(3.0, 75.0, 1000, 500000, 'ENTRY')
        self.assertIn("Price $3.00 outside valid range", result)
        
        # Invalid price (too high)
        result = Governor._validate_inputs(1500.0, 75.0, 1000, 500000, 'ENTRY')
        self.assertIn("Price $1500.00 outside valid range", result)
        
        # Invalid confidence
        result = Governor._validate_inputs(50.0, 105.0, 1000, 500000, 'ENTRY')
        self.assertIn("Confidence 105.0% outside valid range", result)
        
        # Invalid position size for entry
        result = Governor._validate_inputs(50.0, 75.0, -100, 500000, 'ENTRY')
        self.assertIn("Invalid position size: -100", result)
        
        # Zero position size allowed for exit
        result = Governor._validate_inputs(50.0, 75.0, 0, 500000, 'EXIT')
        self.assertIsNone(result)
        
        # Insufficient liquidity
        result = Governor._validate_inputs(50.0, 75.0, 1000, 50000, 'ENTRY')
        self.assertIn("Insufficient liquidity: 50,000 shares", result)
    
    def test_entry_signal_processing(self):
        """Test entry signal processing logic."""
        # Approved entry
        decision, reason = Governor._process_entry_signal(
            'AAPL', 150.0, 75.0, 500, 'Technology', None, []
        )
        self.assertEqual(decision, Decision.ENTER)
        self.assertIn("Entry approved", reason)
        
        # Rejected - low confidence
        decision, reason = Governor._process_entry_signal(
            'TSLA', 200.0, 55.0, 500, 'Automotive', None, []
        )
        self.assertEqual(decision, Decision.NO_TRADE)
        self.assertIn("below minimum", reason)
        
        # Rejected - excessive size
        decision, reason = Governor._process_entry_signal(
            'GOOGL', 2500.0, 85.0, 15000, 'Technology', None, []
        )
        self.assertEqual(decision, Decision.NO_TRADE)
        self.assertIn("exceeds maximum", reason)
    
    def test_exit_signal_processing(self):
        """Test exit signal processing logic."""
        # Normal exit
        decision, reason = Governor._process_exit_signal(
            'MSFT', 5.0, 55.0, []
        )
        self.assertEqual(decision, Decision.EXIT)
        self.assertIn("Exit approved", reason)
        
        # Force exit - low confidence
        decision, reason = Governor._process_exit_signal(
            'TSLA', -3.0, 42.0, []
        )
        self.assertEqual(decision, Decision.EXIT)
        self.assertIn("Force exit: Confidence decayed", reason)
        
        # Force exit - excessive drawdown
        decision, reason = Governor._process_exit_signal(
            'NVDA', -9.5, 55.0, []
        )
        self.assertEqual(decision, Decision.EXIT)
        self.assertIn("Force exit: Drawdown", reason)
    
    def test_sector_exposure_check(self):
        """Test sector exposure validation."""
        existing_positions = [
            {'symbol': 'AAPL', 'sector': 'Technology'},
            {'symbol': 'MSFT', 'sector': 'Technology'},
            {'symbol': 'JPM', 'sector': 'Financial'},
            {'symbol': 'JNJ', 'sector': 'Healthcare'}
        ]
        
        # Adding another tech stock would exceed 25% limit (3/5 = 60%)
        result = Governor._check_sector_exposure('Technology', existing_positions)
        self.assertIsNotNone(result)
        self.assertIn("Technology exposure would be", result)
        
        # Adding healthcare stock would exceed limit (2/5 = 40% > 25%)
        result = Governor._check_sector_exposure('Healthcare', existing_positions)
        self.assertIsNotNone(result)
        self.assertIn("Healthcare exposure would be", result)
        
        # Empty positions list
        result = Governor._check_sector_exposure('Technology', [])
        self.assertIsNone(result)
    
    def test_complete_entry_decisions(self):
        """Test complete entry decision flow."""
        # Approved entry
        decision, reason = Governor.run(
            signal_type='ENTRY',
            symbol='AAPL',
            current_price=150.0,
            confidence_score=75.0,
            position_size=500,
            sector='Technology',
            daily_volume=50000000
        )
        self.assertEqual(decision, Decision.ENTER)
        self.assertIn("Entry approved", reason)
        
        # Rejected entry - validation failure
        decision, reason = Governor.run(
            signal_type='ENTRY',
            symbol='PENNY',
            current_price=2.0,  # Below minimum
            confidence_score=75.0,
            position_size=500,
            sector='Technology',
            daily_volume=50000000
        )
        self.assertEqual(decision, Decision.NO_TRADE)
        self.assertIn("Input validation failed", reason)
    
    def test_complete_exit_decisions(self):
        """Test complete exit decision flow."""
        # Normal exit
        decision, reason = Governor.run(
            signal_type='EXIT',
            symbol='MSFT',
            current_price=310.0,
            confidence_score=70.0,
            position_size=0,
            sector='Technology',
            daily_volume=30000000,
            position_pnl_pct=8.5,
            decayed_confidence=55.0
        )
        self.assertEqual(decision, Decision.EXIT)
        self.assertIn("Exit approved", reason)
        
        # Force exit
        decision, reason = Governor.run(
            signal_type='EXIT',
            symbol='TSLA',
            current_price=180.0,
            confidence_score=65.0,
            position_size=0,
            sector='Automotive',
            daily_volume=25000000,
            position_pnl_pct=-5.0,
            decayed_confidence=40.0  # Below force exit threshold
        )
        self.assertEqual(decision, Decision.EXIT)
        self.assertIn("Force exit", reason)
    
    def test_unknown_signal_type(self):
        """Test handling of unknown signal types."""
        decision, reason = Governor.run(
            signal_type='UNKNOWN',
            symbol='TEST',
            current_price=50.0,
            confidence_score=75.0,
            position_size=500,
            sector='Test',
            daily_volume=500000
        )
        self.assertEqual(decision, Decision.NO_TRADE)
        self.assertIn("Unknown signal type", reason)
    
    def test_decision_summary(self):
        """Test decision summary statistics."""
        decisions = [
            (Decision.ENTER, "Entry approved"),
            (Decision.NO_TRADE, "Low confidence"),
            (Decision.EXIT, "Normal exit"),
            (Decision.EXIT, "Force exit"),
            (Decision.NO_TRADE, "Validation failed")
        ]
        
        summary = Governor.get_decision_summary(decisions)
        
        self.assertEqual(summary['ENTER'], 1)
        self.assertEqual(summary['NO_TRADE'], 2)
        self.assertEqual(summary['EXIT'], 2)
    
    def test_batch_processing_basic(self):
        """Test basic batch processing functionality."""
        df = pd.DataFrame({
            'signal_type': ['ENTRY', 'ENTRY', 'EXIT'],
            'symbol': ['AAPL', 'TSLA', 'MSFT'],
            'current_price': [150.0, 200.0, 310.0],
            'confidence_score': [75.0, 55.0, 70.0],
            'position_size': [500, 300, 0],
            'sector': ['Technology', 'Automotive', 'Technology'],
            'daily_volume': [50000000, 25000000, 30000000],
            'position_pnl_pct': [None, None, 8.5],
            'decayed_confidence': [None, None, 55.0]
        })
        
        result = Governor.batch_decisions(df)
        
        # Check columns added
        self.assertIn('decision', result.columns)
        self.assertIn('reason', result.columns)
        
        # Check data integrity
        self.assertEqual(len(result), 3)
        self.assertEqual(result.iloc[0]['decision'], 'ENTER')  # AAPL approved
        self.assertEqual(result.iloc[1]['decision'], 'NO_TRADE')  # TSLA rejected
        self.assertEqual(result.iloc[2]['decision'], 'EXIT')  # MSFT exit
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Exactly at confidence threshold
        decision, reason = Governor.run(
            signal_type='ENTRY',
            symbol='TEST',
            current_price=50.0,
            confidence_score=60.0,  # Exactly at minimum
            position_size=500,
            sector='Test',
            daily_volume=500000
        )
        self.assertEqual(decision, Decision.ENTER)
        
        # Just below confidence threshold
        decision, reason = Governor.run(
            signal_type='ENTRY',
            symbol='TEST',
            current_price=50.0,
            confidence_score=59.9,  # Just below minimum
            position_size=500,
            sector='Test',
            daily_volume=500000
        )
        self.assertEqual(decision, Decision.NO_TRADE)
        
        # Exactly at position size limit
        decision, reason = Governor.run(
            signal_type='ENTRY',
            symbol='TEST',
            current_price=50.0,
            confidence_score=75.0,
            position_size=10000,  # Exactly at maximum
            sector='Test',
            daily_volume=500000
        )
        self.assertEqual(decision, Decision.ENTER)
        
        # Just above position size limit
        decision, reason = Governor.run(
            signal_type='ENTRY',
            symbol='TEST',
            current_price=50.0,
            confidence_score=75.0,
            position_size=10001,  # Just above maximum
            sector='Test',
            daily_volume=500000
        )
        self.assertEqual(decision, Decision.NO_TRADE)


if __name__ == '__main__':
    unittest.main()