"""
Integration tests for KPI Computer - Tests complete KPI analysis workflows.
"""

import unittest
from unittest.mock import Mock
from src.kpi_computer import KPIComputer


class TestKPIIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up realistic trading scenarios."""
        # Scenario 1: Profitable system with good calibration
        self.profitable_trades = []
        for i in range(20):
            trade = Mock()
            trade.pnl = 150.0 if i % 3 == 0 else -75.0  # 33% win rate, positive expectancy
            self.profitable_trades.append(trade)
        
        # Scenario 2: Losing system
        self.losing_trades = []
        for i in range(10):
            trade = Mock()
            trade.pnl = 50.0 if i % 5 == 0 else -100.0  # 20% win rate, negative expectancy
            self.losing_trades.append(trade)
        
        # Realistic equity curves
        self.profitable_equity = [
            {'total_value': 10000},
            {'total_value': 10150},
            {'total_value': 10075},
            {'total_value': 10225},
            {'total_value': 10150},
            {'total_value': 10300}
        ]
        
        self.losing_equity = [
            {'total_value': 10000},
            {'total_value': 9950},
            {'total_value': 9850},
            {'total_value': 9900},
            {'total_value': 9750},
            {'total_value': 9600}
        ]
        
        # Well-calibrated confidence data
        self.calibrated_confidence = [
            {'confidence_bucket': '60-65', 'outcome': True},
            {'confidence_bucket': '60-65', 'outcome': True},
            {'confidence_bucket': '60-65', 'outcome': True},
            {'confidence_bucket': '60-65', 'outcome': False},
            {'confidence_bucket': '60-65', 'outcome': False},
            {'confidence_bucket': '70-75', 'outcome': True},
            {'confidence_bucket': '70-75', 'outcome': True},
            {'confidence_bucket': '70-75', 'outcome': True},
            {'confidence_bucket': '70-75', 'outcome': False}
        ]
        
        # Poorly calibrated confidence data
        self.miscalibrated_confidence = [
            {'confidence_bucket': '80-85', 'outcome': False},
            {'confidence_bucket': '80-85', 'outcome': False},
            {'confidence_bucket': '80-85', 'outcome': True},
            {'confidence_bucket': '60-65', 'outcome': True},
            {'confidence_bucket': '60-65', 'outcome': True},
            {'confidence_bucket': '60-65', 'outcome': True}
        ]
    
    def test_profitable_system_analysis(self):
        """Test KPI analysis for profitable trading system."""
        kpis = KPIComputer.compute_kpis(
            trades=self.profitable_trades,
            equity_curve=self.profitable_equity,
            confidence_buckets=self.calibrated_confidence
        )
        
        # Should be profitable
        self.assertGreater(kpis['expectancy'], 0)
        self.assertIn("PROFITABLE", kpis['summary'])
        
        # Should have reasonable drawdown
        self.assertLess(kpis['max_drawdown_pct'], 20)
        
        # Should have correct trade count
        self.assertEqual(kpis['total_trades'], 20)
        
        # Should have trade statistics
        stats = kpis['trade_statistics']
        self.assertGreater(stats['avg_win'], 0)
        self.assertLess(stats['avg_loss'], 0)
        self.assertGreater(stats['profit_factor'], 1.0)
        
        # Should have confidence analysis
        self.assertIn('confidence_bucket_stats', kpis)
        self.assertGreater(len(kpis['confidence_bucket_stats']), 0)
    
    def test_losing_system_analysis(self):
        """Test KPI analysis for losing trading system."""
        kpis = KPIComputer.compute_kpis(
            trades=self.losing_trades,
            equity_curve=self.losing_equity,
            confidence_buckets=self.miscalibrated_confidence
        )
        
        # Should be unprofitable
        self.assertLess(kpis['expectancy'], 0)
        self.assertIn("UNPROFITABLE", kpis['summary'])
        
        # Should have significant drawdown
        self.assertGreater(kpis['max_drawdown_pct'], 0)
        
        # Should have low win rate
        self.assertLess(kpis['win_rate_pct'], 50)
        
        # Should have poor profit factor
        stats = kpis['trade_statistics']
        self.assertLess(stats['profit_factor'], 1.0)
    
    def test_confidence_calibration_analysis(self):
        """Test confidence bucket calibration analysis."""
        kpis = KPIComputer.compute_kpis(
            trades=self.profitable_trades,
            equity_curve=self.profitable_equity,
            confidence_buckets=self.calibrated_confidence
        )
        
        bucket_stats = kpis['confidence_bucket_stats']
        
        # 60-65 bucket should be reasonably calibrated (3 wins, 2 losses = 60%)
        bucket_60_65 = bucket_stats['60-65']
        self.assertEqual(bucket_60_65['trades'], 5)
        self.assertEqual(bucket_60_65['wins'], 3)
        self.assertEqual(bucket_60_65['actual_win_rate'], 60.0)
        self.assertEqual(bucket_60_65['expected_win_rate'], 62.5)
        self.assertLess(bucket_60_65['calibration_error'], 5.0)  # Well calibrated
        
        # 70-75 bucket should also be reasonably calibrated (3 wins, 1 loss = 75%)
        bucket_70_75 = bucket_stats['70-75']
        self.assertEqual(bucket_70_75['trades'], 4)
        self.assertEqual(bucket_70_75['wins'], 3)
        self.assertEqual(bucket_70_75['actual_win_rate'], 75.0)
        self.assertEqual(bucket_70_75['expected_win_rate'], 72.5)
        self.assertLess(bucket_70_75['calibration_error'], 5.0)  # Well calibrated
    
    def test_miscalibrated_confidence_analysis(self):
        """Test analysis of poorly calibrated confidence buckets."""
        kpis = KPIComputer.compute_kpis(
            trades=self.losing_trades,
            equity_curve=self.losing_equity,
            confidence_buckets=self.miscalibrated_confidence
        )
        
        bucket_stats = kpis['confidence_bucket_stats']
        
        # 80-85 bucket should be poorly calibrated (1 win, 2 losses = 33.3%)
        bucket_80_85 = bucket_stats['80-85']
        self.assertEqual(bucket_80_85['trades'], 3)
        self.assertEqual(bucket_80_85['wins'], 1)
        self.assertAlmostEqual(bucket_80_85['actual_win_rate'], 33.3, places=1)
        self.assertEqual(bucket_80_85['expected_win_rate'], 82.5)
        self.assertGreater(bucket_80_85['calibration_error'], 40.0)  # Poorly calibrated
        
        # 60-65 bucket should be over-performing (3 wins, 0 losses = 100%)
        bucket_60_65 = bucket_stats['60-65']
        self.assertEqual(bucket_60_65['trades'], 3)
        self.assertEqual(bucket_60_65['wins'], 3)
        self.assertEqual(bucket_60_65['actual_win_rate'], 100.0)
        self.assertGreater(bucket_60_65['calibration_error'], 30.0)  # Over-confident
    
    def test_complete_kpi_report_generation(self):
        """Test complete KPI report generation for realistic scenario."""
        kpis = KPIComputer.compute_kpis(
            trades=self.profitable_trades,
            equity_curve=self.profitable_equity,
            confidence_buckets=self.calibrated_confidence
        )
        
        report = KPIComputer.generate_report(kpis)
        
        # Should contain all major sections
        self.assertIn("=== KPI REPORT ===", report)
        self.assertIn("CORE METRICS:", report)
        self.assertIn("TRADE STATISTICS:", report)
        self.assertIn("CONFIDENCE CALIBRATION:", report)
        self.assertIn("SUMMARY:", report)
        
        # Should contain specific values
        self.assertIn(f"Total Trades: {len(self.profitable_trades)}", report)
        self.assertIn("Expectancy:", report)
        self.assertIn("Max Drawdown:", report)
        self.assertIn("Win Rate:", report)
        
        # Should contain confidence bucket table
        self.assertIn("60-65", report)
        self.assertIn("70-75", report)
        self.assertIn("Actual", report)
        self.assertIn("Expected", report)
        self.assertIn("Error", report)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Single trade
        single_trade = [Mock()]
        single_trade[0].pnl = 100.0
        
        kpis = KPIComputer.compute_kpis(
            trades=single_trade,
            equity_curve=[{'total_value': 10000}, {'total_value': 10100}]
        )
        
        self.assertEqual(kpis['expectancy'], 100.0)
        self.assertEqual(kpis['win_rate_pct'], 100.0)
        self.assertEqual(kpis['total_trades'], 1)
        
        # All losing trades
        all_losses = [Mock() for _ in range(5)]
        for trade in all_losses:
            trade.pnl = -50.0
        
        kpis = KPIComputer.compute_kpis(
            trades=all_losses,
            equity_curve=[{'total_value': 10000}, {'total_value': 9750}]
        )
        
        self.assertEqual(kpis['expectancy'], -50.0)
        self.assertEqual(kpis['win_rate_pct'], 0.0)
        self.assertEqual(kpis['trade_statistics']['profit_factor'], 0.0)
    
    def test_system_comparison_scenario(self):
        """Test KPI computation for system comparison scenario."""
        # System A: High win rate, low expectancy
        system_a_trades = []
        for i in range(100):
            trade = Mock()
            trade.pnl = 10.0 if i < 80 else -200.0  # 80% win rate, negative expectancy
            system_a_trades.append(trade)
        
        # System B: Low win rate, high expectancy
        system_b_trades = []
        for i in range(100):
            trade = Mock()
            trade.pnl = 500.0 if i < 40 else -100.0  # 40% win rate, positive expectancy
            system_b_trades.append(trade)
        
        kpis_a = KPIComputer.compute_kpis(system_a_trades, [])
        kpis_b = KPIComputer.compute_kpis(system_b_trades, [])
        
        # System A should have higher win rate but negative expectancy
        self.assertGreater(kpis_a['win_rate_pct'], kpis_b['win_rate_pct'])
        self.assertLess(kpis_a['expectancy'], 0)
        
        # System B should have lower win rate but positive expectancy
        self.assertLess(kpis_b['win_rate_pct'], kpis_a['win_rate_pct'])
        self.assertGreater(kpis_b['expectancy'], 0)
        
        # System B should be preferred (positive expectancy)
        self.assertIn("PROFITABLE", kpis_b['summary'])
        # System A is marginal (small negative expectancy)
        self.assertIn("MARGINAL", kpis_a['summary'])


if __name__ == '__main__':
    unittest.main()