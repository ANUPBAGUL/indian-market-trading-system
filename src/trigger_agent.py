import pandas as pd
import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass

@dataclass
class TriggerSignals:
    """Trigger detection results"""
    volume_expansion: bool = False
    breakout_from_base: bool = False
    candle_acceptance: bool = False

class TriggerAgent:
    """Detect breakout triggers from established bases"""
    
    @staticmethod
    def detect_volume_expansion(df: pd.DataFrame, expansion_threshold: float = 1.5) -> Tuple[bool, float]:
        """Detect volume expansion on current bar"""
        if len(df) < 20:
            return False, 0.0
        
        # Current volume vs 20-day average
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].tail(20).mean()
        
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        expansion = volume_ratio >= expansion_threshold
        
        return expansion, volume_ratio
    
    @staticmethod
    def detect_breakout_from_base(df: pd.DataFrame, base_period: int = 20, 
                                 breakout_threshold: float = 0.02) -> Tuple[bool, float]:
        """Detect breakout above established base"""
        if len(df) < base_period + 5:
            return False, 0.0
        
        # Define base as recent consolidation period
        base_data = df.tail(base_period + 1).head(base_period)  # Exclude current bar
        base_high = base_data['high'].max()
        
        # Current price vs base high
        current_high = df['high'].iloc[-1]
        breakout_level = base_high * (1 + breakout_threshold)
        
        # Breakout: current high exceeds base high by threshold
        breakout = current_high >= breakout_level
        breakout_percentage = (current_high / base_high - 1) if base_high > 0 else 0
        
        return breakout, breakout_percentage
    
    @staticmethod
    def detect_candle_acceptance(df: pd.DataFrame, acceptance_threshold: float = 0.5) -> Tuple[bool, float]:
        """Detect strong candle acceptance above breakout level"""
        if len(df) < 2:
            return False, 0.0
        
        current_bar = df.iloc[-1]
        
        # Candle range and close position
        candle_range = current_bar['high'] - current_bar['low']
        if candle_range == 0:
            return False, 0.0
        
        # Close position within candle (0 = low, 1 = high)
        close_position = (current_bar['close'] - current_bar['low']) / candle_range
        
        # Strong acceptance: close in upper portion of candle
        acceptance = close_position >= acceptance_threshold
        
        return acceptance, close_position
    
    @classmethod
    def run(cls, df: pd.DataFrame) -> Dict:
        """Run trigger detection on stock data"""
        if len(df) < 25:
            return {
                'trigger_active': False,
                'signals': TriggerSignals(),
                'metrics': {
                    'volume_ratio': 0.0,
                    'breakout_percentage': 0.0,
                    'close_position': 0.0
                }
            }
        
        # Detect individual signals
        vol_expansion, vol_ratio = cls.detect_volume_expansion(df)
        breakout, breakout_pct = cls.detect_breakout_from_base(df)
        acceptance, close_pos = cls.detect_candle_acceptance(df)
        
        # Create signals object
        signals = TriggerSignals(
            volume_expansion=vol_expansion,
            breakout_from_base=breakout,
            candle_acceptance=acceptance
        )
        
        # Trigger is active when 2 of 3 signals are present (more flexible)
        trigger_active = sum([vol_expansion, breakout, acceptance]) >= 2
        
        return {
            'trigger_active': trigger_active,
            'signals': signals,
            'metrics': {
                'volume_ratio': vol_ratio,
                'breakout_percentage': breakout_pct,
                'close_position': close_pos
            }
        }