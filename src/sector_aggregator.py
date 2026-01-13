import pandas as pd
import numpy as np
from typing import Dict

class SectorAggregator:
    """Compute sector-level market microstructure metrics"""
    
    @staticmethod
    def aggregate_sectors(df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate individual stock data to sector level"""
        # Group by date and sector
        sector_groups = df.groupby(['date', 'sector'])
        
        # Calculate sector aggregates
        sector_data = []
        
        for (date, sector), group in sector_groups:
            # Market cap weighted close (using volume as proxy)
            total_volume = group['volume'].sum()
            if total_volume > 0:
                sector_close = (group['close'] * group['volume']).sum() / total_volume
            else:
                sector_close = group['close'].mean()
            
            # Sector volume (sum of all stocks)
            sector_volume = group['volume'].sum()
            
            # Sector RVOL (average of individual RVOLs)
            sector_rvol = group['rvol_20'].mean() if 'rvol_20' in group.columns else np.nan
            
            # Sector breadth (% stocks above SMA20)
            stocks_above_sma = (group['close'] > group['sma_20']).sum() if 'sma_20' in group.columns else 0
            total_stocks = len(group)
            sector_breadth = (stocks_above_sma / total_stocks) * 100 if total_stocks > 0 else 0
            
            sector_data.append({
                'date': date,
                'sector': sector,
                'sector_close': sector_close,
                'sector_volume': sector_volume,
                'sector_rvol': sector_rvol,
                'sector_breadth': sector_breadth,
                'stock_count': total_stocks
            })
        
        return pd.DataFrame(sector_data)
    
    @staticmethod
    def get_sector_stats(sector_df: pd.DataFrame, date: str) -> pd.DataFrame:
        """Get sector statistics for a specific date"""
        day_data = sector_df[sector_df['date'] == date].copy()
        
        if len(day_data) == 0:
            return pd.DataFrame()
        
        # Sort by sector volume for display
        return day_data.sort_values('sector_volume', ascending=False)