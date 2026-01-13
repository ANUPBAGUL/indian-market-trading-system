import pandas as pd
import numpy as np
from typing import Dict, Any

class FeatureComputer:
    """Compute technical features with no lookahead bias"""
    
    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range - volatility measure"""
        high = df['high']
        low = df['low'] 
        close = df['close'].shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return true_range.rolling(window=period).mean()
    
    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average - trend direction"""
        return series.rolling(window=period).mean()
    
    @staticmethod
    def rvol(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Relative Volume - current vs average volume"""
        avg_volume = df['volume'].rolling(window=period).mean()
        return df['volume'] / avg_volume
    
    @classmethod
    def compute_all(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Compute all features for a stock's data"""
        result = df.copy()
        
        result['atr_14'] = cls.atr(df, 14)
        result['sma_20'] = cls.sma(df['close'], 20)
        result['sma_50'] = cls.sma(df['close'], 50)
        result['rvol_20'] = cls.rvol(df, 20)
        
        return result