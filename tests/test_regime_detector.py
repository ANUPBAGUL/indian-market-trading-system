import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.regime_detector import RegimeDetector

class TestRegimeDetector:
    @pytest.fixture
    def sample_index_data(self):
        # 70 days of simple test data for SMA50 calculation
        dates = pd.date_range('2024-01-01', periods=70)
        return pd.DataFrame({
            'date': dates,
            'symbol': ['SPY'] * 70,
            'close': [100.0] * 70  # Flat price for predictable results
        })
    
    @pytest.fixture
    def trending_data(self):
        # Data with clear upward trend
        dates = pd.date_range('2024-01-01', periods=70)
        prices = [100 + i * 2 for i in range(70)]  # +2 per day
        return pd.DataFrame({
            'date': dates,
            'symbol': ['SPY'] * 70,
            'close': prices
        })
    
    def test_calculate_index_trend(self, sample_index_data):
        sma = RegimeDetector.calculate_index_trend(sample_index_data, period=50)
        
        # First 49 values should be NaN
        assert pd.isna(sma.iloc[:49]).all()
        
        # 50th value should be 100.0 (constant price)
        assert sma.iloc[49] == 100.0
        
        # All subsequent values should be 100.0
        assert (sma.iloc[50:] == 100.0).all()
    
    def test_calculate_trend_slope(self):
        # Create simple SMA series
        sma = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110])
        
        slope = RegimeDetector.calculate_trend_slope(sma, lookback=10)
        
        # First 10 values should be NaN
        assert pd.isna(slope.iloc[:10]).all()
        
        # 11th value: (110 - 100) / 10 = 1.0
        assert slope.iloc[10] == 1.0
    
    def test_classify_regime(self):
        slopes = pd.Series([2.0, 0.3, -0.3, -2.0, np.nan])
        
        regimes = RegimeDetector.classify_regime(slopes, slope_threshold=0.5)
        
        assert regimes.iloc[0] == 'risk_on'    # 2.0 > 0.5
        assert regimes.iloc[1] == 'neutral'    # 0.3 between -0.5 and 0.5
        assert regimes.iloc[2] == 'neutral'    # -0.3 between -0.5 and 0.5
        assert regimes.iloc[3] == 'risk_off'   # -2.0 < -0.5
        assert regimes.iloc[4] == 'neutral'    # NaN defaults to neutral
    
    def test_detect_regime_complete_pipeline(self, trending_data):
        result = RegimeDetector.detect_regime(trending_data)
        
        # Check all columns exist
        assert 'index_sma50' in result.columns
        assert 'trend_slope' in result.columns
        assert 'regime' in result.columns
        
        # Check data integrity
        assert len(result) == len(trending_data)
        
        # With upward trending data, should eventually show risk_on
        valid_regimes = result['regime'].dropna()
        assert 'risk_on' in valid_regimes.values
    
    def test_regime_timing(self, sample_index_data):
        result = RegimeDetector.detect_regime(sample_index_data)
        
        # SMA50 should be valid from day 50
        assert pd.isna(result['index_sma50'].iloc[48])
        assert not pd.isna(result['index_sma50'].iloc[49])
        
        # Trend slope should be valid from day 60 (50 + 10)
        assert pd.isna(result['trend_slope'].iloc[58])
        assert not pd.isna(result['trend_slope'].iloc[59])
        
        # Regime should follow trend slope timing
        assert result['regime'].iloc[58] == 'neutral'  # NaN slope = neutral
        assert result['regime'].iloc[59] != 'neutral' or result['trend_slope'].iloc[59] == 0
    
    def test_custom_parameters(self, trending_data):
        # Test with custom parameters
        result = RegimeDetector.detect_regime(
            trending_data, 
            sma_period=20, 
            slope_lookback=5, 
            slope_threshold=1.0
        )
        
        # Should have different timing with shorter periods
        assert not pd.isna(result['index_sma50'].iloc[19])  # SMA20 valid from day 20
        assert not pd.isna(result['trend_slope'].iloc[24])   # Slope valid from day 25
    
    def test_edge_cases(self):
        # Test with minimal data
        minimal_data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=5),
            'close': [100, 101, 102, 103, 104]
        })
        
        result = RegimeDetector.detect_regime(minimal_data)
        
        # Should handle gracefully without errors
        assert len(result) == 5
        assert 'regime' in result.columns
        
        # All regimes should be neutral (insufficient data)
        assert (result['regime'] == 'neutral').all()