import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.trigger_agent import TriggerAgent, TriggerSignals

class TestTriggerAgent:
    @pytest.fixture
    def base_stock_data(self):
        """Basic stock data with established base"""
        dates = pd.date_range('2024-01-01', periods=25)
        data = []
        
        for i, date in enumerate(dates):
            # Create tight base around 100
            close = 100.0 + np.random.uniform(-0.5, 0.5)
            high = close + 0.5
            low = close - 0.5
            volume = 1000000
            
            data.append({
                'date': date,
                'open': close,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    def test_volume_expansion_detection(self):
        """Test volume expansion calculation"""
        # Normal volume then expansion
        data = pd.DataFrame({
            'volume': [1000000] * 19 + [2000000]  # 2x expansion on last bar
        })
        
        expansion, vol_ratio = TriggerAgent.detect_volume_expansion(data)
        
        assert vol_ratio > 1.9  # Approximately 2x
        assert expansion == True  # Above 1.5x threshold
    
    def test_volume_no_expansion(self):
        """Test no volume expansion"""
        data = pd.DataFrame({
            'volume': [1000000] * 20  # Constant volume
        })
        
        expansion, vol_ratio = TriggerAgent.detect_volume_expansion(data)
        
        assert vol_ratio == 1.0
        assert expansion == False  # Below 1.5x threshold
    
    def test_breakout_from_base_detection(self):
        """Test breakout detection"""
        # Base high at 101, current high at 103.5 (>2% above)
        data = pd.DataFrame({
            'high': [101.0] * 25 + [103.5],  # 25 base bars + breakout bar
            'low': [99.0] * 26,
            'close': [100.0] * 26
        })
        
        breakout, breakout_pct = TriggerAgent.detect_breakout_from_base(data)
        
        assert breakout_pct > 0.02  # >2% breakout
        assert breakout == True
    
    def test_no_breakout_from_base(self):
        """Test no breakout scenario"""
        # All bars at same level
        data = pd.DataFrame({
            'high': [101.0] * 21,
            'low': [99.0] * 21,
            'close': [100.0] * 21
        })
        
        breakout, breakout_pct = TriggerAgent.detect_breakout_from_base(data)
        
        assert breakout_pct == 0.0  # No breakout
        assert breakout == False
    
    def test_candle_acceptance_strong(self):
        """Test strong candle acceptance"""
        # Close near high of candle (need 2+ rows for function)
        data = pd.DataFrame({
            'high': [103.0, 104.0],
            'low': [101.0, 102.0],
            'close': [102.0, 103.5]  # Last bar: 75% of range
        })
        
        acceptance, close_pos = TriggerAgent.detect_candle_acceptance(data)
        
        assert close_pos == 0.75  # 75% position
        assert acceptance == True  # Above 50% threshold
    
    def test_candle_acceptance_weak(self):
        """Test weak candle acceptance"""
        # Close near low of candle
        data = pd.DataFrame({
            'high': [103.0, 104.0],
            'low': [101.0, 102.0],
            'close': [102.0, 102.5]  # Last bar: 25% of range
        })
        
        acceptance, close_pos = TriggerAgent.detect_candle_acceptance(data)
        
        assert close_pos == 0.25  # 25% position
        assert acceptance == False  # Below 50% threshold
    
    def test_perfect_trigger_scenario(self):
        """Test all signals firing together"""
        # Create perfect trigger data (26 bars total for proper base calculation)
        base_data = pd.DataFrame({
            'high': [101.0] * 25,
            'low': [99.0] * 25,
            'close': [100.0] * 25,
            'volume': [1000000] * 25
        })
        
        # Add trigger bar
        trigger_bar = pd.DataFrame({
            'high': [104.0],      # >2% breakout above 101
            'low': [102.0],
            'close': [103.5],     # 75% close position
            'volume': [2000000]   # 2x volume
        })
        
        data = pd.concat([base_data, trigger_bar], ignore_index=True)
        result = TriggerAgent.run(data)
        
        assert result['trigger_active'] == True
        assert result['signals'].volume_expansion == True
        assert result['signals'].breakout_from_base == True
        assert result['signals'].candle_acceptance == True
    
    def test_partial_signals_no_trigger(self):
        """Test partial signals don't trigger"""
        # Only volume expansion, no breakout or acceptance (26 bars total)
        data = pd.DataFrame({
            'high': [101.0] * 26,     # No breakout
            'low': [99.0] * 25 + [100.5],
            'close': [100.0] * 25 + [100.6],  # Weak close
            'volume': [1000000] * 25 + [2000000]  # Volume expansion
        })
        
        result = TriggerAgent.run(data)
        
        assert result['trigger_active'] == False  # Not all signals
        assert result['signals'].volume_expansion == True
        assert result['signals'].breakout_from_base == False
        assert result['signals'].candle_acceptance == False
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data"""
        minimal_data = pd.DataFrame({
            'high': [100, 101],
            'low': [99, 100],
            'close': [100, 101],
            'volume': [1000000, 1100000]
        })
        
        result = TriggerAgent.run(minimal_data)
        
        assert result['trigger_active'] == False
        assert result['signals'].volume_expansion == False
        assert result['signals'].breakout_from_base == False
        assert result['signals'].candle_acceptance == False
    
    def test_run_method_structure(self, base_stock_data):
        """Test complete run method structure"""
        result = TriggerAgent.run(base_stock_data)
        
        # Check return structure
        assert 'trigger_active' in result
        assert 'signals' in result
        assert 'metrics' in result
        
        # Check types
        assert isinstance(result['trigger_active'], (bool, np.bool_))
        assert isinstance(result['signals'], TriggerSignals)
        assert isinstance(result['metrics'], dict)
        
        # Check metrics keys
        metrics = result['metrics']
        assert 'volume_ratio' in metrics
        assert 'breakout_percentage' in metrics
        assert 'close_position' in metrics