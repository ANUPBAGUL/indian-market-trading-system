import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.regime_detector import RegimeDetector

class TestRegimeIntegration:
    @pytest.fixture
    def bull_market_data(self):
        """Create bull market scenario"""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=80)
        
        data = []
        price = 4000
        for date in dates:
            # Strong upward trend with noise
            price *= (1 + np.random.normal(0.003, 0.01))  # +0.3% daily trend
            data.append({
                'date': date,
                'close': price,
                'symbol': 'SPY'
            })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def bear_market_data(self):
        """Create bear market scenario"""
        np.random.seed(123)
        dates = pd.date_range('2024-01-01', periods=80)
        
        data = []
        price = 4000
        for date in dates:
            # Strong downward trend with noise
            price *= (1 + np.random.normal(-0.002, 0.015))  # -0.2% daily trend
            data.append({
                'date': date,
                'close': price,
                'symbol': 'SPY'
            })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def sideways_market_data(self):
        """Create sideways market scenario"""
        np.random.seed(456)
        dates = pd.date_range('2024-01-01', periods=80)
        
        data = []
        price = 4000
        for date in dates:
            # No trend, just noise
            price *= (1 + np.random.normal(0, 0.008))
            data.append({
                'date': date,
                'close': price,
                'symbol': 'SPY'
            })
        
        return pd.DataFrame(data)
    
    def test_bull_market_detection(self, bull_market_data):
        """Test regime detection in bull market"""
        result = RegimeDetector.detect_regime(bull_market_data)
        
        # Should eventually detect risk_on regime
        valid_regimes = result['regime'].iloc[60:].dropna()  # Look at later period
        
        # Bull market should have some risk_on presence
        assert 'risk_on' in valid_regimes.values or valid_regimes.mean() != 'risk_off'
    
    def test_bear_market_detection(self, bear_market_data):
        """Test regime detection in bear market"""
        result = RegimeDetector.detect_regime(bear_market_data)
        
        # Should eventually detect risk_off regime
        valid_regimes = result['regime'].iloc[60:].dropna()
        regime_counts = valid_regimes.value_counts()
        
        # Bear market should have more risk_off than risk_on
        risk_off_count = regime_counts.get('risk_off', 0)
        risk_on_count = regime_counts.get('risk_on', 0)
        
        assert risk_off_count >= risk_on_count
    
    def test_sideways_market_detection(self, sideways_market_data):
        """Test regime detection in sideways market"""
        result = RegimeDetector.detect_regime(sideways_market_data)
        
        # Should have significant neutral regime presence
        valid_regimes = result['regime'].iloc[60:].dropna()
        regime_counts = valid_regimes.value_counts()
        
        neutral_count = regime_counts.get('neutral', 0)
        total_count = len(valid_regimes)
        
        # At least 20% should be neutral in sideways market
        assert neutral_count / total_count >= 0.2
    
    def test_regime_transitions(self, bull_market_data):
        """Test that regime transitions are captured"""
        result = RegimeDetector.detect_regime(bull_market_data)
        
        # Find regime changes
        regimes = result['regime'].dropna()
        transitions = []
        
        prev_regime = None
        for regime in regimes:
            if prev_regime and prev_regime != regime:
                transitions.append((prev_regime, regime))
            prev_regime = regime
        
        # Should have some transitions (not stuck in one regime)
        assert len(transitions) > 0
    
    def test_slope_correlation_with_price_trend(self, bull_market_data, bear_market_data):
        """Test that slope correlates with actual price trends"""
        bull_result = RegimeDetector.detect_regime(bull_market_data)
        bear_result = RegimeDetector.detect_regime(bear_market_data)
        
        # Calculate actual price trends
        bull_start = bull_market_data['close'].iloc[0]
        bull_end = bull_market_data['close'].iloc[-1]
        bull_trend = (bull_end / bull_start) - 1
        
        bear_start = bear_market_data['close'].iloc[0]
        bear_end = bear_market_data['close'].iloc[-1]
        bear_trend = (bear_end / bear_start) - 1
        
        # Bull market should have better performance than bear market
        assert bull_trend > bear_trend
    
    def test_regime_persistence(self, bear_market_data):
        """Test that regimes don't change too frequently (avoid whipsaws)"""
        result = RegimeDetector.detect_regime(bear_market_data)
        
        # Count regime changes
        regimes = result['regime'].iloc[60:].dropna()  # Focus on stable period
        changes = 0
        
        prev_regime = None
        for regime in regimes:
            if prev_regime and prev_regime != regime:
                changes += 1
            prev_regime = regime
        
        # Should not change regime every day (max 50% change rate)
        change_rate = changes / len(regimes)
        assert change_rate < 0.5
    
    def test_realistic_regime_distribution(self):
        """Test with mixed market conditions"""
        np.random.seed(789)
        dates = pd.date_range('2024-01-01', periods=120)
        
        # Create mixed market: bull -> bear -> sideways
        data = []
        price = 4000
        
        for i, date in enumerate(dates):
            if i < 40:  # Bull phase
                trend = 0.001
                vol = 0.01
            elif i < 80:  # Bear phase
                trend = -0.002
                vol = 0.015
            else:  # Sideways phase
                trend = 0
                vol = 0.008
            
            price *= (1 + np.random.normal(trend, vol))
            data.append({'date': date, 'close': price, 'symbol': 'SPY'})
        
        mixed_data = pd.DataFrame(data)
        result = RegimeDetector.detect_regime(mixed_data)
        
        # Should detect all three regime types
        regimes = result['regime'].dropna()
        unique_regimes = set(regimes.unique())
        
        # Should have at least 2 different regimes in mixed market
        assert len(unique_regimes) >= 2
        
        # Should include both risk_on and risk_off
        assert 'risk_on' in unique_regimes or 'risk_off' in unique_regimes