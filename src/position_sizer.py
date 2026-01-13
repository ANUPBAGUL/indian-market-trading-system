"""
Hybrid Position Sizing - Combines fixed risk with volatility and confidence adjustments.

The system maintains consistent dollar risk per trade while adapting to market
volatility and signal confidence levels.
"""

from typing import Dict, Tuple
import pandas as pd


class PositionSizer:
    """
    Hybrid position sizing with four key components:
    1. Fixed risk per trade (base risk budget)
    2. ATR-based stop distance (volatility-aware stops)
    3. Volatility-adjusted max size (prevents oversizing volatile stocks)
    4. Confidence-based participation (allocates risk based on signal strength)
    """
    
    # Risk management parameters
    BASE_RISK_PER_TRADE = 0.01  # 1% of account per trade
    ATR_STOP_MULTIPLIER = 2.0   # Stop at 2x ATR below entry
    MAX_VOLATILITY_THRESHOLD = 0.05  # 5% daily volatility cap
    MIN_CONFIDENCE_THRESHOLD = 62    # Minimum confidence to trade
    
    # Confidence participation rates
    CONFIDENCE_PARTICIPATION = {
        60: 0.25,   # 25% participation for 60-65% confidence
        65: 0.40,   # 40% participation for 65-70% confidence  
        70: 0.55,   # 55% participation for 70-75% confidence
        75: 0.70,   # 70% participation for 75-80% confidence
        80: 0.85,   # 85% participation for 80-85% confidence
        85: 1.00,   # 100% participation for 85%+ confidence
    }
    
    @staticmethod
    def position_size(
        account_value: float,
        entry_price: float, 
        atr: float,
        confidence_score: float,
        daily_volatility: float = None
    ) -> Dict[str, float]:
        """
        Calculate position size using hybrid approach.
        
        Args:
            account_value: Total account value
            entry_price: Stock entry price
            atr: Average True Range (14-period)
            confidence_score: Confidence score (0-100)
            daily_volatility: Optional daily volatility override
            
        Returns:
            Dict with position_size, stop_price, risk_amount, participation_rate
            
        Example:
            size_info = PositionSizer.position_size(
                account_value=100000,
                entry_price=50.0,
                atr=2.5,
                confidence_score=78.5
            )
            # Returns: {'position_size': 280, 'stop_price': 45.0, ...}
        """
        # Step 1: Check minimum confidence threshold
        if confidence_score < PositionSizer.MIN_CONFIDENCE_THRESHOLD:
            return {
                'position_size': 0,
                'stop_price': 0.0,
                'risk_amount': 0.0,
                'participation_rate': 0.0,
                'reason': f'Below minimum confidence ({PositionSizer.MIN_CONFIDENCE_THRESHOLD}%)'
            }
        
        # Step 2: Calculate base risk amount
        base_risk = account_value * PositionSizer.BASE_RISK_PER_TRADE
        
        # Step 3: Determine confidence participation rate
        participation_rate = PositionSizer._get_participation_rate(confidence_score)
        adjusted_risk = base_risk * participation_rate
        
        # Step 4: Calculate ATR-based stop distance
        stop_distance = atr * PositionSizer.ATR_STOP_MULTIPLIER
        stop_price = entry_price - stop_distance
        
        # Step 5: Calculate base position size from risk/stop
        base_position_size = adjusted_risk / stop_distance
        
        # Step 6: Apply volatility adjustment if provided
        if daily_volatility is not None:
            volatility_adjustment = PositionSizer._get_volatility_adjustment(daily_volatility)
            final_position_size = base_position_size * volatility_adjustment
        else:
            final_position_size = base_position_size
        
        # Step 7: Round to whole shares
        final_position_size = int(final_position_size)
        
        return {
            'position_size': final_position_size,
            'stop_price': round(stop_price, 2),
            'risk_amount': round(adjusted_risk, 2),
            'participation_rate': participation_rate,
            'stop_distance': round(stop_distance, 2),
            'volatility_adjustment': volatility_adjustment if daily_volatility else 1.0
        }
    
    @staticmethod
    def _get_participation_rate(confidence_score: float) -> float:
        """Map confidence score to participation rate."""
        # Find the appropriate confidence bucket
        for min_conf in sorted(PositionSizer.CONFIDENCE_PARTICIPATION.keys(), reverse=True):
            if confidence_score >= min_conf:
                return PositionSizer.CONFIDENCE_PARTICIPATION[min_conf]
        
        # Below minimum threshold
        return 0.0
    
    @staticmethod
    def _get_volatility_adjustment(daily_volatility: float) -> float:
        """
        Reduce position size for high volatility stocks.
        
        Volatility > 5% daily gets reduced sizing to prevent excessive risk.
        """
        if daily_volatility <= PositionSizer.MAX_VOLATILITY_THRESHOLD:
            return 1.0  # No adjustment for normal volatility
        
        # Linear reduction for high volatility
        # 5% vol = 1.0x, 10% vol = 0.5x
        adjustment = PositionSizer.MAX_VOLATILITY_THRESHOLD / daily_volatility
        return max(adjustment, 0.25)  # Minimum 25% of base size
    
    @staticmethod
    def batch_size(df: pd.DataFrame, account_value: float) -> pd.DataFrame:
        """
        Calculate position sizes for multiple stocks.
        
        Args:
            df: DataFrame with columns: entry_price, atr, confidence_score, daily_volatility (optional)
            account_value: Total account value
            
        Returns:
            DataFrame with added position sizing columns
        """
        results = []
        
        for _, row in df.iterrows():
            daily_vol = row.get('daily_volatility', None)
            
            size_info = PositionSizer.position_size(
                account_value=account_value,
                entry_price=row['entry_price'],
                atr=row['atr'],
                confidence_score=row['confidence_score'],
                daily_volatility=daily_vol
            )
            
            results.append(size_info)
        
        result_df = pd.DataFrame(results)
        return pd.concat([df, result_df], axis=1)