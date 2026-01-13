"""
Integration tests for ConfidenceEngine - Tests realistic trading scenarios.
"""

import unittest
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from confidence_engine import ConfidenceEngine


class TestConfidenceEngineIntegration(unittest.TestCase):
    
    def test_realistic_trading_scenarios(self):
        """Test confidence engine with realistic agent score combinations."""
        scenarios = [
            {
                'name': 'Strong Institutional Setup',
                'scores': {'accumulation': 88, 'trigger': 82, 'sector_momentum': 75, 'regime': 85},
                'expected_bucket': '80-85',
                'min_score': 80
            },
            {
                'name': 'Weak Breakout Attempt', 
                'scores': {'accumulation': 45, 'trigger': 55, 'sector_momentum': 40, 'regime': 60},
                'expected_bucket': 'Below-60',
                'max_score': 60
            },
            {
                'name': 'Mixed Signals',
                'scores': {'accumulation': 72, 'trigger': 68, 'sector_momentum': 65, 'regime': 70},
                'expected_bucket': '65-70',
                'min_score': 65,
                'max_score': 75
            }
        ]
        
        for scenario in scenarios:
            with self.subTest(scenario=scenario['name']):
                score, bucket = ConfidenceEngine.compute(scenario['scores'])
                
                self.assertEqual(bucket, scenario['expected_bucket'])
                
                if 'min_score' in scenario:
                    self.assertGreaterEqual(score, scenario['min_score'])
                if 'max_score' in scenario:
                    self.assertLessEqual(score, scenario['max_score'])
    
    def test_portfolio_screening_workflow(self):
        """Test batch processing for portfolio screening."""
        # Simulate daily screening of 50 stocks
        portfolio_data = pd.DataFrame({
            'symbol': [f'STOCK{i:02d}' for i in range(1, 11)],
            'accumulation': [85, 72, 45, 90, 65, 78, 55, 82, 68, 75],
            'trigger': [78, 65, 50, 85, 60, 75, 45, 80, 62, 70],
            'sector_momentum': [80, 70, 35, 88, 58, 72, 40, 85, 65, 68],
            'regime': [82, 75, 55, 80, 62, 78, 50, 84, 70, 72]
        })
        
        results = ConfidenceEngine.batch_compute(portfolio_data)
        
        # Verify all stocks processed
        self.assertEqual(len(results), 10)
        
        # Check high confidence stocks
        high_conf = results[results['confidence_bucket'].isin(['80-85', '85-90', '90-95', '95-100'])]
        self.assertGreater(len(high_conf), 0, "Should have some high confidence stocks")
        
        # Check low confidence stocks filtered out
        low_conf = results[results['confidence_bucket'] == 'Below-60']
        self.assertGreater(len(low_conf), 0, "Should have some low confidence stocks")
        
        # Verify score ordering makes sense
        sorted_results = results.sort_values('confidence_score', ascending=False)
        self.assertGreater(sorted_results.iloc[0]['confidence_score'], 
                          sorted_results.iloc[-1]['confidence_score'])
    
    def test_agent_weight_impact(self):
        """Test how different agent weights affect final confidence."""
        # Scenario: Strong accumulation but weak other signals
        base_scores = {
            'accumulation': 90,  # Very strong
            'trigger': 50,       # Weak
            'sector_momentum': 45,  # Weak  
            'regime': 55         # Weak
        }
        
        score, bucket = ConfidenceEngine.compute(base_scores)
        
        # With 35% accumulation weight, should still be reasonable confidence
        # 90*0.35 + 50*0.25 + 45*0.20 + 55*0.20 = 31.5 + 12.5 + 9 + 11 = 64
        expected_score = 64.0
        self.assertAlmostEqual(score, expected_score, places=1)
        self.assertEqual(bucket, "60-65")
    
    def test_confidence_distribution(self):
        """Test confidence score distribution across different scenarios."""
        # Generate diverse scenarios
        test_scenarios = []
        
        # High confidence scenarios
        for i in range(3):
            test_scenarios.append({
                'accumulation': 85 + i*3,
                'trigger': 80 + i*2, 
                'sector_momentum': 75 + i*4,
                'regime': 82 + i*3
            })
        
        # Medium confidence scenarios  
        for i in range(3):
            test_scenarios.append({
                'accumulation': 65 + i*3,
                'trigger': 60 + i*4,
                'sector_momentum': 58 + i*5, 
                'regime': 62 + i*4
            })
        
        # Low confidence scenarios
        for i in range(3):
            test_scenarios.append({
                'accumulation': 40 + i*5,
                'trigger': 35 + i*6,
                'sector_momentum': 30 + i*7,
                'regime': 45 + i*4
            })
        
        results = []
        for scores in test_scenarios:
            score, bucket = ConfidenceEngine.compute(scores)
            results.append({'score': score, 'bucket': bucket})
        
        # Verify we get distribution across buckets
        buckets = [r['bucket'] for r in results]
        unique_buckets = set(buckets)
        
        self.assertGreater(len(unique_buckets), 3, 
                          "Should have distribution across multiple confidence buckets")
        
        # Verify scores are properly ordered
        scores = [r['score'] for r in results]
        self.assertGreater(max(scores), 75, "Should have high confidence scenarios")
        self.assertLess(min(scores), 60, "Should have low confidence scenarios")


if __name__ == '__main__':
    unittest.main()