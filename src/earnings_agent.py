import pandas as pd
import numpy as np
from typing import Dict, Optional, Literal
from dataclasses import dataclass
from datetime import datetime, timedelta

ReactionType = Literal['Bullish', 'Neutral', 'Bearish']

@dataclass
class EarningsEvent:
    """Earnings event data"""
    symbol: str
    earnings_date: datetime
    days_to_earnings: int
    post_reaction: Optional[ReactionType] = None

class EarningsAgent:
    """Manage earnings calendar and post-earnings reactions"""
    
    @staticmethod
    def ingest_earnings_calendar(earnings_data: pd.DataFrame) -> Dict[str, datetime]:
        """Ingest earnings calendar data"""
        earnings_calendar = {}
        
        for _, row in earnings_data.iterrows():
            symbol = row['symbol']
            earnings_date = pd.to_datetime(row['earnings_date'])
            earnings_calendar[symbol] = earnings_date
        
        return earnings_calendar
    
    @staticmethod
    def calculate_days_to_earnings(current_date: datetime, 
                                 earnings_calendar: Dict[str, datetime]) -> Dict[str, int]:
        """Calculate days to earnings for each symbol"""
        days_to_earnings = {}
        
        for symbol, earnings_date in earnings_calendar.items():
            days_diff = (earnings_date - current_date).days
            days_to_earnings[symbol] = days_diff
        
        return days_to_earnings
    
    @staticmethod
    def classify_post_earnings_reaction(stock_df: pd.DataFrame, 
                                      earnings_date: datetime,
                                      reaction_window: int = 3) -> ReactionType:
        """Classify post-earnings price/volume reaction"""
        if len(stock_df) < reaction_window + 5:
            return 'Neutral'
        
        # Find earnings date in data
        stock_df['date'] = pd.to_datetime(stock_df['date'])
        earnings_idx = None
        
        for i, row in stock_df.iterrows():
            if row['date'].date() >= earnings_date.date():
                earnings_idx = i
                break
        
        if earnings_idx is None or earnings_idx + reaction_window >= len(stock_df):
            return 'Neutral'
        
        # Pre-earnings baseline (5 days before)
        pre_start = max(0, earnings_idx - 5)
        pre_data = stock_df.iloc[pre_start:earnings_idx]
        
        if len(pre_data) == 0:
            return 'Neutral'
        
        pre_avg_volume = pre_data['volume'].mean()
        pre_close = pre_data['close'].iloc[-1] if len(pre_data) > 0 else stock_df['close'].iloc[earnings_idx]
        
        # Post-earnings data (reaction window)
        post_data = stock_df.iloc[earnings_idx:earnings_idx + reaction_window]
        
        if len(post_data) == 0:
            return 'Neutral'
        
        # Calculate reaction metrics
        post_close = post_data['close'].iloc[-1]
        price_change = (post_close / pre_close - 1) if pre_close > 0 else 0
        
        # Volume surge detection
        post_avg_volume = post_data['volume'].mean()
        volume_surge = (post_avg_volume / pre_avg_volume) if pre_avg_volume > 0 else 1
        
        # Classification logic: price + volume confirmation
        if price_change > 0.03 and volume_surge > 1.5:  # >3% move + volume surge
            return 'Bullish'
        elif price_change < -0.03 and volume_surge > 1.5:  # <-3% move + volume surge
            return 'Bearish'
        else:
            return 'Neutral'  # Weak reaction or no volume confirmation
    
    @classmethod
    def run(cls, stock_data: Dict[str, pd.DataFrame], 
            earnings_calendar_df: pd.DataFrame,
            current_date: datetime) -> Dict[str, EarningsEvent]:
        """Run earnings analysis for all stocks"""
        
        # Ingest earnings calendar
        earnings_calendar = cls.ingest_earnings_calendar(earnings_calendar_df)
        
        # Calculate days to earnings
        days_to_earnings = cls.calculate_days_to_earnings(current_date, earnings_calendar)
        
        # Process each stock
        results = {}
        
        for symbol in earnings_calendar.keys():
            earnings_date = earnings_calendar[symbol]
            days_to = days_to_earnings[symbol]
            
            # Classify post-earnings reaction if earnings already passed
            post_reaction = None
            if days_to < 0 and symbol in stock_data:  # Earnings in the past
                post_reaction = cls.classify_post_earnings_reaction(
                    stock_data[symbol], earnings_date
                )
            
            results[symbol] = EarningsEvent(
                symbol=symbol,
                earnings_date=earnings_date,
                days_to_earnings=days_to,
                post_reaction=post_reaction
            )
        
        return results