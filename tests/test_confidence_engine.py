"""
Unit tests for ConfidenceEngine - Tests individual methods and edge cases.
"""

import unittest
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from confidence_engine import ConfidenceEngine


class TestConfidenceEngine(unittest.TestCase):
    
    def test_compute_high_confidence(self):
        """Test high confidence scenario."""
        scores = {
            'accumulation': 90,
            'trigger': 85,
            'sector_momentum': 80,
            'regime': 88
        }
        
        weighted_score, bucket = ConfidenceEngine.compute(scores)
        
        expected = 90*0.35 + 85*0.25 + 80*0.20 + 88*0.20
        self.assertAlmostEqual(weighted_score, expected, places=1)
        self.assertEqual(bucket, "85-90")
    
    def test_compute_low_confidence(self):
        """Test low confidence scenario."""
        scores = {
            'accumulation': 40,
            'trigger': 45,
            'sector_momentum': 35,
            'regime': 50
        }
        
        weighted_score, bucket = ConfidenceEngine.compute(scores)
        
        expected = 40*0.35 + 45*0.25 + 35*0.20 + 50*0.20
        self.assertAlmostEqual(weighted_score, expected, places=1)
        self.assertEqual(bucket, "Below-60")
    
    def test_compute_boundary_cases(self):
        """Test confidence bucket boundaries."""
        # Test 75.0 exactly
        scores = {'accumulation': 75, 'trigger': 75, 'sector_momentum': 75, 'regime': 75}
        _, bucket = ConfidenceEngine.compute(scores)
        self.assertEqual(bucket, "75-80")
        
        # Test 95+ score
        scores = {'accumulation': 98, 'trigger': 95, 'sector_momentum': 92, 'regime': 97}
        _, bucket = ConfidenceEngine.compute(scores)
        self.assertEqual(bucket, "95-100")
    
    def test_missing_agent_scores(self):
        """Test error handling for missing agent scores."""
        incomplete_scores = {
            'accumulation': 80,
            'trigger': 75
            # Missing sector_momentum and regime
        }
        
        with self.assertRaises(ValueError) as context:
            ConfidenceEngine.compute(incomplete_scores)
        
        self.assertIn("Missing agent scores", str(context.exception))
    
    def test_weights_sum_to_one(self):
        """Test that agent weights sum to 1.0."""
        total_weight = sum(ConfidenceEngine.WEIGHTS.values())
        self.assertAlmostEqual(total_weight, 1.0, places=10)
    
    def test_confidence_bucket_mapping(self):
        """Test confidence bucket string mapping."""
        test_cases = [
            (62.5, "60-65"),
            (67.3, "65-70"),
            (72.1, "70-75"),
            (77.8, "75-80"),
            (82.4, "80-85"),
            (87.9, "85-90"),
            (92.2, "90-95"),
            (97.5, "95-100"),
            (45.0, "Below-60")
        ]
        
        for score, expected_bucket in test_cases:
            actual_bucket = ConfidenceEngine._get_confidence_bucket(score)
            self.assertEqual(actual_bucket, expected_bucket, 
                           f"Score {score} should map to {expected_bucket}")
    
    def test_batch_compute_basic(self):
        """Test batch processing functionality."""
        df = pd.DataFrame({
            'symbol': ['AAPL', 'GOOGL'],
            'accumulation': [85, 70],
            'trigger': [80, 65],
            'sector_momentum': [75, 60],
            'regime': [82, 68]
        })
        
        result = ConfidenceEngine.batch_compute(df)
        
        # Check columns added
        self.assertIn('confidence_score', result.columns)
        self.assertIn('confidence_bucket', result.columns)
        
        # Check original data preserved
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]['symbol'], 'AAPL')
        
        # Check scores computed
        self.assertGreater(result.iloc[0]['confidence_score'], 75)
        self.assertLess(result.iloc[1]['confidence_score'], 70)


if __name__ == '__main__':
    unittest.main()