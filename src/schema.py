from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd

@dataclass
class OHLCVSchema:
    """Schema for daily OHLCV data with sector mapping"""
    symbol: str
    date: str  # YYYY-MM-DD format
    open: float
    high: float
    low: float
    close: float
    volume: int
    sector: Optional[str] = None
    
    @classmethod
    def get_dtypes(cls) -> Dict[str, str]:
        """Return pandas dtypes for efficient loading"""
        return {
            'symbol': 'string',
            'date': 'string',
            'open': 'float64',
            'high': 'float64', 
            'low': 'float64',
            'close': 'float64',
            'volume': 'int64',
            'sector': 'string'
        }