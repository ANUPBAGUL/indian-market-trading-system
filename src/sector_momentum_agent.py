import pandas as pd
import numpy as np
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class SectorMetrics:
    """Sector momentum metrics"""
    relative_performance: float = 0.0
    breadth_score: float = 0.0
    rvol_score: float = 0.0
    sector_score: int = 0

class SectorMomentumAgent:
    """Identify leading sectors for rotation strategies"""
    
    @staticmethod
    def calculate_relative_performance(sector_df: pd.DataFrame, index_df: pd.DataFrame, 
                                     lookback: int = 20) -> Dict[str, float]:
        """Calculate sector performance vs index"""
        if len(sector_df) < lookback or len(index_df) < lookback:
            return {}
        
        # Get unique sectors
        sectors = sector_df['sector'].unique()
        relative_perf = {}
        
        # Index performance
        index_start = index_df['close'].iloc[-lookback]
        index_end = index_df['close'].iloc[-1]
        index_return = (index_end / index_start - 1) if index_start > 0 else 0
        
        for sector in sectors:
            sector_data = sector_df[sector_df['sector'] == sector].tail(lookback)
            if len(sector_data) >= lookback:
                sector_start = sector_data['sector_close'].iloc[0]
                sector_end = sector_data['sector_close'].iloc[-1]
                sector_return = (sector_end / sector_start - 1) if sector_start > 0 else 0
                
                # Relative performance vs index
                relative_perf[sector] = sector_return - index_return
        
        return relative_perf
    
    @staticmethod
    def calculate_breadth_scoring(sector_df: pd.DataFrame, lookback: int = 10) -> Dict[str, float]:
        """Score sectors based on breadth trend"""
        if len(sector_df) < lookback:
            return {}
        
        sectors = sector_df['sector'].unique()
        breadth_scores = {}
        
        for sector in sectors:
            sector_data = sector_df[sector_df['sector'] == sector].tail(lookback)
            if len(sector_data) >= lookback:
                # Average breadth over lookback period
                avg_breadth = sector_data['sector_breadth'].mean()
                
                # Breadth trend (recent vs earlier)
                recent_breadth = sector_data['sector_breadth'].tail(5).mean()
                earlier_breadth = sector_data['sector_breadth'].head(5).mean()
                breadth_trend = recent_breadth - earlier_breadth
                
                # Combined breadth score (level + trend)
                breadth_score = (avg_breadth / 100) * 0.7 + (breadth_trend / 100) * 0.3
                breadth_scores[sector] = max(0, min(1, breadth_score))  # Clamp 0-1
        
        return breadth_scores
    
    @staticmethod
    def calculate_rvol_scoring(sector_df: pd.DataFrame, lookback: int = 10) -> Dict[str, float]:
        """Score sectors based on relative volume"""
        if len(sector_df) < lookback:
            return {}
        
        sectors = sector_df['sector'].unique()
        rvol_scores = {}
        
        for sector in sectors:
            sector_data = sector_df[sector_df['sector'] == sector].tail(lookback)
            if len(sector_data) >= lookback:
                # Average RVOL over lookback period
                avg_rvol = sector_data['sector_rvol'].mean()
                
                # Score based on RVOL level (1.0 = normal, >1.5 = high activity)
                if avg_rvol >= 1.5:
                    rvol_score = 1.0  # High activity
                elif avg_rvol >= 1.2:
                    rvol_score = 0.7  # Elevated activity
                elif avg_rvol >= 1.0:
                    rvol_score = 0.5  # Normal activity
                else:
                    rvol_score = 0.2  # Low activity
                
                rvol_scores[sector] = rvol_score
        
        return rvol_scores
    
    @classmethod
    def calculate_sector_scores(cls, relative_perf: Dict[str, float], 
                               breadth_scores: Dict[str, float],
                               rvol_scores: Dict[str, float]) -> Dict[str, int]:
        """Calculate final sector scores 0-100"""
        all_sectors = set(relative_perf.keys()) | set(breadth_scores.keys()) | set(rvol_scores.keys())
        sector_scores = {}
        
        for sector in all_sectors:
            # Get individual scores (default to 0 if missing)
            rel_perf = relative_perf.get(sector, 0.0)
            breadth = breadth_scores.get(sector, 0.0)
            rvol = rvol_scores.get(sector, 0.0)
            
            # Relative performance scoring (40% weight)
            if rel_perf > 0.05:  # >5% outperformance
                perf_score = 40
            elif rel_perf > 0.02:  # >2% outperformance
                perf_score = 30
            elif rel_perf > 0:  # Positive relative performance
                perf_score = 20
            elif rel_perf > -0.02:  # Minor underperformance
                perf_score = 10
            else:  # Significant underperformance
                perf_score = 0
            
            # Breadth scoring (35% weight)
            breadth_score = int(breadth * 35)
            
            # RVOL scoring (25% weight)
            rvol_score = int(rvol * 25)
            
            # Final score
            final_score = perf_score + breadth_score + rvol_score
            sector_scores[sector] = min(100, final_score)
        
        return sector_scores
    
    @classmethod
    def run(cls, sector_df: pd.DataFrame, index_df: pd.DataFrame) -> Dict[str, SectorMetrics]:
        """Run sector momentum analysis"""
        if len(sector_df) < 20 or len(index_df) < 20:
            return {}
        
        # Calculate individual metrics
        relative_perf = cls.calculate_relative_performance(sector_df, index_df)
        breadth_scores = cls.calculate_breadth_scoring(sector_df)
        rvol_scores = cls.calculate_rvol_scoring(sector_df)
        
        # Calculate final scores
        final_scores = cls.calculate_sector_scores(relative_perf, breadth_scores, rvol_scores)
        
        # Create results
        results = {}
        all_sectors = set(relative_perf.keys()) | set(breadth_scores.keys()) | set(rvol_scores.keys())
        
        for sector in all_sectors:
            results[sector] = SectorMetrics(
                relative_performance=relative_perf.get(sector, 0.0),
                breadth_score=breadth_scores.get(sector, 0.0),
                rvol_score=rvol_scores.get(sector, 0.0),
                sector_score=final_scores.get(sector, 0)
            )
        
        return results