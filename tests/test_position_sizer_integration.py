"""
Integration tests for PositionSizer - Tests realistic trading scenarios.
"""

import unittest
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from position_sizer import PositionSizer


class TestPositionSizerIntegration(unittest.TestCase):
    
    def setUp(self):
        self.account_value = 100000
    
    def test_realistic_trading_scenarios(self):
        """Test position sizing with realistic market scenarios."""
        scenarios = [
            {
                'name': 'High Confidence Blue Chip',
                'entry_price': 150.0,
                'atr': 3.5,
                'confidence_score': 87.2,
                'daily_volatility': 0.025,
                'expected_participation': 1.00,
                'expected_vol_adj': 1.0
            },
            {
                'name': 'Medium Confidence Growth Stock',
                'entry_price': 75.0,
                'atr': 4.2,
                'confidence_score': 68.5,
                'daily_volatility': 0.055,
                'expected_participation': 0.40,
                'expected_vol_adj': 0.909  # 0.05/0.055
            },
            {
                'name': 'High Volatility Momentum Play',
                'entry_price': 200.0,
                'atr': 15.0,
                'confidence_score': 82.1,
                'daily_volatility': 0.12,
                'expected_participation': 0.85,
                'expected_vol_adj': 0.417  # 0.05/0.12
            }
        ]
        
        for scenario in scenarios:
            with self.subTest(scenario=scenario['name']):
                result = PositionSizer.position_size(
                    account_value=self.account_value,
                    entry_price=scenario['entry_price'],
                    atr=scenario['atr'],
                    confidence_score=scenario['confidence_score'],
                    daily_volatility=scenario['daily_volatility']
                )
                
                # Verify participation rate
                self.assertAlmostEqual(
                    result['participation_rate'], 
                    scenario['expected_participation'], 
                    places=2
                )
                
                # Verify volatility adjustment
                self.assertAlmostEqual(
                    result['volatility_adjustment'], 
                    scenario['expected_vol_adj'], 
                    places=2
                )
                
                # Verify position size is reasonable
                self.assertGreater(result['position_size'], 0)
                
                # Verify stop price calculation
                expected_stop = scenario['entry_price'] - (scenario['atr'] * 2.0)
                self.assertEqual(result['stop_price'], expected_stop)
    
    def test_portfolio_screening_workflow(self):
        """Test batch sizing for portfolio screening workflow."""
        # Simulate daily screening results
        portfolio_data = pd.DataFrame({
            'symbol': ['AAPL', 'GOOGL', 'TSLA', 'MSFT', 'NVDA', 'AMZN'],
            'entry_price': [150.0, 2500.0, 200.0, 300.0, 450.0, 3200.0],
            'atr': [3.5, 45.0, 12.0, 8.0, 25.0, 60.0],
            'confidence_score': [85.2, 72.1, 45.8, 89.3, 67.4, 78.9],
            'daily_volatility': [0.035, 0.028, 0.095, 0.025, 0.065, 0.040]
        })
        
        results = PositionSizer.batch_size(portfolio_data, self.account_value)
        
        # Verify all stocks processed
        self.assertEqual(len(results), 6)
        
        # Check that low confidence stocks are filtered out
        low_conf_stocks = results[results['confidence_score'] < 60]
        for _, stock in low_conf_stocks.iterrows():
            self.assertEqual(stock['position_size'], 0)
        
        # Check that tradeable stocks have reasonable sizes
        tradeable_stocks = results[results['position_size'] > 0]
        self.assertGreater(len(tradeable_stocks), 3)
        
        # Verify risk amounts are consistent for same confidence levels
        high_conf_stocks = results[results['confidence_score'] >= 85]
        if len(high_conf_stocks) > 1:
            risk_amounts = high_conf_stocks['risk_amount'].values
            # Should be similar (within volatility adjustments)
            self.assertLess(max(risk_amounts) - min(risk_amounts), 200)
    
    def test_risk_scaling_by_confidence(self):
        """Test how risk scales with confidence levels."""
        base_scenario = {
            'entry_price': 100.0,
            'atr': 4.0,
            'daily_volatility': 0.03
        }
        
        confidence_levels = [62, 68, 73, 78, 83, 88]
        expected_participations = [0.25, 0.40, 0.55, 0.70, 0.85, 1.00]
        
        results = []
        for conf in confidence_levels:
            result = PositionSizer.position_size(
                account_value=self.account_value,
                confidence_score=conf,
                **base_scenario
            )
            results.append(result)
        
        # Verify increasing position sizes with confidence
        position_sizes = [r['position_size'] for r in results]
        for i in range(1, len(position_sizes)):
            self.assertGreater(position_sizes[i], position_sizes[i-1])
        
        # Verify participation rates match expected
        for i, expected_part in enumerate(expected_participations):
            self.assertEqual(results[i]['participation_rate'], expected_part)
    
    def test_volatility_impact_on_sizing(self):
        """Test how volatility affects position sizing."""
        base_scenario = {
            'entry_price': 50.0,
            'atr': 2.5,
            'confidence_score': 80.0
        }
        
        volatility_scenarios = [
            {'vol': 0.02, 'expected_adj': 1.0},      # Low vol, no adjustment
            {'vol': 0.05, 'expected_adj': 1.0},      # Threshold, no adjustment
            {'vol': 0.08, 'expected_adj': 0.625},    # High vol, adjustment
            {'vol': 0.15, 'expected_adj': 0.333},    # Very high vol, adjustment
        ]
        
        results = []
        for scenario in volatility_scenarios:
            result = PositionSizer.position_size(
                account_value=self.account_value,
                daily_volatility=scenario['vol'],
                **base_scenario
            )
            results.append(result)
            
            # Verify volatility adjustment
            self.assertAlmostEqual(
                result['volatility_adjustment'], 
                scenario['expected_adj'], 
                places=2
            )
        
        # Verify decreasing position sizes with increasing volatility
        position_sizes = [r['position_size'] for r in results]
        for i in range(1, len(position_sizes)):
            if volatility_scenarios[i]['vol'] > 0.05:  # Above threshold
                self.assertLessEqual(position_sizes[i], position_sizes[i-1])
    
    def test_extreme_market_conditions(self):
        """Test position sizing under extreme market conditions."""
        extreme_scenarios = [
            {
                'name': 'Market Crash (High Vol, Low Confidence)',
                'entry_price': 25.0,
                'atr': 5.0,
                'confidence_score': 62.0,
                'daily_volatility': 0.15,
                'expect_small_size': True
            },
            {
                'name': 'Bull Market (Low Vol, High Confidence)',
                'entry_price': 100.0,
                'atr': 1.5,
                'confidence_score': 92.0,
                'daily_volatility': 0.015,
                'expect_small_size': False
            },
            {
                'name': 'Penny Stock (High Vol, Medium Confidence)',
                'entry_price': 5.0,
                'atr': 0.8,
                'confidence_score': 71.0,
                'daily_volatility': 0.20,
                'expect_small_size': True
            }
        ]
        
        for scenario in extreme_scenarios:
            with self.subTest(scenario=scenario['name']):
                result = PositionSizer.position_size(
                    account_value=self.account_value,
                    entry_price=scenario['entry_price'],
                    atr=scenario['atr'],
                    confidence_score=scenario['confidence_score'],
                    daily_volatility=scenario['daily_volatility']
                )
                
                # Verify position is generated
                self.assertGreater(result['position_size'], 0)
                
                # Verify risk is controlled
                self.assertLessEqual(result['risk_amount'], 1000)  # Max 1% base risk
                
                # Check size expectations
                if scenario['expect_small_size']:
                    self.assertLess(result['position_size'], 100)
                
                # Verify stop loss is reasonable
                self.assertGreater(result['stop_price'], 0)
                self.assertLess(result['stop_price'], scenario['entry_price'])
    
    def test_account_size_scaling(self):
        """Test that position sizing scales properly with account size."""
        account_sizes = [50000, 100000, 250000, 500000]
        
        base_scenario = {
            'entry_price': 100.0,
            'atr': 5.0,
            'confidence_score': 80.0,
            'daily_volatility': 0.04
        }
        
        results = []
        for account_size in account_sizes:
            result = PositionSizer.position_size(
                account_value=account_size,
                **base_scenario
            )
            results.append(result)
        
        # Verify position sizes scale with account size
        position_sizes = [r['position_size'] for r in results]
        risk_amounts = [r['risk_amount'] for r in results]
        
        # Position sizes should increase with account size
        for i in range(1, len(position_sizes)):
            self.assertGreater(position_sizes[i], position_sizes[i-1])
        
        # Risk amounts should scale proportionally
        for i, account_size in enumerate(account_sizes):
            expected_risk = account_size * 0.01 * 0.85  # 1% * 85% participation
            self.assertAlmostEqual(risk_amounts[i], expected_risk, places=0)


if __name__ == '__main__':
    unittest.main()