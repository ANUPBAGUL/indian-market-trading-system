"""
Unit tests for ConfidenceDecay - Tests individual methods and edge cases.
"""

import unittest
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from confidence_decay import ConfidenceDecay


class TestConfidenceDecay(unittest.TestCase):
    
    def test_time_decay_calculation(self):
        """Test time-based decay calculation."""
        # No decay within grace period
        decay = ConfidenceDecay._calculate_time_decay(5)
        self.assertEqual(decay, 0.0)
        
        decay = ConfidenceDecay._calculate_time_decay(10)
        self.assertEqual(decay, 0.0)
        
        # Linear decay after grace period
        decay = ConfidenceDecay._calculate_time_decay(15)
        expected = (15 - 10) * 0.5  # 5 excess days * 0.5% = 2.5%
        self.assertEqual(decay, expected)
        
        decay = ConfidenceDecay._calculate_time_decay(20)
        expected = (20 - 10) * 0.5  # 10 excess days * 0.5% = 5.0%
        self.assertEqual(decay, expected)
    
    def test_stagnation_decay_calculation(self):
        """Test price stagnation decay calculation."""
        # No decay for significant movement
        decay = ConfidenceDecay._calculate_stagnation_decay(100.0, 97.0)  # 3% movement
        self.assertEqual(decay, 0.0)
        
        # Decay for minimal movement
        decay = ConfidenceDecay._calculate_stagnation_decay(100.0, 99.5)  # 0.5% movement
        self.assertEqual(decay, 2.0)
        
        # Handle zero price case
        decay = ConfidenceDecay._calculate_stagnation_decay(100.0, 0.0)
        self.assertEqual(decay, 0.0)
        
        # Exact threshold case
        decay = ConfidenceDecay._calculate_stagnation_decay(100.0, 98.0)  # Exactly 2%
        self.assertEqual(decay, 0.0)  # At threshold, no decay
    
    def test_sector_decay_calculation(self):
        """Test sector weakness decay calculation."""
        # No decay when sector outperforms
        decay = ConfidenceDecay._calculate_sector_decay(2.0, 1.0)  # +1% relative
        self.assertEqual(decay, 0.0)
        
        # No decay for minor underperformance
        decay = ConfidenceDecay._calculate_sector_decay(1.0, 1.5)  # -0.5% relative
        self.assertEqual(decay, 0.0)
        
        # Decay for significant underperformance
        decay = ConfidenceDecay._calculate_sector_decay(-1.0, 1.0)  # -2% relative
        self.assertEqual(decay, 1.5)
        
        # Decay at threshold
        decay = ConfidenceDecay._calculate_sector_decay(0.0, 1.0)  # -1% relative
        self.assertEqual(decay, 0.0)  # Exactly at threshold, no decay
        
        decay = ConfidenceDecay._calculate_sector_decay(-0.1, 1.0)  # -1.1% relative
        self.assertEqual(decay, 1.5)  # Just below threshold, decay applied
    
    def test_basic_confidence_decay(self):
        """Test basic confidence decay with single factors."""
        # Time decay only
        result = ConfidenceDecay.decay_confidence(
            initial_confidence=80.0,
            position_age_days=15,  # 5 days past grace period
            entry_price=50.0,
            current_price=52.0,
            price_5_days_ago=51.5,  # >2% movement, no stagnation
            sector_performance_5d=1.0,
            market_performance_5d=0.8  # Sector outperforms
        )
        
        self.assertEqual(result['decayed_confidence'], 75.5)  # 80 - 2.5 - 2.0 (stagnation)
        self.assertEqual(result['total_decay'], 4.5)
        self.assertIn('time_decay', result['decay_factors'])
        self.assertIn('stagnation_decay', result['decay_factors'])
        self.assertEqual(result['decay_factors']['time_decay'], 2.5)
        self.assertFalse(result['force_exit'])
    
    def test_multiple_decay_factors(self):
        """Test confidence decay with multiple factors."""
        result = ConfidenceDecay.decay_confidence(
            initial_confidence=70.0,
            position_age_days=18,  # Time decay: 4.0%
            entry_price=100.0,
            current_price=100.5,  # Stagnation decay: 2.0%
            price_5_days_ago=100.3,
            sector_performance_5d=-1.8,  # Sector decay: 1.5%
            market_performance_5d=0.5
        )
        
        expected_decay = 4.0 + 2.0 + 1.5  # 7.5%
        self.assertEqual(result['decayed_confidence'], 62.5)  # 70 - 7.5
        self.assertEqual(result['total_decay'], expected_decay)
        self.assertEqual(len(result['decay_factors']), 3)
        self.assertFalse(result['force_exit'])
    
    def test_force_exit_condition(self):
        """Test forced exit when confidence drops too low."""
        result = ConfidenceDecay.decay_confidence(
            initial_confidence=50.0,  # Start low
            position_age_days=25,     # Heavy time decay: 7.5%
            entry_price=50.0,
            current_price=49.0,
            price_5_days_ago=49.1,    # Stagnation decay: 2.0%
            sector_performance_5d=-2.0,  # Sector decay: 1.5%
            market_performance_5d=0.5
        )
        
        # 50 - 7.5 - 2.0 - 1.5 = 39.0% (below 45% threshold)
        self.assertEqual(result['decayed_confidence'], 39.0)
        self.assertTrue(result['force_exit'])
    
    def test_no_decay_scenarios(self):
        """Test scenarios where no decay should occur."""
        result = ConfidenceDecay.decay_confidence(
            initial_confidence=75.0,
            position_age_days=8,      # Within grace period
            entry_price=50.0,
            current_price=52.0,       # Good movement
            price_5_days_ago=50.5,    # >2% movement
            sector_performance_5d=1.5,  # Sector outperforms
            market_performance_5d=1.0
        )
        
        self.assertEqual(result['decayed_confidence'], 75.0)  # No decay
        self.assertEqual(result['total_decay'], 0.0)
        self.assertEqual(len(result['decay_factors']), 0)
        self.assertFalse(result['force_exit'])
    
    def test_pnl_calculation(self):
        """Test profit/loss percentage calculation."""
        result = ConfidenceDecay.decay_confidence(
            initial_confidence=70.0,
            position_age_days=5,
            entry_price=100.0,
            current_price=105.0,  # 5% gain
            price_5_days_ago=104.0,
            sector_performance_5d=1.0,
            market_performance_5d=0.8
        )
        
        self.assertEqual(result['current_pnl_pct'], 5.0)
        
        # Test loss scenario
        result = ConfidenceDecay.decay_confidence(
            initial_confidence=70.0,
            position_age_days=5,
            entry_price=100.0,
            current_price=97.0,  # 3% loss
            price_5_days_ago=97.5,
            sector_performance_5d=1.0,
            market_performance_5d=0.8
        )
        
        self.assertEqual(result['current_pnl_pct'], -3.0)
    
    def test_should_force_exit(self):
        """Test force exit threshold function."""
        self.assertFalse(ConfidenceDecay.should_force_exit(50.0))
        self.assertFalse(ConfidenceDecay.should_force_exit(45.0))
        self.assertTrue(ConfidenceDecay.should_force_exit(44.9))
        self.assertTrue(ConfidenceDecay.should_force_exit(30.0))
    
    def test_batch_processing_basic(self):
        """Test basic batch processing functionality."""
        df = pd.DataFrame({
            'initial_confidence': [80.0, 70.0],
            'position_age_days': [15, 8],
            'entry_price': [50.0, 100.0],
            'current_price': [52.0, 101.0],
            'price_5_days_ago': [51.5, 100.8],
            'sector_performance_5d': [1.0, -1.5],
            'market_performance_5d': [0.8, 0.5]
        })
        
        result = ConfidenceDecay.batch_decay(df)
        
        # Check columns added
        expected_cols = ['decayed_confidence', 'total_decay', 'decay_factors', 'force_exit']
        for col in expected_cols:
            self.assertIn(col, result.columns)
        
        # Check data integrity
        self.assertEqual(len(result), 2)
        self.assertLess(result.iloc[0]['decayed_confidence'], 80.0)  # Should have decay
        self.assertLess(result.iloc[1]['decayed_confidence'], 70.0)  # Should have decay
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Zero confidence input
        result = ConfidenceDecay.decay_confidence(
            initial_confidence=0.0,
            position_age_days=20,
            entry_price=50.0,
            current_price=50.0,
            price_5_days_ago=50.0,
            sector_performance_5d=0.0,
            market_performance_5d=0.0
        )
        self.assertEqual(result['decayed_confidence'], 0.0)
        
        # Very high initial confidence
        result = ConfidenceDecay.decay_confidence(
            initial_confidence=100.0,
            position_age_days=30,  # Heavy decay
            entry_price=50.0,
            current_price=50.1,   # Stagnant
            price_5_days_ago=50.0,
            sector_performance_5d=-3.0,  # Weak sector
            market_performance_5d=1.0
        )
        # Should still have significant confidence despite decay
        self.assertGreater(result['decayed_confidence'], 80.0)


if __name__ == '__main__':
    unittest.main()