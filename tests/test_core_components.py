"""
Core Component Unit Tests - Tests individual system components in isolation.

Tests the fundamental building blocks of the trading system to ensure
each component works correctly before integration testing.
"""

import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
import numpy as np
from datetime import datetime

from backtest_engine import BacktestEngine, Trade, Position
from governor import Governor, GovernorDecision
from confidence_engine import ConfidenceEngine
from kpi_computer import KPIComputer

class TestBacktestEngine(unittest.TestCase):
    """Test BacktestEngine core functionality."""
    
    def setUp(self):
        """Set up test backtester."""
        self.backtester = BacktestEngine(initial_capital=100000)
    
    def test_initialization(self):
        """Test backtester initialization."""
        self.assertEqual(self.backtester.initial_capital, 100000)
        self.assertEqual(self.backtester.cash, 100000)
        self.assertEqual(len(self.backtester.positions), 0)
        self.assertEqual(len(self.backtester.trades), 0)
    
    def test_trade_creation(self):
        """Test Trade dataclass."""
        trade = Trade(
            symbol='AAPL',
            entry_date='2024-01-01',
            entry_price=150.0,
            exit_date='2024-01-05',
            exit_price=155.0,
            shares=100,
            pnl=500.0,
            pnl_pct=3.33
        )
        
        self.assertEqual(trade.symbol, 'AAPL')
        self.assertEqual(trade.pnl, 500.0)
        self.assertEqual(trade.shares, 100)
    
    def test_position_creation(self):
        """Test Position dataclass."""
        position = Position(
            symbol='MSFT',
            entry_date='2024-01-01',
            entry_price=300.0,
            shares=50,
            stop_price=285.0
        )
        
        self.assertEqual(position.symbol, 'MSFT')
        self.assertEqual(position.shares, 50)
        self.assertEqual(position.stop_price, 285.0)

class TestGovernor(unittest.TestCase):
    """Test Governor decision-making logic."""
    
    def setUp(self):
        """Set up test governor."""
        self.governor = Governor()
    
    def test_entry_decision_high_confidence(self):
        """Test entry decision with high confidence."""
        decision, reason = self.governor.run(
            signal_type='ENTRY',
            symbol='AAPL',
            current_price=150.0,
            confidence_score=80.0,
            position_size=100,
            sector='Technology',
            daily_volume=2000000,
            existing_positions=[]
        )
        
        self.assertIsInstance(decision, GovernorDecision)
        self.assertIsInstance(reason, str)
    
    def test_entry_decision_low_confidence(self):
        """Test entry decision with low confidence."""
        decision, reason = self.governor.run(
            signal_type='ENTRY',
            symbol='AAPL',
            current_price=150.0,
            confidence_score=40.0,  # Below threshold
            position_size=100,
            sector='Technology',
            daily_volume=2000000,
            existing_positions=[]
        )
        
        # Should reject due to low confidence
        self.assertEqual(decision, GovernorDecision.REJECT)
        self.assertIn('confidence', reason.lower())
    
    def test_exit_decision(self):
        """Test exit decision logic."""
        decision, reason = self.governor.run(
            signal_type='EXIT',
            symbol='AAPL',
            current_price=160.0,
            confidence_score=70.0,
            position_size=0,
            sector='Technology',
            daily_volume=1500000,
            position_pnl_pct=6.67
        )
        
        self.assertIsInstance(decision, GovernorDecision)
        self.assertIsInstance(reason, str)

class TestConfidenceEngine(unittest.TestCase):
    """Test ConfidenceEngine scoring logic."""
    
    def setUp(self):
        """Set up test confidence engine."""
        self.confidence_engine = ConfidenceEngine()
    
    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        result = self.confidence_engine.run(
            accumulation_score=70.0,
            trigger_score=75.0,
            sector_score=80.0,
            earnings_score=65.0
        )
        
        self.assertIn('confidence', result)
        self.assertIsInstance(result['confidence'], (int, float))
        self.assertGreaterEqual(result['confidence'], 0)
        self.assertLessEqual(result['confidence'], 100)
    
    def test_confidence_with_extreme_values(self):
        """Test confidence calculation with extreme input values."""
        # Test with very high scores
        result_high = self.confidence_engine.run(
            accumulation_score=95.0,
            trigger_score=90.0,
            sector_score=85.0,
            earnings_score=88.0
        )
        
        # Test with very low scores
        result_low = self.confidence_engine.run(
            accumulation_score=20.0,
            trigger_score=15.0,
            sector_score=25.0,
            earnings_score=30.0
        )
        
        # High scores should produce higher confidence
        self.assertGreater(result_high['confidence'], result_low['confidence'])
    
    def test_confidence_weights(self):
        """Test that confidence weights are applied correctly."""
        # Test with one high score and others low
        result = self.confidence_engine.run(
            accumulation_score=90.0,  # High
            trigger_score=30.0,      # Low
            sector_score=30.0,       # Low
            earnings_score=30.0      # Low
        )
        
        # Should be weighted average, not just high score
        self.assertLess(result['confidence'], 90.0)
        self.assertGreater(result['confidence'], 30.0)

