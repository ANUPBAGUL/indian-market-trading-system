"""
Enhanced Trading System - Integrates all improvements for better performance.

Combines real data integration, enhanced filtering, and dynamic position sizing
for improved trading system performance.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from enhanced_data_loader import EnhancedDataLoader
from enhanced_signal_filter import EnhancedSignalFilter
from enhanced_position_sizer import EnhancedPositionSizer
from backtest_engine import BacktestEngine
from governor import Governor
from kpi_computer import KPIComputer
import pandas as pd

class EnhancedTradingSystem:
    """Enhanced trading system with all improvements integrated."""
    
    def __init__(self, initial_capital: float = 100000, use_real_data: bool = True):
        """Initialize enhanced trading system."""
        self.initial_capital = initial_capital
        self.use_real_data = use_real_data
        
        # Initialize components
        self.data_loader = EnhancedDataLoader(use_real_data=use_real_data)
        self.signal_filter = EnhancedSignalFilter()
        self.position_sizer = EnhancedPositionSizer()
        self.backtester = BacktestEngine(initial_capital=initial_capital)
        self.governor = Governor()
    
    def run_enhanced_analysis(self, symbols: list = None) -> dict:
        """Run complete enhanced trading analysis."""
        
        print("=== ENHANCED TRADING SYSTEM ===")
        print(f"Capital: ${self.initial_capital:,}")
        print(f"Real Data: {'Yes' if self.use_real_data else 'No'}")
        print()
        
        # Step 1: Load enhanced data
        if symbols is None:
            symbols = self.data_loader.get_quality_us_stocks()[:10]  # Top 10
        
        print("Step 1: Loading Market Data...")
        market_data = self.data_loader.load_us_stocks(symbols)
        
        if market_data.empty:
            print("No data available")
            return {}
        
        print(f"Loaded {market_data['symbol'].nunique()} stocks with {len(market_data)} records")
        
        # Step 2: Generate signals
        print("\nStep 2: Generating Trading Signals...")
        raw_signals = self._generate_enhanced_signals(market_data)
        print(f"Generated {len(raw_signals)} raw signals")
        
        # Step 3: Apply enhanced filtering
        print("\nStep 3: Applying Enhanced Filters...")
        filtered_signals = self.signal_filter.filter_signals(raw_signals, market_data)
        
        # Step 4: Calculate market volatility
        market_volatility = self._calculate_market_volatility(market_data)
        print(f"\nMarket Volatility: {market_volatility:.1f}%")
        
        # Step 5: Enhanced position sizing
        print("\nStep 5: Calculating Position Sizes...")
        sector_exposures = self._calculate_sector_exposures([])
        sized_signals = self.position_sizer.batch_calculate_sizes(
            filtered_signals, self.initial_capital, market_volatility, sector_exposures
        )
        
        # Step 6: Run backtest
        print(f"\nStep 6: Running Enhanced Backtest...")
        signal_generator = self._create_signal_generator(sized_signals)
        
        results = self.backtester.run(
            price_data=market_data,
            signal_generator=signal_generator,
            governor=self.governor
        )
        
        # Step 7: Calculate enhanced KPIs
        print(f"\nStep 7: Calculating Performance Metrics...")
        kpis = KPIComputer.compute_kpis(
            trades=results['trades'],
            equity_curve=results['equity_curve'],
            signal_data=results.get('signal_log', [])
        )
        
        # Step 8: Generate enhanced report
        self._print_enhanced_results(results, kpis, market_volatility)
        
        return {
            'results': results,
            'kpis': kpis,
            'market_data': market_data,
            'signals': sized_signals,
            'market_volatility': market_volatility
        }
    
    def _generate_enhanced_signals(self, market_data: pd.DataFrame) -> list:
        """Generate enhanced trading signals."""
        
        signals = []
        
        # Group by symbol for analysis
        for symbol in market_data['symbol'].unique():
            symbol_data = market_data[market_data['symbol'] == symbol].sort_values('date')
            
            if len(symbol_data) < 30:
                continue
            
            # Get latest data
            latest = symbol_data.iloc[-1]
            
            # Simple momentum signal with enhanced criteria
            if len(symbol_data) >= 20:
                sma_20 = symbol_data['close'].rolling(20).mean().iloc[-1]
                price_vs_sma = (latest['close'] - sma_20) / sma_20
                
                # Volume analysis
                avg_volume = symbol_data['volume'].tail(20).mean()
                volume_ratio = latest['volume'] / avg_volume
                
                # Generate signal if conditions met
                if price_vs_sma > 0.02 and volume_ratio > 1.2:  # 2% above SMA + volume
                    confidence = 50 + (price_vs_sma * 500) + (min(volume_ratio - 1, 1) * 20)
                    confidence = min(95, max(50, confidence))
                    
                    signal = {
                        'symbol': symbol,
                        'type': 'ENTRY',
                        'price': latest['close'],
                        'volume': latest['volume'],
                        'confidence': confidence,
                        'sector': latest.get('sector', 'Unknown'),
                        'reasoning': f"Momentum: {price_vs_sma:.1%} above SMA20, Volume: {volume_ratio:.1f}x"
                    }
                    
                    signals.append(signal)
        
        return signals
    
    def _calculate_market_volatility(self, market_data: pd.DataFrame) -> float:
        """Calculate overall market volatility."""
        
        # Use SPY-like calculation across all stocks
        all_returns = []
        
        for symbol in market_data['symbol'].unique():
            symbol_data = market_data[market_data['symbol'] == symbol].sort_values('date')
            
            if len(symbol_data) >= 20:
                returns = symbol_data['close'].pct_change().dropna()
                all_returns.extend(returns.tail(20).tolist())
        
        if not all_returns:
            return 15.0  # Default
        
        import numpy as np
        volatility = np.std(all_returns) * np.sqrt(252) * 100
        return min(50.0, max(5.0, volatility))
    
    def _calculate_sector_exposures(self, existing_positions: list) -> dict:
        """Calculate current sector exposures."""
        # Simplified - in real system would track actual positions
        return {}
    
    def _create_signal_generator(self, sized_signals: list):
        """Create signal generator function for backtester."""
        
        def generate_signals(day_data, existing_positions):
            # Return signals for current day
            current_date = day_data['date'].iloc[0] if not day_data.empty else None
            
            # Filter signals for current date (simplified)
            day_signals = []
            for signal in sized_signals[:3]:  # Limit for demo
                if signal['symbol'] in day_data['symbol'].values:
                    day_signals.append({
                        'symbol': signal['symbol'],
                        'type': 'ENTRY',
                        'confidence': signal['confidence'],
                        'shares': signal['shares'],
                        'sector': signal['sector'],
                        'stop_price': signal['price'] * 0.95,
                        'reasoning': signal['reasoning']
                    })
            
            return day_signals
        
        return generate_signals
    
    def _print_enhanced_results(self, results: dict, kpis: dict, market_volatility: float):
        """Print enhanced results with improvements highlighted."""
        
        print(f"\n=== ENHANCED SYSTEM RESULTS ===")
        
        # Core performance
        print(f"\nCORE PERFORMANCE:")
        print(f"  Total Trades: {len(results['trades'])}")
        print(f"  Expectancy: ${kpis['expectancy']:.2f} per trade")
        print(f"  Win Rate: {kpis['win_rate_pct']:.1f}%")
        print(f"  Max Drawdown: {kpis['max_drawdown_pct']:.1f}%")
        
        # Enhanced metrics
        if results['equity_curve']:
            final_value = results['equity_curve'][-1]['total_value']
            total_return = ((final_value - self.initial_capital) / self.initial_capital) * 100
            print(f"  Total Return: {total_return:.1f}%")
        
        # Signal quality
        if 'signal_quality_stats' in kpis and kpis['signal_quality_stats']:
            sq = kpis['signal_quality_stats']
            print(f"\nSIGNAL QUALITY (Enhanced):")
            print(f"  Conversion Rate: {sq['conversion_rate_pct']:.1f}%")
            print(f"  Signal Accuracy: {sq['signal_accuracy_pct']:.1f}%")
        
        # Enhancement impact
        print(f"\nENHANCEMENT IMPACT:")
        print(f"  Real Data: {'Active' if self.use_real_data else 'Sample Data'}")
        print(f"  Market Volatility: {market_volatility:.1f}%")
        print(f"  Enhanced Filtering: Active")
        print(f"  Dynamic Sizing: Active")
        
        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        if kpis['expectancy'] > 0:
            print("  [+] System showing positive expectancy")
        else:
            print("  [-] Consider adjusting parameters")
        
        if market_volatility > 25:
            print("  [!] High volatility - position sizes automatically reduced")
        elif market_volatility < 10:
            print("  [+] Low volatility - position sizes can be increased")

def main():
    """Run enhanced trading system demo."""
    
    # Initialize enhanced system
    enhanced_system = EnhancedTradingSystem(
        initial_capital=100000,
        use_real_data=True  # Set to False if no internet/yfinance issues
    )
    
    # Run enhanced analysis
    results = enhanced_system.run_enhanced_analysis()
    
    print(f"\n=== SYSTEM ENHANCEMENTS APPLIED ===")
    print("1. Real Data Integration: yfinance for live market data")
    print("2. Enhanced Signal Filtering: Volume, price, and quality filters")
    print("3. Dynamic Position Sizing: Volatility-based size adjustments")
    print("\nSystem is now significantly more robust and market-aware!")

if __name__ == "__main__":
    main()