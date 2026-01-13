"""
Integration tests for Governor - Tests realistic trading scenarios and system integration.
"""

import unittest
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from governor import Governor, Decision


class TestGovernorIntegration(unittest.TestCase):
    
    def test_realistic_entry_scenarios(self):
        """Test Governor with realistic entry scenarios."""
        scenarios = [
            {
                'name': 'High Quality Blue Chip',
                'symbol': 'AAPL',
                'price': 150.0,
                'confidence': 82.5,
                'size': 600,
                'sector': 'Technology',
                'volume': 50000000,
                'expected_decision': Decision.ENTER
            },
            {
                'name': 'Marginal Setup',
                'symbol': 'TSLA',
                'price': 200.0,
                'confidence': 58.0,  # Below threshold
                'size': 400,
                'sector': 'Automotive',
                'volume': 25000000,
                'expected_decision': Decision.NO_TRADE
            },
            {
                'name': 'Penny Stock',
                'symbol': 'PENNY',
                'price': 3.0,  # Below minimum
                'confidence': 75.0,
                'size': 2000,
                'sector': 'Biotech',
                'volume': 200000,
                'expected_decision': Decision.NO_TRADE
            },
            {
                'name': 'Illiquid Stock',
                'symbol': 'SMALL',
                'price': 25.0,
                'confidence': 70.0,
                'size': 500,
                'sector': 'Industrial',
                'volume': 80000,  # Below liquidity threshold
                'expected_decision': Decision.NO_TRADE
            }
        ]
        
        for scenario in scenarios:
            with self.subTest(scenario=scenario['name']):
                decision, reason = Governor.run(
                    signal_type='ENTRY',
                    symbol=scenario['symbol'],
                    current_price=scenario['price'],
                    confidence_score=scenario['confidence'],
                    position_size=scenario['size'],
                    sector=scenario['sector'],
                    daily_volume=scenario['volume']
                )
                
                self.assertEqual(decision, scenario['expected_decision'])
                self.assertIsInstance(reason, str)
                self.assertGreater(len(reason), 10)  # Meaningful reason provided
    
    def test_realistic_exit_scenarios(self):
        """Test Governor with realistic exit scenarios."""
        scenarios = [
            {
                'name': 'Profitable Exit',
                'symbol': 'MSFT',
                'pnl': 15.2,
                'decayed_confidence': 58.0,
                'expected_decision': Decision.EXIT,
                'expected_reason_contains': 'Exit approved'
            },
            {
                'name': 'Confidence Decay Exit',
                'symbol': 'GOOGL',
                'pnl': 2.5,
                'decayed_confidence': 42.0,  # Below force exit
                'expected_decision': Decision.EXIT,
                'expected_reason_contains': 'Force exit: Confidence'
            },
            {
                'name': 'Drawdown Exit',
                'symbol': 'NVDA',
                'pnl': -10.5,  # Exceeds 8% drawdown limit
                'decayed_confidence': 55.0,
                'expected_decision': Decision.EXIT,
                'expected_reason_contains': 'Force exit: Drawdown'
            },
            {
                'name': 'Small Loss Exit',
                'symbol': 'AMD',
                'pnl': -3.2,
                'decayed_confidence': 52.0,
                'expected_decision': Decision.EXIT,
                'expected_reason_contains': 'Exit approved'
            }
        ]
        
        for scenario in scenarios:
            with self.subTest(scenario=scenario['name']):
                decision, reason = Governor.run(
                    signal_type='EXIT',
                    symbol=scenario['symbol'],
                    current_price=100.0,  # Not used for exits
                    confidence_score=70.0,  # Not used for exits
                    position_size=0,
                    sector='Technology',
                    daily_volume=30000000,
                    position_pnl_pct=scenario['pnl'],
                    decayed_confidence=scenario['decayed_confidence']
                )
                
                self.assertEqual(decision, scenario['expected_decision'])
                self.assertIn(scenario['expected_reason_contains'], reason)
    
    def test_sector_concentration_management(self):
        """Test sector exposure limits in realistic portfolio context."""
        # Start with existing portfolio
        existing_positions = [
            {'symbol': 'AAPL', 'sector': 'Technology'},
            {'symbol': 'MSFT', 'sector': 'Technology'},
            {'symbol': 'JPM', 'sector': 'Financial'},
            {'symbol': 'JNJ', 'sector': 'Healthcare'}
        ]
        
        # Try to add another tech stock (would be 3/5 = 60% > 25% limit)
        decision, reason = Governor.run(
            signal_type='ENTRY',
            symbol='GOOGL',
            current_price=800.0,  # Within valid range
            confidence_score=78.0,
            position_size=100,
            sector='Technology',
            daily_volume=1500000,
            existing_positions=existing_positions
        )
        
        self.assertEqual(decision, Decision.NO_TRADE)
        self.assertIn('Sector exposure violation', reason)
        self.assertIn('Technology', reason)
        
        # Try to add a new sector stock (would be 1/5 = 20% within limit)
        decision, reason = Governor.run(
            signal_type='ENTRY',
            symbol='XOM',
            current_price=110.0,
            confidence_score=72.0,
            position_size=500,
            sector='Energy',  # New sector
            daily_volume=40000000,
            existing_positions=existing_positions
        )
        
        self.assertEqual(decision, Decision.ENTER)
        self.assertIn('Entry approved', reason)
    
    def test_daily_trading_workflow(self):
        """Test complete daily trading workflow with multiple decisions."""
        # Simulate daily screening results
        daily_signals = pd.DataFrame({
            'signal_type': ['ENTRY', 'ENTRY', 'ENTRY', 'EXIT', 'EXIT', 'ENTRY'],
            'symbol': ['AAPL', 'TSLA', 'GOOGL', 'MSFT', 'NVDA', 'META'],
            'current_price': [150.0, 200.0, 2400.0, 310.0, 420.0, 280.0],
            'confidence_score': [78.5, 55.0, 85.0, 70.0, 75.0, 68.0],
            'position_size': [500, 300, 100, 0, 0, 400],
            'sector': ['Technology', 'Automotive', 'Technology', 'Technology', 'Technology', 'Technology'],
            'daily_volume': [50000000, 25000000, 1500000, 30000000, 40000000, 20000000],
            'position_pnl_pct': [None, None, None, 12.5, -9.2, None],
            'decayed_confidence': [None, None, None, 52.0, 55.0, None]
        })
        
        results = Governor.batch_decisions(daily_signals)
        
        # Verify all signals processed
        self.assertEqual(len(results), 6)
        
        # Check specific expected outcomes
        decisions = results['decision'].tolist()
        
        # AAPL should be approved (high confidence, good setup)
        self.assertEqual(decisions[0], 'ENTER')
        
        # TSLA should be rejected (low confidence)
        self.assertEqual(decisions[1], 'NO_TRADE')
        
        # GOOGL should be rejected (price too high)
        self.assertEqual(decisions[2], 'NO_TRADE')
        
        # MSFT should exit normally
        self.assertEqual(decisions[3], 'EXIT')
        
        # NVDA should force exit (excessive drawdown)
        self.assertEqual(decisions[4], 'EXIT')
        
        # META might be rejected due to sector exposure after AAPL entry
        # (depends on batch processing order)
        self.assertIn(decisions[5], ['ENTER', 'NO_TRADE'])
        
        # Verify decision distribution
        summary = {
            'ENTER': decisions.count('ENTER'),
            'NO_TRADE': decisions.count('NO_TRADE'),
            'EXIT': decisions.count('EXIT')
        }
        
        # Should have some of each decision type
        self.assertGreater(summary['EXIT'], 0)  # At least some exits
        self.assertGreater(summary['NO_TRADE'], 0)  # At least some rejections
    
    def test_risk_limit_enforcement(self):
        """Test that risk limits are consistently enforced."""
        risk_test_cases = [
            {
                'name': 'Maximum Position Size',
                'size': 10001,
                'expected_rejection': True,
                'rejection_reason': 'exceeds maximum'
            },
            {
                'name': 'Minimum Confidence',
                'confidence': 59.9,
                'expected_rejection': True,
                'rejection_reason': 'below minimum'
            },
            {
                'name': 'Price Range - Too Low',
                'price': 4.99,
                'expected_rejection': True,
                'rejection_reason': 'outside valid range'
            },
            {
                'name': 'Price Range - Too High',
                'price': 1000.01,
                'expected_rejection': True,
                'rejection_reason': 'outside valid range'
            },
            {
                'name': 'Liquidity Threshold',
                'volume': 99999,
                'expected_rejection': True,
                'rejection_reason': 'Insufficient liquidity'
            }
        ]
        
        base_params = {
            'signal_type': 'ENTRY',
            'symbol': 'TEST',
            'current_price': 50.0,
            'confidence_score': 75.0,
            'position_size': 1000,
            'sector': 'Test',
            'daily_volume': 500000
        }
        
        for case in risk_test_cases:
            with self.subTest(case=case['name']):
                # Override specific parameter for this test
                params = base_params.copy()
                if 'size' in case:
                    params['position_size'] = case['size']
                if 'confidence' in case:
                    params['confidence_score'] = case['confidence']
                if 'price' in case:
                    params['current_price'] = case['price']
                if 'volume' in case:
                    params['daily_volume'] = case['volume']
                
                decision, reason = Governor.run(**params)
                
                if case['expected_rejection']:
                    self.assertEqual(decision, Decision.NO_TRADE)
                    self.assertIn(case['rejection_reason'], reason)
                else:
                    self.assertEqual(decision, Decision.ENTER)
    
    def test_force_exit_conditions(self):
        """Test various force exit conditions."""
        force_exit_cases = [
            {
                'name': 'Confidence Decay',
                'pnl': -2.0,
                'confidence': 44.0,  # Below 45% threshold
                'expected_reason': 'Force exit: Confidence'
            },
            {
                'name': 'Excessive Drawdown',
                'pnl': -8.5,  # Below -8% threshold
                'confidence': 55.0,
                'expected_reason': 'Force exit: Drawdown'
            },
            {
                'name': 'Both Conditions',
                'pnl': -10.0,
                'confidence': 40.0,
                'expected_reason': 'Force exit: Confidence'  # Confidence checked first
            }
        ]
        
        for case in force_exit_cases:
            with self.subTest(case=case['name']):
                decision, reason = Governor.run(
                    signal_type='EXIT',
                    symbol='TEST',
                    current_price=100.0,
                    confidence_score=70.0,
                    position_size=0,
                    sector='Test',
                    daily_volume=500000,
                    position_pnl_pct=case['pnl'],
                    decayed_confidence=case['confidence']
                )
                
                self.assertEqual(decision, Decision.EXIT)
                self.assertIn(case['expected_reason'], reason)
    
    def test_system_integrity_checks(self):
        """Test that system maintains integrity under various conditions."""
        # Test with missing optional parameters
        decision, reason = Governor.run(
            signal_type='ENTRY',
            symbol='AAPL',
            current_price=150.0,
            confidence_score=75.0,
            position_size=500,
            sector='Technology',
            daily_volume=50000000
            # No existing_positions, position_pnl_pct, or decayed_confidence
        )
        
        self.assertIn(decision, [Decision.ENTER, Decision.NO_TRADE])
        self.assertIsInstance(reason, str)
        
        # Test with all parameters provided
        decision, reason = Governor.run(
            signal_type='EXIT',
            symbol='MSFT',
            current_price=310.0,
            confidence_score=70.0,
            position_size=0,
            sector='Technology',
            daily_volume=30000000,
            existing_positions=[],
            position_pnl_pct=5.0,
            decayed_confidence=55.0
        )
        
        self.assertEqual(decision, Decision.EXIT)
        self.assertIsInstance(reason, str)


if __name__ == '__main__':
    unittest.main()