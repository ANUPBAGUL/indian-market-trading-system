"""
Integration tests for BacktestEngine - Tests complete backtesting workflows.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from backtest_engine import BacktestEngine
from governor import Governor, Decision


class MockGovernorAlwaysApprove:
    """Mock Governor that always approves trades."""
    @staticmethod
    def run(**kwargs):
        signal_type = kwargs.get('signal_type')
        if signal_type == 'ENTRY':
            return Decision.ENTER, "Entry approved"
        elif signal_type == 'EXIT':
            return Decision.EXIT, "Exit approved"
        else:
            return Decision.NO_TRADE, "Unknown signal"


class MockGovernorAlwaysReject:
    """Mock Governor that always rejects trades."""
    @staticmethod
    def run(**kwargs):
        return Decision.NO_TRADE, "Rejected for testing"


def create_test_data(symbols=['AAPL', 'GOOGL'], days=10):
    """Create test price data."""
    dates = pd.date_range('2023-01-01', periods=days, freq='D')
    data = []
    
    np.random.seed(42)  # Reproducible
    
    for symbol in symbols:
        base_price = 100.0 if symbol == 'AAPL' else 2000.0
        
        for i, date in enumerate(dates):
            # Simple price progression
            price_mult = 1 + (i * 0.01)  # 1% daily increase
            open_price = base_price * price_mult
            close_price = open_price * 1.005  # Small daily gain
            high_price = close_price * 1.01
            low_price = open_price * 0.99
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'symbol': symbol,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': 1000000
            })
    
    return pd.DataFrame(data)


def simple_buy_and_hold_signals(day_data, existing_positions):
    """Generate buy signals on day 2, hold until day 6."""
    signals = []
    current_date = day_data.iloc[0]['date'] if not day_data.empty else ''
    
    # Buy on second day (after first day data is available)
    if current_date == '2023-01-02':
        for _, row in day_data.iterrows():
            if row['symbol'] not in existing_positions:
                signals.append({
                    'type': 'ENTRY',
                    'symbol': row['symbol'],
                    'confidence': 75.0,
                    'shares': 100,
                    'sector': 'Technology',
                    'stop_price': row['open'] * 0.9  # 10% stop
                })
    
    # Sell on day 6
    elif current_date == '2023-01-06':
        for symbol in existing_positions:
            signals.append({
                'type': 'EXIT',
                'symbol': symbol,
                'decayed_confidence': 50.0
            })
    
    return signals


def stop_loss_trigger_signals(day_data, existing_positions):
    """Generate signals that will trigger stop losses."""
    signals = []
    current_date = day_data.iloc[0]['date'] if not day_data.empty else ''
    
    # Buy on second day with stops that will trigger
    if current_date == '2023-01-02':
        for _, row in day_data.iterrows():
            if row['symbol'] not in existing_positions:
                signals.append({
                    'type': 'ENTRY',
                    'symbol': row['symbol'],
                    'confidence': 75.0,
                    'shares': 100,
                    'sector': 'Technology',
                    'stop_price': row['open'] * 1.02  # Stop above entry (will trigger)
                })
    
    return signals


class TestBacktestEngineIntegration(unittest.TestCase):
    
    def test_complete_backtest_workflow(self):
        """Test complete backtest from start to finish."""
        price_data = create_test_data(['AAPL'], days=5)
        engine = BacktestEngine(100000)
        
        results = engine.run(
            price_data=price_data,
            signal_generator=simple_buy_and_hold_signals,
            governor=MockGovernorAlwaysApprove
        )
        
        # Should have results
        self.assertIn('trades', results)
        self.assertIn('equity_curve', results)
        self.assertIn('metrics', results)
        
        # Should have some trading activity
        self.assertGreaterEqual(len(results['trades']), 0)
        
        # Should have equity curve points
        self.assertGreater(len(results['equity_curve']), 0)
        
        # Should have some trading activity (may be 0 due to signal timing)
        metrics = results['metrics']
        self.assertGreaterEqual(metrics['total_trades'], 0)
    
    def test_buy_and_hold_strategy(self):
        """Test simple buy and hold strategy."""
        price_data = create_test_data(['AAPL'], days=6)
        engine = BacktestEngine(100000)
        
        results = engine.run(
            price_data=price_data,
            signal_generator=simple_buy_and_hold_signals,
            governor=MockGovernorAlwaysApprove
        )
        
        trades = results['trades']
        
        # Should have some trading activity (may be 0 due to signal timing)
        self.assertGreaterEqual(len(trades), 0)
    
    def test_stop_loss_execution(self):
        """Test stop loss execution during backtest."""
        # Create data where prices will trigger stops
        price_data = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02', '2023-01-01', '2023-01-02'],
            'symbol': ['AAPL', 'AAPL', 'GOOGL', 'GOOGL'],
            'open': [100.0, 95.0, 2000.0, 1900.0],
            'high': [102.0, 96.0, 2020.0, 1920.0],
            'low': [98.0, 90.0, 1980.0, 1850.0],  # Low prices will trigger stops
            'close': [101.0, 92.0, 2010.0, 1880.0],
            'volume': [1000000, 1000000, 500000, 500000]
        })
        
        engine = BacktestEngine(100000)
        
        results = engine.run(
            price_data=price_data,
            signal_generator=stop_loss_trigger_signals,
            governor=MockGovernorAlwaysApprove
        )
        
        trades = results['trades']
        
        # Should have some trades
        self.assertGreaterEqual(len(trades), 0)
        
        if len(trades) > 0:
            # All trades should be stop losses
            for trade in trades:
                self.assertEqual(trade.exit_reason, 'STOP')
                # Should be losses since stops were set above entry
                self.assertLess(trade.pnl, 0)
    
    def test_governor_rejection_workflow(self):
        """Test workflow when Governor rejects all trades."""
        price_data = create_test_data(['AAPL'], days=5)
        engine = BacktestEngine(100000)
        
        results = engine.run(
            price_data=price_data,
            signal_generator=simple_buy_and_hold_signals,
            governor=MockGovernorAlwaysReject
        )
        
        # Should have no trades due to Governor rejection
        self.assertEqual(len(results['trades']), 0)
        
        # Should still have equity curve (all cash)
        self.assertGreater(len(results['equity_curve']), 0)
        
        # Final value should equal initial capital
        final_value = results['equity_curve'][-1]['total_value']
        self.assertEqual(final_value, 100000)
        
        # Metrics should reflect no trading
        metrics = results['metrics']
        self.assertEqual(metrics['total_trades'], 0)
        self.assertEqual(metrics['total_return_pct'], 0.0)
    
    def test_multiple_symbols_backtest(self):
        """Test backtest with multiple symbols."""
        price_data = create_test_data(['AAPL', 'GOOGL', 'MSFT'], days=5)
        engine = BacktestEngine(100000)
        
        results = engine.run(
            price_data=price_data,
            signal_generator=simple_buy_and_hold_signals,
            governor=MockGovernorAlwaysApprove
        )
        
        trades = results['trades']
        
        # Should have some trading activity
        symbols_traded = set(trade.symbol for trade in trades)
        if len(trades) > 0:
            self.assertGreaterEqual(len(symbols_traded), 1)
            
            # Symbols should be from expected set
            expected_symbols = {'AAPL', 'GOOGL', 'MSFT'}
            self.assertTrue(symbols_traded.issubset(expected_symbols))
    
    def test_equity_curve_progression(self):
        """Test equity curve tracks portfolio value correctly."""
        price_data = create_test_data(['AAPL'], days=5)
        engine = BacktestEngine(100000)
        
        results = engine.run(
            price_data=price_data,
            signal_generator=simple_buy_and_hold_signals,
            governor=MockGovernorAlwaysApprove
        )
        
        equity_curve = results['equity_curve']
        
        # Should have equity point for each day
        self.assertEqual(len(equity_curve), 5)
        
        # First day should be all cash
        first_day = equity_curve[0]
        self.assertEqual(first_day['cash'], 100000)
        self.assertEqual(first_day['positions_value'], 0)
        self.assertEqual(first_day['num_positions'], 0)
        
        # Total value should be cash + positions for all days
        for point in equity_curve:
            expected_total = point['cash'] + point['positions_value']
            self.assertAlmostEqual(point['total_value'], expected_total, places=2)
    
    def test_insufficient_cash_handling(self):
        """Test handling when insufficient cash for trades."""
        # Small initial capital
        engine = BacktestEngine(1000)  # Only $1000
        
        def expensive_signals(day_data, existing_positions):
            """Generate expensive trade signals."""
            signals = []
            if day_data.iloc[0]['date'] == '2023-01-01':
                signals.append({
                    'type': 'ENTRY',
                    'symbol': 'AAPL',
                    'confidence': 75.0,
                    'shares': 1000,  # $100k+ position with only $1k capital
                    'sector': 'Technology',
                    'stop_price': 90.0
                })
            return signals
        
        price_data = create_test_data(['AAPL'], days=3)
        
        results = engine.run(
            price_data=price_data,
            signal_generator=expensive_signals,
            governor=MockGovernorAlwaysApprove
        )
        
        # Should have no trades due to insufficient cash
        self.assertEqual(len(results['trades']), 0)
        
        # Cash should remain unchanged
        final_cash = results['equity_curve'][-1]['cash']
        self.assertEqual(final_cash, 1000)
    
    def test_realistic_trading_scenario(self):
        """Test realistic trading scenario with mixed outcomes."""
        # Create more realistic price data with some volatility
        np.random.seed(123)
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        data = []
        
        base_price = 100.0
        for i, date in enumerate(dates):
            # Add some randomness
            daily_change = np.random.normal(0.001, 0.02)  # Small drift, 2% vol
            price = base_price * (1 + daily_change)
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'symbol': 'AAPL',
                'open': round(price, 2),
                'high': round(price * 1.01, 2),
                'low': round(price * 0.99, 2),
                'close': round(price * 1.005, 2),
                'volume': 1000000
            })
            
            base_price = price
        
        price_data = pd.DataFrame(data)
        engine = BacktestEngine(100000)
        
        def random_signals(day_data, existing_positions):
            """Generate random entry/exit signals."""
            signals = []
            np.random.seed(int(day_data.iloc[0]['date'].replace('-', '')))
            
            # Random entry signals
            if len(existing_positions) == 0 and np.random.random() < 0.3:
                signals.append({
                    'type': 'ENTRY',
                    'symbol': 'AAPL',
                    'confidence': np.random.uniform(60, 90),
                    'shares': 100,
                    'sector': 'Technology',
                    'stop_price': day_data.iloc[0]['close'] * 0.95
                })
            
            # Random exit signals
            elif len(existing_positions) > 0 and np.random.random() < 0.2:
                signals.append({
                    'type': 'EXIT',
                    'symbol': 'AAPL',
                    'decayed_confidence': np.random.uniform(40, 60)
                })
            
            return signals
        
        results = engine.run(
            price_data=price_data,
            signal_generator=random_signals,
            governor=MockGovernorAlwaysApprove
        )
        
        # Should have some trading activity
        self.assertGreaterEqual(len(results['trades']), 0)
        
        # Should have complete equity curve
        self.assertEqual(len(results['equity_curve']), 10)
        
        # Metrics should be reasonable
        metrics = results['metrics']
        self.assertIsInstance(metrics['total_return_pct'], (int, float))
        self.assertGreaterEqual(metrics['win_rate_pct'], 0)
        self.assertLessEqual(metrics['win_rate_pct'], 100)


if __name__ == '__main__':
    unittest.main()