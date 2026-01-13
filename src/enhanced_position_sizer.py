"""
Enhanced Position Sizer - Dynamic sizing based on market volatility.

Improves position sizing by incorporating market volatility and 
enhanced risk management features.
"""

import numpy as np
from typing import Dict, List, Optional

class EnhancedPositionSizer:
    """Enhanced position sizer with dynamic volatility adjustments."""
    
    def __init__(self):
        """Initialize enhanced position sizer."""
        self.base_risk_pct = 1.5  # Base risk per trade
        self.max_risk_pct = 2.5   # Maximum risk per trade
        self.min_risk_pct = 0.5   # Minimum risk per trade
        
    def calculate_dynamic_size(
        self,
        stock_price: float,
        atr: float,
        account_value: float,
        confidence: float,
        market_volatility: float,
        sector_concentration: float = 0.0
    ) -> Dict:
        """
        Calculate position size with dynamic volatility adjustment.
        
        Args:
            stock_price: Current stock price
            atr: Average True Range (volatility measure)
            account_value: Total account value
            confidence: Signal confidence (0-100)
            market_volatility: Market volatility percentage (0-100)
            sector_concentration: Current sector exposure (0-100)
            
        Returns:
            Dict with position details
        """
        
        # Step 1: Base position sizing
        base_risk_amount = account_value * (self.base_risk_pct / 100)
        
        # Step 2: Confidence adjustment
        confidence_multiplier = self._get_confidence_multiplier(confidence)
        
        # Step 3: Dynamic volatility adjustment
        volatility_multiplier = self._get_volatility_multiplier(market_volatility)
        
        # Step 4: Sector concentration adjustment
        sector_multiplier = self._get_sector_multiplier(sector_concentration)
        
        # Step 5: Calculate adjusted risk
        adjusted_risk_pct = self.base_risk_pct * confidence_multiplier * volatility_multiplier * sector_multiplier
        adjusted_risk_pct = max(self.min_risk_pct, min(self.max_risk_pct, adjusted_risk_pct))
        
        # Step 6: Calculate position size
        risk_amount = account_value * (adjusted_risk_pct / 100)
        stop_distance = atr * 2.0  # 2 ATR stop
        shares = int(risk_amount / stop_distance)
        
        # Step 7: Position value limits
        max_position_value = account_value * 0.20  # Max 20% per position
        max_shares_by_value = int(max_position_value / stock_price)
        shares = min(shares, max_shares_by_value)
        
        # Ensure minimum viable position
        if shares < 1:
            shares = 1
        
        position_value = shares * stock_price
        actual_risk_pct = (shares * stop_distance / account_value) * 100
        
        return {
            'shares': shares,
            'position_value': position_value,
            'risk_amount': shares * stop_distance,
            'risk_percentage': actual_risk_pct,
            'stop_distance': stop_distance,
            'confidence_multiplier': confidence_multiplier,
            'volatility_multiplier': volatility_multiplier,
            'sector_multiplier': sector_multiplier,
            'reasoning': self._generate_sizing_reasoning(
                confidence, market_volatility, sector_concentration,
                confidence_multiplier, volatility_multiplier, sector_multiplier
            )
        }
    
    def _get_confidence_multiplier(self, confidence: float) -> float:
        """Calculate confidence-based size multiplier."""
        if confidence >= 80:
            return 1.3  # Increase size for high confidence
        elif confidence >= 70:
            return 1.1
        elif confidence >= 60:
            return 1.0  # Base size
        elif confidence >= 50:
            return 0.8
        else:
            return 0.6  # Reduce size for low confidence
    
    def _get_volatility_multiplier(self, market_volatility: float) -> float:
        """Calculate volatility-based size multiplier."""
        # Reduce size as volatility increases
        if market_volatility >= 30:  # Very high volatility
            return 0.6
        elif market_volatility >= 20:  # High volatility
            return 0.8
        elif market_volatility >= 15:  # Moderate volatility
            return 0.9
        elif market_volatility >= 10:  # Low volatility
            return 1.0
        else:  # Very low volatility
            return 1.1
    
    def _get_sector_multiplier(self, sector_concentration: float) -> float:
        """Calculate sector concentration multiplier."""
        # Reduce size as sector concentration increases
        if sector_concentration >= 40:  # High concentration
            return 0.7
        elif sector_concentration >= 30:  # Moderate concentration
            return 0.85
        elif sector_concentration >= 20:  # Some concentration
            return 0.95
        else:  # Low concentration
            return 1.0
    
    def _generate_sizing_reasoning(
        self,
        confidence: float,
        market_volatility: float,
        sector_concentration: float,
        conf_mult: float,
        vol_mult: float,
        sector_mult: float
    ) -> str:
        """Generate human-readable reasoning for position size."""
        
        reasons = []
        
        if conf_mult > 1.0:
            reasons.append(f"Increased size for {confidence:.0f}% confidence")
        elif conf_mult < 1.0:
            reasons.append(f"Reduced size for {confidence:.0f}% confidence")
        
        if vol_mult < 1.0:
            reasons.append(f"Reduced for {market_volatility:.0f}% market volatility")
        elif vol_mult > 1.0:
            reasons.append(f"Increased for low {market_volatility:.0f}% volatility")
        
        if sector_mult < 1.0:
            reasons.append(f"Reduced for {sector_concentration:.0f}% sector exposure")
        
        if not reasons:
            return "Standard position sizing applied"
        
        return "; ".join(reasons)
    
    def calculate_market_volatility(self, price_data: List[float], window: int = 20) -> float:
        """Calculate market volatility from price data."""
        if len(price_data) < window:
            return 15.0  # Default moderate volatility
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(price_data)):
            daily_return = (price_data[i] - price_data[i-1]) / price_data[i-1]
            returns.append(daily_return)
        
        # Calculate volatility (annualized)
        volatility = np.std(returns[-window:]) * np.sqrt(252) * 100
        
        return min(50.0, max(5.0, volatility))  # Cap between 5% and 50%
    
    def batch_calculate_sizes(
        self,
        signals: List[Dict],
        account_value: float,
        market_volatility: float,
        sector_exposures: Dict[str, float]
    ) -> List[Dict]:
        """Calculate position sizes for multiple signals."""
        
        sized_signals = []
        
        for signal in signals:
            sector = signal.get('sector', 'Unknown')
            sector_concentration = sector_exposures.get(sector, 0.0)
            
            size_info = self.calculate_dynamic_size(
                stock_price=signal['price'],
                atr=signal.get('atr', signal['price'] * 0.02),
                account_value=account_value,
                confidence=signal['confidence'],
                market_volatility=market_volatility,
                sector_concentration=sector_concentration
            )
            
            # Add sizing info to signal
            enhanced_signal = signal.copy()
            enhanced_signal.update(size_info)
            
            sized_signals.append(enhanced_signal)
        
        return sized_signals

# Convenience function
def calculate_enhanced_position_size(
    stock_price: float,
    atr: float,
    account_value: float,
    confidence: float,
    market_volatility: float = 15.0
) -> Dict:
    """Quick function for enhanced position sizing."""
    
    sizer = EnhancedPositionSizer()
    return sizer.calculate_dynamic_size(
        stock_price=stock_price,
        atr=atr,
        account_value=account_value,
        confidence=confidence,
        market_volatility=market_volatility
    )