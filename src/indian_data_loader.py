"""
Indian Market Data Loader - Handles NSE/BSE data formats and sources.

Supports multiple Indian data sources including Yahoo Finance (.NS/.BO),
NSE API, and CSV files with Indian market conventions.
"""

import pandas as pd
import yfinance as yf
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import os

from indian_market_config import IndianDataValidator, IndianSectorMapper, is_indian_trading_day

class IndianDataLoader:
    """
    Data loader optimized for Indian equity markets.
    Handles NSE/BSE symbols, Indian date formats, and market conventions.
    """
    
    def __init__(self, data_source: str = "yahoo"):
        """
        Initialize Indian data loader.
        
        Args:
            data_source: 'yahoo', 'csv', or 'nse_api'
        """
        self.data_source = data_source
        self.sector_mapper = IndianSectorMapper()
    
    def load_stock_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        exchange: str = "NSE"
    ) -> pd.DataFrame:
        """
        Load Indian stock data for multiple symbols.
        
        Args:
            symbols: List of Indian stock symbols (e.g., ['RELIANCE', 'TCS'])
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            exchange: 'NSE' or 'BSE'
            
        Returns:
            DataFrame with columns: date, symbol, open, high, low, close, volume, sector
        """
        if self.data_source == "yahoo":
            return self._load_from_yahoo(symbols, start_date, end_date, exchange)
        elif self.data_source == "csv":
            return self._load_from_csv(symbols, start_date, end_date)
        else:
            raise ValueError(f"Unsupported data source: {self.data_source}")
    
    def _load_from_yahoo(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        exchange: str
    ) -> pd.DataFrame:
        """Load data from Yahoo Finance with Indian exchange suffixes."""
        
        # Add exchange suffix for Yahoo Finance
        suffix = ".NS" if exchange == "NSE" else ".BO"
        yahoo_symbols = [f"{symbol}{suffix}" for symbol in symbols]
        
        all_data = []
        
        print(f"Loading {len(symbols)} Indian stocks from Yahoo Finance...")
        
        for i, (original_symbol, yahoo_symbol) in enumerate(zip(symbols, yahoo_symbols)):
            try:
                # Download data
                ticker = yf.Ticker(yahoo_symbol)
                data = ticker.history(start=start_date, end=end_date)
                
                if data.empty:
                    print(f"No data for {original_symbol}")
                    continue
                
                # Prepare DataFrame
                df = data.reset_index()
                df['symbol'] = original_symbol
                df['date'] = df['Date'].dt.strftime('%Y-%m-%d')
                
                # Rename columns to match schema
                df = df.rename(columns={
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                })
                
                # Add sector information
                df['sector'] = self.sector_mapper.get_sector(original_symbol)
                
                # Select required columns
                df = df[['date', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'sector']]
                
                # Filter trading days only
                df = df[df['date'].apply(is_indian_trading_day)]
                
                all_data.append(df)
                
                if (i + 1) % 10 == 0:
                    print(f"Loaded {i + 1}/{len(symbols)} stocks...")
                    
            except Exception as e:
                print(f"Error loading {original_symbol}: {e}")
                continue
        
        if not all_data:
            return pd.DataFrame()
        
        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Validate data format
        IndianDataValidator.validate_data_format(combined_df)
        
        print(f"Successfully loaded {len(combined_df)} records for {combined_df['symbol'].nunique()} stocks")
        return combined_df
    
    def _load_from_csv(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """Load data from CSV files (Indian format)."""
        
        all_data = []
        
        for symbol in symbols:
            csv_path = f"data/indian_stocks/{symbol}.csv"
            
            if not os.path.exists(csv_path):
                print(f"CSV file not found for {symbol}: {csv_path}")
                continue
            
            try:
                df = pd.read_csv(csv_path)
                
                # Standardize column names
                df.columns = df.columns.str.lower()
                
                # Clean symbol
                df['symbol'] = IndianDataValidator.clean_symbol(symbol)
                
                # Add sector
                df['sector'] = self.sector_mapper.get_sector(symbol)
                
                # Filter date range
                df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
                
                # Filter trading days
                df = df[df['date'].apply(is_indian_trading_day)]
                
                all_data.append(df)
                
            except Exception as e:
                print(f"Error loading CSV for {symbol}: {e}")
                continue
        
        if not all_data:
            return pd.DataFrame()
        
        combined_df = pd.concat(all_data, ignore_index=True)
        IndianDataValidator.validate_data_format(combined_df)
        
        return combined_df
    
    def load_index_data(
        self,
        index_name: str = "NIFTY50",
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """Load Indian market index data for regime detection."""
        
        from indian_market_config import INDIAN_INDICES
        
        if index_name not in INDIAN_INDICES:
            raise ValueError(f"Unsupported index: {index_name}")
        
        yahoo_symbol = INDIAN_INDICES[index_name]
        
        try:
            ticker = yf.Ticker(yahoo_symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                raise ValueError(f"No data available for {index_name}")
            
            df = data.reset_index()
            df['date'] = df['Date'].dt.strftime('%Y-%m-%d')
            df['symbol'] = index_name
            
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            return df[['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            print(f"Error loading index {index_name}: {e}")
            return pd.DataFrame()
    
    def get_nifty50_stocks(self) -> List[str]:
        """Get current NIFTY 50 stock list."""
        # Major NIFTY 50 stocks (update periodically)
        return [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR',
            'ICICIBANK', 'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK',
            'LT', 'AXISBANK', 'MARUTI', 'SUNPHARMA', 'ULTRACEMCO',
            'ASIANPAINT', 'NESTLEIND', 'BAJFINANCE', 'HCLTECH', 'WIPRO',
            'TATAMOTORS', 'NTPC', 'ONGC', 'POWERGRID', 'TECHM',
            'TATASTEEL', 'INDUSINDBK', 'BAJAJ-AUTO', 'DRREDDY', 'JSWSTEEL',
            'M&M', 'GRASIM', 'CIPLA', 'COALINDIA', 'HEROMOTOCO',
            'BRITANNIA', 'EICHERMOT', 'IOC', 'BPCL', 'HINDALCO',
            'DIVISLAB', 'ADANIPORTS', 'UPL', 'SHREECEM', 'TITAN',
            'BAJAJFINSV', 'HDFCLIFE', 'SBILIFE', 'VEDL', 'APOLLOHOSP'
        ]
    
    def create_sample_data(self, symbols: List[str] = None) -> pd.DataFrame:
        """Create sample Indian market data for testing."""
        
        if symbols is None:
            symbols = ['RELIANCE', 'TCS', 'HDFCBANK']
        
        # Generate 60 days of sample data
        dates = pd.date_range(
            start='2024-01-01',
            end='2024-03-01',
            freq='D'
        )
        
        # Filter to trading days only
        trading_dates = [d.strftime('%Y-%m-%d') for d in dates if is_indian_trading_day(d.strftime('%Y-%m-%d'))]
        
        all_data = []
        
        for symbol in symbols:
            base_price = {'RELIANCE': 2500, 'TCS': 3500, 'HDFCBANK': 1600}.get(symbol, 1000)
            
            for date in trading_dates:
                # Generate realistic Indian stock data
                open_price = base_price * (0.98 + 0.04 * pd.np.random.random())
                high_price = open_price * (1.0 + 0.03 * pd.np.random.random())
                low_price = open_price * (1.0 - 0.03 * pd.np.random.random())
                close_price = low_price + (high_price - low_price) * pd.np.random.random()
                volume = int(1000000 * (0.5 + pd.np.random.random()))
                
                all_data.append({
                    'date': date,
                    'symbol': symbol,
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': volume,
                    'sector': self.sector_mapper.get_sector(symbol)
                })
        
        return pd.DataFrame(all_data)

# Convenience function for quick data loading
def load_indian_stocks(
    symbols: List[str],
    start_date: str,
    end_date: str,
    exchange: str = "NSE"
) -> pd.DataFrame:
    """Quick function to load Indian stock data."""
    loader = IndianDataLoader(data_source="yahoo")
    return loader.load_stock_data(symbols, start_date, end_date, exchange)