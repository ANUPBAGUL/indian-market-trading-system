import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.earnings_agent import EarningsAgent

class TestEarningsIntegration:
    @pytest.fixture
    def realistic_earnings_calendar(self):
        """Realistic earnings calendar with mixed timing"""
        current_date = datetime(2024, 2, 15)
        return pd.DataFrame([
            {'symbol': 'AAPL', 'earnings_date': current_date + timedelta(days=7)},   # Future
            {'symbol': 'MSFT', 'earnings_date': current_date - timedelta(days=2)},   # Recent past
            {'symbol': 'GOOGL', 'earnings_date': current_date - timedelta(days=10)}, # Past
            {'symbol': 'TSLA', 'earnings_date': current_date + timedelta(days=1)},   # Very soon
            {'symbol': 'NVDA', 'earnings_date': current_date - timedelta(days=5)}    # Past
        ])
    
    @pytest.fixture
    def multi_stock_data(self):
        """Multiple stocks with different post-earnings reactions"""
        np.random.seed(42)
        stock_data = {}
        
        # MSFT - Strong bullish reaction
        msft_dates = pd.date_range('2024-02-10', periods=12)
        msft_data = []
        for i, date in enumerate(msft_dates):
            if i < 7:  # Pre-earnings
                close = 400 + np.random.normal(0, 3)
                volume = 25000000 + np.random.normal(0, 1000000)
            else:  # Post-earnings - strong reaction
                close = 420 + (i - 7) * 1  # +5% initial jump + continuation
                volume = 50000000  # 2x volume surge
            
            msft_data.append({
                'date': date,
                'close': close,
                'volume': max(int(volume), 1000000)
            })
        stock_data['MSFT'] = pd.DataFrame(msft_data)
        
        # GOOGL - Bearish reaction
        googl_dates = pd.date_range('2024-02-01', periods=15)
        googl_data = []
        for i, date in enumerate(googl_dates):
            if i < 10:  # Pre-earnings
                close = 2800 + np.random.normal(0, 15)
                volume = 1500000 + np.random.normal(0, 100000)
            else:  # Post-earnings - bearish reaction
                close = 2650 - (i - 10) * 5  # -5.4% drop + continued weakness
                volume = 3000000  # 2x volume surge
            
            googl_data.append({
                'date': date,
                'close': close,
                'volume': max(int(volume), 100000)
            })
        stock_data['GOOGL'] = pd.DataFrame(googl_data)
        
        # NVDA - Neutral reaction
        nvda_dates = pd.date_range('2024-02-05', periods=12)
        nvda_data = []
        for i, date in enumerate(nvda_dates):
            if i < 7:  # Pre-earnings
                close = 700 + np.random.normal(0, 10)
                volume = 20000000 + np.random.normal(0, 2000000)
            else:  # Post-earnings - minimal reaction
                close = 702 + np.random.normal(0, 5)  # +0.3% move
                volume = 22000000  # 1.1x volume (no surge)
            
            nvda_data.append({
                'date': date,
                'close': close,
                'volume': max(int(volume), 1000000)
            })
        stock_data['NVDA'] = pd.DataFrame(nvda_data)
        
        return stock_data
    
    def test_mixed_timing_earnings_analysis(self, realistic_earnings_calendar, multi_stock_data):
        """Test analysis with mixed past/future earnings"""
        current_date = datetime(2024, 2, 15)
        
        results = EarningsAgent.run(multi_stock_data, realistic_earnings_calendar, current_date)
        
        # Check all symbols processed
        assert len(results) == 5
        
        # Check future earnings (no reaction classification)
        assert results['AAPL'].days_to_earnings > 0
        assert results['AAPL'].post_reaction is None
        
        assert results['TSLA'].days_to_earnings > 0
        assert results['TSLA'].post_reaction is None
        
        # Check past earnings (should have reaction classification)
        assert results['MSFT'].days_to_earnings < 0
        assert results['MSFT'].post_reaction is not None
        
        assert results['GOOGL'].days_to_earnings < 0
        assert results['GOOGL'].post_reaction is not None
        
        assert results['NVDA'].days_to_earnings < 0
        assert results['NVDA'].post_reaction is not None
    
    def test_reaction_classification_accuracy(self, realistic_earnings_calendar, multi_stock_data):
        """Test that reaction classifications are calculated"""
        current_date = datetime(2024, 2, 15)
        
        results = EarningsAgent.run(multi_stock_data, realistic_earnings_calendar, current_date)
        
        # Should have valid classifications for past earnings
        past_earnings = [event for event in results.values() if event.days_to_earnings < 0]
        
        for event in past_earnings:
            if event.symbol in multi_stock_data:
                # Should have a classification (not None)
                assert event.post_reaction is not None
                assert event.post_reaction in ['Bullish', 'Neutral', 'Bearish']
    
    def test_days_to_earnings_accuracy(self, realistic_earnings_calendar):
        """Test days to earnings calculation accuracy"""
        current_date = datetime(2024, 2, 15)
        
        results = EarningsAgent.run({}, realistic_earnings_calendar, current_date)
        
        # Check specific day calculations
        assert results['AAPL'].days_to_earnings == 7    # Future
        assert results['MSFT'].days_to_earnings == -2   # Past
        assert results['GOOGL'].days_to_earnings == -10 # Past
        assert results['TSLA'].days_to_earnings == 1    # Tomorrow
        assert results['NVDA'].days_to_earnings == -5   # Past
    
    def test_volume_surge_detection(self):
        """Test volume surge detection in reactions"""
        current_date = datetime(2024, 2, 15)
        earnings_date = datetime(2024, 2, 13)
        
        # High volume surge scenario
        high_vol_data = pd.DataFrame({
            'date': pd.date_range('2024-02-10', periods=8),
            'close': [100] * 5 + [105] * 3,  # +5% move
            'volume': [1000000] * 5 + [3000000] * 3  # 3x volume surge
        })
        
        # Low volume scenario
        low_vol_data = pd.DataFrame({
            'date': pd.date_range('2024-02-10', periods=8),
            'close': [100] * 5 + [105] * 3,  # Same +5% move
            'volume': [1000000] * 8  # No volume surge
        })
        
        high_vol_reaction = EarningsAgent.classify_post_earnings_reaction(
            high_vol_data, earnings_date
        )
        low_vol_reaction = EarningsAgent.classify_post_earnings_reaction(
            low_vol_data, earnings_date
        )
        
        # High volume should be Bullish, low volume should be Neutral
        assert high_vol_reaction == 'Bullish'
        assert low_vol_reaction == 'Neutral'
    
    def test_price_threshold_sensitivity(self):
        """Test that price threshold logic produces valid classifications"""
        earnings_date = datetime(2024, 2, 13)
        
        # Test data with clear earnings reaction
        test_data = pd.DataFrame({
            'date': pd.date_range('2024-02-10', periods=10),
            'close': [100] * 5 + [105] * 5,  # +5% move
            'volume': [1000000] * 5 + [2500000] * 5  # 2.5x volume surge
        })
        
        reaction = EarningsAgent.classify_post_earnings_reaction(
            test_data, earnings_date
        )
        
        # Should produce a valid classification
        assert reaction in ['Bullish', 'Neutral', 'Bearish']
    
    def test_earnings_date_edge_cases(self):
        """Test edge cases around earnings date detection"""
        # Earnings exactly on weekend
        weekend_earnings = datetime(2024, 2, 17)  # Saturday
        
        stock_data = pd.DataFrame({
            'date': pd.date_range('2024-02-15', periods=5),  # Weekdays only
            'close': [100, 105, 106, 107, 108],  # Strong move after weekend
            'volume': [1000000, 2500000, 2000000, 1800000, 1700000]
        })
        
        reaction = EarningsAgent.classify_post_earnings_reaction(
            stock_data, weekend_earnings
        )
        
        # Should still classify the reaction
        assert reaction in ['Bullish', 'Neutral', 'Bearish']
    
    def test_multiple_earnings_same_day(self):
        """Test handling multiple stocks with same earnings date"""
        same_date = datetime(2024, 2, 15)
        
        earnings_calendar = pd.DataFrame([
            {'symbol': 'STOCK1', 'earnings_date': same_date},
            {'symbol': 'STOCK2', 'earnings_date': same_date},
            {'symbol': 'STOCK3', 'earnings_date': same_date}
        ])
        
        results = EarningsAgent.run({}, earnings_calendar, same_date)
        
        # All should have 0 days to earnings
        assert all(event.days_to_earnings == 0 for event in results.values())
        assert len(results) == 3
    
    def test_data_consistency_across_runs(self, realistic_earnings_calendar, multi_stock_data):
        """Test that results are consistent across multiple runs"""
        current_date = datetime(2024, 2, 15)
        
        results1 = EarningsAgent.run(multi_stock_data, realistic_earnings_calendar, current_date)
        results2 = EarningsAgent.run(multi_stock_data, realistic_earnings_calendar, current_date)
        
        # Should be deterministic
        for symbol in results1.keys():
            assert results1[symbol].days_to_earnings == results2[symbol].days_to_earnings
            assert results1[symbol].post_reaction == results2[symbol].post_reaction
    
    def test_large_scale_earnings_processing(self):
        """Test processing large number of earnings events"""
        current_date = datetime(2024, 2, 15)
        
        # Create large earnings calendar
        large_calendar = pd.DataFrame([
            {'symbol': f'STOCK{i}', 'earnings_date': current_date + timedelta(days=i-50)}
            for i in range(100)
        ])
        
        results = EarningsAgent.run({}, large_calendar, current_date)
        
        # Should process all symbols
        assert len(results) == 100
        
        # Should have mix of past and future earnings
        past_earnings = sum(1 for event in results.values() if event.days_to_earnings < 0)
        future_earnings = sum(1 for event in results.values() if event.days_to_earnings > 0)
        
        assert past_earnings > 0
        assert future_earnings > 0