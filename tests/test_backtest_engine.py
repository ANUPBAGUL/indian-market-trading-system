"""
Unit tests for BacktestEngine - Tests individual methods and components.
"""

import unittest
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from backtest_engine import BacktestEngine, Trade, Position
from governor import Governor, Decision


class MockGovernor:
    """Mock Governor for testing."""
    @staticmethod
    def run(**kwargs):
        signal_type = kwargs.get('signal_type')
        confidence = kwargs.get('confidence_score', 70)
        
        if signal_type == 'ENTRY':
            if confidence >= 60:
                return Decision.ENTER, "Entry approved"
            else:
                return Decision.NO_TRADE, "Low confidence"
        elif signal_type == 'EXIT':
            return Decision.EXIT, "Exit approved"
        else:
            return Decision.NO_TRADE, "Unknown signal"


class TestBacktestEngine(unittest.TestCase):
    
    def setUp(self):
        self.engine = BacktestEngine(initial_capital=100000)
        self.sample_data = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-01', '2023-01-02', '2023-01-02'],
            'symbol': ['AAPL', 'GOOGL', 'AAPL', 'GOOGL'],
            'open': [150.0, 2500.0, 152.0, 2480.0],
            'high': [155.0, 2520.0, 156.0, 2490.0],
            'low': [148.0, 2480.0, 150.0, 2470.0],
            'close': [153.0, 2510.0, 154.0, 2485.0],
            'volume': [1000000, 500000, 1200000, 600000]
        })
    
    def test_initialization(self):
        """Test BacktestEngine initialization."""
        engine = BacktestEngine(50000)
        self.assertEqual(engine.initial_capital, 50000)
        self.assertEqual(engine.cash, 50000)
        self.assertEqual(len(engine.positions), 0)
        self.assertEqual(len(engine.trades), 0)
        self.assertEqual(len(engine.equity_curve), 0)
    
    def test_trade_creation(self):
        """Test Trade dataclass creation."""
        trade = Trade(
            symbol='AAPL',
            entry_date='2023-01-01',
            entry_price=150.0,
            exit_date='2023-01-02',
            exit_price=155.0,
            shares=100,
            pnl=500.0,
            pnl_pct=3.33,
            exit_reason='SIGNAL'
        )
        
        self.assertEqual(trade.symbol, 'AAPL')
        self.assertEqual(trade.pnl, 500.0)
        self.assertEqual(trade.exit_reason, 'SIGNAL')
    
    def test_position_creation(self):
        """Test Position dataclass creation."""
        position = Position(
            symbol='GOOGL',
            entry_date='2023-01-01',
            entry_price=2500.0,
            shares=10,
            stop_price=2300.0
        )
        
        self.assertEqual(position.symbol, 'GOOGL')
        self.assertEqual(position.shares, 10)
        self.assertEqual(position.stop_price, 2300.0)
    
    def test_calculate_total_value(self):
        """Test portfolio value calculation."""
        # Add a position
        self.engine.positions['AAPL'] = Position(
            symbol='AAPL',
            entry_date='2023-01-01',
            entry_price=150.0,
            shares=100,
            stop_price=138.0
        )
        self.engine.cash = 85000  # Reduced by position cost
        
        day_data = self.sample_data[self.sample_data['date'] == '2023-01-01']
        total_value = self.engine._calculate_total_value(day_data)
        
        # Cash + position value (100 shares * $153 close)
        expected_value = 85000 + (100 * 153.0)
        self.assertEqual(total_value, expected_value)
    
    def test_process_stops_triggered(self):
        """Test stop loss execution when triggered."""
        # Add position with stop at $140
        self.engine.positions['AAPL'] = Position(
            symbol='AAPL',
            entry_date='2023-01-01',
            entry_price=150.0,
            shares=100,
            stop_price=140.0
        )
        self.engine.current_date = '2023-01-02'
        self.engine.cash = 85000
        
        # Create data where low price hits stop
        day_data = pd.DataFrame({
            'date': ['2023-01-02'],
            'symbol': ['AAPL'],
            'open': [145.0],
            'high': [147.0],
            'low': [139.0],  # Hits stop at 140
            'close': [142.0],
            'volume': [1000000]
        })
        
        self.engine._process_stops(day_data)
        
        # Position should be closed
        self.assertEqual(len(self.engine.positions), 0)
        self.assertEqual(len(self.engine.trades), 1)
        
        # Check trade details
        trade = self.engine.trades[0]
        self.assertEqual(trade.exit_price, 140.0)
        self.assertEqual(trade.exit_reason, 'STOP')
        self.assertEqual(trade.pnl, -1000.0)  # (140-150) * 100
        
        # Cash should be updated
        expected_cash = 85000 + (140.0 * 100)
        self.assertEqual(self.engine.cash, expected_cash)
    
    def test_process_stops_not_triggered(self):
        """Test stop loss not triggered when price stays above stop."""
        # Add position with stop at $140
        self.engine.positions['AAPL'] = Position(
            symbol='AAPL',
            entry_date='2023-01-01',
            entry_price=150.0,
            shares=100,
            stop_price=140.0
        )
        
        # Create data where low price doesn't hit stop
        day_data = pd.DataFrame({
            'date': ['2023-01-02'],
            'symbol': ['AAPL'],
            'open': [152.0],
            'high': [155.0],
            'low': [148.0],  # Above stop at 140
            'close': [154.0],
            'volume': [1000000]
        })
        
        self.engine._process_stops(day_data)
        
        # Position should remain open
        self.assertEqual(len(self.engine.positions), 1)
        self.assertEqual(len(self.engine.trades), 0)
    
    def test_process_entry_signal_approved(self):
        """Test entry signal processing when approved by Governor."""
        signal = {
            'type': 'ENTRY',
            'symbol': 'AAPL',
            'confidence': 75.0,
            'shares': 100,
            'sector': 'Technology',
            'stop_price': 138.0
        }
        
        day_data = self.sample_data[self.sample_data['date'] == '2023-01-01']
        self.engine.current_date = '2023-01-01'
        
        self.engine._process_entry_signal(signal, day_data, MockGovernor)
        
        # Position should be created
        self.assertEqual(len(self.engine.positions), 1)
        self.assertIn('AAPL', self.engine.positions)
        
        position = self.engine.positions['AAPL']
        self.assertEqual(position.entry_price, 150.0)  # Open price
        self.assertEqual(position.shares, 100)
        
        # Cash should be reduced
        expected_cash = 100000 - (150.0 * 100)
        self.assertEqual(self.engine.cash, expected_cash)
    
    def test_process_entry_signal_rejected(self):
        """Test entry signal processing when rejected by Governor."""
        signal = {
            'type': 'ENTRY',
            'symbol': 'AAPL',
            'confidence': 50.0,  # Below threshold
            'shares': 100,
            'sector': 'Technology',
            'stop_price': 138.0
        }
        
        day_data = self.sample_data[self.sample_data['date'] == '2023-01-01']
        self.engine.current_date = '2023-01-01'
        
        self.engine._process_entry_signal(signal, day_data, MockGovernor)
        
        # No position should be created
        self.assertEqual(len(self.engine.positions), 0)
        self.assertEqual(self.engine.cash, 100000)  # Cash unchanged
    
    def test_process_exit_signal(self):
        """Test exit signal processing."""
        # Add existing position
        self.engine.positions['AAPL'] = Position(
            symbol='AAPL',
            entry_date='2023-01-01',
            entry_price=150.0,
            shares=100,
            stop_price=138.0
        )
        self.engine.cash = 85000
        self.engine.current_date = '2023-01-02'
        
        signal = {
            'type': 'EXIT',
            'symbol': 'AAPL',
            'decayed_confidence': 45.0
        }
        
        day_data = self.sample_data[self.sample_data['date'] == '2023-01-02']
        
        self.engine._process_exit_signal(signal, day_data, MockGovernor)
        
        # Position should be closed
        self.assertEqual(len(self.engine.positions), 0)
        self.assertEqual(len(self.engine.trades), 1)
        
        # Check trade details
        trade = self.engine.trades[0]
        self.assertEqual(trade.exit_price, 152.0)  # Open price
        self.assertEqual(trade.exit_reason, 'SIGNAL')
        self.assertEqual(trade.pnl, 200.0)  # (152-150) * 100
        
        # Cash should be updated
        expected_cash = 85000 + (152.0 * 100)
        self.assertEqual(self.engine.cash, expected_cash)
    
    def test_update_equity_curve(self):
        """Test equity curve update."""
        self.engine.current_date = '2023-01-01'
        day_data = self.sample_data[self.sample_data['date'] == '2023-01-01']
        
        self.engine._update_equity_curve(day_data)
        
        self.assertEqual(len(self.engine.equity_curve), 1)
        
        point = self.engine.equity_curve[0]
        self.assertEqual(point['date'], '2023-01-01')
        self.assertEqual(point['cash'], 100000)
        self.assertEqual(point['total_value'], 100000)
        self.assertEqual(point['num_positions'], 0)
    
    def test_generate_results(self):
        """Test results generation."""
        # Add sample trade
        self.engine.trades.append(Trade(
            symbol='AAPL',
            entry_date='2023-01-01',
            entry_price=150.0,
            exit_date='2023-01-02',
            exit_price=155.0,
            shares=100,
            pnl=500.0,
            pnl_pct=3.33,
            exit_reason='SIGNAL'
        ))
        
        # Add equity curve point
        self.engine.equity_curve.append({
            'date': '2023-01-02',
            'cash': 100000,
            'positions_value': 500,
            'total_value': 100500,
            'num_positions': 0
        })
        
        results = self.engine._generate_results()
        
        self.assertIn('trades', results)
        self.assertIn('equity_curve', results)
        self.assertIn('metrics', results)
        
        metrics = results['metrics']
        self.assertEqual(metrics['total_trades'], 1)
        self.assertEqual(metrics['winning_trades'], 1)
        self.assertEqual(metrics['win_rate_pct'], 100.0)
        self.assertAlmostEqual(metrics['total_return_pct'], 0.5, places=1)


