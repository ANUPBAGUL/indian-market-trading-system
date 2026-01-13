"""
Integration tests for Walk-Forward Tester - Tests complete workflows.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.walk_forward_tester import WalkForwardTester


class TestWalkForwardIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up realistic test environment."""
        # Create 2 years of daily data
        dates = pd.date_range('2022-01-01', '2023-12-31', freq='D')
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        self.market_data = []
        for date in dates:
            for symbol in symbols:
                base_price = {'AAPL': 150, 'MSFT': 250, 'GOOGL': 2800}[symbol]
                
                # Add realistic price movement
                days_from_start = (date - dates[0]).days
                trend = 1 + (days_from_start * 0.0001)
                noise = np.random.normal(1, 0.015)
                
                price = base_price * trend * noise
                
                self.market_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'symbol': symbol,
                    'open': price * 0.995,
                    'high': price * 1.02,
                    'low': price * 0.98,
                    'close': price,
                    'volume': np.random.randint(800000, 1500000),
                    'sector': 'Technology'
                })
        
        self.market_df = pd.DataFrame(self.market_data)
        
        # Test configurations
        self.short_config = WalkForwardTester(train_days=90, test_days=30, step_days=15)
        self.long_config = WalkForwardTester(train_days=180, test_days=60, step_days=30)
    
    def test_complete_walk_forward_workflow(self):
        """Test complete walk-forward testing from start to finish."""
        frozen_params = {
            'confidence_threshold': 65,
            'risk_per_trade': 0.015,
            'max_positions': 3
        }
        
        results = self.short_config.run_walk_forward(
            data=self.market_df,
            start_date='2022-06-01',
            end_date='2023-06-30',
            frozen_params=frozen_params
        )
        
        # Should generate multiple windows
        self.assertGreater(results['total_windows'], 5)
        
        # Each window should have complete results
        for window in results['window_results']:
            self.assertIn('window_id', window)
            self.assertIn('train_start', window)
            self.assertIn('test_start', window)
            self.assertIn('kpis', window)
            self.assertIn('trades_count', window)
        
        # Should have aggregated metrics
        agg = results['aggregated_kpis']
        self.assertIn('avg_expectancy', agg)
        self.assertIn('avg_win_rate', agg)
        self.assertIn('windows_with_trades', agg)
        
        # Should have robustness analysis
        robust = results['robustness_metrics']
        self.assertIn('consistency_score', robust)
        self.assertIn('profitable_windows_pct', robust)
        self.assertIn('expectancy_std', robust)
    
    def test_different_window_configurations(self):
        """Test walk-forward with different window sizes."""
        frozen_params = {'confidence_threshold': 70, 'risk_per_trade': 0.01}
        
        # Short windows
        short_results = self.short_config.run_walk_forward(
            data=self.market_df,
            start_date='2022-08-01',
            end_date='2023-03-31',
            frozen_params=frozen_params
        )
        
        # Long windows  
        long_results = self.long_config.run_walk_forward(
            data=self.market_df,
            start_date='2022-08-01',
            end_date='2023-03-31',
            frozen_params=frozen_params
        )
        
        # Short config should generate more windows
        self.assertGreater(
            short_results['total_windows'],
            long_results['total_windows']
        )
        
        # Both should have valid results
        self.assertGreater(short_results['total_windows'], 0)
        self.assertGreater(long_results['total_windows'], 0)
    
    def test_parameter_impact_analysis(self):
        """Test how different frozen parameters affect results."""
        # Conservative parameters
        conservative_params = {
            'confidence_threshold': 80,  # High threshold
            'risk_per_trade': 0.005     # Low risk
        }
        
        # Aggressive parameters
        aggressive_params = {
            'confidence_threshold': 60,  # Low threshold
            'risk_per_trade': 0.02      # High risk
        }
        
        conservative_results = self.short_config.run_walk_forward(
            data=self.market_df,
            start_date='2022-09-01',
            end_date='2023-04-30',
            frozen_params=conservative_params
        )
        
        aggressive_results = self.short_config.run_walk_forward(
            data=self.market_df,
            start_date='2022-09-01',
            end_date='2023-04-30',
            frozen_params=aggressive_params
        )
        
        # Both should complete successfully
        self.assertGreater(conservative_results['total_windows'], 0)
        self.assertGreater(aggressive_results['total_windows'], 0)
        
        # Parameters should be preserved
        self.assertEqual(
            conservative_results['frozen_parameters']['confidence_threshold'],
            80
        )
        self.assertEqual(
            aggressive_results['frozen_parameters']['confidence_threshold'],
            60
        )
    
    def test_robustness_detection_scenarios(self):
        """Test robustness detection across different scenarios."""
        # Test with consistent parameters (should be more robust)
        consistent_params = {
            'confidence_threshold': 65,
            'risk_per_trade': 0.01
        }
        
        results = self.short_config.run_walk_forward(
            data=self.market_df,
            start_date='2022-07-01',
            end_date='2023-05-31',
            frozen_params=consistent_params
        )
        
        robust_metrics = results['robustness_metrics']
        
        # Should calculate robustness indicators
        self.assertIsInstance(robust_metrics['profitable_windows_pct'], float)
        self.assertIsInstance(robust_metrics['expectancy_std'], float)
        self.assertIsInstance(robust_metrics['consistency_score'], float)
        
        # Should have expectancy range
        exp_range = robust_metrics['expectancy_range']
        self.assertIn('min', exp_range)
        self.assertIn('max', exp_range)
        self.assertLessEqual(exp_range['min'], exp_range['max'])
    
    def test_temporal_separation_validation(self):
        """Test that train/test periods never overlap."""
        results = self.short_config.run_walk_forward(
            data=self.market_df,
            start_date='2022-10-01',
            end_date='2023-02-28',
            frozen_params={'confidence_threshold': 70}
        )
        
        # Check temporal separation for each window
        for window in results['window_results']:
            train_end = pd.to_datetime(window['train_end'])
            test_start = pd.to_datetime(window['test_start'])
            
            # Test should start after train ends
            self.assertGreater(test_start, train_end)
            
            # Should be exactly 1 day gap
            self.assertEqual((test_start - train_end).days, 1)
    
    def test_performance_consistency_analysis(self):
        """Test performance consistency across multiple periods."""
        results = self.long_config.run_walk_forward(
            data=self.market_df,
            start_date='2022-08-01',
            end_date='2023-08-31',
            frozen_params={
                'confidence_threshold': 65,
                'risk_per_trade': 0.012
            }
        )
        
        # Extract expectancies from all windows
        expectancies = []
        for window in results['window_results']:
            if window['trades_count'] > 0:
                expectancies.append(window['kpis']['expectancy'])
        
        if len(expectancies) > 1:
            # Calculate variance manually to verify robustness metrics
            import statistics
            actual_std = statistics.stdev(expectancies)
            reported_std = results['robustness_metrics']['expectancy_std']
            
            # Should match (within rounding)
            self.assertAlmostEqual(actual_std, reported_std, places=1)
    
    def test_summary_report_generation(self):
        """Test complete summary report generation."""
        results = self.short_config.run_walk_forward(
            data=self.market_df,
            start_date='2022-11-01',
            end_date='2023-03-31',
            frozen_params={
                'confidence_threshold': 75,
                'risk_per_trade': 0.008
            }
        )
        
        report = self.short_config.generate_summary_report(results)
        
        # Should be comprehensive report
        self.assertGreater(len(report), 500)  # Substantial content
        
        # Should contain all key sections
        required_sections = [
            "WALK-FORWARD TESTING RESULTS",
            "TESTING CONFIGURATION", 
            "AGGREGATED PERFORMANCE",
            "ROBUSTNESS ANALYSIS",
            "OVERFITTING ASSESSMENT"
        ]
        
        for section in required_sections:
            self.assertIn(section, report)
        
        # Should contain configuration details
        self.assertIn("90 days", report)  # Train window
        self.assertIn("30 days", report)  # Test window
        self.assertIn("15 days", report)  # Step size
    
    def test_edge_case_handling(self):
        """Test handling of edge cases and boundary conditions."""
        # Test with very short data period
        short_data = self.market_df[
            (self.market_df['date'] >= '2023-01-01') & 
            (self.market_df['date'] <= '2023-02-28')
        ].copy()
        
        results = self.short_config.run_walk_forward(
            data=short_data,
            start_date='2023-01-15',
            end_date='2023-02-15',
            frozen_params={'confidence_threshold': 65}
        )
        
        # Should handle gracefully (may have 0 or few windows)
        self.assertIsInstance(results['total_windows'], int)
        self.assertGreaterEqual(results['total_windows'], 0)
        
        # Should still generate valid report
        report = self.short_config.generate_summary_report(results)
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 30)
    
    def test_overfitting_detection_workflow(self):
        """Test complete overfitting detection workflow."""
        # Use parameters that might show instability
        unstable_params = {
            'confidence_threshold': 55,  # Very low threshold
            'risk_per_trade': 0.025     # High risk
        }
        
        results = self.long_config.run_walk_forward(
            data=self.market_df,
            start_date='2022-06-01',
            end_date='2023-09-30',
            frozen_params=unstable_params
        )
        
        # Should detect potential issues through variance
        robust_metrics = results['robustness_metrics']
        
        # High variance should result in low consistency score
        if robust_metrics['expectancy_std'] > 100:
            self.assertLess(robust_metrics['consistency_score'], 50)
        
        # Report should contain overfitting assessment
        report = self.long_config.generate_summary_report(results)
        self.assertIn("OVERFITTING ASSESSMENT", report)
        self.assertIn("KILLS OVERFITTING", report)


if __name__ == '__main__':
    unittest.main()