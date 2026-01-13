"""
Integration Tests - Tests complete system workflows and component interactions.

Tests the full pipeline from data loading through signal generation,
backtesting, and KPI calculation to ensure system integrity.
"""

import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from backtest_engine import BacktestEngine
from kpi_computer import KPIComputer
from governor import Governor
from confidence_engine import ConfidenceEngine
from accumulation_agent import AccumulationAgent
from trigger_agent import TriggerAgent

class TestSystemIntegration(unittest.TestCase):
    """Test complete system integration."""
    
    def setUp(self):
        """Set up test data and components."""
        # Create sample market data
        self.sample_data = self._create_sample_data()
        
        # Initialize system components
        self.backtester = BacktestEngine(initial_capital=100000)
        self.governor = Governor()
        self.confidence_engine = ConfidenceEngine()
        
    def _create_sample_data(self):
        """Create realistic sample market data."""
        dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        data = []
        for date in dates:
            if date.weekday() < 5:  # Trading days only
                for symbol in symbols:
                    base_price = {'AAPL': 150, 'MSFT': 300, 'GOOGL': 120}[symbol]
                    
                    # Generate realistic OHLCV
                    open_price = base_price * (0.98 + 0.04 * np.random.random())
                    high_price = open_price * (1.0 + 0.02 * np.random.random())
                    low_price = open_price * (1.0 - 0.02 * np.random.random())
                    close_price = low_price + (high_price - low_price) * np.random.random()
                    volume = int(1000000 * (0.5 + np.random.random()))
                    
                    data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'symbol': symbol,
                        'open': round(open_price, 2),
                        'high': round(high_price, 2),
                        'low': round(low_price, 2),
                        'close': round(close_price, 2),
                        'volume': volume
                    })
        
        return pd.DataFrame(data)
    
    def _create_simple_signal_generator(self):
        """Create a simple signal generator for testing."""
        def generate_signals(day_data, existing_positions):
            signals = []
            
            for _, row in day_data.iterrows():
                symbol = row['symbol']
                
                # Skip if already have position
                if symbol in existing_positions:
                    continue
                
                # Simple momentum signal
                price_change = (row['close'] - row['open']) / row['open']
                
                if price_change > 0.01:  # 1% up
                    confidence = 70.0
                    shares = 100
                    
                    signal = {
                        'symbol': symbol,
                        'type': 'ENTRY',
                        'confidence': confidence,
                        'shares': shares,
                        'sector': 'Technology',
                        'stop_price': row['close'] * 0.95,
                        'reasoning': f"Momentum signal: {price_change:.2%}"
                    }
                    signals.append(signal)
            
            return signals
        
        return generate_signals
    
    def test_complete_backtest_workflow(self):
        """Test complete backtesting workflow."""
        signal_generator = self._create_simple_signal_generator()
        
        # Run backtest
        results = self.backtester.run(
            price_data=self.sample_data,
            signal_generator=signal_generator,
            governor=self.governor
        )
        
        # Verify results structure
        self.assertIn('trades', results)
        self.assertIn('equity_curve', results)
        self.assertIn('signal_log', results)
        self.assertIn('metrics', results)
        
        # Verify equity curve
        self.assertGreater(len(results['equity_curve']), 0)
        self.assertEqual(results['equity_curve'][0]['total_value'], 100000)
    
    def test_kpi_calculation_with_signal_data(self):
        """Test KPI calculation including Signal Quality."""
        signal_generator = self._create_simple_signal_generator()
        
        # Run backtest
        results = self.backtester.run(
            price_data=self.sample_data,
            signal_generator=signal_generator,
            governor=self.governor
        )
        
        # Calculate KPIs
        kpis = KPIComputer.compute_kpis(
            trades=results['trades'],
            equity_curve=results['equity_curve'],
            signal_data=results['signal_log']
        )
        
        # Verify KPI structure
        required_keys = [
            'expectancy', 'max_drawdown_pct', 'win_rate_pct',
            'signal_quality_stats', 'trade_statistics', 'total_trades'
        ]
        
        for key in required_keys:
            self.assertIn(key, kpis)
        
        # Verify signal quality stats if signals were generated
        if results['signal_log']:
            sq = kpis['signal_quality_stats']
            self.assertIn('total_signals', sq)
            self.assertIn('conversion_rate_pct', sq)
            self.assertIn('signal_accuracy_pct', sq)
    
    def test_agent_integration(self):
        """Test agent integration with confidence engine."""
        # Create sample symbol data
        symbol_data = {
            'current_price': 150.0,
            'volume': 1000000,
            'high': 152.0,
            'low': 148.0,
            'open': 149.0
        }
        
        market_data = {'market_trend': 'bullish'}
        
        # Test individual agents
        accumulation_agent = AccumulationAgent()
        trigger_agent = TriggerAgent()
        
        acc_result = accumulation_agent.run(symbol_data, market_data)
        trigger_result = trigger_agent.run(symbol_data, market_data)
        
        # Verify agent outputs
        self.assertIn('confidence', acc_result)
        self.assertIn('confidence', trigger_result)
        self.assertIsInstance(acc_result['confidence'], (int, float))
        self.assertIsInstance(trigger_result['confidence'], (int, float))
        
        # Test confidence engine integration
        confidence_result = self.confidence_engine.run(
            accumulation_score=acc_result['confidence'],
            trigger_score=trigger_result['confidence'],
            sector_score=70.0,
            earnings_score=70.0
        )
        
        self.assertIn('confidence', confidence_result)
        self.assertIsInstance(confidence_result['confidence'], (int, float))
    
    def test_governor_integration(self):
        """Test Governor integration with system."""
        # Test entry decision
        decision, reason = self.governor.run(
            signal_type='ENTRY',
            symbol='AAPL',
            current_price=150.0,
            confidence_score=75.0,
            position_size=100,
            sector='Technology',
            daily_volume=1000000,
            existing_positions=[]
        )
        
        self.assertIsNotNone(decision)
        self.assertIsInstance(reason, str)
        
        # Test exit decision
        decision, reason = self.governor.run(
            signal_type='EXIT',
            symbol='AAPL',
            current_price=155.0,
            confidence_score=70.0,
            position_size=0,
            sector='Technology',
            daily_volume=1000000,
            position_pnl_pct=3.33
        )
        
        self.assertIsNotNone(decision)
        self.assertIsInstance(reason, str)

