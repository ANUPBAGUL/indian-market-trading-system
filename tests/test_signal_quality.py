"""
Unit Tests for Signal Quality KPI - Tests the new signal tracking functionality.

Tests signal conversion rates, accuracy calculations, and rejection analysis
to ensure the Signal Quality KPI works correctly.
"""

import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from kpi_computer import KPIComputer
from backtest_engine import Trade

class TestSignalQualityKPI(unittest.TestCase):
    """Test Signal Quality KPI calculations."""
    
    def setUp(self):
        """Set up test data."""
        # Sample trades
        self.trades = [
            Trade(symbol='AAPL', entry_date='2024-01-02', entry_price=150.0, 
                  exit_date='2024-01-10', exit_price=155.0, shares=100, pnl=500.0),
            Trade(symbol='MSFT', entry_date='2024-01-03', entry_price=300.0, 
                  exit_date='2024-01-11', exit_price=290.0, shares=50, pnl=-500.0),
        ]
        
        # Sample equity curve
        self.equity_curve = [
            {'date': '2024-01-01', 'total_value': 100000},
            {'date': '2024-01-15', 'total_value': 100000},
        ]
        
        # Sample signal data
        self.signal_data = [
            {'date': '2024-01-02', 'symbol': 'AAPL', 'executed': True, 'rejection_reason': None},
            {'date': '2024-01-03', 'symbol': 'MSFT', 'executed': True, 'rejection_reason': None},
            {'date': '2024-01-04', 'symbol': 'GOOGL', 'executed': False, 'rejection_reason': 'Governor rejected'},
            {'date': '2024-01-05', 'symbol': 'TSLA', 'executed': False, 'rejection_reason': 'Insufficient cash'},
        ]
    
    def test_signal_conversion_rate(self):
        """Test signal conversion rate calculation."""
        kpis = KPIComputer.compute_kpis(
            trades=self.trades,
            equity_curve=self.equity_curve,
            signal_data=self.signal_data
        )
        
        sq = kpis['signal_quality_stats']
        self.assertEqual(sq['total_signals'], 4)
        self.assertEqual(sq['executed_signals'], 2)
        self.assertEqual(sq['conversion_rate_pct'], 50.0)
    
    def test_signal_accuracy(self):
        """Test signal accuracy calculation."""
        kpis = KPIComputer.compute_kpis(
            trades=self.trades,
            equity_curve=self.equity_curve,
            signal_data=self.signal_data
        )
        
        sq = kpis['signal_quality_stats']
        self.assertEqual(sq['profitable_signals'], 1)  # Only AAPL was profitable
        self.assertEqual(sq['signal_accuracy_pct'], 50.0)  # 1 out of 2 executed signals
    
    def test_rejection_reasons(self):
        """Test rejection reason analysis."""
        kpis = KPIComputer.compute_kpis(
            trades=self.trades,
            equity_curve=self.equity_curve,
            signal_data=self.signal_data
        )
        
        sq = kpis['signal_quality_stats']
        expected_rejections = {
            'Governor rejected': 1,
            'Insufficient cash': 1
        }
        self.assertEqual(sq['rejection_reasons'], expected_rejections)
    
    def test_empty_signal_data(self):
        """Test handling of empty signal data."""
        kpis = KPIComputer.compute_kpis(
            trades=self.trades,
            equity_curve=self.equity_curve,
            signal_data=[]
        )
        
        self.assertEqual(kpis['signal_quality_stats'], {})
    
    def test_no_signal_data(self):
        """Test handling when signal_data is None."""
        kpis = KPIComputer.compute_kpis(
            trades=self.trades,
            equity_curve=self.equity_curve,
            signal_data=None
        )
        
        self.assertEqual(kpis['signal_quality_stats'], {})

class TestIndianMarketConfig(unittest.TestCase):
    """Test Indian market configuration."""
    
    def test_indian_market_imports(self):
        """Test that Indian market modules can be imported."""
        try:
            from indian_market_config import IndianMarketConfig, IndianSectorMapper
            from indian_data_loader import IndianDataLoader
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import Indian market modules: {e}")
    
    def test_sector_mapping(self):
        """Test Indian sector mapping functionality."""
        from indian_market_config import IndianSectorMapper
        
        # Test known mappings
        self.assertEqual(IndianSectorMapper.get_sector('RELIANCE'), 'Energy')
        self.assertEqual(IndianSectorMapper.get_sector('TCS'), 'IT')
        self.assertEqual(IndianSectorMapper.get_sector('HDFCBANK'), 'Banking')
        
        # Test unknown symbol
        self.assertEqual(IndianSectorMapper.get_sector('UNKNOWN'), 'Others')
    
    def test_indian_market_config(self):
        """Test Indian market configuration values."""
        from indian_market_config import INDIAN_MARKET_CONFIG
        
        self.assertEqual(INDIAN_MARKET_CONFIG.market_open_time, "09:15")
        self.assertEqual(INDIAN_MARKET_CONFIG.market_close_time, "15:30")
        self.assertEqual(INDIAN_MARKET_CONFIG.currency, "INR")
        self.assertEqual(INDIAN_MARKET_CONFIG.max_position_risk_pct, 2.0)

if __name__ == '__main__':
    unittest.main()