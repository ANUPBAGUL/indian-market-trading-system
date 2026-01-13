"""
Governor Agent - Final decision authority with veto power over all trading decisions.

The Governor serves as the single point of authority that can override any
trading decision based on risk management rules and system integrity checks.
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
import pandas as pd


class Decision(Enum):
    """Trading decisions that the Governor can make."""
    ENTER = "ENTER"
    NO_TRADE = "NO_TRADE"
    EXIT = "EXIT"


class Governor:
    """
    Governor Agent with three key responsibilities:
    1. Decision rules (ENTER / NO_TRADE / EXIT)
    2. Veto enforcement (hard limits and sanity checks)
    3. Decision reason logging (audit trail)
    """
    
    # Risk management limits
    MAX_POSITION_SIZE = 10000      # Maximum shares per position
    MIN_CONFIDENCE = 62.0          # Minimum confidence to enter
    MAX_CORRELATION = 0.7          # Maximum position correlation
    MAX_SECTOR_EXPOSURE = 0.25     # Maximum 25% in any sector
    MIN_LIQUIDITY = 100000         # Minimum daily volume
    
    # Price validation limits
    MAX_PRICE_CHANGE = 0.15        # 15% max price change from signal
    MIN_PRICE = 5.0                # Minimum stock price
    MAX_PRICE = 1000.0             # Maximum stock price
    
    # Exit conditions
    FORCE_EXIT_CONFIDENCE = 45.0   # Force exit below this confidence
    MAX_DRAWDOWN = 0.08            # 8% max drawdown from peak
    
    @staticmethod
    def run(
        signal_type: str,
        symbol: str,
        current_price: float,
        confidence_score: float,
        position_size: int,
        sector: str,
        daily_volume: int,
        existing_positions: Optional[List[Dict]] = None,
        position_pnl_pct: Optional[float] = None,
        decayed_confidence: Optional[float] = None
    ) -> Tuple[Decision, str]:
        """
        Make final trading decision with veto power.
        
        Args:
            signal_type: 'ENTRY' or 'EXIT' signal from agents
            symbol: Stock symbol
            current_price: Current stock price
            confidence_score: Agent confidence (0-100)
            position_size: Proposed position size
            sector: Stock sector
            daily_volume: Average daily volume
            existing_positions: List of current positions
            position_pnl_pct: Current position P&L percentage
            decayed_confidence: Confidence after decay (for exits)
            
        Returns:
            Tuple of (Decision, reason_string)
            
        Example:
            decision, reason = Governor.run(
                signal_type='ENTRY',
                symbol='AAPL',
                current_price=150.0,
                confidence_score=75.0,
                position_size=500,
                sector='Technology',
                daily_volume=50000000
            )
            # Returns: (Decision.ENTER, "Entry approved: All checks passed")
        """
        reasons = []
        
        # Step 1: Basic validation checks (skip size check for exits)
        validation_result = Governor._validate_inputs(
            current_price, confidence_score, position_size, daily_volume, signal_type
        )
        if validation_result:
            return Decision.NO_TRADE, f"Input validation failed: {validation_result}"
        
        # Step 2: Process based on signal type
        if signal_type == 'ENTRY':
            return Governor._process_entry_signal(
                symbol, current_price, confidence_score, position_size, 
                sector, existing_positions, reasons
            )
        elif signal_type == 'EXIT':
            return Governor._process_exit_signal(
                symbol, position_pnl_pct, decayed_confidence, reasons
            )
        else:
            return Decision.NO_TRADE, f"Unknown signal type: {signal_type}"
    
    @staticmethod
    def _validate_inputs(
        price: float, 
        confidence: float, 
        size: int, 
        volume: int,
        signal_type: str = 'ENTRY'
    ) -> Optional[str]:
        """Validate basic input parameters."""
        if not (Governor.MIN_PRICE <= price <= Governor.MAX_PRICE):
            return f"Price ${price:.2f} outside valid range"
        
        if not (0 <= confidence <= 100):
            return f"Confidence {confidence:.1f}% outside valid range"
        
        if size <= 0 and signal_type == 'ENTRY':
            return f"Invalid position size: {size}"
        
        if volume < Governor.MIN_LIQUIDITY:
            return f"Insufficient liquidity: {volume:,} shares"
        
        return None
    
    @staticmethod
    def _process_entry_signal(
        symbol: str,
        price: float,
        confidence: float,
        size: int,
        sector: str,
        existing_positions: Optional[List[Dict]],
        reasons: List[str]
    ) -> Tuple[Decision, str]:
        """Process entry signal with risk checks."""
        
        # Check minimum confidence
        if confidence < Governor.MIN_CONFIDENCE:
            return Decision.NO_TRADE, f"Confidence {confidence:.1f}% below minimum {Governor.MIN_CONFIDENCE}%"
        
        # Check position size limits
        if size > Governor.MAX_POSITION_SIZE:
            return Decision.NO_TRADE, f"Position size {size} exceeds maximum {Governor.MAX_POSITION_SIZE}"
        
        # Check sector exposure if existing positions provided
        if existing_positions:
            sector_check = Governor._check_sector_exposure(sector, existing_positions)
            if sector_check:
                return Decision.NO_TRADE, f"Sector exposure violation: {sector_check}"
        
        # All checks passed
        reasons.append("All risk checks passed")
        reasons.append(f"Confidence: {confidence:.1f}%")
        reasons.append(f"Position size: {size} shares")
        
        return Decision.ENTER, f"Entry approved: {', '.join(reasons)}"
    
    @staticmethod
    def _process_exit_signal(
        symbol: str,
        pnl_pct: Optional[float],
        decayed_confidence: Optional[float],
        reasons: List[str]
    ) -> Tuple[Decision, str]:
        """Process exit signal with exit conditions."""
        
        # Force exit on low decayed confidence
        if decayed_confidence is not None and decayed_confidence < Governor.FORCE_EXIT_CONFIDENCE:
            return Decision.EXIT, f"Force exit: Confidence decayed to {decayed_confidence:.1f}%"
        
        # Force exit on excessive drawdown
        if pnl_pct is not None and pnl_pct < -Governor.MAX_DRAWDOWN * 100:
            return Decision.EXIT, f"Force exit: Drawdown {pnl_pct:.1f}% exceeds limit"
        
        # Standard exit conditions met
        reasons.append("Exit conditions satisfied")
        if pnl_pct is not None:
            reasons.append(f"P&L: {pnl_pct:.1f}%")
        if decayed_confidence is not None:
            reasons.append(f"Decayed confidence: {decayed_confidence:.1f}%")
        
        return Decision.EXIT, f"Exit approved: {', '.join(reasons)}"
    
    @staticmethod
    def _check_sector_exposure(sector: str, existing_positions: List[Dict]) -> Optional[str]:
        """Check if adding position would violate sector exposure limits."""
        if not existing_positions:
            return None
        
        # Count existing sector exposure
        sector_positions = [pos for pos in existing_positions if pos.get('sector') == sector]
        sector_count = len(sector_positions)
        total_positions = len(existing_positions)
        
        if total_positions == 0:
            return None
        
        # Calculate exposure after adding new position
        new_sector_exposure = (sector_count + 1) / (total_positions + 1)
        
        if new_sector_exposure > Governor.MAX_SECTOR_EXPOSURE:
            return f"{sector} exposure would be {new_sector_exposure:.1%} (max {Governor.MAX_SECTOR_EXPOSURE:.1%})"
        
        return None
    
    @staticmethod
    def batch_decisions(df: pd.DataFrame) -> pd.DataFrame:
        """
        Process multiple trading decisions in batch.
        
        Args:
            df: DataFrame with columns: signal_type, symbol, current_price,
                confidence_score, position_size, sector, daily_volume,
                position_pnl_pct (optional), decayed_confidence (optional)
                
        Returns:
            DataFrame with added decision and reason columns
        """
        results = []
        
        # Get existing positions for sector exposure checks
        existing_positions = []
        
        for _, row in df.iterrows():
            decision, reason = Governor.run(
                signal_type=row['signal_type'],
                symbol=row['symbol'],
                current_price=row['current_price'],
                confidence_score=row['confidence_score'],
                position_size=row['position_size'],
                sector=row['sector'],
                daily_volume=row['daily_volume'],
                existing_positions=existing_positions,
                position_pnl_pct=row.get('position_pnl_pct'),
                decayed_confidence=row.get('decayed_confidence')
            )
            
            results.append({
                'decision': decision.value,
                'reason': reason
            })
            
            # Update existing positions for next iteration
            if decision == Decision.ENTER:
                existing_positions.append({
                    'symbol': row['symbol'],
                    'sector': row['sector']
                })
        
        result_df = pd.DataFrame(results)
        return pd.concat([df, result_df], axis=1)
    
    @staticmethod
    def get_decision_summary(decisions: List[Tuple[Decision, str]]) -> Dict[str, int]:
        """Get summary statistics of decisions made."""
        summary = {
            'ENTER': 0,
            'NO_TRADE': 0,
            'EXIT': 0
        }
        
        for decision, _ in decisions:
            summary[decision.value] += 1
        
        return summary