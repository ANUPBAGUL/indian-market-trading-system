"""
System Refinement Notes - Minimal threshold adjustments based on behavior analysis.

These adjustments address what feels forced while preserving what works naturally.
"""

# REFINEMENT RECOMMENDATIONS

## 1. TRIGGER AGENT - Reduce Rigidity
# Current: Requires ALL 3 signals (too restrictive)
# Adjustment: Require 2 of 3 signals for trigger activation

# In trigger_agent.py, line ~85:
# OLD: trigger_active = vol_expansion and breakout and acceptance
# NEW: trigger_active = sum([vol_expansion, breakout, acceptance]) >= 2

## 2. PAPER TRADING - Lower Entry Threshold  
# Current: 65% confidence threshold (too few signals)
# Adjustment: Lower to 62% for more signal generation

# In paper_trading_engine.py, line ~95:
# OLD: if confidence > 65.0:
# NEW: if confidence > 62.0:

## 3. ACCUMULATION AGENT - Soften Volume Threshold
# Current: 1.5x volume ratio (may miss subtle accumulation)
# Adjustment: Lower to 1.3x for better sensitivity

# In accumulation_agent.py, line ~25:
# OLD: absorption = volume_ratio > 1.5 and current_range < avg_range * 0.8
# NEW: absorption = volume_ratio > 1.3 and current_range < avg_range * 0.8

## 4. VOLATILITY COMPRESSION - Modern Market Adjustment
# Current: 70% compression threshold (too strict for current volatility)
# Adjustment: Relax to 75% to account for modern market conditions

# In accumulation_agent.py, line ~40:
# OLD: compression = compression_ratio < 0.7  # 30% compression
# NEW: compression = compression_ratio < 0.75  # 25% compression

## 5. RELATIVE STRENGTH - Sector Rotation Sensitivity
# Current: 2% outperformance threshold (too high)
# Adjustment: Lower to 1.5% for better sector rotation detection

# In accumulation_agent.py, line ~75:
# OLD: strength = relative_performance > 0.02  # Outperforming by 2%+
# NEW: strength = relative_performance > 0.015  # Outperforming by 1.5%+

## 6. CONFIDENCE BUCKETS - Simplify Granularity
# Current: 5-point buckets (60-65, 65-70, etc.) - too granular
# Adjustment: Use 10-point buckets for clearer differentiation

# In confidence_engine.py, line ~25:
# OLD: CONFIDENCE_BUCKETS = [(60, 65), (65, 70), (70, 75), (75, 80), (80, 85), (85, 90), (90, 95), (95, 100)]
# NEW: CONFIDENCE_BUCKETS = [(60, 70), (70, 80), (80, 90), (90, 100)]

## 7. GOVERNOR ALIGNMENT - Sync Minimum Thresholds
# Current: Governor min (60%) vs system threshold (65%) mismatch
# Adjustment: Align Governor minimum with paper trading threshold

# In governor.py, line ~30:
# OLD: MIN_CONFIDENCE = 60.0
# NEW: MIN_CONFIDENCE = 62.0  # Match paper trading threshold

## RATIONALE FOR CHANGES

### What These Adjustments Fix:
1. **Signal Generation**: More realistic entry opportunities
2. **Market Adaptation**: Better fit for current volatility environment  
3. **Threshold Harmony**: Consistent confidence requirements across components
4. **Flexibility**: Less rigid binary requirements, more nuanced scoring

### What Remains Unchanged:
1. **Core Logic**: No new features or algorithms
2. **Risk Management**: Position sizing and stop logic preserved
3. **Agent Architecture**: Fundamental design stays intact
4. **Weighting System**: Proven agent weights maintained

### Expected Impact:
- **15-25% more signals** from relaxed thresholds
- **Better signal quality** from 2-of-3 trigger logic
- **Improved sector rotation** detection from lower relative strength bar
- **Cleaner confidence interpretation** from simplified buckets

### Monitoring Points:
- **Win rate changes** from increased signal volume
- **Drawdown impact** from more aggressive entry criteria
- **Signal quality** maintenance with relaxed thresholds
- **Confidence calibration** accuracy with new buckets

## IMPLEMENTATION PRIORITY

### Phase 1 (Immediate):
1. Trigger Agent 2-of-3 logic
2. Paper trading threshold alignment
3. Governor threshold sync

### Phase 2 (Next Review):
1. Volume and volatility adjustments
2. Relative strength refinement
3. Confidence bucket simplification

### Success Metrics:
- Signal generation increases 15-25%
- Win rate remains above 45%
- Max drawdown stays under 15%
- Confidence buckets show proper calibration

## CONCLUSION

These minimal adjustments address the most forced aspects of the system while preserving its natural strengths. The changes focus on threshold refinement rather than structural modifications, maintaining system integrity while improving practical usability.

The key insight: **Reduce binary requirements, increase threshold sensitivity, maintain risk discipline.**
"""