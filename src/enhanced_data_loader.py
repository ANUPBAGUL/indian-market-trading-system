"""
Enhanced Data Loader - Real market data integration with improved filtering.

Integrates yfinance for live data feeds and adds enhanced signal filtering
with volume and price requirements.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class EnhancedDataLoader:
    """Enhanced data loader with real market data and filtering."""
    
    # Enhanced filtering parameters
    MIN_DAILY_VOLUME = 1000000  # 1M shares minimum
    MIN_PRICE = 10.0  # Avoid penny stocks
    MAX_PRICE = 1000.0  # Avoid extreme high-priced stocks
    MIN_MARKET_CAP = 1000000000  # $1B minimum market cap
    
    def __init__(self, use_real_data: bool = True):
        """Initialize enhanced data loader."""
        self.use_real_data = use_real_data
        
    def load_us_stocks(self, symbols: List[str], period: str = "6mo") -> pd.DataFrame:
        """Load US stock data with enhanced filtering."""
        
        if not self.use_real_data:
            return self._create_sample_data(symbols)
        
        print(f"Loading real market data for {len(symbols)} US stocks...")
        
        all_data = []
        successful_loads = 0
        
        for symbol in symbols:
            try:
                # Download real data
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period)
                
                if data.empty:
                    continue
                
                # Get additional info for filtering
                info = ticker.info
                
                # Apply enhanced filtering
                if not self._passes_filters(data, info):
                    print(f"  {symbol}: Filtered out (volume/price/market cap)")
                    continue
                
                # Prepare DataFrame
                df = data.reset_index()
                df['symbol'] = symbol
                df['date'] = df['Date'].dt.strftime('%Y-%m-%d')
                
                # Rename columns
                df = df.rename(columns={
                    'Open': 'open',
                    'High': 'high', 
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                })
                
                # Add sector info
                df['sector'] = info.get('sector', 'Unknown')
                
                # Select required columns
                df = df[['date', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'sector']]
                
                all_data.append(df)
                successful_loads += 1
                
                print(f"  {symbol}: Loaded {len(df)} records")
                
            except Exception as e:
                print(f"  {symbol}: Error - {e}")
                continue
        
        if not all_data:
            print("No data loaded, falling back to sample data")
            return self._create_sample_data(symbols[:3])
        
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"Successfully loaded {successful_loads}/{len(symbols)} stocks")
        
        return combined_df
    
    def _passes_filters(self, data: pd.DataFrame, info: Dict) -> bool:
        """Apply enhanced filtering criteria."""
        
        # Check average volume
        avg_volume = data['Volume'].mean()
        if avg_volume < self.MIN_DAILY_VOLUME:
            return False
        
        # Check price range
        current_price = data['Close'].iloc[-1]
        if current_price < self.MIN_PRICE or current_price > self.MAX_PRICE:
            return False
        
        # Check market cap if available
        market_cap = info.get('marketCap', 0)
        if market_cap > 0 and market_cap < self.MIN_MARKET_CAP:
            return False
        
        # Check for sufficient data
        if len(data) < 30:  # Need at least 30 days
            return False
        
        return True
    
    def _create_sample_data(self, symbols: List[str]) -> pd.DataFrame:
        """Create sample data when real data unavailable."""
        
        print("Creating sample data...")
        
        # Generate 60 days of data
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=80),
            end=datetime.now(),
            freq='D'
        )
        
        # Filter to trading days
        trading_dates = [d for d in dates if d.weekday() < 5][-60:]
        
        all_data = []
        
        for symbol in symbols:
            base_price = {'AAPL': 150, 'MSFT': 300, 'GOOGL': 120}.get(symbol, 100)
            
            for date in trading_dates:
                # Generate realistic OHLCV
                open_price = base_price * (0.98 + 0.04 * np.random.random())
                high_price = open_price * (1.0 + 0.03 * np.random.random())
                low_price = open_price * (1.0 - 0.03 * np.random.random())
                close_price = low_price + (high_price - low_price) * np.random.random()
                
                # Ensure minimum volume
                volume = int(self.MIN_DAILY_VOLUME * (1 + np.random.random()))
                
                all_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'symbol': symbol,
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': volume,
                    'sector': 'Technology'
                })
        
        return pd.DataFrame(all_data)
    
    def get_quality_us_stocks(self) -> List[str]:
        """Get list of quality US stocks that pass filters."""
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
            'NVDA', 'META', 'NFLX', 'CRM', 'ADBE',
            'PYPL', 'INTC', 'AMD', 'ORCL', 'CSCO'
        ]

# Convenience function
def load_enhanced_us_data(symbols: List[str] = None, use_real_data: bool = True) -> pd.DataFrame:
    """Quick function to load enhanced US stock data."""
    
    loader = EnhancedDataLoader(use_real_data=use_real_data)
    
    if symbols is None:
        symbols = loader.get_quality_us_stocks()
    
    return loader.load_us_stocks(symbols)