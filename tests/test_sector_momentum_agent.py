import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.sector_momentum_agent import SectorMomentumAgent, SectorMetrics

class TestSectorMomentumAgent:
    @pytest.fixture
    def sample_sector_data(self):
        """Basic sector data for testing"""
        dates = pd.date_range('2024-01-01', periods=25)
        data = []
        
        for date in dates:
            # Technology sector
            data.append({
                'date': date,
                'sector': 'Technology',
                'sector_close': 100.0,
                'sector_breadth': 70.0,
                'sector_rvol': 1.3
            })
            
            # Healthcare sector
            data.append({
                'date': date,
                'sector': 'Healthcare',
                'sector_close': 80.0,
                'sector_breadth': 50.0,
                'sector_rvol': 1.0
            })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def sample_index_data(self):
        """Basic index data for testing"""
        dates = pd.date_range('2024-01-01', periods=25)
        return pd.DataFrame({
            'date': dates,
            'close': [200.0] * 25,
            'volume': [1000000] * 25
        })
    
    def test_relative_performance_calculation(self):
        """Test relative performance vs index"""
        # Sector outperforming index
        sector_df = pd.DataFrame({
            'sector': ['Tech'] * 20,
            'sector_close': [100.0] * 10 + [110.0] * 10  # +10% performance
        })
        
        index_df = pd.DataFrame({
            'close': [200.0] * 10 + [204.0] * 10  # +2% performance
        })
        
        rel_perf = SectorMomentumAgent.calculate_relative_performance(
            sector_df, index_df, lookback=20
        )
        
        assert 'Tech' in rel_perf
        assert rel_perf['Tech'] > 0.05  # Should show ~8% outperformance
    
    def test_breadth_scoring_calculation(self):
        """Test breadth scoring logic"""
        # High breadth with improving trend
        sector_df = pd.DataFrame({
            'sector': ['Tech'] * 10,
            'sector_breadth': [60.0] * 5 + [80.0] * 5  # Improving breadth
        })
        
        breadth_scores = SectorMomentumAgent.calculate_breadth_scoring(sector_df)
        
        assert 'Tech' in breadth_scores
        assert 0 <= breadth_scores['Tech'] <= 1
        assert breadth_scores['Tech'] > 0.5  # Should be high due to good breadth
    
    def test_rvol_scoring_tiers(self):
        """Test RVOL scoring tiers"""
        # High RVOL sector
        high_rvol_df = pd.DataFrame({
            'sector': ['Tech'] * 10,
            'sector_rvol': [1.6] * 10  # High activity
        })
        
        # Low RVOL sector
        low_rvol_df = pd.DataFrame({
            'sector': ['Energy'] * 10,
            'sector_rvol': [0.8] * 10  # Low activity
        })
        
        combined_df = pd.concat([high_rvol_df, low_rvol_df])
        rvol_scores = SectorMomentumAgent.calculate_rvol_scoring(combined_df)
        
        assert rvol_scores['Tech'] == 1.0  # High activity tier
        assert rvol_scores['Energy'] == 0.2  # Low activity tier
    
    def test_sector_score_calculation(self):
        """Test final sector score calculation"""
        rel_perf = {'Tech': 0.06}  # 6% outperformance = 40 points
        breadth_scores = {'Tech': 0.8}  # 0.8 * 35 = 28 points
        rvol_scores = {'Tech': 1.0}  # 1.0 * 25 = 25 points
        
        final_scores = SectorMomentumAgent.calculate_sector_scores(
            rel_perf, breadth_scores, rvol_scores
        )
        
        assert final_scores['Tech'] == 93  # 40 + 28 + 25 = 93
    
    def test_score_bounds(self):
        """Test that scores stay within 0-100 bounds"""
        # Extreme positive case
        rel_perf = {'Tech': 0.10}  # Very high outperformance
        breadth_scores = {'Tech': 1.0}  # Perfect breadth
        rvol_scores = {'Tech': 1.0}  # High RVOL
        
        final_scores = SectorMomentumAgent.calculate_sector_scores(
            rel_perf, breadth_scores, rvol_scores
        )
        
        assert 0 <= final_scores['Tech'] <= 100
    
    def test_negative_performance_scoring(self):
        """Test scoring for underperforming sectors"""
        rel_perf = {'Energy': -0.05}  # 5% underperformance = 0 points
        breadth_scores = {'Energy': 0.2}  # Poor breadth
        rvol_scores = {'Energy': 0.2}  # Low RVOL
        
        final_scores = SectorMomentumAgent.calculate_sector_scores(
            rel_perf, breadth_scores, rvol_scores
        )
        
        assert final_scores['Energy'] < 20  # Should be low score
    
    def test_run_method_complete(self, sample_sector_data, sample_index_data):
        """Test complete run method"""
        results = SectorMomentumAgent.run(sample_sector_data, sample_index_data)
        
        # Check return structure
        assert isinstance(results, dict)
        assert 'Technology' in results
        assert 'Healthcare' in results
        
        # Check result types
        for sector, metrics in results.items():
            assert isinstance(metrics, SectorMetrics)
            assert isinstance(metrics.sector_score, int)
            assert 0 <= metrics.sector_score <= 100
            assert isinstance(metrics.relative_performance, float)
            assert isinstance(metrics.breadth_score, float)
            assert isinstance(metrics.rvol_score, float)
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data"""
        minimal_sector_data = pd.DataFrame({
            'sector': ['Tech'] * 5,
            'sector_close': [100] * 5,
            'sector_breadth': [70] * 5,
            'sector_rvol': [1.2] * 5
        })
        
        minimal_index_data = pd.DataFrame({
            'close': [200] * 5
        })
        
        results = SectorMomentumAgent.run(minimal_sector_data, minimal_index_data)
        
        # Should return empty dict for insufficient data
        assert results == {}
    
    def test_missing_sectors_handling(self):
        """Test handling when sectors have different data availability"""
        rel_perf = {'Tech': 0.05, 'Health': 0.02}
        breadth_scores = {'Tech': 0.7}  # Missing Health
        rvol_scores = {'Health': 0.8}  # Missing Tech
        
        final_scores = SectorMomentumAgent.calculate_sector_scores(
            rel_perf, breadth_scores, rvol_scores
        )
        
        # Should handle missing data gracefully
        assert 'Tech' in final_scores
        assert 'Health' in final_scores
        assert final_scores['Tech'] > 0
        assert final_scores['Health'] > 0