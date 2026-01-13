import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.accumulation_agent import AccumulationAgent, AccumulationEvidence

class TestAccumulationAgent:
    @pytest.fixture
    def sample_stock_data(self):
        """Basic stock data for testing"""
        dates = pd.date_range('2024-01-01', periods=30)
        return pd.DataFrame({
            'date': dates,
            'symbol': ['TEST'] * 30,
            'open': [100.0] * 30,
            'high': [105.0] * 30,
            'low': [95.0] * 30,
            'close': [100.0] * 30,
            'volume': [1000000] * 30,
            'atr_14': [5.0] * 30
        })
    
    @pytest.fixture
    def sector_data(self):
        """Basic sector data for testing"""
        dates = pd.date_range('2024-01-01', periods=30)
        return pd.DataFrame({
            'date': dates,
            'sector': ['Technology'] * 30,
            'sector_close': [200.0] * 30
        })
    
    def test_volume_absorption_detection(self):
        """Test volume absorption calculation"""
        # High volume, low volatility scenario
        data = pd.DataFrame({
            'volume': [1000000] * 19 + [2000000],  # 2x volume on last day
            'high': [105.0] * 19 + [101.0],        # Lower range on high volume day
            'low': [95.0] * 19 + [99.0],
            'close': [100.0] * 20
        })
        
        absorption, vol_ratio = AccumulationAgent.calculate_volume_absorption(data)
        
        assert vol_ratio > 1.8  # Approximately 2x average volume
        assert absorption == True  # High volume + low volatility
    
    def test_volatility_compression_detection(self):
        """Test volatility compression calculation"""
        # Create data with declining ATR
        atr_values = [10.0] * 20 + [5.0] * 10  # ATR drops from 10 to 5
        data = pd.DataFrame({
            'atr_14': atr_values
        })
        
        compression, comp_ratio = AccumulationAgent.calculate_volatility_compression(data)
        
        assert comp_ratio == 0.5  # 50% compression
        assert compression == True  # >30% compression
    
    def test_tight_base_detection(self):
        """Test tight base calculation"""
        # Tight range near highs
        data = pd.DataFrame({
            'high': [100.0] * 15,
            'low': [96.0] * 15,    # 4% range
            'close': [99.0] * 15   # Close to highs
        })
        
        tight_base, range_pct = AccumulationAgent.calculate_tight_base(data)
        
        assert range_pct < 0.08  # <8% range
        assert tight_base == True  # Tight base detected
    
    def test_relative_strength_calculation(self):
        """Test relative strength vs sector"""
        # Stock outperforming sector
        stock_data = pd.DataFrame({
            'close': [100.0] + [110.0] * 19  # +10% performance
        })
        
        sector_data = pd.DataFrame({
            'sector_close': [200.0] + [204.0] * 19  # +2% performance
        })
        
        strength, rel_perf = AccumulationAgent.calculate_relative_strength(
            stock_data, sector_data
        )
        
        assert rel_perf > 0.05  # Outperforming by >5%
        assert strength == True  # Relative strength detected
    
    def test_accumulation_score_calculation(self):
        """Test score calculation logic"""
        # All evidence flags active
        evidence = AccumulationEvidence(
            volume_absorption=True,
            volatility_compression=True,
            tight_base=True,
            relative_strength=True
        )
        
        score = AccumulationAgent.calculate_accumulation_score(
            evidence, 2.5, 0.4, 0.04, 0.06  # Strong metrics
        )
        
        # Base: 4 × 25 = 100, Bonus: 4 × 10 = 40, Max: 100
        assert score == 100
    
    def test_partial_evidence_scoring(self):
        """Test scoring with partial evidence"""
        evidence = AccumulationEvidence(
            volume_absorption=True,
            volatility_compression=False,
            tight_base=True,
            relative_strength=False
        )
        
        score = AccumulationAgent.calculate_accumulation_score(
            evidence, 1.8, 0.8, 0.06, 0.01  # Weak metrics
        )
        
        # Base: 2 × 25 = 50, No bonus points
        assert score == 50
    
    def test_run_method_complete(self, sample_stock_data, sector_data):
        """Test complete run method"""
        result = AccumulationAgent.run(sample_stock_data, sector_data)
        
        # Check return structure
        assert 'accumulation_score' in result
        assert 'evidence' in result
        assert 'metrics' in result
        
        # Check types
        assert isinstance(result['accumulation_score'], int)
        assert isinstance(result['evidence'], AccumulationEvidence)
        assert isinstance(result['metrics'], dict)
        
        # Check metrics keys
        metrics = result['metrics']
        assert 'volume_ratio' in metrics
        assert 'compression_ratio' in metrics
        assert 'range_percentage' in metrics
        assert 'relative_performance' in metrics
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data"""
        minimal_data = pd.DataFrame({
            'close': [100, 101, 102],
            'volume': [1000000, 1100000, 1200000]
        })
        
        result = AccumulationAgent.run(minimal_data)
        
        assert result['accumulation_score'] == 0
        assert not result['evidence'].volume_absorption
        assert not result['evidence'].volatility_compression
        assert not result['evidence'].tight_base
        assert not result['evidence'].relative_strength
    
    def test_no_sector_data_handling(self, sample_stock_data):
        """Test handling when no sector data provided"""
        result = AccumulationAgent.run(sample_stock_data, None)
        
        # Should still work, just no relative strength
        assert 'accumulation_score' in result
        assert not result['evidence'].relative_strength
        assert result['metrics']['relative_performance'] == 0.0