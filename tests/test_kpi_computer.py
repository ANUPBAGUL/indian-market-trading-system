"""
Unit tests for KPI Computer - Tests all KPI calculation methods.
"""

import unittest
from unittest.mock import Mock
from src.kpi_computer import KPIComputer


class TestKPIComputer(unittest.TestCase):
    
    def setUp(self):
        """Set up test data."""
        # Mock trades with pnl attributes
        self.winning_trade = Mock()
        self.winning_trade.pnl = 100.0
        
        self.losing_trade = Mock()
        self.losing_trade.pnl = -50.0
        
        self.trades = [self.winning_trade, self.losing_trade]
        
        # Equity curve data
        self.equity_curve = [
            {'total_value': 10000},
            {'total_value': 10100},
            {'total_value': 9800},
            {'total_value': 10200}
        ]
        
        # Confidence bucket data
        self.confidence_data = [
            {'confidence_bucket': '60-65', 'outcome': True},
            {'confidence_bucket': '60-65', 'outcome': False},
            {'confidence_bucket': '70-75', 'outcome': True}
        ]
    
    def test_calculate_expectancy(self):
        """Test expectancy calculation."""
        expectancy = KPIComputer._calculate_expectancy(self.trades)
        self.assertEqual(expectancy, 25.0)  # (100 - 50) / 2
        
        # Empty trades
        self.assertEqual(KPIComputer._calculate_expectancy([]), 0.0)
    
    def test_calculate_max_drawdown(self):
        """Test max drawdown calculation."""
        drawdown = KPIComputer._calculate_max_drawdown(self.equity_curve)
        # Peak 10100, trough 9800 = (10100-9800)/10100 = 2.97%
        self.assertAlmostEqual(drawdown, 2.97, places=1)
        
        # Single point
        single_point = [{'total_value': 10000}]
        self.assertEqual(KPIComputer._calculate_max_drawdown(single_point), 0.0)
    
    def test_calculate_win_rate(self):
        """Test win rate calculation."""
        win_rate = KPIComputer._calculate_win_rate(self.trades)
        self.assertEqual(win_rate, 50.0)  # 1 win out of 2 trades
        
        # All winning trades
        all_wins = [self.winning_trade, self.winning_trade]
        self.assertEqual(KPIComputer._calculate_win_rate(all_wins), 100.0)
        
        # Empty trades
        self.assertEqual(KPIComputer._calculate_win_rate([]), 0.0)
    
    def test_analyze_confidence_buckets(self):
        """Test confidence bucket analysis."""
        stats = KPIComputer._analyze_confidence_buckets(self.confidence_data)
        
        # 60-65 bucket: 1 win, 1 loss = 50% actual vs 62.5% expected
        bucket_60_65 = stats['60-65']
        self.assertEqual(bucket_60_65['trades'], 2)
        self.assertEqual(bucket_60_65['wins'], 1)
        self.assertEqual(bucket_60_65['actual_win_rate'], 50.0)
        self.assertEqual(bucket_60_65['expected_win_rate'], 62.5)
        
        # 70-75 bucket: 1 win, 0 losses = 100% actual vs 72.5% expected
        bucket_70_75 = stats['70-75']
        self.assertEqual(bucket_70_75['trades'], 1)
        self.assertEqual(bucket_70_75['wins'], 1)
        self.assertEqual(bucket_70_75['actual_win_rate'], 100.0)
        
        # Empty data
        self.assertEqual(KPIComputer._analyze_confidence_buckets([]), {})
    
    def test_extract_expected_rate(self):
        """Test expected rate extraction from bucket names."""
        self.assertEqual(KPIComputer._extract_expected_rate('60-65'), 62.5)
        self.assertEqual(KPIComputer._extract_expected_rate('70-75'), 72.5)
        self.assertIsNone(KPIComputer._extract_expected_rate('invalid'))
        self.assertIsNone(KPIComputer._extract_expected_rate('60'))
    
    def test_calculate_trade_stats(self):
        """Test detailed trade statistics."""
        stats = KPIComputer._calculate_trade_stats(self.trades)
        
        self.assertEqual(stats['avg_win'], 100.0)
        self.assertEqual(stats['avg_loss'], -50.0)
        self.assertEqual(stats['largest_win'], 100.0)
        self.assertEqual(stats['largest_loss'], -50.0)
        self.assertEqual(stats['profit_factor'], 2.0)  # 100 / 50
        
        # Empty trades
        self.assertEqual(KPIComputer._calculate_trade_stats([]), {})
    
    def test_generate_summary(self):
        """Test summary generation."""
        summary = KPIComputer._generate_summary(25.0, 5.0, 50.0, 10)
        self.assertIn("PROFITABLE", summary)
        self.assertIn("MODERATE", summary)
        
        # Unprofitable system
        summary = KPIComputer._generate_summary(-100.0, 20.0, 30.0, 5)
        self.assertIn("UNPROFITABLE", summary)
        self.assertIn("HIGH", summary)
    
    def test_compute_kpis_full(self):
        """Test complete KPI computation."""
        kpis = KPIComputer.compute_kpis(
            trades=self.trades,
            equity_curve=self.equity_curve,
            confidence_buckets=self.confidence_data
        )
        
        self.assertEqual(kpis['expectancy'], 25.0)
        self.assertAlmostEqual(kpis['max_drawdown_pct'], 2.97, places=1)
        self.assertEqual(kpis['win_rate_pct'], 50.0)
        self.assertEqual(kpis['total_trades'], 2)
        self.assertIn('confidence_bucket_stats', kpis)
        self.assertIn('trade_statistics', kpis)
        self.assertIn('summary', kpis)
    
    def test_compute_kpis_empty(self):
        """Test KPI computation with no trades."""
        kpis = KPIComputer.compute_kpis([], [])
        
        self.assertEqual(kpis['expectancy'], 0.0)
        self.assertEqual(kpis['max_drawdown_pct'], 0.0)
        self.assertEqual(kpis['win_rate_pct'], 0.0)
        self.assertEqual(kpis['total_trades'], 0)
        self.assertEqual(kpis['summary'], "No trades to analyze")
    
    def test_generate_report(self):
        """Test KPI report generation."""
        kpis = KPIComputer.compute_kpis(
            trades=self.trades,
            equity_curve=self.equity_curve,
            confidence_buckets=self.confidence_data
        )
        
        report = KPIComputer.generate_report(kpis)
        
        self.assertIn("=== KPI REPORT ===", report)
        self.assertIn("CORE METRICS:", report)
        self.assertIn("Expectancy: $25.00", report)
        self.assertIn("TRADE STATISTICS:", report)
        self.assertIn("CONFIDENCE CALIBRATION:", report)
        self.assertIn("SUMMARY:", report)
        
        # Empty report
        empty_kpis = KPIComputer._empty_kpis()
        empty_report = KPIComputer.generate_report(empty_kpis)
        self.assertIn("No trades to analyze", empty_report)


if __name__ == '__main__':
    unittest.main()