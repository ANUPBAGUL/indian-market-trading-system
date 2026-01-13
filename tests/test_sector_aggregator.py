import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.sector_aggregator import SectorAggregator

class TestSectorAggregator:
    @pytest.fixture
    def sample_stock_data(self):
        return pd.DataFrame({
            'date': [datetime(2024, 1, 15)] * 4,
            'sector': ['Tech', 'Tech', 'Health', 'Health'],
            'symbol': ['AAPL', 'MSFT', 'JNJ', 'PFE'],
            'close': [100.0, 200.0, 150.0, 50.0],
            'volume': [1000000, 2000000, 500000, 1500000],
            'sma_20': [95.0, 210.0, 140.0, 55.0],
            'rvol_20': [1.2, 0.8, 1.5, 0.9]
        })
    
    def test_sector_close_volume_weighted(self, sample_stock_data):
        result = SectorAggregator.aggregate_sectors(sample_stock_data)
        
        # Tech sector: (100*1M + 200*2M) / (1M+2M) = 500M/3M = 166.67
        tech_close = result[result['sector'] == 'Tech']['sector_close'].iloc[0]
        assert abs(tech_close - 166.67) < 0.01
        
        # Health sector: (150*0.5M + 50*1.5M) / (0.5M+1.5M) = 150M/2M = 75.0
        health_close = result[result['sector'] == 'Health']['sector_close'].iloc[0]
        assert health_close == 75.0
    
    def test_sector_volume_sum(self, sample_stock_data):
        result = SectorAggregator.aggregate_sectors(sample_stock_data)
        
        # Tech sector: 1M + 2M = 3M
        tech_volume = result[result['sector'] == 'Tech']['sector_volume'].iloc[0]
        assert tech_volume == 3000000
        
        # Health sector: 0.5M + 1.5M = 2M
        health_volume = result[result['sector'] == 'Health']['sector_volume'].iloc[0]
        assert health_volume == 2000000
    
    def test_sector_rvol_average(self, sample_stock_data):
        result = SectorAggregator.aggregate_sectors(sample_stock_data)
        
        # Tech sector: (1.2 + 0.8) / 2 = 1.0
        tech_rvol = result[result['sector'] == 'Tech']['sector_rvol'].iloc[0]
        assert tech_rvol == 1.0
        
        # Health sector: (1.5 + 0.9) / 2 = 1.2
        health_rvol = result[result['sector'] == 'Health']['sector_rvol'].iloc[0]
        assert health_rvol == 1.2
    
    def test_sector_breadth_percentage(self, sample_stock_data):
        result = SectorAggregator.aggregate_sectors(sample_stock_data)
        
        # Tech sector: AAPL (100>95=True), MSFT (200>210=False) = 1/2 = 50%
        tech_breadth = result[result['sector'] == 'Tech']['sector_breadth'].iloc[0]
        assert tech_breadth == 50.0
        
        # Health sector: JNJ (150>140=True), PFE (50>55=False) = 1/2 = 50%
        health_breadth = result[result['sector'] == 'Health']['sector_breadth'].iloc[0]
        assert health_breadth == 50.0
    
    def test_stock_count(self, sample_stock_data):
        result = SectorAggregator.aggregate_sectors(sample_stock_data)
        
        # Both sectors should have 2 stocks each
        assert all(result['stock_count'] == 2)
    
    def test_get_sector_stats(self, sample_stock_data):
        sector_df = SectorAggregator.aggregate_sectors(sample_stock_data)
        stats = SectorAggregator.get_sector_stats(sector_df, '2024-01-15')
        
        # Should return data for the specified date
        assert len(stats) == 2
        assert 'Tech' in stats['sector'].values
        assert 'Health' in stats['sector'].values
        
        # Should be sorted by volume (Tech has higher volume)
        assert stats.iloc[0]['sector'] == 'Tech'
    
    def test_empty_date(self, sample_stock_data):
        sector_df = SectorAggregator.aggregate_sectors(sample_stock_data)
        stats = SectorAggregator.get_sector_stats(sector_df, '2024-12-31')
        
        # Should return empty DataFrame for non-existent date
        assert len(stats) == 0
    
    def test_missing_features(self):
        # Test with data missing SMA and RVOL columns
        data = pd.DataFrame({
            'date': [datetime(2024, 1, 15)] * 2,
            'sector': ['Tech', 'Tech'],
            'symbol': ['AAPL', 'MSFT'],
            'close': [100.0, 200.0],
            'volume': [1000000, 2000000]
        })
        
        result = SectorAggregator.aggregate_sectors(data)
        
        # Should handle missing columns gracefully
        assert pd.isna(result['sector_rvol'].iloc[0])
        assert result['sector_breadth'].iloc[0] == 0.0