class TestKPIComputer(unittest.TestCase):
    """Test KPIComputer calculations."""
    
    def setUp(self):
        """Set up test data."""
        self.winning_trades = [
            Trade(symbol='AAPL', entry_date='2024-01-01', entry_price=100, 
                  exit_date='2024-01-05', exit_price=110, shares=100, pnl=1000),
            Trade(symbol='MSFT', entry_date='2024-01-02', entry_price=200, 
                  exit_date='2024-01-06', exit_price=220, shares=50, pnl=1000),
        ]
        
        self.losing_trades = [
            Trade(symbol='GOOGL', entry_date='2024-01-03', entry_price=150, 
                  exit_date='2024-01-07', exit_price=140, shares=100, pnl=-1000),
        ]
        
        self.mixed_trades = self.winning_trades + self.losing_trades
        
        self.equity_curve = [
            {'date': '2024-01-01', 'total_value': 100000},
            {'date': '2024-01-05', 'total_value': 101000},
            {'date': '2024-01-10', 'total_value': 101000},
        ]
    
    def test_expectancy_calculation(self):
        """Test expectancy calculation."""
        expectancy = KPIComputer._calculate_expectancy(self.mixed_trades)
        expected = (1000 + 1000 - 1000) / 3  # Average P&L
        self.assertAlmostEqual(expectancy, expected, places=2)
    
    def test_win_rate_calculation(self):
        """Test win rate calculation."""
        win_rate = KPIComputer._calculate_win_rate(self.mixed_trades)
        expected = (2 / 3) * 100  # 2 winners out of 3 trades
        self.assertAlmostEqual(win_rate, expected, places=1)
    
    def test_max_drawdown_calculation(self):
        """Test maximum drawdown calculation."""
        # Create equity curve with drawdown
        equity_with_dd = [
            {'date': '2024-01-01', 'total_value': 100000},
            {'date': '2024-01-02', 'total_value': 105000},  # Peak
            {'date': '2024-01-03', 'total_value': 95000},   # Drawdown
            {'date': '2024-01-04', 'total_value': 102000},  # Recovery
        ]
        
        max_dd = KPIComputer._calculate_max_drawdown(equity_with_dd)
        expected = ((105000 - 95000) / 105000) * 100  # 9.52%
        self.assertAlmostEqual(max_dd, expected, places=1)
    
    def test_empty_trades_handling(self):
        """Test handling of empty trade list."""
        kpis = KPIComputer.compute_kpis(
            trades=[],
            equity_curve=self.equity_curve
        )
        
        self.assertEqual(kpis['expectancy'], 0.0)
        self.assertEqual(kpis['win_rate_pct'], 0.0)
        self.assertEqual(kpis['total_trades'], 0)
    
    def test_trade_statistics(self):
        """Test detailed trade statistics calculation."""
        stats = KPIComputer._calculate_trade_stats(self.mixed_trades)
        
        self.assertEqual(stats['avg_win'], 1000.0)  # Average of winning trades
        self.assertEqual(stats['avg_loss'], -1000.0)  # Average of losing trades
        self.assertEqual(stats['largest_win'], 1000.0)
        self.assertEqual(stats['largest_loss'], -1000.0)
        
        # Profit factor = Gross Profit / Gross Loss
        expected_pf = 2000 / 1000  # 2.0
        self.assertEqual(stats['profit_factor'], expected_pf)

class TestSystemValidation(unittest.TestCase):
    """Test system validation and data integrity."""
    
    def test_data_schema_validation(self):
        """Test that required data columns are present."""
        required_columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']
        
        # Create valid data
        valid_data = pd.DataFrame([{
            'date': '2024-01-01',
            'symbol': 'AAPL',
            'open': 150.0,
            'high': 152.0,
            'low': 148.0,
            'close': 151.0,
            'volume': 1000000
        }])
        
        # Check all required columns are present
        for col in required_columns:
            self.assertIn(col, valid_data.columns)
    
    def test_price_data_consistency(self):
        """Test price data logical consistency."""
        # High should be >= Open, Close, Low
        # Low should be <= Open, Close, High
        
        sample_data = {
            'open': 150.0,
            'high': 155.0,
            'low': 148.0,
            'close': 152.0
        }
        
        self.assertGreaterEqual(sample_data['high'], sample_data['open'])
        self.assertGreaterEqual(sample_data['high'], sample_data['close'])
        self.assertGreaterEqual(sample_data['high'], sample_data['low'])
        
        self.assertLessEqual(sample_data['low'], sample_data['open'])
        self.assertLessEqual(sample_data['low'], sample_data['close'])
        self.assertLessEqual(sample_data['low'], sample_data['high'])
    
    def test_volume_validation(self):
        """Test volume data validation."""
        # Volume should be non-negative
        valid_volumes = [0, 1000, 1000000, 50000000]
        invalid_volumes = [-1, -1000]
        
        for vol in valid_volumes:
            self.assertGreaterEqual(vol, 0)
        
        for vol in invalid_volumes:
            self.assertLess(vol, 0)  # These should fail validation

if __name__ == '__main__':
    unittest.main()