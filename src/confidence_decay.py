"""
Confidence Decay System - Systematically reduces position confidence over time.

The system prevents hope-based holding by applying objective decay factors
that force disciplined position management and capital recycling.
"""

from typing import Dict, Optional
import pandas as pd


class ConfidenceDecay:
    """
    Confidence decay system with four key mechanisms:
    1. Time-based decay (aging positions lose conviction)
    2. Price stagnation decay (sideways movement reduces confidence)
    3. Sector weakness decay (sector underperformance impacts confidence)
    4. Forced exit condition (minimum confidence threshold)
    """
    
    # Decay parameters
    TIME_DECAY_RATE = 0.5      # 0.5% per day after day 10
    STAGNATION_THRESHOLD = 0.02 # 2% price movement threshold
    STAGNATION_DECAY = 2.0     # 2% decay for stagnant positions
    SECTOR_DECAY_RATE = 1.5    # 1.5% decay when sector underperforms
    MIN_CONFIDENCE = 45.0      # Force exit below 45% confidence
    
    # Time thresholds
    GRACE_PERIOD_DAYS = 10     # No time decay for first 10 days
    STAGNATION_PERIOD = 5      # Check stagnation over 5 days
    
    @staticmethod
    def decay_confidence(
        initial_confidence: float,
        position_age_days: int,
        entry_price: float,
        current_price: float,
        price_5_days_ago: float,
        sector_performance_5d: float,
        market_performance_5d: float
    ) -> Dict[str, float]:
        """
        Apply confidence decay based on multiple factors.
        
        Args:
            initial_confidence: Original confidence score (0-100)
            position_age_days: Days since position entry
            entry_price: Original entry price
            current_price: Current stock price
            price_5_days_ago: Price 5 days ago for stagnation check
            sector_performance_5d: Sector 5-day performance (%)
            market_performance_5d: Market 5-day performance (%)
            
        Returns:
            Dict with decayed_confidence, decay_factors, force_exit
            
        Example:
            decay_info = ConfidenceDecay.decay_confidence(
                initial_confidence=75.0,
                position_age_days=15,
                entry_price=50.0,
                current_price=51.0,
                price_5_days_ago=50.8,
                sector_performance_5d=-1.2,
                market_performance_5d=0.8
            )
            # Returns: {'decayed_confidence': 68.5, 'force_exit': False, ...}
        """
        decay_factors = {}
        total_decay = 0.0
        
        # 1. Time-based decay
        time_decay = ConfidenceDecay._calculate_time_decay(position_age_days)
        if time_decay > 0:
            decay_factors['time_decay'] = time_decay
            total_decay += time_decay
        
        # 2. Price stagnation decay
        stagnation_decay = ConfidenceDecay._calculate_stagnation_decay(
            current_price, price_5_days_ago
        )
        if stagnation_decay > 0:
            decay_factors['stagnation_decay'] = stagnation_decay
            total_decay += stagnation_decay
        
        # 3. Sector weakness decay
        sector_decay = ConfidenceDecay._calculate_sector_decay(
            sector_performance_5d, market_performance_5d
        )
        if sector_decay > 0:
            decay_factors['sector_decay'] = sector_decay
            total_decay += sector_decay
        
        # Apply total decay
        decayed_confidence = max(0.0, initial_confidence - total_decay)
        
        # 4. Forced exit condition
        force_exit = decayed_confidence < ConfidenceDecay.MIN_CONFIDENCE
        
        return {
            'decayed_confidence': round(decayed_confidence, 1),
            'total_decay': round(total_decay, 1),
            'decay_factors': decay_factors,
            'force_exit': force_exit,
            'current_pnl_pct': round(((current_price - entry_price) / entry_price) * 100, 1)
        }
    
    @staticmethod
    def _calculate_time_decay(position_age_days: int) -> float:
        """Calculate time-based confidence decay."""
        if position_age_days <= ConfidenceDecay.GRACE_PERIOD_DAYS:
            return 0.0
        
        # Linear decay after grace period
        excess_days = position_age_days - ConfidenceDecay.GRACE_PERIOD_DAYS
        return excess_days * ConfidenceDecay.TIME_DECAY_RATE
    
    @staticmethod
    def _calculate_stagnation_decay(current_price: float, price_5_days_ago: float) -> float:
        """Calculate price stagnation decay."""
        if price_5_days_ago == 0:
            return 0.0
        
        price_change_pct = abs((current_price - price_5_days_ago) / price_5_days_ago)
        
        # Apply decay if price movement is below threshold
        if price_change_pct < ConfidenceDecay.STAGNATION_THRESHOLD:
            return ConfidenceDecay.STAGNATION_DECAY
        
        return 0.0
    
    @staticmethod
    def _calculate_sector_decay(sector_perf: float, market_perf: float) -> float:
        """Calculate sector weakness decay."""
        # Apply decay if sector underperforms market by significant margin
        relative_performance = sector_perf - market_perf
        
        if relative_performance < -1.0:  # Sector underperforms by >1%
            return ConfidenceDecay.SECTOR_DECAY_RATE
        
        return 0.0
    
    @staticmethod
    def batch_decay(df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply confidence decay to multiple positions.
        
        Args:
            df: DataFrame with columns: initial_confidence, position_age_days,
                entry_price, current_price, price_5_days_ago, 
                sector_performance_5d, market_performance_5d
                
        Returns:
            DataFrame with added decay columns
        """
        results = []
        
        for _, row in df.iterrows():
            decay_info = ConfidenceDecay.decay_confidence(
                initial_confidence=row['initial_confidence'],
                position_age_days=row['position_age_days'],
                entry_price=row['entry_price'],
                current_price=row['current_price'],
                price_5_days_ago=row['price_5_days_ago'],
                sector_performance_5d=row['sector_performance_5d'],
                market_performance_5d=row['market_performance_5d']
            )
            
            results.append(decay_info)
        
        result_df = pd.DataFrame(results)
        return pd.concat([df, result_df], axis=1)
    
    @staticmethod
    def should_force_exit(decayed_confidence: float) -> bool:
        """Check if position should be force exited due to low confidence."""
        return decayed_confidence < ConfidenceDecay.MIN_CONFIDENCE