"""
Unit tests for Walk-Forward Tester - Tests core functionality.
"""

import unittest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime, timedelta
from src.walk_forward_tester import WalkForwardTester


class TestWalkForwardTester(unittest.TestCase):
    
    def setUp(self):
        """Set up test data."""
        self.tester = WalkForwardTester(train_days=60, test_days=20, step_days=10)
        
        # Sample data
        dates = pd.date_range('2023-01-01', '2023-06-30', freq='D')
        self.test_data = pd.DataFrame({
            'date': [d.strftime('%Y-%m-%d') for d in dates] * 2,
            'symbol': ['AAPL'] * len(dates) + ['MSFT'] * len(dates),
            'close': [100.0] * len(dates) * 2,
            'volume': [1000000] * len(dates) * 2
        })
        
        self.frozen_params = {
            'confidence_threshold': 70,
            'risk_per_trade': 0.01
        }
    
    def test_initialization(self):
        """Test WalkForwardTester initialization."""
        tester = WalkForwardTester(100, 30, 15)
        self.assertEqual(tester.train_days, 100)
        self.assertEqual(tester.test_days, 30)
        self.assertEqual(tester.step_days, 15)
    
    def test_generate_windows(self):
        """Test rolling window generation."""
        windows = self.tester._generate_windows('2023-01-01', '2023-03-31')
        
        # Should generate multiple windows
        self.assertGreater(len(windows), 0)
        
        # Check first window structure
        train_start, train_end, test_start, test_end = windows[0]
        self.assertEqual(train_start, '2023-01-01')
        
        # Test period should follow train period
        train_end_dt = pd.to_datetime(train_end)
        test_start_dt = pd.to_datetime(test_start)
        self.assertEqual((test_start_dt - train_end_dt).days, 1)
    
    def test_filter_data(self):
        """Test data filtering by date range."""
        filtered = self.tester._filter_data(self.test_data, '2023-02-01', '2023-02-28')
        
        # Should only contain February data
        self.assertTrue(all(filtered['date'] >= '2023-02-01'))
        self.assertTrue(all(filtered['date'] <= '2023-02-28'))
        
        # Should contain both symbols
        self.assertEqual(set(filtered['symbol']), {'AAPL', 'MSFT'})
    
    def test_simulate_backtest_results(self):
        """Test backtest simulation."""
        sample_data = self.test_data.head(20)
        results = self.tester._simulate_backtest_results(sample_data, self.frozen_params)
        
        # Should return proper structure
        self.assertIn('trades', results)
        self.assertIn('equity_curve', results)
        
        # Should have some trades
        self.assertGreater(len(results['trades']), 0)
        
        # Trades should have pnl attribute
        for trade in results['trades']:
            self.assertTrue(hasattr(trade, 'pnl'))
    
    def test_aggregate_window_kpis(self):
        """Test KPI aggregation across windows."""
        # Mock window results
        window_results = [
            {
                'kpis': {'expectancy': 100, 'win_rate_pct': 60, 'max_drawdown_pct': 5},
                'trades_count': 10
            },
            {
                'kpis': {'expectancy': 200, 'win_rate_pct': 70, 'max_drawdown_pct': 3},
                'trades_count': 8
            }
        ]
        
        agg_kpis = self.tester._aggregate_window_kpis(window_results)
        
        # Should calculate averages
        self.assertEqual(agg_kpis['avg_expectancy'], 150.0)  # (100+200)/2
        self.assertEqual(agg_kpis['avg_win_rate'], 65.0)     # (60+70)/2
        self.assertEqual(agg_kpis['windows_with_trades'], 2)
    
    def test_calculate_robustness_metrics(self):
        """Test robustness metrics calculation."""
        window_results = [
            {'kpis': {'expectancy': 100, 'win_rate_pct': 60}, 'trades_count': 5},
            {'kpis': {'expectancy': 200, 'win_rate_pct': 70}, 'trades_count': 8},
            {'kpis': {'expectancy': -50, 'win_rate_pct': 30}, 'trades_count': 3}
        ]
        
        metrics = self.tester._calculate_robustness_metrics(window_results)
        
        # Should calculate profitable windows percentage
        self.assertEqual(metrics['profitable_windows_pct'], 66.7)  # 2/3 positive
        
        # Should have expectancy range
        self.assertEqual(metrics['expectancy_range']['min'], -50)
        self.assertEqual(metrics['expectancy_range']['max'], 200)
        
        # Should have consistency score
        self.assertIn('consistency_score', metrics)
    
    def test_empty_window_results(self):
        """Test handling of empty results."""
        agg_kpis = self.tester._aggregate_window_kpis([])
        self.assertEqual(agg_kpis, {})
        
        metrics = self.tester._calculate_robustness_metrics([])
        self.assertEqual(metrics, {})
    
    @patch('src.walk_forward_tester.KPIComputer.compute_kpis')
    def test_run_walk_forward(self, mock_compute_kpis):
        """Test complete walk-forward execution."""
        # Mock KPI computation
        mock_compute_kpis.return_value = {
            'expectancy': 150.0,
            'win_rate_pct': 65.0,
            'max_drawdown_pct': 2.5
        }
        
        results = self.tester.run_walk_forward(
            data=self.test_data,
            start_date='2023-02-01',
            end_date='2023-04-30',
            frozen_params=self.frozen_params
        )
        
        # Should return complete results structure
        self.assertIn('window_results', results)
        self.assertIn('aggregated_kpis', results)
        self.assertIn('total_windows', results)
        self.assertIn('frozen_parameters', results)
        self.assertIn('robustness_metrics', results)
        
        # Should preserve frozen parameters
        self.assertEqual(results['frozen_parameters'], self.frozen_params)
    
    def test_generate_summary_report(self):
        """Test summary report generation."""
        # Mock results
        results = {
            'window_results': [
                {'kpis': {'expectancy': 100}, 'trades_count': 5}
            ],
            'total_windows': 5,
            'aggregated_kpis': {
                'avg_expectancy': 120.0,
                'avg_win_rate': 65.0,
                'avg_max_drawdown': 3.0,
                'windows_with_trades': 4,
                'total_windows': 5
            },
            'robustness_metrics': {
                'consistency_score': 45.0,
                'profitable_windows_pct': 80.0,
                'expectancy_std': 25.0,
                'expectancy_range': {'min': 50.0, 'max': 200.0}
            }
        }
        
        report = self.tester.generate_summary_report(results)
        
        # Should contain key sections
        self.assertIn("WALK-FORWARD TESTING RESULTS", report)
        self.assertIn("TESTING CONFIGURATION", report)
        self.assertIn("AGGREGATED PERFORMANCE", report)
        self.assertIn("ROBUSTNESS ANALYSIS", report)
        self.assertIn("OVERFITTING ASSESSMENT", report)
        self.assertIn("HOW THIS KILLS OVERFITTING", report)
        
        # Should contain specific values
        self.assertIn("$120.00", report)  # Average expectancy
        self.assertIn("65.0%", report)    # Average win rate
        self.assertIn("80.0%", report)    # Profitable windows
    
    def test_empty_summary_report(self):
        """Test summary report with no windows."""
        results = {'window_results': []}
        report = self.tester.generate_summary_report(results)
        self.assertIn("No valid windows", report)


if __name__ == '__main__':
    unittest.main()