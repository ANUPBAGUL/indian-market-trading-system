import pytest
import pandas as pd
import numpy as np
import tempfile
import os

from src.data_loader import DataLoader
from src.features import FeatureComputer

class TestIntegration:
    @pytest.fixture
    def extended_sample_data(self):
        # 60 days of realistic test data
        dates = pd.date_range('2024-01-01', periods=60)
        np.random.seed(42)
        
        data = []
        base_price = 100.0
        
        for i, date in enumerate(dates):
            # Simple price evolution
            base_price += np.random.normal(0, 1)
            
            data.append({
                'symbol': 'TEST',
                'date': date.strftime('%Y-%m-%d'),
                'open': base_price + np.random.normal(0, 0.5),
                'high': base_price + abs(np.random.normal(2, 1)),
                'low': base_price - abs(np.random.normal(2, 1)),
                'close': base_price,
                'volume': int(1000000 + np.random.normal(0, 200000)),
                'sector': 'Technology'
            })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def temp_data_file(self, extended_sample_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            extended_sample_data.to_csv(f.name, index=False)
            yield f.name
        os.unlink(f.name)
    
    def test_full_pipeline(self, temp_data_file):
        """Test complete data loading -> feature computation pipeline"""
        # Load data
        loader = DataLoader()
        df = loader.load_csv(temp_data_file)
        
        # Compute features
        features_df = FeatureComputer.compute_all(df)
        
        # Validate pipeline results
        assert len(features_df) == 60
        assert 'atr_14' in features_df.columns
        assert 'sma_20' in features_df.columns
        assert 'sma_50' in features_df.columns
        assert 'rvol_20' in features_df.columns
        
        # Check feature timing
        assert pd.isna(features_df['atr_14'].iloc[12])  # Day 13 should be NaN
        assert not pd.isna(features_df['atr_14'].iloc[13])  # Day 14 should have value
        
        assert pd.isna(features_df['sma_20'].iloc[18])  # Day 19 should be NaN
        assert not pd.isna(features_df['sma_20'].iloc[19])  # Day 20 should have value
        
        assert pd.isna(features_df['sma_50'].iloc[48])  # Day 49 should be NaN
        assert not pd.isna(features_df['sma_50'].iloc[49])  # Day 50 should have value
    
    def test_feature_consistency(self, extended_sample_data):
        """Test that features are consistent across multiple computations"""
        features1 = FeatureComputer.compute_all(extended_sample_data)
        features2 = FeatureComputer.compute_all(extended_sample_data)
        
        # Results should be identical
        pd.testing.assert_frame_equal(features1, features2)
    
    def test_realistic_feature_ranges(self, extended_sample_data):
        """Test that computed features fall within realistic ranges"""
        features_df = FeatureComputer.compute_all(extended_sample_data)
        
        # ATR should be positive
        atr_values = features_df['atr_14'].dropna()
        assert (atr_values > 0).all()
        
        # RVOL should be positive
        rvol_values = features_df['rvol_20'].dropna()
        assert (rvol_values > 0).all()
        
        # SMAs should be close to price range
        price_min = extended_sample_data['close'].min()
        price_max = extended_sample_data['close'].max()
        
        sma20_values = features_df['sma_20'].dropna()
        assert (sma20_values >= price_min * 0.8).all()
        assert (sma20_values <= price_max * 1.2).all()