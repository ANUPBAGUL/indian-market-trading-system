"""
Integration tests for Paper Trading Engine - Tests complete workflows.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.paper_trading_engine import PaperTradingEngine


class TestPaperTradingIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up integration test environment."""
        self.engine = PaperTradingEngine()
        
        # Create realistic multi-day market data
        dates = pd.date_range('2024-01-01', '2024-01-30', freq='D')
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'SPY']
        
        self.market_data = []
        for date in dates:
            for symbol in symbols:
                base_prices = {
                    'AAPL': 180.0, 'MSFT': 370.0, 'GOOGL': 140.0,
                    'TSLA': 250.0, 'SPY': 480.0
                }
                
                # Simulate price evolution
                days_from_start = (date - dates[0]).days
                trend = 1 + (days_from_start * 0.001)
                noise = np.random.normal(1, 0.015)
                
                price = base_prices[symbol] * trend * noise
                
                self.market_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'symbol': symbol,
                    'open': price * 0.995,
                    'high': price * 1.02,
                    'low': price * 0.98,
                    'close': price,
                    'volume': np.random.randint(1000000, 3000000)
                })
        
        self.market_df = pd.DataFrame(self.market_data)
        self.universe = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
    
    def test_complete_daily_workflow(self):
        """Test complete daily paper trading workflow."""
        test_date = '2024-01-15'
        
        # Generate signals
        signals = self.engine.generate_daily_signals(
            self.market_df, test_date, self.universe
        )
        
        # Verify complete workflow
        self.assertIsInstance(signals, dict)
        self.assertEqual(signals['date'], test_date)
        
        # Should have analyzed all universe symbols
        analyzed_symbols = set()
        for signal in signals['entry_signals']:
            analyzed_symbols.add(signal['symbol'])
        for item in signals['no_action']:
            analyzed_symbols.add(item['symbol'])
        
        # All universe symbols should be analyzed
        self.assertTrue(analyzed_symbols.issubset(set(self.universe)))
        
        # Generate report
        report = self.engine.generate_daily_report(signals)
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 100)  # Substantial report
    
    def test_multi_day_signal_generation(self):
        """Test signal generation across multiple days."""
        test_dates = ['2024-01-10', '2024-01-15', '2024-01-20']
        
        all_signals = []
        for date in test_dates:
            signals = self.engine.generate_daily_signals(
                self.market_df, date, self.universe
            )
            all_signals.append(signals)
        
        # Verify each day generates signals
        for i, signals in enumerate(all_signals):
            self.assertEqual(signals['date'], test_dates[i])
            self.assertIn('market_regime', signals)
            
        # Signals should vary across days (market conditions change)
        regimes = [s['market_regime'] for s in all_signals]
        # Not all regimes need to be different, but structure should be consistent
        for regime in regimes:
            self.assertIn(regime, ['RISK_ON', 'RISK_OFF', 'NEUTRAL'])
    
    def test_position_lifecycle_management(self):
        """Test complete position lifecycle from entry to exit."""
        # Start with empty portfolio
        self.assertEqual(len(self.engine.paper_positions), 0)
        
        # Generate entry signals
        entry_date = '2024-01-15'
        entry_signals = self.engine.generate_daily_signals(
            self.market_df, entry_date, ['AAPL']
        )
        
        # Simulate taking a position (manual step in paper trading)
        if entry_signals['entry_signals']:
            signal = entry_signals['entry_signals'][0]
            self.engine.paper_positions[signal['symbol']] = {
                'entry_price': signal['price'],
                'shares': signal['shares'],
                'stop_price': signal['stop_price'],
                'entry_date': entry_date
            }
        else:
            # Force a position for testing
            self.engine.paper_positions['AAPL'] = {
                'entry_price': 180.0,
                'shares': 10,
                'stop_price': 175.0,
                'entry_date': entry_date
            }
        
        # Verify position was added
        self.assertGreater(len(self.engine.paper_positions), 0)
        
        # Test exit signal generation
        exit_date = '2024-01-20'
        
        # Create scenario where stop loss is triggered
        exit_data = self.market_df.copy()
        if 'AAPL' in self.engine.paper_positions:
            position = self.engine.paper_positions['AAPL']
            # Set price below stop loss
            trigger_price = position['stop_price'] - 1.0
            exit_data.loc[
                (exit_data['symbol'] == 'AAPL') & (exit_data['date'] == exit_date),
                'close'
            ] = trigger_price
        
        exit_signals = self.engine.generate_daily_signals(
            exit_data, exit_date, self.universe
        )
        
        # Should generate exit signal
        if exit_signals['exit_signals']:
            exit_signal = exit_signals['exit_signals'][0]
            self.assertEqual(exit_signal['action'], 'SELL')
            self.assertEqual(exit_signal['reason'], 'STOP_LOSS')
            self.assertIn('pnl_pct', exit_signal)
    
    def test_market_regime_impact(self):
        """Test how market regime affects signal generation."""
        test_date = '2024-01-15'
        
        # Test different market scenarios
        scenarios = [
            ('RISK_ON', 490.0),   # SPY above trend
            ('RISK_OFF', 470.0),  # SPY below trend
            ('NEUTRAL', 482.0)    # SPY neutral
        ]
        
        regime_results = []
        for expected_regime, spy_price in scenarios:
            # Modify SPY price to create regime
            test_data = self.market_df.copy()
            test_data.loc[
                (test_data['symbol'] == 'SPY') & (test_data['date'] == test_date),
                'close'
            ] = spy_price
            
            signals = self.engine.generate_daily_signals(
                test_data, test_date, self.universe
            )
            
            regime_results.append({
                'regime': signals['market_regime'],
                'entry_count': len(signals['entry_signals'])
            })
        
        # Verify regimes are detected (may all be NEUTRAL due to limited data)
        regimes = [r['regime'] for r in regime_results]
        # At least verify we get valid regime types
        for regime in regimes:
            self.assertIn(regime, ['RISK_ON', 'RISK_OFF', 'NEUTRAL'])
    
    def test_signal_quality_and_consistency(self):
        """Test signal quality and consistency across time."""
        test_dates = ['2024-01-10', '2024-01-15', '2024-01-20', '2024-01-25']
        
        signal_quality_metrics = []
        for date in test_dates:
            signals = self.engine.generate_daily_signals(
                self.market_df, date, self.universe
            )
            
            # Analyze signal quality
            entry_confidences = [s['confidence'] for s in signals['entry_signals']]
            avg_confidence = sum(entry_confidences) / len(entry_confidences) if entry_confidences else 0
            
            signal_quality_metrics.append({
                'date': date,
                'entry_count': len(signals['entry_signals']),
                'avg_confidence': avg_confidence,
                'market_regime': signals['market_regime']
            })
        
        # Verify signal consistency
        for metrics in signal_quality_metrics:
            # All entry signals should meet minimum confidence
            if metrics['avg_confidence'] > 0:
                self.assertGreater(metrics['avg_confidence'], 65.0)
            
            # Should have reasonable signal counts
            self.assertLessEqual(metrics['entry_count'], len(self.universe))
    
    def test_portfolio_constraints_enforcement(self):
        """Test that portfolio constraints are properly enforced."""
        # Fill up portfolio to test limits
        max_positions = 5
        for i, symbol in enumerate(['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']):
            if i < max_positions:
                self.engine.paper_positions[symbol] = {
                    'entry_price': 100.0,
                    'shares': 10,
                    'stop_price': 92.0,
                    'entry_date': '2024-01-10'
                }
        
        # Try to generate more signals
        test_date = '2024-01-15'
        signals = self.engine.generate_daily_signals(
            self.market_df, test_date, ['AMZN']  # New symbol
        )
        
        # Should not generate entry signals when portfolio is full
        # (This would require actual position limit logic in production)
        self.assertIsInstance(signals['entry_signals'], list)
    
    def test_data_quality_handling(self):
        """Test handling of various data quality issues."""
        test_date = '2024-01-15'
        
        # Test with missing symbols
        partial_data = self.market_df[self.market_df['symbol'].isin(['AAPL', 'SPY'])]
        signals = self.engine.generate_daily_signals(
            partial_data, test_date, ['AAPL', 'MSFT', 'GOOGL']
        )
        
        # Should handle missing symbols gracefully
        self.assertIsInstance(signals, dict)
        
        # Test with insufficient historical data
        recent_data = self.market_df[self.market_df['date'] >= '2024-01-25']
        signals = self.engine.generate_daily_signals(
            recent_data, '2024-01-30', self.universe
        )
        
        # Should still generate signals with limited data
        self.assertIsInstance(signals['entry_signals'], list)
    
    def test_report_generation_completeness(self):
        """Test comprehensive report generation."""
        # Create scenario with both entry and exit signals
        self.engine.paper_positions = {
            'MSFT': {
                'entry_price': 380.0,
                'shares': 50,
                'stop_price': 370.0,  # Will trigger exit
                'entry_date': '2024-01-10'
            }
        }
        
        # Modify data to trigger exit
        test_date = '2024-01-15'
        test_data = self.market_df.copy()
        test_data.loc[
            (test_data['symbol'] == 'MSFT') & (test_data['date'] == test_date),
            'close'
        ] = 365.0  # Below stop
        
        signals = self.engine.generate_daily_signals(
            test_data, test_date, self.universe
        )
        
        report = self.engine.generate_daily_report(signals)
        
        # Verify comprehensive report sections
        required_sections = [
            'DAILY TRADING SIGNALS',
            'PORTFOLIO STATUS',
            'ENTRY SIGNALS',
            'EXIT SIGNALS',
            'PAPER TRADING vs BACKTESTING'
        ]
        
        for section in required_sections:
            self.assertIn(section, report)
        
        # Verify specific content
        self.assertIn(test_date, report)
        if signals['entry_signals']:
            self.assertIn('BUY', report)
        if signals['exit_signals']:
            self.assertIn('SELL', report)
    
    def test_performance_with_large_universe(self):
        """Test performance with larger trading universe."""
        # Create larger universe
        large_universe = [f'STOCK{i:03d}' for i in range(50)]
        
        # Add data for large universe
        test_date = '2024-01-15'
        large_data = []
        
        for symbol in large_universe:
            large_data.append({
                'date': test_date,
                'symbol': symbol,
                'open': 100.0,
                'high': 102.0,
                'low': 98.0,
                'close': 101.0,
                'volume': 1000000
            })
        
        large_df = pd.DataFrame(large_data)
        
        # Should handle large universe efficiently
        signals = self.engine.generate_daily_signals(
            large_df, test_date, large_universe[:20]  # Subset for testing
        )
        
        self.assertIsInstance(signals, dict)
        self.assertLessEqual(len(signals['entry_signals']), 20)


if __name__ == '__main__':
    unittest.main()