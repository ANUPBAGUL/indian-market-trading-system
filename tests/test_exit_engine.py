"""
Unit tests for ExitEngine - Tests individual methods and edge cases.
"""

import unittest
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from exit_engine import ExitEngine


class TestExitEngine(unittest.TestCase):
    
    def test_initial_stop_calculation(self):
        """Test initial stop setting for new positions."""
        result = ExitEngine.update(
            current_price=50.0,
            entry_price=50.0,
            current_atr=2.0,
            sma20=49.5,
            existing_stop=None,  # New position
            position_age_days=0
        )
        
        # Weak trend (price near SMA) should use 1.5x k-factor
        expected_stop = 50.0 - (1.5 * 2.0)  # 47.0
        self.assertEqual(result['stop_price'], 47.0)
        self.assertEqual(result['k_factor'], 1.5)
        self.assertEqual(result['stop_type'], 'initial')
        self.assertEqual(result['trend_strength'], 'weak')
    
    def test_trailing_stop_advancement(self):
        """Test trailing stop moves higher with price."""
        result = ExitEngine.update(
            current_price=55.0,
            entry_price=50.0,
            current_atr=2.2,
            sma20=52.0,  # Strong trend
            existing_stop=46.0,
            position_age_days=8
        )
        
        # Strong trend should use 2.5x k-factor
        # New trailing stop: 55.0 - (2.5 * 2.2) = 49.5
        # Should be higher than existing 46.0
        self.assertEqual(result['stop_price'], 49.5)
        self.assertEqual(result['k_factor'], 2.5)
        self.assertEqual(result['stop_type'], 'trailing')
        self.assertEqual(result['trend_strength'], 'strong')
    
    def test_trailing_stop_holds(self):
        """Test trailing stop doesn't move down."""
        result = ExitEngine.update(
            current_price=52.0,
            entry_price=50.0,
            current_atr=2.0,
            sma20=51.0,
            existing_stop=49.0,  # Higher than calculated trailing stop
            position_age_days=5
        )
        
        # Calculated trailing: 52.0 - (2.0 * 2.0) = 48.0
        # Should hold existing 49.0 stop
        self.assertEqual(result['stop_price'], 49.0)
        self.assertEqual(result['stop_type'], 'held')
    
    def test_trend_strength_assessment(self):
        """Test trend strength classification."""
        test_cases = [
            (50.0, 50.5, 'weak'),    # Within 2% of SMA
            (50.0, 48.0, 'normal'),  # 4% above SMA
            (50.0, 47.0, 'strong'),  # 6% above SMA
        ]
        
        for price, sma, expected_trend in test_cases:
            trend = ExitEngine._assess_trend_strength(price, sma)
            self.assertEqual(trend, expected_trend)
    
    def test_k_factor_selection(self):
        """Test k-factor selection based on trend and age."""
        test_cases = [
            ('weak', 0, 1.5),      # Weak trend, new position
            ('normal', 0, 2.0),    # Normal trend, new position
            ('strong', 0, 2.5),    # Strong trend, new position
            ('normal', 6, 2.0),    # Normal trend, mature position
            ('strong', 12, 2.5),   # Strong trend, very mature position
        ]
        
        for trend, age, expected_k in test_cases:
            k_factor = ExitEngine._select_k_factor(trend, age)
            self.assertEqual(k_factor, expected_k)
    
    def test_profit_loss_calculation(self):
        """Test profit/loss percentage calculation."""
        result = ExitEngine.update(
            current_price=55.0,
            entry_price=50.0,
            current_atr=2.0,
            sma20=52.0,
            existing_stop=47.0,
            position_age_days=5
        )
        
        expected_pnl = ((55.0 - 50.0) / 50.0) * 100  # 10.0%
        self.assertEqual(result['profit_loss_pct'], 10.0)
    
    def test_atr_distance_calculation(self):
        """Test ATR distance calculation."""
        result = ExitEngine.update(
            current_price=50.0,
            entry_price=50.0,
            current_atr=2.5,
            sma20=47.0,  # Strong trend
            existing_stop=None,
            position_age_days=0
        )
        
        expected_distance = 2.5 * 2.5  # k_factor * ATR
        self.assertEqual(result['atr_distance'], 6.25)
    
    def test_stop_out_detection(self):
        """Test stop-out detection logic."""
        test_cases = [
            (48.0, 47.0, False),  # Above stop
            (47.0, 47.0, True),   # At stop
            (46.5, 47.0, True),   # Below stop
        ]
        
        for price, stop, expected_stopped in test_cases:
            is_stopped = ExitEngine.is_stopped_out(price, stop)
            self.assertEqual(is_stopped, expected_stopped)
    
    def test_batch_processing_basic(self):
        """Test basic batch processing functionality."""
        df = pd.DataFrame({
            'current_price': [52.0, 105.0],
            'entry_price': [50.0, 100.0],
            'current_atr': [2.0, 4.0],
            'sma20': [51.0, 102.0],
            'existing_stop': [47.0, 96.0],
            'position_age_days': [5, 8]
        })
        
        result = ExitEngine.batch_update(df)
        
        # Check columns added
        expected_cols = ['stop_price', 'k_factor', 'trend_strength', 'stop_type']
        for col in expected_cols:
            self.assertIn(col, result.columns)
        
        # Check data integrity
        self.assertEqual(len(result), 2)
        self.assertGreater(result.iloc[0]['stop_price'], 47.0)  # Should trail higher
        self.assertGreater(result.iloc[1]['stop_price'], 96.0)  # Should trail higher
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Zero ATR
        result = ExitEngine.update(
            current_price=50.0,
            entry_price=50.0,
            current_atr=0.0,
            sma20=50.0,
            existing_stop=None,
            position_age_days=0
        )
        self.assertEqual(result['stop_price'], 50.0)  # No stop distance
        
        # Very high ATR
        result = ExitEngine.update(
            current_price=100.0,
            entry_price=100.0,
            current_atr=20.0,
            sma20=95.0,
            existing_stop=None,
            position_age_days=0
        )
        expected_stop = 100.0 - (2.5 * 20.0)  # Strong trend, wide stop
        self.assertEqual(result['stop_price'], 50.0)


if __name__ == '__main__':
    unittest.main()