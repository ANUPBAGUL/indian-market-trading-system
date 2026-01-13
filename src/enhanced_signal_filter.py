"""
Enhanced Signal Filter - Advanced filtering with volume, price, and quality checks.

Implements comprehensive signal filtering to improve signal quality
and reduce false positives.
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np

class EnhancedSignalFilter:
    """Enhanced signal filtering with multiple quality criteria."""
    
    def __init__(self):
        """Initialize enhanced signal filter."""
        # Volume filters
        self.min_daily_volume = 1000000  # 1M shares
        self.min_avg_volume_20d = 500000  # 500K average
        self.volume_spike_threshold = 1.5  # 50% above average
        
        # Price filters
        self.min_price = 10.0  # Avoid penny stocks
        self.max_price = 1000.0  # Avoid extreme prices
        self.min_price_change = 0.005  # 0.5% minimum move
        
        # Quality filters
        self.min_data_points = 30  # Need 30+ days of data
        self.max_gap_percentage = 0.10  # 10% max gap
        self.min_market_cap = 1000000000  # $1B minimum
        
        # Technical filters
        self.min_atr_percentage = 0.01  # 1% minimum ATR
        self.max_atr_percentage = 0.08  # 8% maximum ATR
    
    def filter_signals(self, signals: List[Dict], market_data: pd.DataFrame) -> List[Dict]:
        """Apply comprehensive filtering to signals."""
        
        filtered_signals = []
        filter_stats = {
            'total_signals': len(signals),
            'volume_filtered': 0,
            'price_filtered': 0,
            'quality_filtered': 0,
            'technical_filtered': 0,
            'passed_filters': 0
        }
        
        for signal in signals:
            symbol = signal['symbol']
            
            # Get symbol data
            symbol_data = market_data[market_data['symbol'] == symbol]
            if symbol_data.empty:
                filter_stats['quality_filtered'] += 1
                continue
            
            # Apply filters
            if not self._passes_volume_filter(signal, symbol_data):
                filter_stats['volume_filtered'] += 1
                continue
            
            if not self._passes_price_filter(signal, symbol_data):
                filter_stats['price_filtered'] += 1
                continue
            
            if not self._passes_quality_filter(signal, symbol_data):
                filter_stats['quality_filtered'] += 1
                continue
            
            if not self._passes_technical_filter(signal, symbol_data):
                filter_stats['technical_filtered'] += 1
                continue
            
            # Add quality metrics to signal
            enhanced_signal = self._enhance_signal(signal, symbol_data)
            filtered_signals.append(enhanced_signal)
            filter_stats['passed_filters'] += 1
        
        # Print filter summary
        self._print_filter_summary(filter_stats)
        
        return filtered_signals
    
    def _passes_volume_filter(self, signal: Dict, data: pd.DataFrame) -> bool:
        """Check volume-based filters."""
        
        current_volume = signal.get('volume', data['volume'].iloc[-1])
        avg_volume_20d = data['volume'].tail(20).mean()
        
        # Minimum daily volume
        if current_volume < self.min_daily_volume:
            return False
        
        # Minimum average volume
        if avg_volume_20d < self.min_avg_volume_20d:
            return False
        
        # Volume spike (optional enhancement)
        volume_ratio = current_volume / avg_volume_20d
        if volume_ratio < 0.5:  # Too low volume vs average
            return False
        
        return True
    
    def _passes_price_filter(self, signal: Dict, data: pd.DataFrame) -> bool:
        """Check price-based filters."""
        
        current_price = signal.get('price', data['close'].iloc[-1])
        
        # Price range filter
        if current_price < self.min_price or current_price > self.max_price:
            return False
        
        # Price movement filter
        if len(data) >= 2:
            prev_price = data['close'].iloc[-2]
            price_change = abs(current_price - prev_price) / prev_price
            if price_change < self.min_price_change:
                return False
        
        # Gap filter (avoid excessive gaps)
        if len(data) >= 2:
            prev_close = data['close'].iloc[-2]
            current_open = data['open'].iloc[-1]
            gap_percentage = abs(current_open - prev_close) / prev_close
            if gap_percentage > self.max_gap_percentage:
                return False
        
        return True
    
    def _passes_quality_filter(self, signal: Dict, data: pd.DataFrame) -> bool:
        """Check data quality filters."""
        
        # Sufficient data points
        if len(data) < self.min_data_points:
            return False
        
        # Check for missing data
        missing_data_pct = data.isnull().sum().sum() / (len(data) * len(data.columns))
        if missing_data_pct > 0.05:  # More than 5% missing
            return False
        
        # Check for zero volume days
        zero_volume_days = (data['volume'] == 0).sum()
        if zero_volume_days > len(data) * 0.1:  # More than 10% zero volume
            return False
        
        return True
    
    def _passes_technical_filter(self, signal: Dict, data: pd.DataFrame) -> bool:
        """Check technical analysis filters."""
        
        if len(data) < 20:
            return True  # Skip if insufficient data
        
        # Calculate ATR
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift(1))
        low_close = abs(data['low'] - data['close'].shift(1))
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(14).mean().iloc[-1]
        atr_percentage = atr / data['close'].iloc[-1]
        
        # ATR range filter
        if atr_percentage < self.min_atr_percentage or atr_percentage > self.max_atr_percentage:
            return False
        
        # Trend consistency (optional)
        sma_20 = data['close'].rolling(20).mean().iloc[-1]
        current_price = data['close'].iloc[-1]
        
        # Avoid choppy/sideways markets
        price_vs_sma = abs(current_price - sma_20) / sma_20
        if price_vs_sma < 0.02:  # Too close to moving average
            return False
        
        return True
    
    def _enhance_signal(self, signal: Dict, data: pd.DataFrame) -> Dict:
        """Add quality metrics to signal."""
        
        enhanced_signal = signal.copy()
        
        # Add volume metrics
        current_volume = data['volume'].iloc[-1]
        avg_volume_20d = data['volume'].tail(20).mean()
        enhanced_signal['volume_ratio'] = current_volume / avg_volume_20d
        enhanced_signal['avg_volume_20d'] = avg_volume_20d
        
        # Add price metrics
        current_price = data['close'].iloc[-1]
        sma_20 = data['close'].rolling(20).mean().iloc[-1]
        enhanced_signal['price_vs_sma20'] = (current_price - sma_20) / sma_20 * 100
        
        # Add volatility metrics
        if len(data) >= 14:
            high_low = data['high'] - data['low']
            high_close = abs(data['high'] - data['close'].shift(1))
            low_close = abs(data['low'] - data['close'].shift(1))
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(14).mean().iloc[-1]
            enhanced_signal['atr'] = atr
            enhanced_signal['atr_percentage'] = atr / current_price * 100
        
        # Add quality score
        enhanced_signal['quality_score'] = self._calculate_quality_score(signal, data)
        
        return enhanced_signal
    
    def _calculate_quality_score(self, signal: Dict, data: pd.DataFrame) -> float:
        """Calculate overall signal quality score (0-100)."""
        
        score = 50  # Base score
        
        # Volume quality
        current_volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].tail(20).mean()
        volume_ratio = current_volume / avg_volume
        
        if volume_ratio > 2.0:
            score += 15  # High volume
        elif volume_ratio > 1.5:
            score += 10
        elif volume_ratio < 0.8:
            score -= 10  # Low volume
        
        # Price action quality
        if len(data) >= 5:
            recent_range = data['high'].tail(5).max() - data['low'].tail(5).min()
            current_price = data['close'].iloc[-1]
            range_percentage = recent_range / current_price
            
            if 0.03 <= range_percentage <= 0.08:  # Good range
                score += 10
            elif range_percentage > 0.12:  # Too volatile
                score -= 10
        
        # Trend quality
        if len(data) >= 20:
            sma_20 = data['close'].rolling(20).mean().iloc[-1]
            current_price = data['close'].iloc[-1]
            trend_strength = abs(current_price - sma_20) / sma_20
            
            if trend_strength > 0.05:  # Strong trend
                score += 10
            elif trend_strength < 0.02:  # Weak trend
                score -= 5
        
        return max(0, min(100, score))
    
    def _print_filter_summary(self, stats: Dict):
        """Print filtering summary."""
        
        total = stats['total_signals']
        if total == 0:
            return
        
        print(f"\n=== SIGNAL FILTERING SUMMARY ===")
        print(f"Total Signals: {total}")
        print(f"Volume Filtered: {stats['volume_filtered']} ({stats['volume_filtered']/total*100:.1f}%)")
        print(f"Price Filtered: {stats['price_filtered']} ({stats['price_filtered']/total*100:.1f}%)")
        print(f"Quality Filtered: {stats['quality_filtered']} ({stats['quality_filtered']/total*100:.1f}%)")
        print(f"Technical Filtered: {stats['technical_filtered']} ({stats['technical_filtered']/total*100:.1f}%)")
        print(f"Passed Filters: {stats['passed_filters']} ({stats['passed_filters']/total*100:.1f}%)")

# Convenience function
def filter_signals_enhanced(signals: List[Dict], market_data: pd.DataFrame) -> List[Dict]:
    """Quick function for enhanced signal filtering."""
    
    filter_engine = EnhancedSignalFilter()
    return filter_engine.filter_signals(signals, market_data)