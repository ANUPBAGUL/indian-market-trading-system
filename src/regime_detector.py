import pandas as pd
import numpy as np
from typing import Literal

RegimeType = Literal['risk_on', 'neutral', 'risk_off']

class RegimeDetector:
    """Detect market regime for risk management"""
    
    @staticmethod
    def calculate_index_trend(df: pd.DataFrame, period: int = 50) -> pd.Series:
        """Calculate index SMA50 trend"""
        return df['close'].rolling(window=period).mean()
    
    @staticmethod
    def calculate_trend_slope(sma: pd.Series, lookback: int = 10) -> pd.Series:
        """Calculate trend slope over lookback period"""
        # Slope = (current_sma - past_sma) / lookback_days
        past_sma = sma.shift(lookback)
        slope = (sma - past_sma) / lookback
        return slope
    
    @staticmethod
    def classify_regime(slope: pd.Series, slope_threshold: float = 0.5) -> pd.Series:
        """Classify market regime based on trend slope"""
        def get_regime(slope_val):
            if pd.isna(slope_val):
                return 'neutral'
            elif slope_val > slope_threshold:
                return 'risk_on'
            elif slope_val < -slope_threshold:
                return 'risk_off'
            else:
                return 'neutral'
        
        return slope.apply(get_regime)
    
    @classmethod
    def detect_regime(cls, df: pd.DataFrame, sma_period: int = 50, 
                     slope_lookback: int = 10, slope_threshold: float = 0.5) -> pd.DataFrame:
        """Complete regime detection pipeline"""
        result = df.copy()
        
        # Calculate index trend
        result['index_sma50'] = cls.calculate_index_trend(df, sma_period)
        
        # Calculate trend slope
        result['trend_slope'] = cls.calculate_trend_slope(result['index_sma50'], slope_lookback)
        
        # Classify regime
        result['regime'] = cls.classify_regime(result['trend_slope'], slope_threshold)
        
        return result