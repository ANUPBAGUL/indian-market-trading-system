"""
Integration tests for ExitEngine - Tests realistic trading scenarios.
"""

import unittest
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from exit_engine import ExitEngine


class TestExitEngineIntegration(unittest.TestCase):
    
    def test_complete_trade_lifecycle(self):
        """Test complete trade from entry to exit."""
        # Simulate a winning trade over 15 days
        trade_timeline = [
            {'day': 1, 'price': 50.0, 'atr': 2.0, 'sma20': 49.5, 'prev_stop': None},
            {'day': 3, 'price': 52.0, 'atr': 2.1, 'sma20': 50.2, 'prev_stop': 47.0},
            {'day': 5, 'price': 54.5, 'atr': 2.2, 'sma20': 51.0, 'prev_stop': 47.8},
            {'day': 8, 'price': 57.0, 'atr': 2.4, 'sma20': 52.5, 'prev_stop': 49.0},
            {'day': 12, 'price': 59.5, 'atr': 2.6, 'sma20': 54.8, 'prev_stop': 51.0},
            {'day': 15, 'price': 61.0, 'atr': 2.5, 'sma20': 56.2, 'prev_stop': 53.0},
        ]
        
        entry_price = 50.0
        results = []
        
        for data in trade_timeline:
            result = ExitEngine.update(
                current_price=data['price'],
                entry_price=entry_price,
                current_atr=data['atr'],
                sma20=data['sma20'],
                existing_stop=data['prev_stop'],
                position_age_days=data['day']
            )
            results.append(result)
        
        # Verify stop progression
        stop_prices = [r['stop_price'] for r in results]
        
        # Stops should generally trend higher (allowing for holds)
        self.assertGreater(stop_prices[-1], stop_prices[0])  # Final > Initial
        
        # Verify trend strength evolution
        trend_strengths = [r['trend_strength'] for r in results]
        self.assertEqual(trend_strengths[0], 'weak')    # Start weak
        self.assertEqual(trend_strengths[-1], 'strong') # End strong
        
        # Verify k-factor adaptation
        k_factors = [r['k_factor'] for r in results]
        self.assertEqual(k_factors[0], 1.5)  # Start tight
        self.assertEqual(k_factors[-1], 2.5) # End wide
    
    def test_different_market_scenarios(self):
        """Test exit engine across different market scenarios."""
        scenarios = [
            {
                'name': 'Sideways Market',
                'price': 51.0,
                'entry': 50.0,
                'atr': 1.8,
                'sma20': 50.8,
                'age': 10,
                'expected_trend': 'weak',
                'expected_k': 1.5
            },
            {
                'name': 'Bull Market Breakout',
                'price': 58.0,
                'entry': 50.0,
                'atr': 2.8,
                'sma20': 53.0,
                'age': 12,
                'expected_trend': 'strong',
                'expected_k': 2.5
            },
            {
                'name': 'Moderate Uptrend',
                'price': 53.5,
                'entry': 50.0,
                'atr': 2.2,
                'sma20': 51.5,
                'age': 6,
                'expected_trend': 'normal',
                'expected_k': 2.0
            }
        ]
        
        for scenario in scenarios:
            with self.subTest(scenario=scenario['name']):
                result = ExitEngine.update(
                    current_price=scenario['price'],
                    entry_price=scenario['entry'],
                    current_atr=scenario['atr'],
                    sma20=scenario['sma20'],
                    existing_stop=scenario['entry'] - 3.0,  # Previous stop
                    position_age_days=scenario['age']
                )
                
                self.assertEqual(result['trend_strength'], scenario['expected_trend'])
                self.assertEqual(result['k_factor'], scenario['expected_k'])
                self.assertGreater(result['stop_price'], scenario['entry'] - 3.0)
    
    def test_portfolio_exit_management(self):
        """Test batch exit management for multiple positions."""
        portfolio_data = pd.DataFrame({
            'symbol': ['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'NVDA'],
            'current_price': [155.0, 2650.0, 220.0, 310.0, 450.0],
            'entry_price': [150.0, 2500.0, 200.0, 300.0, 400.0],
            'current_atr': [3.5, 50.0, 15.0, 8.0, 25.0],
            'sma20': [152.0, 2580.0, 205.0, 308.0, 425.0],
            'existing_stop': [147.0, 2450.0, 185.0, 294.0, 375.0],
            'position_age_days': [5, 12, 3, 8, 15]
        })
        
        results = ExitEngine.batch_update(portfolio_data)
        
        # Verify all positions processed
        self.assertEqual(len(results), 5)
        
        # Check that all stops are reasonable
        for _, row in results.iterrows():
            self.assertGreater(row['stop_price'], 0)
            self.assertLess(row['stop_price'], row['current_price'])
            self.assertIn(row['trend_strength'], ['weak', 'normal', 'strong'])
            self.assertIn(row['k_factor'], [1.5, 2.0, 2.5])
        
        # Verify profitable positions have trailing stops
        profitable_positions = results[results['profit_loss_pct'] > 0]
        self.assertGreater(len(profitable_positions), 3)
        
        for _, pos in profitable_positions.iterrows():
            # Stop should be reasonably close to entry for profitable positions
            self.assertGreater(pos['stop_price'], pos['entry_price'] * 0.90)
    
    def test_stop_evolution_patterns(self):
        """Test different stop evolution patterns."""
        base_scenario = {
            'entry_price': 100.0,
            'current_atr': 4.0,
            'position_age_days': 7
        }
        
        # Test ascending price with different trend strengths
        price_scenarios = [
            {'price': 102.0, 'sma20': 101.5, 'expected_trend': 'weak'},
            {'price': 105.0, 'sma20': 101.0, 'expected_trend': 'normal'},
            {'price': 110.0, 'sma20': 103.0, 'expected_trend': 'strong'},
        ]
        
        previous_stop = 96.0  # Initial stop
        
        for scenario in price_scenarios:
            result = ExitEngine.update(
                current_price=scenario['price'],
                sma20=scenario['sma20'],
                existing_stop=previous_stop,
                **base_scenario
            )
            
            # Verify trend assessment
            self.assertEqual(result['trend_strength'], scenario['expected_trend'])
            
            # Verify stop advancement
            self.assertGreaterEqual(result['stop_price'], previous_stop)
            
            # Update for next iteration
            previous_stop = result['stop_price']
    
    def test_volatile_market_conditions(self):
        """Test exit management in volatile markets."""
        volatile_scenarios = [
            {
                'name': 'High Volatility Stock',
                'current_price': 50.0,
                'entry_price': 45.0,
                'current_atr': 8.0,  # Very high ATR
                'sma20': 47.0,
                'existing_stop': 40.0,
                'position_age_days': 5
            },
            {
                'name': 'Low Volatility Stock',
                'current_price': 105.0,
                'entry_price': 100.0,
                'current_atr': 1.0,  # Very low ATR
                'sma20': 102.0,
                'existing_stop': 98.0,
                'position_age_days': 8
            }
        ]
        
        for scenario in volatile_scenarios:
            with self.subTest(scenario=scenario['name']):
                result = ExitEngine.update(**{k: v for k, v in scenario.items() if k != 'name'})
                
                # Verify stop holds or advances
                self.assertGreaterEqual(result['stop_price'], scenario['existing_stop'])
                self.assertLess(result['stop_price'], scenario['current_price'])
                
                # Verify ATR distance scales with volatility
                expected_distance = result['k_factor'] * scenario['current_atr']
                self.assertEqual(result['atr_distance'], expected_distance)
    
    def test_position_age_impact(self):
        """Test how position age affects k-factor selection."""
        base_scenario = {
            'current_price': 55.0,
            'entry_price': 50.0,
            'current_atr': 2.5,
            'sma20': 52.0,  # Strong trend
            'existing_stop': 48.0
        }
        
        age_scenarios = [
            {'age': 1, 'expected_k': 2.5},   # New strong trend
            {'age': 5, 'expected_k': 2.5},   # Young strong trend
            {'age': 12, 'expected_k': 2.5},  # Mature strong trend
        ]
        
        for scenario in age_scenarios:
            result = ExitEngine.update(
                position_age_days=scenario['age'],
                **base_scenario
            )
            
            self.assertEqual(result['k_factor'], scenario['expected_k'])
    
    def test_stop_out_scenarios(self):
        """Test various stop-out scenarios."""
        stop_scenarios = [
            {'price': 47.5, 'stop': 48.0, 'should_exit': True, 'reason': 'Below stop'},
            {'price': 48.0, 'stop': 48.0, 'should_exit': True, 'reason': 'At stop'},
            {'price': 48.1, 'stop': 48.0, 'should_exit': False, 'reason': 'Above stop'},
        ]
        
        for scenario in stop_scenarios:
            is_stopped = ExitEngine.is_stopped_out(scenario['price'], scenario['stop'])
            self.assertEqual(is_stopped, scenario['should_exit'], 
                           f"Failed for {scenario['reason']}")


if __name__ == '__main__':
    unittest.main()