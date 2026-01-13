"""
Realistic Daily Backtester - Simulates trading with proper fill assumptions.

The backtester processes daily data sequentially, executes trades at next-open,
and maintains a complete trade log without lookahead bias.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd


@dataclass
class Trade:
    """Individual trade record."""
    symbol: str
    entry_date: str
    entry_price: float
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    shares: int = 0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    exit_reason: str = ""


@dataclass
class Position:
    """Active position record."""
    symbol: str
    entry_date: str
    entry_price: float
    shares: int
    stop_price: float
    current_value: float = 0.0


class BacktestEngine:
    """
    Realistic daily backtester with four key components:
    1. Daily loop (sequential processing without lookahead)
    2. Next-open fills (realistic execution timing)
    3. Stop execution logic (intraday stop monitoring)
    4. Trade log (complete audit trail)
    """
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        self.signal_log: List[Dict] = []  # Track all signals for quality analysis
        self.current_date = ""
    
    def run(
        self,
        price_data: pd.DataFrame,
        signal_generator,
        governor
    ) -> Dict:
        """
        Run backtest with daily loop processing.
        
        Args:
            price_data: DataFrame with columns: date, symbol, open, high, low, close, volume
            signal_generator: Function that generates trading signals
            governor: Governor agent for decision validation
            
        Returns:
            Dict with trades, equity_curve, and performance metrics
            
        Example:
            results = backtester.run(
                price_data=daily_prices,
                signal_generator=my_signal_func,
                governor=Governor
            )
        """
        # Group data by date for daily processing
        daily_data = price_data.groupby('date')
        dates = sorted(price_data['date'].unique())
        
        print(f"Starting backtest: {dates[0]} to {dates[-1]}")
        print(f"Initial capital: ${self.initial_capital:,.0f}")
        
        for i, date in enumerate(dates):
            self.current_date = date
            day_data = daily_data.get_group(date)
            
            # Step 1: Check stops on existing positions (using intraday data)
            self._process_stops(day_data)
            
            # Step 2: Generate signals using yesterday's close data
            if i > 0:  # Need previous day for signal generation
                prev_date = dates[i-1]
                prev_data = daily_data.get_group(prev_date)
                signals = signal_generator(prev_data, self.positions)
                
                # Step 3: Process signals through Governor
                for signal in signals:
                    self._process_signal(signal, day_data, governor)
            
            # Step 4: Update position values and equity curve
            self._update_equity_curve(day_data)
            
            if i % 50 == 0:  # Progress update
                total_value = self._calculate_total_value(day_data)
                print(f"Date: {date}, Portfolio Value: ${total_value:,.0f}")
        
        return self._generate_results()
    
    def _process_stops(self, day_data: pd.DataFrame):
        """Process stop orders using intraday price action."""
        positions_to_close = []
        
        for symbol, position in self.positions.items():
            stock_data = day_data[day_data['symbol'] == symbol]
            if stock_data.empty:
                continue
            
            row = stock_data.iloc[0]
            
            # Check if stop was hit during the day
            if row['low'] <= position.stop_price:
                # Stop triggered - close position at stop price
                exit_price = position.stop_price
                pnl = (exit_price - position.entry_price) * position.shares
                pnl_pct = ((exit_price - position.entry_price) / position.entry_price) * 100
                
                # Create trade record
                trade = Trade(
                    symbol=symbol,
                    entry_date=position.entry_date,
                    entry_price=position.entry_price,
                    exit_date=self.current_date,
                    exit_price=exit_price,
                    shares=position.shares,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    exit_reason="STOP"
                )
                
                self.trades.append(trade)
                self.cash += exit_price * position.shares
                positions_to_close.append(symbol)
        
        # Remove closed positions
        for symbol in positions_to_close:
            del self.positions[symbol]
    
    def _process_signal(self, signal: Dict, day_data: pd.DataFrame, governor):
        """Process trading signal through Governor and execute if approved."""
        symbol = signal['symbol']
        signal_type = signal['type']  # 'ENTRY' or 'EXIT'
        
        # Log signal for quality analysis
        signal_record = {
            'date': self.current_date,
            'symbol': symbol,
            'type': signal_type,
            'confidence': signal.get('confidence', 70.0),
            'executed': False,
            'rejection_reason': None
        }
        
        if signal_type == 'ENTRY':
            executed, reason = self._process_entry_signal(signal, day_data, governor)
            signal_record['executed'] = executed
            signal_record['rejection_reason'] = reason if not executed else None
        elif signal_type == 'EXIT':
            executed, reason = self._process_exit_signal(signal, day_data, governor)
            signal_record['executed'] = executed
            signal_record['rejection_reason'] = reason if not executed else None
        
        self.signal_log.append(signal_record)
    
    def _process_entry_signal(self, signal: Dict, day_data: pd.DataFrame, governor) -> Tuple[bool, Optional[str]]:
        """Process entry signal with next-open execution."""
        symbol = signal['symbol']
        
        # Skip if already have position
        if symbol in self.positions:
            return False, "Already have position"
        
        # Get stock data for execution
        stock_data = day_data[day_data['symbol'] == symbol]
        if stock_data.empty:
            return False, "No price data"
        
        row = stock_data.iloc[0]
        
        # Governor decision
        decision, reason = governor.run(
            signal_type='ENTRY',
            symbol=symbol,
            current_price=row['open'],  # Use open price for decision
            confidence_score=signal.get('confidence', 70.0),
            position_size=signal.get('shares', 100),
            sector=signal.get('sector', 'Unknown'),
            daily_volume=row['volume'],
            existing_positions=[{'symbol': s, 'sector': 'Unknown'} for s in self.positions.keys()]
        )
        
        if decision.value != 'ENTER':
            return False, f"Governor rejected: {reason}"
        
        # Execute at next open (today's open represents next-day execution)
        entry_price = row['open']
        shares = signal.get('shares', 100)
        cost = entry_price * shares
        
        # Check if we have enough cash
        if cost > self.cash:
            return False, "Insufficient cash"
        
        # Create position
        position = Position(
            symbol=symbol,
            entry_date=self.current_date,
            entry_price=entry_price,
            shares=shares,
            stop_price=signal.get('stop_price', entry_price * 0.92)  # Default 8% stop
        )
        
        self.positions[symbol] = position
        self.cash -= cost
        return True, None
    
    def _process_exit_signal(self, signal: Dict, day_data: pd.DataFrame, governor) -> Tuple[bool, Optional[str]]:
        """Process exit signal with next-open execution."""
        symbol = signal['symbol']
        
        # Skip if no position
        if symbol not in self.positions:
            return False, "No position to exit"
        
        position = self.positions[symbol]
        stock_data = day_data[day_data['symbol'] == symbol]
        if stock_data.empty:
            return False, "No price data"
        
        row = stock_data.iloc[0]
        
        # Calculate current P&L for Governor
        current_pnl_pct = ((row['open'] - position.entry_price) / position.entry_price) * 100
        
        # Governor decision
        decision, reason = governor.run(
            signal_type='EXIT',
            symbol=symbol,
            current_price=row['open'],
            confidence_score=70.0,  # Not used for exits
            position_size=0,
            sector='Unknown',
            daily_volume=row['volume'],
            position_pnl_pct=current_pnl_pct,
            decayed_confidence=signal.get('decayed_confidence', 50.0)
        )
        
        if decision.value != 'EXIT':
            return False, f"Governor rejected: {reason}"
        
        # Execute exit at open price
        exit_price = row['open']
        pnl = (exit_price - position.entry_price) * position.shares
        pnl_pct = ((exit_price - position.entry_price) / position.entry_price) * 100
        
        # Create trade record
        trade = Trade(
            symbol=symbol,
            entry_date=position.entry_date,
            entry_price=position.entry_price,
            exit_date=self.current_date,
            exit_price=exit_price,
            shares=position.shares,
            pnl=pnl,
            pnl_pct=pnl_pct,
            exit_reason="SIGNAL"
        )
        
        self.trades.append(trade)
        self.cash += exit_price * position.shares
        del self.positions[symbol]
        return True, None
    
    def _update_equity_curve(self, day_data: pd.DataFrame):
        """Update equity curve with current portfolio value."""
        total_value = self._calculate_total_value(day_data)
        
        equity_point = {
            'date': self.current_date,
            'cash': self.cash,
            'positions_value': total_value - self.cash,
            'total_value': total_value,
            'num_positions': len(self.positions)
        }
        
        self.equity_curve.append(equity_point)
    
    def _calculate_total_value(self, day_data: pd.DataFrame) -> float:
        """Calculate total portfolio value using current prices."""
        total_value = self.cash
        
        for symbol, position in self.positions.items():
            stock_data = day_data[day_data['symbol'] == symbol]
            if not stock_data.empty:
                current_price = stock_data.iloc[0]['close']
                position_value = current_price * position.shares
                total_value += position_value
        
        return total_value
    
    def _generate_results(self) -> Dict:
        """Generate final backtest results."""
        if not self.equity_curve:
            return {'trades': [], 'equity_curve': [], 'metrics': {}}
        
        final_value = self.equity_curve[-1]['total_value']
        total_return = ((final_value - self.initial_capital) / self.initial_capital) * 100
        
        # Calculate basic metrics
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]
        
        metrics = {
            'total_return_pct': round(total_return, 2),
            'final_value': round(final_value, 2),
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate_pct': round(len(winning_trades) / max(len(self.trades), 1) * 100, 1),
            'avg_win': round(sum(t.pnl for t in winning_trades) / max(len(winning_trades), 1), 2),
            'avg_loss': round(sum(t.pnl for t in losing_trades) / max(len(losing_trades), 1), 2),
        }
        
        return {
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'signal_log': self.signal_log,
            'metrics': metrics
        }