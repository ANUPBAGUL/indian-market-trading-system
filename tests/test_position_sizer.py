"""
Unit tests for PositionSizer - Tests individual methods and edge cases.
"""

import unittest
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from position_sizer import PositionSizer


class TestPositionSizer(unittest.TestCase):
    
    def setUp(self):
        self.account_value = 100000
        self.base_risk = self.account_value * 0.01  # $1000
    
    def test_basic_position_sizing(self):
        """Test basic position sizing calculation."""
        result = PositionSizer.position_size(
            account_value=self.account_value,
            entry_price=50.0,
            atr=2.0,
            confidence_score=80.0
        )
        
        expected_stop = 50.0 - (2.0 * 2.0)  # 46.0
        expected_risk = self.base_risk * 0.85  # 80% confidence = 85% participation
        expected_size = int(expected_risk / 4.0)  # risk / stop_distance
        
        self.assertEqual(result['stop_price'], 46.0)
        self.assertEqual(result['risk_amount'], 850.0)
        self.assertEqual(result['position_size'], expected_size)
        self.assertEqual(result['participation_rate'], 0.85)
    
    def test_confidence_thresholds(self):
        """Test confidence participation mapping."""
        test_cases = [
            (55.0, 0.0),   # Below threshold
            (62.0, 0.25),  # 60+ bucket
            (68.0, 0.40),  # 65+ bucket
            (73.0, 0.55),  # 70+ bucket
            (78.0, 0.70),  # 75+ bucket
            (83.0, 0.85),  # 80+ bucket
            (88.0, 1.00),  # 85+ bucket
        ]
        
        for confidence, expected_participation in test_cases:
            result = PositionSizer.position_size(
                account_value=self.account_value,
                entry_price=100.0,
                atr=5.0,
                confidence_score=confidence
            )
            
            if confidence < 60:
                self.assertEqual(result['position_size'], 0)
            else:
                self.assertEqual(result['participation_rate'], expected_participation)
    
    def test_volatility_adjustment(self):
        """Test volatility-based size reduction."""
        # Normal volatility (no adjustment)
        result_normal = PositionSizer.position_size(
            account_value=self.account_value,
            entry_price=50.0,
            atr=2.0,
            confidence_score=80.0,
            daily_volatility=0.03  # 3% - below threshold
        )
        self.assertEqual(result_normal['volatility_adjustment'], 1.0)
        
        # High volatility (adjustment applied)
        result_high = PositionSizer.position_size(
            account_value=self.account_value,
            entry_price=50.0,
            atr=2.0,
            confidence_score=80.0,
            daily_volatility=0.10  # 10% - above threshold
        )
        expected_adj = 0.05 / 0.10  # MAX_THRESHOLD / daily_vol
        self.assertEqual(result_high['volatility_adjustment'], expected_adj)
        self.assertLess(result_high['position_size'], result_normal['position_size'])
    
    def test_atr_stop_calculation(self):
        """Test ATR-based stop distance calculation."""
        test_cases = [
            (100.0, 2.5, 95.0),   # 100 - (2.5 * 2.0)
            (50.0, 1.0, 48.0),    # 50 - (1.0 * 2.0)
            (25.0, 0.5, 24.0),    # 25 - (0.5 * 2.0)
        ]
        
        for entry_price, atr, expected_stop in test_cases:
            result = PositionSizer.position_size(
                account_value=self.account_value,
                entry_price=entry_price,
                atr=atr,
                confidence_score=80.0
            )
            
            self.assertEqual(result['stop_price'], expected_stop)
            self.assertEqual(result['stop_distance'], atr * 2.0)
    
    def test_risk_consistency(self):
        """Test that risk remains consistent across different scenarios."""
        scenarios = [
            {'price': 20.0, 'atr': 1.0},
            {'price': 100.0, 'atr': 5.0},
            {'price': 500.0, 'atr': 25.0}
        ]
        
        confidence = 75.0  # 70% participation
        expected_risk = self.base_risk * 0.70
        
        for scenario in scenarios:
            result = PositionSizer.position_size(
                account_value=self.account_value,
                entry_price=scenario['price'],
                atr=scenario['atr'],
                confidence_score=confidence
            )
            
            self.assertAlmostEqual(result['risk_amount'], expected_risk, places=0)
    
    def test_below_threshold_confidence(self):
        """Test handling of below-threshold confidence."""
        result = PositionSizer.position_size(
            account_value=self.account_value,
            entry_price=50.0,
            atr=2.0,
            confidence_score=55.0  # Below 60% threshold
        )
        
        self.assertEqual(result['position_size'], 0)
        self.assertEqual(result['risk_amount'], 0.0)
        self.assertEqual(result['participation_rate'], 0.0)
        self.assertIn('Below minimum confidence', result['reason'])
    
    def test_participation_rate_mapping(self):
        """Test internal participation rate mapping function."""
        test_cases = [
            (59.0, 0.0),
            (60.0, 0.25),
            (65.0, 0.40),
            (70.0, 0.55),
            (75.0, 0.70),
            (80.0, 0.85),
            (85.0, 1.00),
            (95.0, 1.00),
        ]
        
        for confidence, expected_rate in test_cases:
            actual_rate = PositionSizer._get_participation_rate(confidence)
            self.assertEqual(actual_rate, expected_rate)
    
    def test_volatility_adjustment_edge_cases(self):
        """Test volatility adjustment edge cases."""
        # Exactly at threshold
        adj_threshold = PositionSizer._get_volatility_adjustment(0.05)
        self.assertEqual(adj_threshold, 1.0)
        
        # Very high volatility (minimum adjustment)
        adj_high = PositionSizer._get_volatility_adjustment(0.20)
        self.assertEqual(adj_high, 0.25)  # Minimum adjustment
        
        # Moderate high volatility
        adj_moderate = PositionSizer._get_volatility_adjustment(0.08)
        expected = 0.05 / 0.08
        self.assertAlmostEqual(adj_moderate, expected, places=3)
    
    def test_batch_processing_basic(self):
        """Test basic batch processing functionality."""
        df = pd.DataFrame({
            'entry_price': [50.0, 100.0],
            'atr': [2.0, 4.0],
            'confidence_score': [80.0, 70.0],
            'daily_volatility': [0.03, 0.06]
        })
        
        result = PositionSizer.batch_size(df, self.account_value)
        
        # Check columns added
        expected_cols = ['position_size', 'stop_price', 'risk_amount', 'participation_rate']
        for col in expected_cols:
            self.assertIn(col, result.columns)
        
        # Check data integrity
        self.assertEqual(len(result), 2)
        self.assertGreater(result.iloc[0]['position_size'], 0)
        self.assertGreater(result.iloc[1]['position_size'], 0)


if __name__ == '__main__':
    unittest.main()