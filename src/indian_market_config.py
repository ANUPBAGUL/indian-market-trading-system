"""
Indian Market Configuration - NSE/BSE specific settings and parameters.

Adapts the trading system for Indian equity markets with proper
trading hours, data formats, and market-specific considerations.
"""

from dataclasses import dataclass
from typing import Dict, List
import pandas as pd

@dataclass
class IndianMarketConfig:
    """Configuration for Indian equity markets."""
    
    # Trading hours (IST)
    market_open_time: str = "09:15"
    market_close_time: str = "15:30"
    pre_market_start: str = "09:00"
    post_market_end: str = "16:00"
    
    # Market holidays (major ones - update annually)
    market_holidays: List[str] = None
    
    # Currency and lot sizes
    currency: str = "INR"
    min_lot_size: int = 1
    
    # Risk parameters (adapted for Indian volatility)
    max_position_risk_pct: float = 2.0  # Higher volatility than US
    max_portfolio_risk_pct: float = 8.0
    max_sector_allocation_pct: float = 35.0
    
    # Confidence thresholds (slightly relaxed for Indian market)
    min_confidence_threshold: float = 60.0
    high_confidence_threshold: float = 75.0
    
    # Volume requirements (adapted for Indian liquidity)
    min_daily_volume: int = 100000  # Shares
    min_avg_volume_20d: int = 50000
    
    # Price filters
    min_stock_price: float = 10.0  # INR
    max_stock_price: float = 10000.0  # INR
    
    def __post_init__(self):
        if self.market_holidays is None:
            self.market_holidays = [
                "2024-01-26",  # Republic Day
                "2024-03-08",  # Holi
                "2024-03-29",  # Good Friday
                "2024-08-15",  # Independence Day
                "2024-10-02",  # Gandhi Jayanti
                "2024-11-01",  # Diwali
                # Add more as needed
            ]

class IndianSectorMapper:
    """Maps Indian stocks to sectors using NSE classifications."""
    
    # Major Indian sectors
    SECTOR_MAPPING = {
        # Banking & Financial Services
        'HDFCBANK': 'Banking', 'ICICIBANK': 'Banking', 'SBIN': 'Banking',
        'KOTAKBANK': 'Banking', 'AXISBANK': 'Banking', 'INDUSINDBK': 'Banking',
        'BAJFINANCE': 'NBFC', 'BAJAJFINSV': 'NBFC', 'HDFCLIFE': 'Insurance',
        
        # IT Services
        'TCS': 'IT', 'INFY': 'IT', 'WIPRO': 'IT', 'HCLTECH': 'IT',
        'TECHM': 'IT', 'LTI': 'IT', 'MINDTREE': 'IT',
        
        # FMCG
        'HINDUNILVR': 'FMCG', 'ITC': 'FMCG', 'NESTLEIND': 'FMCG',
        'BRITANNIA': 'FMCG', 'DABUR': 'FMCG', 'MARICO': 'FMCG',
        
        # Pharmaceuticals
        'SUNPHARMA': 'Pharma', 'DRREDDY': 'Pharma', 'CIPLA': 'Pharma',
        'DIVISLAB': 'Pharma', 'BIOCON': 'Pharma', 'LUPIN': 'Pharma',
        
        # Automobiles
        'MARUTI': 'Auto', 'TATAMOTORS': 'Auto', 'M&M': 'Auto',
        'BAJAJ-AUTO': 'Auto', 'HEROMOTOCO': 'Auto', 'EICHERMOT': 'Auto',
        
        # Metals & Mining
        'TATASTEEL': 'Metals', 'JSWSTEEL': 'Metals', 'HINDALCO': 'Metals',
        'VEDL': 'Metals', 'COALINDIA': 'Mining', 'NMDC': 'Mining',
        
        # Energy & Oil
        'RELIANCE': 'Energy', 'ONGC': 'Oil&Gas', 'IOC': 'Oil&Gas',
        'BPCL': 'Oil&Gas', 'GAIL': 'Oil&Gas', 'NTPC': 'Power',
        
        # Telecom
        'BHARTIARTL': 'Telecom', 'IDEA': 'Telecom', 'RCOM': 'Telecom',
        
        # Infrastructure
        'LT': 'Infrastructure', 'ULTRACEMCO': 'Cement', 'GRASIM': 'Cement',
        'SHREECEM': 'Cement', 'ACC': 'Cement'
    }
    
    @classmethod
    def get_sector(cls, symbol: str) -> str:
        """Get sector for Indian stock symbol."""
        # Remove .NS or .BO suffix if present
        clean_symbol = symbol.replace('.NS', '').replace('.BO', '')
        return cls.SECTOR_MAPPING.get(clean_symbol, 'Others')
    
    @classmethod
    def get_sector_stocks(cls, sector: str) -> List[str]:
        """Get all stocks in a sector."""
        return [symbol for symbol, sec in cls.SECTOR_MAPPING.items() if sec == sector]

class IndianDataValidator:
    """Validates Indian market data format and quality."""
    
    REQUIRED_COLUMNS = [
        'date', 'symbol', 'open', 'high', 'low', 'close', 'volume'
    ]
    
    @staticmethod
    def validate_data_format(df: pd.DataFrame) -> bool:
        """Validate Indian market data format."""
        # Check required columns
        missing_cols = set(IndianDataValidator.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing columns: {missing_cols}")
        
        # Check for Indian stock symbols (should have .NS or .BO or be clean NSE symbols)
        sample_symbols = df['symbol'].head(10).tolist()
        
        # Validate date format
        try:
            pd.to_datetime(df['date'].head())
        except:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")
        
        # Check for reasonable price ranges (INR)
        if df['close'].min() < 0 or df['close'].max() > 100000:
            raise ValueError("Unreasonable price range detected")
        
        return True
    
    @staticmethod
    def clean_symbol(symbol: str) -> str:
        """Clean Indian stock symbol for consistency."""
        # Remove exchange suffixes and standardize
        symbol = symbol.replace('.NS', '').replace('.BO', '')
        symbol = symbol.replace('-', '').replace('&', '')
        return symbol.upper()

# Indian market specific constants
INDIAN_MARKET_CONFIG = IndianMarketConfig()

# Major Indian indices for market regime detection
INDIAN_INDICES = {
    'NIFTY50': '^NSEI',
    'SENSEX': '^BSESN',
    'NIFTY_BANK': '^NSEBANK',
    'NIFTY_IT': '^CNXIT',
    'NIFTY_FMCG': '^CNXFMCG'
}

# Indian market trading calendar helpers
def is_indian_trading_day(date_str: str) -> bool:
    """Check if given date is a trading day in Indian markets."""
    import datetime
    
    date_obj = pd.to_datetime(date_str).date()
    
    # Check if weekend
    if date_obj.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Check if holiday
    if date_str in INDIAN_MARKET_CONFIG.market_holidays:
        return False
    
    return True

def get_indian_market_hours() -> Dict[str, str]:
    """Get Indian market trading hours."""
    return {
        'pre_market_start': INDIAN_MARKET_CONFIG.pre_market_start,
        'market_open': INDIAN_MARKET_CONFIG.market_open_time,
        'market_close': INDIAN_MARKET_CONFIG.market_close_time,
        'post_market_end': INDIAN_MARKET_CONFIG.post_market_end
    }