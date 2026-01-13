import pytest
import pandas as pd
import numpy as np

from src.features import FeatureComputer

class TestFeatureComputer:
    @pytest.fixture
    def sample_ohlcv(self):
        # 30 days of simple test data
        dates = pd.date_range('2024-01-01', periods=30)
        return pd.DataFrame({
            'date': dates,
            'open': [100.0] * 30,
            'high': [105.0] * 30,
            'low': [95.0] * 30,
            'close': [100.0] * 30,
            'volume': [1000000] * 30
        })
    
    def test_atr_calculation(self, sample_ohlcv):
        atr = FeatureComputer.atr(sample_ohlcv, period=14)
        
        # First 13 values should be NaN
        assert pd.isna(atr.iloc[:13]).all()
        
        # 14th value should be 10.0 (high-low = 105-95 = 10)
        assert atr.iloc[13] == 10.0
        
        # All subsequent values should be 10.0 (constant range)
        assert (atr.iloc[14:] == 10.0).all()
    
    def test_sma_calculation(self, sample_ohlcv):
        sma = FeatureComputer.sma(sample_ohlcv['close'], period=20)
        
        # First 19 values should be NaN
        assert pd.isna(sma.iloc[:19]).all()
        
        # 20th value should be 100.0 (constant close price)
        assert sma.iloc[19] == 100.0
    
    def test_rvol_calculation(self, sample_ohlcv):
        rvol = FeatureComputer.rvol(sample_ohlcv, period=20)
        
        # First 19 values should be NaN
        assert pd.isna(rvol.iloc[:19]).all()
        
        # 20th value should be 1.0 (current volume / average volume = constant)
        assert rvol.iloc[19] == 1.0
    
    def test_compute_all(self, sample_ohlcv):
        result = FeatureComputer.compute_all(sample_ohlcv)
        
        # Check all feature columns exist
        assert 'atr_14' in result.columns
        assert 'sma_20' in result.columns
        assert 'sma_50' in result.columns
        assert 'rvol_20' in result.columns
        
        # Check original columns preserved
        assert 'close' in result.columns
        assert len(result) == len(sample_ohlcv)
    
    def test_no_lookahead_bias(self):
        # Test with changing prices to ensure no lookahead
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=25),
            'open': list(range(100, 125)),
            'high': list(range(105, 130)),
            'low': list(range(95, 120)),
            'close': list(range(100, 125)),
            'volume': [1000000] * 25
        })
        
        sma = FeatureComputer.sma(df['close'], period=20)
        
        # SMA at position 19 should only use data from positions 0-19
        expected_sma = df['close'].iloc[:20].mean()
        assert abs(sma.iloc[19] - expected_sma) < 0.01