class TestIndianMarketIntegration(unittest.TestCase):
    """Test Indian market system integration."""
    
    def test_indian_market_demo_components(self):
        """Test that Indian market demo components work together."""
        try:
            # Import Indian market demo
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'examples'))
            from indian_market_demo import IndianMarketDemo
            
            # Test sample data creation
            demo = IndianMarketDemo()
            sample_data = demo.create_sample_data(days=10)
            
            # Verify data structure
            self.assertGreater(len(sample_data), 0)
            required_columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'sector']
            for col in required_columns:
                self.assertIn(col, sample_data.columns)
            
            # Test signal generator creation
            signal_generator = demo.create_indian_signal_generator()
            self.assertIsNotNone(signal_generator)
            
            # Test signal generation
            day_data = sample_data[sample_data['date'] == sample_data['date'].iloc[0]]
            signals = signal_generator(day_data, {})
            
            # Verify signals structure
            for signal in signals:
                required_keys = ['symbol', 'type', 'confidence', 'shares', 'sector']
                for key in required_keys:
                    self.assertIn(key, signal)
            
        except ImportError:
            self.skipTest("Indian market modules not available")
    
    def test_indian_market_config_integration(self):
        """Test Indian market configuration integration."""
        try:
            from indian_market_config import (
                INDIAN_MARKET_CONFIG, 
                IndianSectorMapper, 
                is_indian_trading_day
            )
            
            # Test configuration values
            self.assertIsNotNone(INDIAN_MARKET_CONFIG.market_open_time)
            self.assertIsNotNone(INDIAN_MARKET_CONFIG.currency)
            
            # Test sector mapper
            sector = IndianSectorMapper.get_sector('RELIANCE')
            self.assertIsInstance(sector, str)
            
            # Test trading day function
            is_trading = is_indian_trading_day('2024-01-15')  # Monday
            self.assertIsInstance(is_trading, bool)
            
        except ImportError:
            self.skipTest("Indian market configuration not available")

class TestSystemRobustness(unittest.TestCase):
    """Test system robustness and error handling."""
    
    def test_empty_data_handling(self):
        """Test system behavior with empty data."""
        empty_df = pd.DataFrame()
        backtester = BacktestEngine()
        
        def empty_signal_generator(day_data, existing_positions):
            return []
        
        # Should not crash with empty data
        try:
            results = backtester.run(
                price_data=empty_df,
                signal_generator=empty_signal_generator,
                governor=Governor()
            )
            # Should return empty results gracefully
            self.assertEqual(len(results['trades']), 0)
        except Exception as e:
            # If it raises an exception, it should be handled gracefully
            self.assertIsInstance(e, (ValueError, KeyError))
    
    def test_malformed_signal_handling(self):
        """Test handling of malformed signals."""
        sample_data = pd.DataFrame([{
            'date': '2024-01-01',
            'symbol': 'TEST',
            'open': 100, 'high': 102, 'low': 98, 'close': 101,
            'volume': 1000000
        }])
        
        def malformed_signal_generator(day_data, existing_positions):
            return [{'incomplete': 'signal'}]  # Missing required fields
        
        backtester = BacktestEngine()
        
        # Should handle malformed signals gracefully
        try:
            results = backtester.run(
                price_data=sample_data,
                signal_generator=malformed_signal_generator,
                governor=Governor()
            )
            # Should complete without crashing
            self.assertIsNotNone(results)
        except Exception as e:
            # Should be a handled exception type
            self.assertIsInstance(e, (KeyError, ValueError, AttributeError))

if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)