def simple_signal_generator(day_data, existing_positions):
    """Simple signal generator for testing."""
    return [
        {
            'type': 'ENTRY',
            'symbol': 'AAPL',
            'confidence': 75.0,
            'shares': 100,
            'sector': 'Technology',
            'stop_price': 138.0
        }
    ]


class TestBacktestEngineSignalProcessing(unittest.TestCase):
    
    def test_process_signal_entry(self):
        """Test signal processing for entry signals."""
        engine = BacktestEngine(100000)
        engine.current_date = '2023-01-01'
        
        signal = {
            'type': 'ENTRY',
            'symbol': 'AAPL',
            'confidence': 75.0,
            'shares': 100,
            'sector': 'Technology',
            'stop_price': 138.0
        }
        
        day_data = pd.DataFrame({
            'date': ['2023-01-01'],
            'symbol': ['AAPL'],
            'open': [150.0],
            'high': [155.0],
            'low': [148.0],
            'close': [153.0],
            'volume': [1000000]
        })
        
        engine._process_signal(signal, day_data, MockGovernor)
        
        self.assertEqual(len(engine.positions), 1)
        self.assertIn('AAPL', engine.positions)
    
    def test_process_signal_exit(self):
        """Test signal processing for exit signals."""
        engine = BacktestEngine(100000)
        engine.current_date = '2023-01-02'
        
        # Add existing position
        engine.positions['AAPL'] = Position(
            symbol='AAPL',
            entry_date='2023-01-01',
            entry_price=150.0,
            shares=100,
            stop_price=138.0
        )
        
        signal = {
            'type': 'EXIT',
            'symbol': 'AAPL',
            'decayed_confidence': 45.0
        }
        
        day_data = pd.DataFrame({
            'date': ['2023-01-02'],
            'symbol': ['AAPL'],
            'open': [152.0],
            'high': [155.0],
            'low': [150.0],
            'close': [154.0],
            'volume': [1000000]
        })
        
        engine._process_signal(signal, day_data, MockGovernor)
        
        self.assertEqual(len(engine.positions), 0)
        self.assertEqual(len(engine.trades), 1)


if __name__ == '__main__':
    unittest.main()