import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.trigger_agent import TriggerAgent

class TestTriggerIntegration:
    @pytest.fixture
    def true_breakout_data(self):
        """Create realistic true breakout scenario"""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=30)
        
        data = []
        for i, date in enumerate(dates):
            if i < 25:
                # Tight base formation
                close = 100.0 + np.random.uniform(-1, 1)
                high = close + np.random.uniform(0.2, 0.8)
                low = close - np.random.uniform(0.2, 0.8)
                volume = 1000000 + np.random.normal(0, 100000)
            elif i == 25:
                # Breakout bar
                close = 103.0   # Strong close
                high = 103.5    # Clear breakout
                low = 101.5     # Gap up
                volume = 2000000  # Volume expansion
            else:
                # Follow through
                close = 103.0 + (i - 25) * 0.2
                high = close + 0.3
                low = close - 0.2
                volume = 1300000
            
            data.append({
                'symbol': 'BREAKOUT',
                'date': date,
                'open': close + np.random.uniform(-0.1, 0.1),
                'high': max(high, close),
                'low': min(low, close),
                'close': close,
                'volume': max(int(volume), 100000)
            })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def false_breakout_data(self):
        """Create false breakout scenario"""
        np.random.seed(123)
        dates = pd.date_range('2024-01-01', periods=30)
        
        data = []
        for i, date in enumerate(dates):
            if i < 25:
                # Base formation
                close = 100.0 + np.random.uniform(-1, 1)
                high = close + np.random.uniform(0.3, 1.0)
                low = close - np.random.uniform(0.3, 1.0)
                volume = 1000000 + np.random.normal(0, 150000)
            elif i == 25:
                # False breakout bar - weak volume, poor close
                close = 100.8   # Weak close
                high = 102.5    # Reaches high but can't hold
                low = 99.5      # Wide range
                volume = 1100000  # Minimal volume increase
            else:
                # Failure
                close = 99.0 - (i - 25) * 0.3
                high = close + 0.5
                low = close - 0.8
                volume = 900000
            
            data.append({
                'symbol': 'FALSE_BO',
                'date': date,
                'open': close + np.random.uniform(-0.1, 0.1),
                'high': max(high, close),
                'low': min(low, close),
                'close': close,
                'volume': max(int(volume), 100000)
            })
        
        return pd.DataFrame(data)
    
    @pytest.fixture
    def normal_trading_data(self):
        """Create normal trading without breakout"""
        np.random.seed(456)
        dates = pd.date_range('2024-01-01', periods=30)
        
        data = []
        for i, date in enumerate(dates):
            # Normal random walk
            close = 100.0 + np.random.normal(0, 2)
            high = close + np.random.uniform(0.5, 2.0)
            low = close - np.random.uniform(0.5, 2.0)
            volume = 1000000 + np.random.normal(0, 200000)
            
            data.append({
                'symbol': 'NORMAL',
                'date': date,
                'open': close + np.random.uniform(-0.2, 0.2),
                'high': max(high, close),
                'low': min(low, close),
                'close': close,
                'volume': max(int(volume), 100000)
            })
        
        return pd.DataFrame(data)
    
    def test_true_vs_false_breakout_detection(self, true_breakout_data, false_breakout_data):
        """Test that true breakouts have different characteristics than false ones"""
        true_result = TriggerAgent.run(true_breakout_data)
        false_result = TriggerAgent.run(false_breakout_data)
        
        # At minimum, results should be calculated without errors
        assert 'trigger_active' in true_result
        assert 'trigger_active' in false_result
        
        # Volume ratios should be different
        true_vol = true_result['metrics']['volume_ratio']
        false_vol = false_result['metrics']['volume_ratio']
        assert true_vol != false_vol or (true_vol == 0 and false_vol == 0)
    
    def test_volume_expansion_in_breakout(self, true_breakout_data):
        """Test volume expansion detection in realistic scenario"""
        result = TriggerAgent.run(true_breakout_data)
        
        # Should detect volume expansion
        volume_ratio = result['metrics']['volume_ratio']
        assert volume_ratio > 1.0  # Some expansion detected
    
    def test_breakout_percentage_calculation(self, true_breakout_data):
        """Test breakout percentage with real data"""
        result = TriggerAgent.run(true_breakout_data)
        
        # Should calculate valid breakout percentage
        breakout_pct = result['metrics']['breakout_percentage']
        assert breakout_pct >= 0  # Valid percentage calculated
    
    def test_candle_acceptance_measurement(self, true_breakout_data):
        """Test candle acceptance with real candle data"""
        result = TriggerAgent.run(true_breakout_data)
        
        # Should calculate valid close position
        close_pos = result['metrics']['close_position']
        assert 0 <= close_pos <= 1  # Valid position (0-100%)
    
    def test_normal_trading_no_trigger(self, normal_trading_data):
        """Test that normal trading doesn't trigger"""
        result = TriggerAgent.run(normal_trading_data)
        
        # Normal trading should not trigger
        assert result['trigger_active'] == False
    
    def test_trigger_consistency(self, true_breakout_data):
        """Test that same data produces consistent results"""
        result1 = TriggerAgent.run(true_breakout_data)
        result2 = TriggerAgent.run(true_breakout_data)
        
        # Should be deterministic
        assert result1['trigger_active'] == result2['trigger_active']
        assert result1['signals'].volume_expansion == result2['signals'].volume_expansion
        assert result1['signals'].breakout_from_base == result2['signals'].breakout_from_base
        assert result1['signals'].candle_acceptance == result2['signals'].candle_acceptance
    
    def test_signal_independence(self):
        """Test that signals can fire independently"""
        # Volume expansion only (need 26 bars for proper calculation)
        vol_only_data = pd.DataFrame({
            'high': [100.0] * 26,
            'low': [99.0] * 26,
            'close': [99.2] * 25 + [99.3],  # Weak close
            'volume': [1000000] * 25 + [2000000]  # Volume expansion
        })
        
        result = TriggerAgent.run(vol_only_data)
        
        assert result['signals'].volume_expansion == True
        assert result['signals'].breakout_from_base == False
        assert result['signals'].candle_acceptance == False
        assert result['trigger_active'] == False  # Not all signals
    
    def test_edge_case_handling(self):
        """Test edge cases and boundary conditions"""
        # Zero volume scenario
        zero_vol_data = pd.DataFrame({
            'high': [100.0] * 21,
            'low': [99.0] * 21,
            'close': [100.0] * 21,
            'volume': [0] * 21
        })
        
        result = TriggerAgent.run(zero_vol_data)
        
        # Should handle gracefully
        assert result['trigger_active'] == False
        assert result['metrics']['volume_ratio'] == 0.0
    
    def test_realistic_trigger_thresholds(self, true_breakout_data):
        """Test that thresholds work with realistic data"""
        result = TriggerAgent.run(true_breakout_data)
        
        # Check that metrics are within realistic ranges
        metrics = result['metrics']
        
        # Volume ratio should be reasonable (not extreme)
        assert 0 <= metrics['volume_ratio'] <= 10
        
        # Breakout percentage should be reasonable
        assert -0.1 <= metrics['breakout_percentage'] <= 0.2  # -10% to +20%
        
        # Close position should be valid
        assert 0 <= metrics['close_position'] <= 1