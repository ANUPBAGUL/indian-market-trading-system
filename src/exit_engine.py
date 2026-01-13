"""
Exit Engine - ATR-based stop management with dynamic k-factor selection.

The engine manages position exits using volatility-adaptive stops that trail
price movements while protecting against adverse moves.
"""

from typing import Dict, Optional
import pandas as pd


class ExitEngine:
    """
    ATR-based exit management with three key components:
    1. Initial ATR stop (entry protection)
    2. ATR trailing stop (profit protection)
    3. Dynamic k-factor selection (trend adaptation)
    """
    
    # K-factor selection based on trend strength
    K_FACTORS = {
        'tight': 1.5,    # Weak trends, quick exits
        'normal': 2.0,   # Standard trends
        'wide': 2.5      # Strong trends, room to breathe
    }
    
    # Trend strength thresholds (price vs 20-period SMA)
    TREND_THRESHOLDS = {
        'weak': 0.02,    # Within 2% of SMA = weak trend
        'normal': 0.05,  # 2-5% above SMA = normal trend
        'strong': 0.05   # >5% above SMA = strong trend
    }
    
    @staticmethod
    def update(
        current_price: float,
        entry_price: float,
        current_atr: float,
        sma20: float,
        existing_stop: Optional[float] = None,
        position_age_days: int = 0
    ) -> Dict[str, float]:
        """
        Update exit levels based on current market conditions.
        
        Args:
            current_price: Current stock price
            entry_price: Original entry price
            current_atr: Current 14-period ATR
            sma20: 20-period simple moving average
            existing_stop: Current stop level (None for new position)
            position_age_days: Days since position entry
            
        Returns:
            Dict with stop_price, k_factor, trend_strength, stop_type
            
        Example:
            exit_info = ExitEngine.update(
                current_price=52.50,
                entry_price=50.00,
                current_atr=1.80,
                sma20=51.20,
                existing_stop=48.00,
                position_age_days=5
            )
            # Returns: {'stop_price': 49.00, 'k_factor': 2.0, ...}
        """
        # Step 1: Determine trend strength
        trend_strength = ExitEngine._assess_trend_strength(current_price, sma20)
        
        # Step 2: Select appropriate k-factor
        k_factor = ExitEngine._select_k_factor(trend_strength, position_age_days)
        
        # Step 3: Calculate new stop level
        if existing_stop is None:
            # Initial stop: entry price - (k * ATR)
            new_stop = entry_price - (k_factor * current_atr)
            stop_type = 'initial'
        else:
            # Trailing stop: max(existing_stop, current_price - (k * ATR))
            trailing_stop = current_price - (k_factor * current_atr)
            new_stop = max(existing_stop, trailing_stop)
            stop_type = 'trailing' if new_stop > existing_stop else 'held'
        
        return {
            'stop_price': round(new_stop, 2),
            'k_factor': k_factor,
            'trend_strength': trend_strength,
            'stop_type': stop_type,
            'atr_distance': round(k_factor * current_atr, 2),
            'profit_loss_pct': round(((current_price - entry_price) / entry_price) * 100, 1)
        }
    
    @staticmethod
    def _assess_trend_strength(current_price: float, sma20: float) -> str:
        """
        Assess trend strength based on price relative to SMA20.
        
        Returns: 'weak', 'normal', or 'strong'
        """
        price_vs_sma = (current_price - sma20) / sma20
        
        if abs(price_vs_sma) <= ExitEngine.TREND_THRESHOLDS['weak']:
            return 'weak'
        elif abs(price_vs_sma) <= ExitEngine.TREND_THRESHOLDS['normal']:
            return 'normal'
        else:
            return 'strong'
    
    @staticmethod
    def _select_k_factor(trend_strength: str, position_age_days: int) -> float:
        """
        Select k-factor based on trend strength and position maturity.
        
        Newer positions get tighter stops, mature positions in strong trends get wider stops.
        """
        # Base k-factor from trend strength
        if trend_strength == 'weak':
            base_k = ExitEngine.K_FACTORS['tight']
        elif trend_strength == 'normal':
            base_k = ExitEngine.K_FACTORS['normal']
        else:  # strong
            base_k = ExitEngine.K_FACTORS['wide']
        
        # Adjust for position age (mature positions get slightly wider stops)
        if position_age_days >= 10 and trend_strength == 'strong':
            return ExitEngine.K_FACTORS['wide']
        elif position_age_days >= 5 and trend_strength in ['normal', 'strong']:
            return max(base_k, ExitEngine.K_FACTORS['normal'])
        else:
            return base_k
    
    @staticmethod
    def batch_update(df: pd.DataFrame) -> pd.DataFrame:
        """
        Update exit levels for multiple positions.
        
        Args:
            df: DataFrame with columns: current_price, entry_price, current_atr, 
                sma20, existing_stop (optional), position_age_days (optional)
                
        Returns:
            DataFrame with added exit management columns
        """
        results = []
        
        for _, row in df.iterrows():
            existing_stop = row.get('existing_stop', None)
            position_age = row.get('position_age_days', 0)
            
            exit_info = ExitEngine.update(
                current_price=row['current_price'],
                entry_price=row['entry_price'],
                current_atr=row['current_atr'],
                sma20=row['sma20'],
                existing_stop=existing_stop,
                position_age_days=position_age
            )
            
            results.append(exit_info)
        
        result_df = pd.DataFrame(results)
        return pd.concat([df, result_df], axis=1)
    
    @staticmethod
    def is_stopped_out(current_price: float, stop_price: float) -> bool:
        """Check if position should be exited based on stop level."""
        return current_price <= stop_price