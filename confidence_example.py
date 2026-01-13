"""
Confidence Engine Examples - Demonstrates weighted scoring and bucket classification.
"""

import sys
sys.path.append('src')
import pandas as pd
from confidence_engine import ConfidenceEngine


def main():
    print("=== CONFIDENCE ENGINE EXAMPLES ===\n")
    
    # Example 1: High Confidence Setup
    print("1. HIGH CONFIDENCE SETUP")
    high_conf_scores = {
        'accumulation': 88,      # Strong institutional buying
        'trigger': 82,           # Clean breakout with volume
        'sector_momentum': 75,   # Sector in favor
        'regime': 85             # Risk-on environment
    }
    
    score, bucket = ConfidenceEngine.compute(high_conf_scores)
    print(f"   Agent Scores: {high_conf_scores}")
    print(f"   Weighted Score: {score:.1f}")
    print(f"   Confidence Bucket: {bucket}")
    print(f"   -> Strong setup with institutional backing\n")
    
    # Example 2: Medium Confidence Setup  
    print("2. MEDIUM CONFIDENCE SETUP")
    med_conf_scores = {
        'accumulation': 72,      # Moderate accumulation
        'trigger': 68,           # Weak breakout signal
        'sector_momentum': 65,   # Neutral sector
        'regime': 70             # Neutral regime
    }
    
    score, bucket = ConfidenceEngine.compute(med_conf_scores)
    print(f"   Agent Scores: {med_conf_scores}")
    print(f"   Weighted Score: {score:.1f}")
    print(f"   Confidence Bucket: {bucket}")
    print(f"   -> Marginal setup, proceed with caution\n")
    
    # Example 3: Low Confidence Setup
    print("3. LOW CONFIDENCE SETUP")
    low_conf_scores = {
        'accumulation': 45,      # No institutional interest
        'trigger': 55,           # Weak trigger
        'sector_momentum': 40,   # Sector out of favor
        'regime': 60             # Risk-off environment
    }
    
    score, bucket = ConfidenceEngine.compute(low_conf_scores)
    print(f"   Agent Scores: {low_conf_scores}")
    print(f"   Weighted Score: {score:.1f}")
    print(f"   Confidence Bucket: {bucket}")
    print(f"   -> Avoid - multiple negative signals\n")
    
    # Example 4: Batch Processing
    print("4. BATCH PROCESSING EXAMPLE")
    batch_data = pd.DataFrame({
        'symbol': ['AAPL', 'GOOGL', 'TSLA', 'MSFT'],
        'accumulation': [85, 72, 45, 90],
        'trigger': [78, 65, 50, 85],
        'sector_momentum': [80, 70, 35, 88],
        'regime': [82, 75, 55, 80]
    })
    
    results = ConfidenceEngine.batch_compute(batch_data)
    print(results[['symbol', 'confidence_score', 'confidence_bucket']].to_string(index=False))
    print()
    
    # Example 5: Weight Impact Analysis
    print("5. WEIGHT IMPACT ANALYSIS")
    print("   Same raw scores, different agent emphasis:")
    
    base_scores = {
        'accumulation': 80,
        'trigger': 60, 
        'sector_momentum': 70,
        'regime': 90
    }
    
    score, bucket = ConfidenceEngine.compute(base_scores)
    print(f"   Current Weights: Acc(35%) Trig(25%) Sect(20%) Reg(20%)")
    print(f"   Result: {score:.1f} -> {bucket}")
    print(f"   -> Accumulation weight (35%) dominates despite weak trigger")


if __name__ == "__main__":
    main()