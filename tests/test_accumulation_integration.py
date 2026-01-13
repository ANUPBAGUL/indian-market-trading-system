import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.features import FeatureComputer
from src.accumulation_agent import AccumulationAgent

class TestAccumulationIntegration:
    @pytest.fixture
    def accumulation_stock_data(self):
        """Create stock showing accumulation pattern"""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=50)
        
        data = []
        base_price = 100.0
        
        for i, date in enumerate(dates):
            if i < 20:
                # Normal phase
                price_change = np.random.normal(0, 0.02)
                volume = 1000000 + np.random.normal(0, 200000)
                range_mult = 1.0
            else:
                # Accumulation phase: tight range, high volume
                price_change = np.random.normal(0, 0.005)  # Low volatility
                volume = 2000000 + np.random.normal(0, 300000)  # High volume
                range_mult = 0.3  # Tight ranges
            
            base_price *= (1 + price_change)
            
            # Generate OHLC
            range_size = base_price * 0.03 * range_mult
            high = base_price + range_size
            low = base_price - range_size
            
            data.append({
                'symbol': 'ACCUM',
                'date': date,
                'open': base_price,
                'high': high,
                'low': low,
                'close': base_price,
                'volume': max(int(volume), 100000),
                'sector': 'Technology'
            })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def normal_stock_data(self):
        """Create stock with normal trading pattern"""
        np.random.seed(123)
        dates = pd.date_range('2024-01-01', periods=50)
        
        data = []
        base_price = 100.0
        
        for date in dates:
            # Consistent normal trading
            price_change = np.random.normal(0, 0.02)
            base_price *= (1 + price_change)
            
            range_size = base_price * 0.03
            high = base_price + range_size
            low = base_price - range_size
            volume = 1000000 + np.random.normal(0, 300000)
            
            data.append({
                'symbol': 'NORMAL',
                'date': date,
                'open': base_price,
                'high': high,
                'low': low,
                'close': base_price,
                'volume': max(int(volume), 100000),
                'sector': 'Technology'
            })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def outperforming_sector_data(self):
        """Create sector data that underperforms stocks"""
        dates = pd.date_range('2024-01-01', periods=50)
        
        data = []
        sector_price = 200.0
        
        for date in dates:
            # Sector declines slightly
            sector_price *= (1 + np.random.normal(-0.001, 0.01))
            
            data.append({
                'date': date,
                'sector': 'Technology',
                'sector_close': sector_price
            })
        
        return pd.DataFrame(data)
    
    def test_accumulation_vs_normal_detection(self, accumulation_stock_data, normal_stock_data, outperforming_sector_data):
        """Test that accumulation pattern scores higher than normal pattern"""
        # Compute features for both stocks
        accum_features = FeatureComputer.compute_all(accumulation_stock_data)
        normal_features = FeatureComputer.compute_all(normal_stock_data)
        
        # Run accumulation analysis
        accum_result = AccumulationAgent.run(accum_features, outperforming_sector_data)
        normal_result = AccumulationAgent.run(normal_features, outperforming_sector_data)
        
        # Accumulation pattern should score higher
        assert accum_result['accumulation_score'] > normal_result['accumulation_score']
    
    def test_evidence_flags_in_accumulation(self, accumulation_stock_data, outperforming_sector_data):
        """Test that accumulation pattern triggers evidence flags"""
        features = FeatureComputer.compute_all(accumulation_stock_data)
        result = AccumulationAgent.run(features, outperforming_sector_data)
        
        evidence = result['evidence']
        
        # Should detect some accumulation evidence
        evidence_count = sum([
            evidence.volume_absorption,
            evidence.volatility_compression,
            evidence.tight_base,
            evidence.relative_strength
        ])
        
        assert evidence_count > 0  # At least one flag should be active
    
    def test_volume_absorption_in_realistic_scenario(self, accumulation_stock_data):
        """Test volume absorption detection with realistic data"""
        features = FeatureComputer.compute_all(accumulation_stock_data)
        result = AccumulationAgent.run(features)
        
        # Check volume metrics
        volume_ratio = result['metrics']['volume_ratio']
        
        # Should calculate a valid volume ratio
        assert volume_ratio > 0  # Valid ratio calculated
    
    def test_volatility_compression_detection(self, accumulation_stock_data):
        """Test volatility compression with computed ATR"""
        features = FeatureComputer.compute_all(accumulation_stock_data)
        result = AccumulationAgent.run(features)
        
        # Should detect some level of compression
        compression_ratio = result['metrics']['compression_ratio']
        assert compression_ratio > 0  # Valid compression ratio calculated
    
    def test_relative_strength_calculation(self, accumulation_stock_data, outperforming_sector_data):
        """Test relative strength with real performance data"""
        features = FeatureComputer.compute_all(accumulation_stock_data)
        result = AccumulationAgent.run(features, outperforming_sector_data)
        
        # Should show positive relative performance
        rel_perf = result['metrics']['relative_performance']
        assert rel_perf != 0.0  # Should calculate actual relative performance
    
    def test_score_consistency(self, accumulation_stock_data, outperforming_sector_data):
        """Test that same data produces consistent scores"""
        features = FeatureComputer.compute_all(accumulation_stock_data)
        
        result1 = AccumulationAgent.run(features, outperforming_sector_data)
        result2 = AccumulationAgent.run(features, outperforming_sector_data)
        
        # Should be deterministic
        assert result1['accumulation_score'] == result2['accumulation_score']
        assert result1['evidence'].volume_absorption == result2['evidence'].volume_absorption
    
    def test_score_bounds(self, accumulation_stock_data, normal_stock_data):
        """Test that scores stay within 0-100 bounds"""
        accum_features = FeatureComputer.compute_all(accumulation_stock_data)
        normal_features = FeatureComputer.compute_all(normal_stock_data)
        
        accum_result = AccumulationAgent.run(accum_features)
        normal_result = AccumulationAgent.run(normal_features)
        
        # Check bounds
        assert 0 <= accum_result['accumulation_score'] <= 100
        assert 0 <= normal_result['accumulation_score'] <= 100
    
    def test_pipeline_integration(self, accumulation_stock_data, outperforming_sector_data):
        """Test full pipeline from raw data to accumulation score"""
        # Complete pipeline: raw data -> features -> accumulation analysis
        features = FeatureComputer.compute_all(accumulation_stock_data)
        result = AccumulationAgent.run(features, outperforming_sector_data)
        
        # Validate complete result structure
        assert isinstance(result['accumulation_score'], int)
        assert hasattr(result['evidence'], 'volume_absorption')
        assert hasattr(result['evidence'], 'volatility_compression')
        assert hasattr(result['evidence'], 'tight_base')
        assert hasattr(result['evidence'], 'relative_strength')
        
        # Validate metrics
        metrics = result['metrics']
        assert all(isinstance(v, (int, float)) for v in metrics.values())
        assert all(not np.isnan(v) for v in metrics.values() if v != 0.0)