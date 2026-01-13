import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.earnings_agent import EarningsAgent, EarningsEvent

class TestEarningsAgent:
    @pytest.fixture
    def sample_earnings_calendar(self):
        """Basic earnings calendar data"""
        return pd.DataFrame([
            {'symbol': 'AAPL', 'earnings_date': '2024-02-20'},
            {'symbol': 'MSFT', 'earnings_date': '2024-02-15'},
            {'symbol': 'GOOGL', 'earnings_date': '2024-02-10'}
        ])
    
    @pytest.fixture
    def sample_stock_data(self):
        """Stock data with earnings reaction"""
        dates = pd.date_range('2024-02-10', periods=10)
        return pd.DataFrame({
            'date': dates,
            'open': [100] * 10,
            'high': [105] * 5 + [110] * 5,  # Higher highs post-earnings
            'low': [95] * 5 + [100] * 5,
            'close': [100] * 5 + [108] * 5,  # +8% post-earnings
            'volume': [1000000] * 5 + [2500000] * 5  # 2.5x volume surge
        })
    
    def test_earnings_calendar_ingestion(self, sample_earnings_calendar):
        """Test earnings calendar ingestion"""
        calendar = EarningsAgent.ingest_earnings_calendar(sample_earnings_calendar)
        
        assert 'AAPL' in calendar
        assert 'MSFT' in calendar
        assert 'GOOGL' in calendar
        
        # Check date conversion
        assert isinstance(calendar['AAPL'], datetime)
        assert calendar['AAPL'].date() == datetime(2024, 2, 20).date()
    
    def test_days_to_earnings_calculation(self):
        """Test days to earnings calculation"""
        current_date = datetime(2024, 2, 15)
        earnings_calendar = {
            'FUTURE': datetime(2024, 2, 20),  # +5 days
            'PAST': datetime(2024, 2, 10),    # -5 days
            'TODAY': datetime(2024, 2, 15)    # 0 days
        }
        
        days_to = EarningsAgent.calculate_days_to_earnings(current_date, earnings_calendar)
        
        assert days_to['FUTURE'] == 5
        assert days_to['PAST'] == -5
        assert days_to['TODAY'] == 0
    
    def test_bullish_reaction_classification(self):
        """Test bullish post-earnings reaction"""
        # Create bullish reaction data
        dates = pd.date_range('2024-02-10', periods=10)
        stock_data = pd.DataFrame({
            'date': dates,
            'close': [100] * 5 + [108] * 5,  # +8% move
            'volume': [1000000] * 5 + [2000000] * 5  # 2x volume
        })
        
        earnings_date = datetime(2024, 2, 15)
        reaction = EarningsAgent.classify_post_earnings_reaction(stock_data, earnings_date)
        
        assert reaction == 'Bullish'
    
    def test_bearish_reaction_classification(self):
        """Test bearish post-earnings reaction"""
        # Create bearish reaction data
        dates = pd.date_range('2024-02-10', periods=10)
        stock_data = pd.DataFrame({
            'date': dates,
            'close': [100] * 5 + [92] * 5,   # -8% move
            'volume': [1000000] * 5 + [2000000] * 5  # 2x volume
        })
        
        earnings_date = datetime(2024, 2, 15)
        reaction = EarningsAgent.classify_post_earnings_reaction(stock_data, earnings_date)
        
        assert reaction == 'Bearish'
    
    def test_neutral_reaction_classification(self):
        """Test neutral post-earnings reaction"""
        # Create neutral reaction data (small move)
        dates = pd.date_range('2024-02-10', periods=10)
        stock_data = pd.DataFrame({
            'date': dates,
            'close': [100] * 5 + [102] * 5,  # +2% move (below 3% threshold)
            'volume': [1000000] * 5 + [2000000] * 5  # 2x volume
        })
        
        earnings_date = datetime(2024, 2, 15)
        reaction = EarningsAgent.classify_post_earnings_reaction(stock_data, earnings_date)
        
        assert reaction == 'Neutral'
    
    def test_neutral_reaction_no_volume(self):
        """Test neutral reaction due to no volume confirmation"""
        # Create data with big move but no volume surge
        dates = pd.date_range('2024-02-10', periods=10)
        stock_data = pd.DataFrame({
            'date': dates,
            'close': [100] * 5 + [108] * 5,  # +8% move
            'volume': [1000000] * 10  # No volume surge
        })
        
        earnings_date = datetime(2024, 2, 15)
        reaction = EarningsAgent.classify_post_earnings_reaction(stock_data, earnings_date)
        
        assert reaction == 'Neutral'  # No volume confirmation
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data"""
        # Very limited data
        minimal_data = pd.DataFrame({
            'date': [datetime(2024, 2, 15)],
            'close': [100],
            'volume': [1000000]
        })
        
        earnings_date = datetime(2024, 2, 15)
        reaction = EarningsAgent.classify_post_earnings_reaction(minimal_data, earnings_date)
        
        assert reaction == 'Neutral'  # Default for insufficient data
    
    def test_earnings_date_not_found(self):
        """Test when earnings date is not in data range"""
        dates = pd.date_range('2024-02-01', periods=5)
        stock_data = pd.DataFrame({
            'date': dates,
            'close': [100] * 5,
            'volume': [1000000] * 5
        })
        
        # Earnings date outside data range
        earnings_date = datetime(2024, 2, 20)
        reaction = EarningsAgent.classify_post_earnings_reaction(stock_data, earnings_date)
        
        assert reaction == 'Neutral'
    
    def test_run_method_complete(self, sample_earnings_calendar):
        """Test complete run method"""
        current_date = datetime(2024, 2, 15)
        
        # Create stock data for past earnings
        stock_data = {
            'GOOGL': pd.DataFrame({
                'date': pd.date_range('2024-02-05', periods=10),
                'close': [100] * 5 + [108] * 5,  # Bullish reaction
                'volume': [1000000] * 5 + [2000000] * 5
            })
        }
        
        results = EarningsAgent.run(stock_data, sample_earnings_calendar, current_date)
        
        # Check return structure
        assert isinstance(results, dict)
        assert 'AAPL' in results
        assert 'MSFT' in results
        assert 'GOOGL' in results
        
        # Check result types
        for symbol, event in results.items():
            assert isinstance(event, EarningsEvent)
            assert isinstance(event.days_to_earnings, int)
            assert event.symbol == symbol
            assert isinstance(event.earnings_date, datetime)
        
        # Check past earnings has reaction classification
        assert results['GOOGL'].post_reaction is not None
        
        # Check future earnings has no reaction
        assert results['AAPL'].post_reaction is None
    
    def test_earnings_event_dataclass(self):
        """Test EarningsEvent dataclass structure"""
        event = EarningsEvent(
            symbol='TEST',
            earnings_date=datetime(2024, 2, 15),
            days_to_earnings=5,
            post_reaction='Bullish'
        )
        
        assert event.symbol == 'TEST'
        assert event.earnings_date == datetime(2024, 2, 15)
        assert event.days_to_earnings == 5
        assert event.post_reaction == 'Bullish'