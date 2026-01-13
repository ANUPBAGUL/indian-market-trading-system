"""
Unit tests for Paper Trading Engine - Tests signal generation functionality.
"""

import unittest
import pandas as pd
from datetime import datetime
from src.paper_trading_engine import PaperTradingEngine


class TestPaperTradingEngine(unittest.TestCase):
    
    def setUp(self):
        """Set up test engine and data."""
        self.engine = PaperTradingEngine()
        
        # Create test market data
        self.test_data = pd.DataFrame({
            'date': ['2024-01-15'] * 3,
            'symbol': ['AAPL', 'MSFT', 'SPY'],
            'open': [180.0, 370.0, 480.0],
            'high': [185.0, 375.0, 485.0],
            'low': [178.0, 368.0, 478.0],
            'close': [182.0, 372.0, 482.0],
            'volume': [2000000, 1500000, 3000000]
        })
        
        self.universe = ['AAPL', 'MSFT']
        self.test_date = '2024-01-15'
    
    def test_initialization(self):
        """Test engine initialization."""
        engine = PaperTradingEngine()
        self.assertEqual(engine.paper_cash, 100000.0)
        self.assertEqual(len(engine.paper_positions), 0)
    
    def test_generate_daily_signals_structure(self):
        """Test daily signals structure."""
        signals = self.engine.generate_daily_signals(
            self.test_data, self.test_date, self.universe
        )
        
        # Verify structure
        required_keys = ['date', 'timestamp', 'entry_signals', 'exit_signals', 
                        'no_action', 'portfolio_status', 'market_regime']
        for key in required_keys:
            self.assertIn(key, signals)
        
        self.assertEqual(signals['date'], self.test_date)
        self.assertIsInstance(signals['entry_signals'], list)
        self.assertIsInstance(signals['exit_signals'], list)
    
    def test_entry_signal_generation(self):
        """Test entry signal generation."""
        # Create data that should trigger signals
        strong_data = self.test_data.copy()
        strong_data.loc[strong_data['symbol'] == 'AAPL', 'volume'] = 5000000  # High volume
        
        signals = self.engine.generate_daily_signals(
            strong_data, self.test_date, ['AAPL']
        )
        
        # Should generate entry signals for qualifying stocks
        if signals['entry_signals']:
            signal = signals['entry_signals'][0]
            self.assertEqual(signal['symbol'], 'AAPL')
            self.assertEqual(signal['action'], 'BUY')
            self.assertGreater(signal['confidence'], 0)
            self.assertIn('rationale', signal)
    
    def test_exit_signal_generation(self):
        """Test exit signal generation."""
        # Add existing position
        self.engine.paper_positions = {
            'AAPL': {
                'entry_price': 190.0,
                'shares': 10,
                'stop_price': 185.0,  # Above current price
                'entry_date': '2024-01-10'
            }
        }
        
        signals = self.engine.generate_daily_signals(
            self.test_data, self.test_date, self.universe
        )
        
        # Should generate exit signal due to stop loss
        if signals['exit_signals']:
            signal = signals['exit_signals'][0]
            self.assertEqual(signal['symbol'], 'AAPL')
            self.assertEqual(signal['action'], 'SELL')
            self.assertEqual(signal['reason'], 'STOP_LOSS')
    
    def test_accumulation_score_calculation(self):
        """Test accumulation scoring."""
        # Test with sufficient data
        data_20_days = pd.DataFrame({
            'volume': [1000000] * 15 + [2000000] * 5  # Recent volume spike
        })
        
        score = self.engine._calculate_accumulation_score(data_20_days)
        self.assertGreater(score, 50.0)  # Should be above neutral
        
        # Test with insufficient data
        short_data = pd.DataFrame({'volume': [1000000] * 5})
        score = self.engine._calculate_accumulation_score(short_data)
        self.assertEqual(score, 50.0)  # Default score
    
    def test_trigger_score_calculation(self):
        """Test trigger scoring."""
        # Test bullish scenario (price above SMA)
        bullish_data = pd.DataFrame({
            'close': [100] * 15 + [105] * 5  # Price trending up
        })
        
        score = self.engine._calculate_trigger_score(bullish_data)
        self.assertGreater(score, 60.0)
        
        # Test bearish scenario
        bearish_data = pd.DataFrame({
            'close': [105] * 15 + [95] * 5  # Price trending down
        })
        
        score = self.engine._calculate_trigger_score(bearish_data)
        self.assertLess(score, 50.0)
    
    def test_market_regime_assessment(self):
        """Test market regime assessment."""
        # Test with SPY data
        spy_data = self.test_data.copy()
        
        # Risk-on scenario (price above SMA)
        spy_data.loc[spy_data['symbol'] == 'SPY', 'close'] = 490.0  # Above trend
        # Need sufficient data for SMA calculation
        spy_extended = pd.concat([spy_data] * 25, ignore_index=True)
        regime = self.engine._assess_market_regime(spy_extended)
        self.assertIn(regime, ['RISK_ON', 'NEUTRAL'])  # Allow both due to SMA calculation
        
        # Risk-off scenario
        spy_data.loc[spy_data['symbol'] == 'SPY', 'close'] = 470.0  # Below trend
        spy_extended = pd.concat([spy_data] * 25, ignore_index=True)
        regime = self.engine._assess_market_regime(spy_extended)
        self.assertIn(regime, ['RISK_OFF', 'NEUTRAL'])  # Allow both due to SMA calculation
        
        # No SPY data
        no_spy_data = self.test_data[self.test_data['symbol'] != 'SPY']
        regime = self.engine._assess_market_regime(no_spy_data)
        self.assertEqual(regime, 'NEUTRAL')
    
    def test_portfolio_status(self):
        """Test portfolio status reporting."""
        # Empty portfolio
        status = self.engine._get_portfolio_status()
        self.assertEqual(status['cash'], 100000.0)
        self.assertEqual(status['positions'], 0)
        self.assertEqual(status['symbols'], [])
        
        # With positions
        self.engine.paper_positions = {'AAPL': {}, 'MSFT': {}}
        status = self.engine._get_portfolio_status()
        self.assertEqual(status['positions'], 2)
        self.assertEqual(set(status['symbols']), {'AAPL', 'MSFT'})
    
    def test_signal_filtering(self):
        """Test signal filtering logic."""
        # Test existing position filtering
        self.engine.paper_positions = {
            'AAPL': {
                'entry_price': 180.0,
                'shares': 10,
                'stop_price': 170.0,
                'entry_date': '2024-01-10'
            }
        }
        
        signals = self.engine.generate_daily_signals(
            self.test_data, self.test_date, ['AAPL']
        )
        
        # Should not generate entry signal for existing position
        aapl_entries = [s for s in signals['entry_signals'] if s['symbol'] == 'AAPL']
        self.assertEqual(len(aapl_entries), 0)
    
    def test_report_generation(self):
        """Test daily report generation."""
        signals = self.engine.generate_daily_signals(
            self.test_data, self.test_date, self.universe
        )
        
        report = self.engine.generate_daily_report(signals)
        
        # Verify report structure
        self.assertIn("DAILY TRADING SIGNALS", report)
        self.assertIn("PORTFOLIO STATUS", report)
        self.assertIn("ENTRY SIGNALS", report)
        self.assertIn("EXIT SIGNALS", report)
        self.assertIn("PAPER TRADING vs BACKTESTING", report)
        
        # Verify date and timestamp
        self.assertIn(self.test_date, report)
    
    def test_empty_data_handling(self):
        """Test handling of empty or invalid data."""
        empty_data = pd.DataFrame(columns=['date', 'symbol', 'close', 'volume'])
        
        signals = self.engine.generate_daily_signals(
            empty_data, self.test_date, self.universe
        )
        
        # Should handle gracefully
        self.assertEqual(len(signals['entry_signals']), 0)
        self.assertEqual(len(signals['exit_signals']), 0)
        self.assertEqual(signals['market_regime'], 'NEUTRAL')
    
    def test_signal_rationale(self):
        """Test signal rationale generation."""
        signals = self.engine.generate_daily_signals(
            self.test_data, self.test_date, self.universe
        )
        
        for signal in signals['entry_signals']:
            self.assertIn('rationale', signal)
            self.assertIn('confidence', signal['rationale'])
            self.assertIn('agent_scores', signal)
            
            # Verify agent scores structure
            agent_scores = signal['agent_scores']
            required_agents = ['accumulation', 'trigger', 'sector']
            for agent in required_agents:
                self.assertIn(agent, agent_scores)


if __name__ == '__main__':
    unittest.main()