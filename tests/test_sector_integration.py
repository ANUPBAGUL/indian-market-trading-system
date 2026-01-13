import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.data_loader import DataLoader
from src.features import FeatureComputer
from src.sector_aggregator import SectorAggregator

class TestSectorIntegration:
    @pytest.fixture
    def multi_sector_data(self):
        """Create 30 days of multi-sector stock data"""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=30)
        
        stocks = [
            {'symbol': 'AAPL', 'sector': 'Technology', 'base_price': 180, 'base_volume': 45000000},
            {'symbol': 'MSFT', 'sector': 'Technology', 'base_price': 380, 'base_volume': 28000000},
            {'symbol': 'JNJ', 'sector': 'Healthcare', 'base_price': 160, 'base_volume': 8500000},
            {'symbol': 'PFE', 'sector': 'Healthcare', 'base_price': 30, 'base_volume': 42000000},
            {'symbol': 'JPM', 'sector': 'Financial', 'base_price': 170, 'base_volume': 12000000}
        ]
        
        all_data = []
        for stock in stocks:
            price = stock['base_price']
            for date in dates:
                # Simple price evolution
                price *= (1 + np.random.normal(0, 0.02))
                
                all_data.append({
                    'symbol': stock['symbol'],
                    'date': date,
                    'open': price * (1 + np.random.normal(0, 0.005)),
                    'high': price * (1 + abs(np.random.normal(0.01, 0.005))),
                    'low': price * (1 - abs(np.random.normal(0.01, 0.005))),
                    'close': price,
                    'volume': int(stock['base_volume'] * (1 + np.random.normal(0, 0.3))),
                    'sector': stock['sector']
                })
        
        return pd.DataFrame(all_data)
    
    def test_full_pipeline_to_sectors(self, multi_sector_data):
        """Test complete pipeline: raw data -> features -> sector aggregates"""
        # Compute features
        features_df = FeatureComputer.compute_all(multi_sector_data)
        
        # Aggregate to sectors
        sector_df = SectorAggregator.aggregate_sectors(features_df)
        
        # Validate pipeline results
        assert len(sector_df) > 0
        assert 'sector_close' in sector_df.columns
        assert 'sector_volume' in sector_df.columns
        assert 'sector_rvol' in sector_df.columns
        assert 'sector_breadth' in sector_df.columns
        
        # Should have 3 sectors
        unique_sectors = sector_df['sector'].unique()
        assert len(unique_sectors) == 3
        assert 'Technology' in unique_sectors
        assert 'Healthcare' in unique_sectors
        assert 'Financial' in unique_sectors
    
    def test_sector_metrics_validity(self, multi_sector_data):
        """Test that sector metrics fall within realistic ranges"""
        features_df = FeatureComputer.compute_all(multi_sector_data)
        sector_df = SectorAggregator.aggregate_sectors(features_df)
        
        # Filter to days where features are available
        valid_data = sector_df.dropna(subset=['sector_rvol', 'sector_breadth'])
        
        # Sector close should be positive
        assert (valid_data['sector_close'] > 0).all()
        
        # Sector volume should be positive
        assert (valid_data['sector_volume'] > 0).all()
        
        # Sector RVOL should be positive
        assert (valid_data['sector_rvol'] > 0).all()
        
        # Sector breadth should be 0-100%
        assert (valid_data['sector_breadth'] >= 0).all()
        assert (valid_data['sector_breadth'] <= 100).all()
    
    def test_sector_consistency_across_dates(self, multi_sector_data):
        """Test that sector aggregation is consistent across multiple dates"""
        features_df = FeatureComputer.compute_all(multi_sector_data)
        sector_df = SectorAggregator.aggregate_sectors(features_df)
        
        # Each date should have same number of sectors
        date_sector_counts = sector_df.groupby('date').size()
        assert date_sector_counts.nunique() == 1  # All dates have same count
        
        # Each sector should appear on every date
        for sector in ['Technology', 'Healthcare', 'Financial']:
            sector_dates = sector_df[sector_df['sector'] == sector]['date'].nunique()
            total_dates = sector_df['date'].nunique()
            assert sector_dates == total_dates
    
    def test_sector_breadth_calculation(self, multi_sector_data):
        """Test sector breadth calculation with known data"""
        # Use only last few days where SMA20 is available
        features_df = FeatureComputer.compute_all(multi_sector_data)
        last_date = features_df['date'].max()
        
        # Get last day data
        last_day = features_df[features_df['date'] == last_date]
        
        # Calculate expected breadth for Technology sector manually
        tech_stocks = last_day[last_day['sector'] == 'Technology']
        if len(tech_stocks) > 0 and not tech_stocks['sma_20'].isna().all():
            expected_breadth = (tech_stocks['close'] > tech_stocks['sma_20']).mean() * 100
            
            # Get computed breadth
            sector_df = SectorAggregator.aggregate_sectors(features_df)
            last_sector_day = sector_df[sector_df['date'] == last_date]
            tech_breadth = last_sector_day[last_sector_day['sector'] == 'Technology']['sector_breadth'].iloc[0]
            
            assert abs(tech_breadth - expected_breadth) < 0.01
    
    def test_volume_weighted_close(self, multi_sector_data):
        """Test that sector close is properly volume-weighted"""
        # Use simple test case
        test_data = pd.DataFrame({
            'date': [datetime(2024, 1, 15)] * 2,
            'sector': ['Test', 'Test'],
            'symbol': ['A', 'B'],
            'close': [100.0, 200.0],
            'volume': [1000000, 2000000],  # B has 2x volume of A
            'sma_20': [90.0, 190.0],
            'rvol_20': [1.0, 1.0]
        })
        
        sector_df = SectorAggregator.aggregate_sectors(test_data)
        
        # Expected: (100*1M + 200*2M) / (1M+2M) = 500M/3M = 166.67
        expected_close = (100 * 1000000 + 200 * 2000000) / (1000000 + 2000000)
        actual_close = sector_df['sector_close'].iloc[0]
        
        assert abs(actual_close - expected_close) < 0.01