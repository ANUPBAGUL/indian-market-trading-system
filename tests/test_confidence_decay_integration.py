"""
Integration tests for ConfidenceDecay - Tests realistic trading scenarios.
"""

import unittest
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from confidence_decay import ConfidenceDecay


class TestConfidenceDecayIntegration(unittest.TestCase):
    
    def test_complete_trade_lifecycle(self):
        """Test confidence decay over complete trade lifecycle."""
        # Simulate a deteriorating trade over 25 days
        timeline_data = [
            {'day': 1, 'price': 50.0, 'price_5d_ago': 50.0, 'sector': 0.5, 'market': 0.3},
            {'day': 5, 'price': 51.0, 'price_5d_ago': 50.0, 'sector': 1.0, 'market': 0.8},
            {'day': 10, 'price': 51.5, 'price_5d_ago': 51.0, 'sector': 0.5, 'market': 1.0},
            {'day': 15, 'price': 51.3, 'price_5d_ago': 51.5, 'sector': -0.5, 'market': 0.5},
            {'day': 20, 'price': 51.1, 'price_5d_ago': 51.3, 'sector': -1.8, 'market': 0.2},
            {'day': 25, 'price': 50.8, 'price_5d_ago': 51.1, 'sector': -2.2, 'market': 0.5},
        ]
        
        initial_confidence = 75.0
        entry_price = 50.0
        results = []
        
        for data in timeline_data:
            result = ConfidenceDecay.decay_confidence(
                initial_confidence=initial_confidence,
                position_age_days=data['day'],
                entry_price=entry_price,
                current_price=data['price'],
                price_5_days_ago=data['price_5d_ago'],
                sector_performance_5d=data['sector'],
                market_performance_5d=data['market']
            )
            results.append(result)
        
        # Verify progressive decay
        confidences = [r['decayed_confidence'] for r in results]
        
        # Confidence should generally decline over time
        self.assertGreater(confidences[0], confidences[-1])
        
        # Early days should have minimal decay
        self.assertGreater(confidences[1], 70.0)  # Day 5
        
        # Later days should show significant decay
        self.assertLess(confidences[-1], 65.0)  # Day 25
        
        # Check that decay factors accumulate
        final_result = results[-1]
        self.assertGreater(len(final_result['decay_factors']), 1)
    
    def test_different_market_scenarios(self):
        """Test confidence decay across different market scenarios."""
        scenarios = [
            {
                'name': 'Bull Market Winner',
                'initial_confidence': 80.0,
                'age': 12,
                'entry_price': 50.0,
                'current_price': 58.0,  # Strong winner
                'price_5d_ago': 56.0,   # Good momentum
                'sector_perf': 2.5,
                'market_perf': 1.8,
                'expected_minimal_decay': True
            },
            {
                'name': 'Sideways Grinder',
                'initial_confidence': 70.0,
                'age': 18,
                'entry_price': 100.0,
                'current_price': 101.0,  # Minimal gain
                'price_5d_ago': 100.8,   # Stagnant
                'sector_perf': 0.2,
                'market_perf': 0.5,
                'expected_minimal_decay': False
            },
            {
                'name': 'Sector Rotation Victim',
                'initial_confidence': 75.0,
                'age': 15,
                'entry_price': 25.0,
                'current_price': 26.0,   # Small gain
                'price_5d_ago': 25.8,    # Stagnant
                'sector_perf': -3.0,     # Sector weak
                'market_perf': 1.0,
                'expected_minimal_decay': False
            }
        ]
        
        for scenario in scenarios:
            with self.subTest(scenario=scenario['name']):
                result = ConfidenceDecay.decay_confidence(
                    initial_confidence=scenario['initial_confidence'],
                    position_age_days=scenario['age'],
                    entry_price=scenario['entry_price'],
                    current_price=scenario['current_price'],
                    price_5_days_ago=scenario['price_5d_ago'],
                    sector_performance_5d=scenario['sector_perf'],
                    market_performance_5d=scenario['market_perf']
                )
                
                if scenario['expected_minimal_decay']:
                    # Strong performers should have minimal decay
                    self.assertGreater(result['decayed_confidence'], 
                                     scenario['initial_confidence'] - 5.0)
                else:
                    # Weak performers should have significant decay
                    self.assertLess(result['decayed_confidence'], 
                                   scenario['initial_confidence'] - 3.0)
    
    def test_portfolio_decay_management(self):
        """Test batch decay management for portfolio positions."""
        portfolio_data = pd.DataFrame({
            'symbol': ['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'NVDA'],
            'initial_confidence': [85.0, 72.0, 68.0, 79.0, 81.0],
            'position_age_days': [8, 15, 22, 12, 18],
            'entry_price': [150.0, 2500.0, 200.0, 300.0, 400.0],
            'current_price': [155.0, 2480.0, 198.0, 305.0, 402.0],
            'price_5_days_ago': [154.0, 2485.0, 198.2, 304.8, 401.5],
            'sector_performance_5d': [1.2, -1.5, -2.8, 0.8, 1.0],
            'market_performance_5d': [0.8, 0.5, 0.5, 0.5, 0.5]
        })
        
        results = ConfidenceDecay.batch_decay(portfolio_data)
        
        # Verify all positions processed
        self.assertEqual(len(results), 5)
        
        # Check that all positions have some decay applied
        for i, row in results.iterrows():
            original_conf = row['initial_confidence']
            decayed_conf = row['decayed_confidence']
            
            # Most positions should have some decay (except very young winners)
            if row['position_age_days'] > 10:
                self.assertLess(decayed_conf, original_conf)
        
        # Check for force exits
        force_exits = results[results['force_exit'] == True]
        
        # Verify positions with heavy decay factors get flagged
        heavy_decay_positions = results[results['total_decay'] > 8.0]
        if len(heavy_decay_positions) > 0:
            # These should be close to or at force exit
            for _, pos in heavy_decay_positions.iterrows():
                self.assertLess(pos['decayed_confidence'], 60.0)
    
    def test_decay_factor_interactions(self):
        """Test how different decay factors interact."""
        base_scenario = {
            'initial_confidence': 70.0,
            'entry_price': 50.0,
            'current_price': 51.0,
            'sector_performance_5d': 0.5,
            'market_performance_5d': 0.8
        }
        
        # Test individual factors
        scenarios = [
            # Time decay only
            {'age': 20, 'price_5d_ago': 49.0, 'expected_factors': ['time_decay']},
            # Stagnation decay only  
            {'age': 5, 'price_5d_ago': 50.9, 'expected_factors': ['stagnation_decay']},
            # Combined factors
            {'age': 18, 'price_5d_ago': 50.95, 'expected_factors': ['time_decay', 'stagnation_decay']},
        ]
        
        for i, scenario in enumerate(scenarios):
            with self.subTest(f"Scenario {i+1}"):
                result = ConfidenceDecay.decay_confidence(
                    position_age_days=scenario['age'],
                    price_5_days_ago=scenario['price_5d_ago'],
                    **base_scenario
                )
                
                # Verify expected factors are present
                for expected_factor in scenario['expected_factors']:
                    self.assertIn(expected_factor, result['decay_factors'])
                
                # Verify total decay matches sum of individual factors
                expected_total = sum(result['decay_factors'].values())
                self.assertAlmostEqual(result['total_decay'], expected_total, places=1)
    
    def test_force_exit_scenarios(self):
        """Test various scenarios that trigger force exits."""
        force_exit_scenarios = [
            {
                'name': 'Old Stagnant Position',
                'initial_confidence': 55.0,  # Start marginal
                'age': 25,                    # Heavy time decay
                'stagnant': True,             # Add stagnation decay
                'weak_sector': True           # Add sector decay
            },
            {
                'name': 'Moderate Age High Decay',
                'initial_confidence': 48.0,  # Start lower
                'age': 18,                    # Moderate time decay
                'stagnant': True,             # Add stagnation decay
                'weak_sector': True           # Add sector decay
            },
            {
                'name': 'Young Position Heavy Sector Weakness',
                'initial_confidence': 48.0,  # Start very low
                'age': 8,                     # No time decay
                'stagnant': True,             # Add stagnation decay
                'weak_sector': True           # Add sector decay
            }
        ]
        
        for scenario in force_exit_scenarios:
            with self.subTest(scenario=scenario['name']):
                result = ConfidenceDecay.decay_confidence(
                    initial_confidence=scenario['initial_confidence'],
                    position_age_days=scenario['age'],
                    entry_price=50.0,
                    current_price=50.5,
                    price_5_days_ago=50.4 if scenario['stagnant'] else 49.0,
                    sector_performance_5d=-2.5 if scenario['weak_sector'] else 0.5,
                    market_performance_5d=0.5
                )
                
                # All scenarios should trigger force exit
                self.assertTrue(result['force_exit'])
                self.assertLess(result['decayed_confidence'], 45.0)
    
    def test_confidence_preservation_scenarios(self):
        """Test scenarios where confidence should be preserved."""
        preservation_scenarios = [
            {
                'name': 'Young Strong Winner',
                'initial_confidence': 85.0,
                'age': 5,                     # Within grace period
                'entry_price': 50.0,
                'current_price': 55.0,       # Strong winner
                'price_5d_ago': 53.0,        # Good momentum
                'sector_perf': 2.0,          # Strong sector
                'market_perf': 1.5
            },
            {
                'name': 'Moderate Age Good Performance',
                'initial_confidence': 78.0,
                'age': 12,                    # Some time decay
                'entry_price': 100.0,
                'current_price': 108.0,      # Good winner
                'price_5d_ago': 105.0,       # Good momentum
                'sector_perf': 1.8,          # Outperforming sector
                'market_perf': 1.2
            }
        ]
        
        for scenario in preservation_scenarios:
            with self.subTest(scenario=scenario['name']):
                result = ConfidenceDecay.decay_confidence(
                    initial_confidence=scenario['initial_confidence'],
                    position_age_days=scenario['age'],
                    entry_price=scenario['entry_price'],
                    current_price=scenario['current_price'],
                    price_5_days_ago=scenario['price_5d_ago'],
                    sector_performance_5d=scenario['sector_perf'],
                    market_performance_5d=scenario['market_perf']
                )
                
                # Should have minimal decay
                decay_percentage = (result['total_decay'] / scenario['initial_confidence']) * 100
                self.assertLess(decay_percentage, 10.0)  # Less than 10% decay
                self.assertFalse(result['force_exit'])
    
    def test_realistic_position_aging(self):
        """Test realistic position aging over extended periods."""
        # Track same position over 30 days with varying conditions
        initial_confidence = 80.0
        entry_price = 50.0
        
        # Simulate realistic price and sector evolution
        daily_data = [
            # Week 1: Strong start
            (5, 52.0, 50.0, 1.5, 1.0),
            (10, 53.5, 52.0, 1.2, 0.8),
            # Week 2-3: Momentum fades
            (15, 54.0, 53.5, 0.5, 0.6),
            (20, 53.8, 54.0, -0.8, 0.3),
            # Week 4: Deterioration
            (25, 53.2, 53.8, -1.5, 0.2),
            (30, 52.8, 53.2, -2.2, 0.1),
        ]
        
        results = []
        for day, price, price_5d_ago, sector_perf, market_perf in daily_data:
            result = ConfidenceDecay.decay_confidence(
                initial_confidence=initial_confidence,
                position_age_days=day,
                entry_price=entry_price,
                current_price=price,
                price_5_days_ago=price_5d_ago,
                sector_performance_5d=sector_perf,
                market_performance_5d=market_perf
            )
            results.append((day, result))
        
        # Verify realistic decay progression
        confidences = [r[1]['decayed_confidence'] for r in results]
        
        # Should show progressive decline
        self.assertGreater(confidences[0], confidences[-1])
        
        # Early stages should maintain high confidence
        self.assertGreater(confidences[0], 75.0)
        
        # Later stages should show significant decay
        self.assertLess(confidences[-1], 70.0)
        
        # Check that decay accelerates as conditions worsen
        early_decay = confidences[0] - confidences[1]
        late_decay = confidences[-2] - confidences[-1]
        self.assertGreater(late_decay, early_decay)


if __name__ == '__main__':
    unittest.main()