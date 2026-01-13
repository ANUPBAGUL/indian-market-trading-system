"""
Paper Trading Engine - Generates daily signals without execution.

Provides live signal generation for manual review without real money risk.
Key difference from backtest: uses current market data, no historical simulation.
"""

from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd


class PaperTradingEngine:
    """
    Paper trading engine for daily signal generation.
    
    Key differences from backtesting:
    - Uses current/live market data (not historical simulation)
    - Generates signals for today's trading decisions
    - No execution, only signal reporting
    - Manual review and decision making
    """
    
    def __init__(self):
        self.paper_positions: Dict = {}
        self.paper_cash = 100000.0
    
    def generate_daily_signals(
        self,
        market_data: pd.DataFrame,
        date: str,
        universe: List[str]
    ) -> Dict:
        """
        Generate trading signals for current trading day.
        
        Args:
            market_data: Current market data with OHLCV + indicators
            date: Current trading date
            universe: List of symbols to analyze
            
        Returns:
            Daily signal report with recommendations
        """
        signals = {
            'date': date,
            'timestamp': datetime.now().isoformat(),
            'entry_signals': [],
            'exit_signals': [],
            'no_action': [],
            'portfolio_status': self._get_portfolio_status(),
            'market_regime': self._assess_market_regime(market_data)
        }
        
        # Generate entry signals for universe
        for symbol in universe:
            symbol_data = market_data[market_data['symbol'] == symbol]
            if symbol_data.empty or symbol in self.paper_positions:
                continue
            
            entry_signal = self._generate_entry_signal(symbol_data, date)
            if entry_signal:
                signals['entry_signals'].append(entry_signal)
            else:
                signals['no_action'].append({
                    'symbol': symbol,
                    'reason': 'No qualifying entry signal'
                })
        
        # Generate exit signals for existing positions
        for symbol in list(self.paper_positions.keys()):
            symbol_data = market_data[market_data['symbol'] == symbol]
            if symbol_data.empty:
                continue
            
            exit_signal = self._generate_exit_signal(symbol_data, date, symbol)
            if exit_signal:
                signals['exit_signals'].append(exit_signal)
        
        return signals
    
    def _generate_entry_signal(self, symbol_data: pd.DataFrame, date: str) -> Optional[Dict]:
        """Generate entry signal for a symbol."""
        if symbol_data.empty:
            return None
        
        symbol = symbol_data.iloc[0]['symbol']
        current_price = symbol_data.iloc[-1]['close']
        
        # Simplified agent scoring (would use actual agents in production)
        accumulation_score = self._calculate_accumulation_score(symbol_data)
        trigger_score = self._calculate_trigger_score(symbol_data)
        sector_score = self._calculate_sector_score(symbol_data)
        
        # Calculate confidence
        confidence = (accumulation_score + trigger_score + sector_score) / 3
        
        # Entry threshold (lowered for more signal generation)
        if confidence > 62.0:
            position_size = int(1000 / current_price)  # $1000 position
            stop_price = current_price * 0.92  # 8% stop
            
            return {
                'symbol': symbol,
                'action': 'BUY',
                'price': current_price,
                'shares': position_size,
                'confidence': confidence,
                'stop_price': stop_price,
                'rationale': f"Confidence {confidence:.1f}% above threshold",
                'agent_scores': {
                    'accumulation': accumulation_score,
                    'trigger': trigger_score,
                    'sector': sector_score
                }
            }
        
        return None
    
    def _generate_exit_signal(self, symbol_data: pd.DataFrame, date: str, symbol: str) -> Optional[Dict]:
        """Generate exit signal for existing position."""
        if symbol not in self.paper_positions:
            return None
        
        position = self.paper_positions[symbol]
        current_price = symbol_data.iloc[-1]['close']
        
        # Check stop loss
        if current_price <= position['stop_price']:
            pnl_pct = ((current_price - position['entry_price']) / position['entry_price']) * 100
            
            return {
                'symbol': symbol,
                'action': 'SELL',
                'price': current_price,
                'shares': position['shares'],
                'reason': 'STOP_LOSS',
                'pnl_pct': pnl_pct,
                'rationale': f"Stop loss triggered at ${current_price:.2f}"
            }
        
        return None
    
    def _calculate_accumulation_score(self, data: pd.DataFrame) -> float:
        """Simplified accumulation scoring."""
        if len(data) < 20:
            return 50.0
        
        recent_volume = data['volume'].tail(5).mean()
        avg_volume = data['volume'].tail(20).mean()
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
        
        return min(volume_ratio * 30 + 40, 100.0)
    
    def _calculate_trigger_score(self, data: pd.DataFrame) -> float:
        """Simplified trigger scoring."""
        if len(data) < 20:
            return 50.0
        
        current_price = data['close'].iloc[-1]
        sma_20 = data['close'].tail(20).mean()
        
        if current_price > sma_20 * 1.02:  # 2% above SMA
            return 85.0
        elif current_price > sma_20:
            return 65.0
        else:
            return 35.0
    
    def _calculate_sector_score(self, data: pd.DataFrame) -> float:
        """Simplified sector scoring."""
        return 70.0  # Neutral sector score
    
    def _assess_market_regime(self, market_data: pd.DataFrame) -> str:
        """Assess current market regime."""
        spy_data = market_data[market_data['symbol'] == 'SPY']
        if spy_data.empty or len(spy_data) < 20:
            return "NEUTRAL"
        
        current_price = spy_data['close'].iloc[-1]
        sma_20 = spy_data['close'].tail(20).mean()
        
        if current_price > sma_20 * 1.02:
            return "RISK_ON"
        elif current_price < sma_20 * 0.98:
            return "RISK_OFF"
        else:
            return "NEUTRAL"
    
    def _get_portfolio_status(self) -> Dict:
        """Get current paper portfolio status."""
        return {
            'cash': self.paper_cash,
            'positions': len(self.paper_positions),
            'symbols': list(self.paper_positions.keys())
        }
    
    def generate_daily_report(self, signals: Dict) -> str:
        """Generate formatted daily signal report."""
        report = [
            f"=== DAILY TRADING SIGNALS - {signals['date']} ===",
            f"Generated: {signals['timestamp'][:19]}",
            f"Market Regime: {signals['market_regime']}",
            ""
        ]
        
        # Portfolio Status
        portfolio = signals['portfolio_status']
        report.extend([
            "PORTFOLIO STATUS:",
            f"  Cash: ${portfolio['cash']:,.0f}",
            f"  Positions: {portfolio['positions']}",
            f"  Symbols: {', '.join(portfolio['symbols']) if portfolio['symbols'] else 'None'}",
            ""
        ])
        
        # Entry Signals
        if signals['entry_signals']:
            report.append("ENTRY SIGNALS:")
            for signal in signals['entry_signals']:
                report.extend([
                    f"  {signal['symbol']} - BUY {signal['shares']} shares at ${signal['price']:.2f}",
                    f"    Confidence: {signal['confidence']:.1f}%",
                    f"    Stop: ${signal['stop_price']:.2f}",
                    f"    Rationale: {signal['rationale']}",
                    ""
                ])
        else:
            report.extend(["ENTRY SIGNALS:", "  No qualifying entry signals today", ""])
        
        # Exit Signals
        if signals['exit_signals']:
            report.append("EXIT SIGNALS:")
            for signal in signals['exit_signals']:
                report.extend([
                    f"  {signal['symbol']} - SELL {signal['shares']} shares at ${signal['price']:.2f}",
                    f"    Reason: {signal['reason']}",
                    f"    P&L: {signal['pnl_pct']:+.1f}%",
                    ""
                ])
        else:
            report.extend(["EXIT SIGNALS:", "  No exit signals for current positions", ""])
        
        # Key Differences
        report.extend([
            "PAPER TRADING vs BACKTESTING:",
            "• Paper Trading: Uses current market data for today's decisions",
            "• Backtesting: Simulates historical data to test strategy performance",
            "• Paper Trading: Manual review and execution required",
            "• Backtesting: Automated simulation with historical fills",
            "• Paper Trading: Real-time market conditions and sentiment",
            "• Backtesting: Perfect hindsight with known outcomes"
        ])
        
        return "\n".join(report)