"""
Confidence Engine - Aggregates agent scores into calibrated confidence buckets.

The engine combines multiple agent scores using weighted averages and maps
the result to discrete confidence buckets for consistent interpretation.
"""

from typing import Dict, Tuple
import pandas as pd


class ConfidenceEngine:
    """
    Aggregates agent scores into calibrated confidence buckets.
    
    Weights reflect each agent's importance in the decision process:
    - Accumulation: 35% (primary signal strength)
    - Trigger: 25% (entry timing quality) 
    - Sector Momentum: 20% (market context)
    - Regime: 20% (macro environment)
    """
    
    # Agent weights (must sum to 1.0)
    WEIGHTS = {
        'accumulation': 0.35,
        'trigger': 0.25, 
        'sector_momentum': 0.20,
        'regime': 0.20
    }
    
    # Confidence bucket thresholds (simplified 10-point buckets)
    CONFIDENCE_BUCKETS = [
        (60, 70), (70, 80), (80, 90), (90, 100)
    ]
    
    @staticmethod
    def compute(agent_scores: Dict[str, float]) -> Tuple[float, str]:
        """
        Compute weighted confidence score and bucket.
        
        Args:
            agent_scores: Dict with keys: accumulation, trigger, sector_momentum, regime
                         Values should be 0-100 scores
        
        Returns:
            Tuple of (weighted_score, confidence_bucket)
            
        Example:
            scores = {
                'accumulation': 85,
                'trigger': 75, 
                'sector_momentum': 70,
                'regime': 80
            }
            score, bucket = ConfidenceEngine.compute(scores)
            # Returns: (78.5, "75-80")
        """
        # Validate inputs
        required_agents = set(ConfidenceEngine.WEIGHTS.keys())
        provided_agents = set(agent_scores.keys())
        
        if not required_agents.issubset(provided_agents):
            missing = required_agents - provided_agents
            raise ValueError(f"Missing agent scores: {missing}")
        
        # Compute weighted average
        weighted_score = sum(
            agent_scores[agent] * weight 
            for agent, weight in ConfidenceEngine.WEIGHTS.items()
        )
        
        # Map to confidence bucket
        bucket = ConfidenceEngine._get_confidence_bucket(weighted_score)
        
        return weighted_score, bucket
    
    @staticmethod
    def _get_confidence_bucket(score: float) -> str:
        """Map weighted score to confidence bucket string."""
        for min_val, max_val in ConfidenceEngine.CONFIDENCE_BUCKETS:
            if min_val <= score < max_val:
                return f"{min_val}-{max_val}"
        
        # Handle edge case for perfect scores
        if score >= 90:
            return "90-100"
        
        # Below minimum confidence threshold
        return "Below-60"
    
    @staticmethod
    def batch_compute(df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute confidence for multiple stocks at once.
        
        Args:
            df: DataFrame with columns: accumulation, trigger, sector_momentum, regime
        
        Returns:
            DataFrame with added columns: confidence_score, confidence_bucket
        """
        results = []
        
        for _, row in df.iterrows():
            agent_scores = {
                'accumulation': row['accumulation'],
                'trigger': row['trigger'],
                'sector_momentum': row['sector_momentum'], 
                'regime': row['regime']
            }
            
            score, bucket = ConfidenceEngine.compute(agent_scores)
            results.append({'confidence_score': score, 'confidence_bucket': bucket})
        
        result_df = pd.DataFrame(results)
        return pd.concat([df, result_df], axis=1)